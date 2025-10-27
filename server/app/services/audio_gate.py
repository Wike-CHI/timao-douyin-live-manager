"""
Lightweight audio gating to suppress background music and keep speech-like segments.

Heuristics (no ML):
- Band energy ratios: voice band (300–3400 Hz) vs. low/high bands
- Spectral centroid/flatness to detect overly tonal/noisy content
- Envelope modulation energy (2–8 Hz) typical for human speech syllabic rate

Returns True if segment is likely human speech; False if likely background music.
"""
from __future__ import annotations

import math
from typing import Tuple

import numpy as np


def _stft_mag(y: np.ndarray, n_fft: int = 512, hop: int = 160, win: int = 400) -> np.ndarray:
    """Compute magnitude STFT for mono PCM float32 in [-1,1]."""
    if y.ndim != 1:
        y = y.reshape(-1)
    # Hann window
    w = np.hanning(win).astype(np.float32)
    # Pad to center
    pad = win // 2
    ypad = np.pad(y, (pad, pad), mode="reflect")
    frames = (len(ypad) - win) // hop + 1
    if frames <= 0:
        return np.empty((0, n_fft // 2 + 1), dtype=np.float32)
    out = np.empty((frames, n_fft // 2 + 1), dtype=np.float32)
    for i in range(frames):
        s = i * hop
        frame = ypad[s : s + win]
        if frame.shape[0] < win:
            frame = np.pad(frame, (0, win - frame.shape[0]))
        spec = np.fft.rfft(frame * w, n=n_fft)
        out[i] = np.abs(spec).astype(np.float32)
    return out


def _band_energy(mag: np.ndarray, sr: int, f_lo: float, f_hi: float) -> float:
    n_fft = (mag.shape[1] - 1) * 2
    freqs = np.linspace(0, sr / 2.0, mag.shape[1])
    mask = (freqs >= f_lo) & (freqs < f_hi)
    if not np.any(mask):
        return 0.0
    return float(np.sum(mag[:, mask] ** 2))


def _spectral_centroid(mag: np.ndarray, sr: int) -> float:
    freqs = np.linspace(0, sr / 2.0, mag.shape[1], dtype=np.float32)
    num = (mag * freqs).sum(axis=1)
    den = (mag + 1e-8).sum(axis=1)
    c = num / den
    return float(np.clip(np.median(c), 0.0, sr / 2.0))


def _spectral_flatness(mag: np.ndarray) -> float:
    # median over frames of per-frame geometric mean / arithmetic mean
    with np.errstate(divide="ignore", invalid="ignore"):
        gm = np.exp(np.mean(np.log(mag + 1e-8), axis=1))
        am = np.mean(mag + 1e-8, axis=1)
        sf = gm / (am + 1e-12)
    return float(np.clip(np.median(sf), 1e-6, 1.0))


def _envelope_modulation(y: np.ndarray, sr: int) -> float:
    """Compute ratio of envelope modulation energy in 2–8 Hz over 0–20 Hz."""
    # Short RMS over 20 ms frames => envelope at 50 Hz sampling
    hop = int(sr * 0.02)
    if hop <= 0:
        return 0.0
    n = max(1, len(y) // hop)
    env = np.empty(n, dtype=np.float32)
    for i in range(n):
        s = i * hop
        e = min(len(y), s + hop)
        seg = y[s:e]
        env[i] = float(np.sqrt(np.mean(seg * seg) + 1e-12))
    # Detrend
    env = env - np.mean(env)
    spec = np.fft.rfft(env)
    freqs = np.fft.rfftfreq(len(env), d=0.02)
    pwr = (spec.real ** 2 + spec.imag ** 2)
    band_2_8 = np.logical_and(freqs >= 2.0, freqs <= 8.0)
    band_0_20 = freqs <= 20.0
    e28 = float(np.sum(pwr[band_2_8]))
    e020 = float(np.sum(pwr[band_0_20]) + 1e-12)
    return e28 / e020


def is_speech_like(pcm16: bytes, sr: int = 16000) -> Tuple[bool, dict]:
    """Return (keep, debug) where keep=True indicates human speech-like segment.

    Enhanced thresholds for better background music suppression and voice detection.
    """
    if not pcm16 or len(pcm16) == 0:
        return False, {"reason": "empty"}
    y = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    if y.size < sr * 0.1:
        return False, {"reason": "too_short"}
    rms = float(np.sqrt(np.mean(y * y) + 1e-12))
    if rms < 0.003:  # 降低RMS阈值，提高对轻声说话的敏感度
        return False, {"reason": "too_quiet", "rms": rms}

    mag = _stft_mag(y, n_fft=512, hop=160, win=400)
    if mag.shape[0] == 0:
        return False, {"reason": "no_frames"}

    # Band energies
    e_low = _band_energy(mag, sr, 0, 300)
    e_voice = _band_energy(mag, sr, 300, 3400)
    e_high = _band_energy(mag, sr, 3400, sr / 2)
    et = e_low + e_voice + e_high + 1e-12
    r_voice = e_voice / et
    r_high = e_high / et
    r_low = e_low / et

    # Spectral stats
    centroid = _spectral_centroid(mag, sr)
    flatness = _spectral_flatness(mag)
    mod = _envelope_modulation(y, sr)

    # Enhanced heuristics for better music suppression
    # 1. 人声频带要求（进一步放宽，优先保证语音通过）
    voice_dominant = r_voice >= 0.30  # 进一步降低要求，确保语音不被误过滤
    
    # 2. 频谱质心范围（扩大范围适应更多语音特征）
    centroid_human = 150 <= centroid <= 3500  # 进一步扩大范围，适应更多语音类型
    
    # 3. 调制能量检测（进一步降低要求）
    modulation_present = mod >= 0.05  # 进一步降低要求，适应轻声语音
    
    # 4. 频谱平坦度要求（进一步放宽）
    flatness_ok = flatness <= 0.8  # 进一步放宽，避免过度抑制
    
    # 5. 低频能量抑制（进一步放宽）
    low_freq_ok = r_low <= 0.60  # 进一步放宽，适应低音语音
    
    # 6. 高频能量检查（进一步放宽范围）
    high_freq_ok = 0.000001 <= r_high <= 0.70  # 进一步放宽上限
    
    # 7. 音乐特征检测（保持较高阈值，精确识别强音乐特征）
    harmonic_strength = _detect_harmonic_structure(mag, sr)
    music_like = harmonic_strength > 0.75  # 适度降低，但仍保持较高标准
    
    # 8. 节拍检测（保持较高阈值，精确识别强节拍）
    beat_regularity = _detect_beat_regularity(y, sr)
    regular_beat = beat_regularity > 0.65  # 适度降低，但仍保持较高标准
    
    # 综合判断：基础条件满足且没有强音乐特征
    basic_speech_criteria = (
        voice_dominant and 
        centroid_human and 
        modulation_present and 
        flatness_ok and 
        low_freq_ok and 
        high_freq_ok
    )
    
    # 音乐排除条件：只有在检测到强音乐特征时才排除
    strong_music_features = music_like or regular_beat
    
    # 最终判断：满足基础语音条件且没有强音乐特征
    keep = basic_speech_criteria and not strong_music_features
    
    dbg = {
        "rms": rms,
        "r_voice": r_voice,
        "r_high": r_high,
        "r_low": r_low,
        "centroid": centroid,
        "flatness": flatness,
        "mod": mod,
        "harmonic_strength": harmonic_strength,
        "beat_regularity": beat_regularity,
        "voice_dominant": voice_dominant,
        "centroid_human": centroid_human,
        "modulation_present": modulation_present,
        "flatness_ok": flatness_ok,
        "low_freq_ok": low_freq_ok,
        "high_freq_ok": high_freq_ok,
        "music_like": music_like,
        "regular_beat": regular_beat,
        "basic_speech_criteria": basic_speech_criteria,
        "strong_music_features": strong_music_features,
    }
    return bool(keep), dbg


def _detect_harmonic_structure(mag: np.ndarray, sr: int) -> float:
    """检测谐波结构强度，音乐通常有强谐波结构"""
    if mag.shape[0] == 0:
        return 0.0
    
    # 计算频谱的峰值
    freqs = np.linspace(0, sr / 2.0, mag.shape[1], dtype=np.float32)
    avg_mag = np.mean(mag, axis=0)
    
    # 寻找峰值
    peaks = []
    for i in range(1, len(avg_mag) - 1):
        if avg_mag[i] > avg_mag[i-1] and avg_mag[i] > avg_mag[i+1]:
            if avg_mag[i] > np.mean(avg_mag) * 1.5:  # 只考虑显著峰值
                peaks.append((freqs[i], avg_mag[i]))
    
    if len(peaks) < 2:
        return 0.0
    
    # 检查谐波关系
    peaks.sort(key=lambda x: x[1], reverse=True)  # 按幅度排序
    fundamental_candidates = peaks[:3]  # 取前3个最强峰值作为基频候选
    
    max_harmonic_score = 0.0
    for fund_freq, fund_amp in fundamental_candidates:
        if fund_freq < 50:  # 基频太低，跳过
            continue
            
        harmonic_score = 0.0
        harmonic_count = 0
        
        # 检查2-6次谐波
        for h in range(2, 7):
            target_freq = fund_freq * h
            if target_freq > sr / 2:
                break
                
            # 在目标频率附近寻找峰值
            tolerance = fund_freq * 0.1  # 10%容差
            for peak_freq, peak_amp in peaks:
                if abs(peak_freq - target_freq) < tolerance:
                    harmonic_score += peak_amp / fund_amp
                    harmonic_count += 1
                    break
        
        if harmonic_count > 0:
            avg_harmonic_strength = harmonic_score / harmonic_count
            max_harmonic_score = max(max_harmonic_score, avg_harmonic_strength)
    
    return float(np.clip(max_harmonic_score, 0.0, 1.0))


def _detect_beat_regularity(y: np.ndarray, sr: int) -> float:
    """检测节拍规律性，音乐通常有规律节拍"""
    if len(y) < sr:  # 至少需要1秒音频
        return 0.0
    
    # 计算包络
    hop_length = 512
    frame_length = 1024
    
    # 简单的包络提取
    envelope = []
    for i in range(0, len(y) - frame_length, hop_length):
        frame = y[i:i + frame_length]
        envelope.append(np.sqrt(np.mean(frame ** 2)))
    
    envelope = np.array(envelope)
    if len(envelope) < 10:
        return 0.0
    
    # 计算包络的自相关
    envelope = envelope - np.mean(envelope)
    autocorr = np.correlate(envelope, envelope, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    
    if len(autocorr) < 10:
        return 0.0
    
    # 寻找周期性峰值
    autocorr = autocorr / (autocorr[0] + 1e-8)  # 归一化
    
    # 在合理的节拍范围内寻找峰值 (60-180 BPM)
    min_period = int(sr / hop_length * 60 / 180)  # 180 BPM对应的最小周期
    max_period = int(sr / hop_length * 60 / 60)   # 60 BPM对应的最大周期
    
    if max_period >= len(autocorr):
        max_period = len(autocorr) - 1
    
    if min_period >= max_period:
        return 0.0
    
    # 寻找最强的周期性
    max_periodicity = 0.0
    for i in range(min_period, max_period):
        if i < len(autocorr):
            max_periodicity = max(max_periodicity, autocorr[i])
    
    return float(np.clip(max_periodicity, 0.0, 1.0))

