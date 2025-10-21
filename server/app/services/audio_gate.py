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

    Thresholds tuned empirically; may need adjustments per stream.
    """
    if not pcm16:
        return False, {"reason": "empty"}
    y = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    if y.size < sr * 0.1:
        return False, {"reason": "too_short"}
    rms = float(np.sqrt(np.mean(y * y) + 1e-12))
    if rms < 0.005:
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

    # Spectral stats
    centroid = _spectral_centroid(mag, sr)
    flatness = _spectral_flatness(mag)
    mod = _envelope_modulation(y, sr)

    # Heuristics
    # voice band should dominate; centroid in human region; modulation present; flatness not too high
    keep = (
        (r_voice >= 0.45) and (300 <= centroid <= 2200) and (mod >= 0.10) and (flatness <= 0.6)
    )
    dbg = {
        "rms": rms,
        "r_voice": r_voice,
        "r_high": r_high,
        "centroid": centroid,
        "flatness": flatness,
        "mod": mod,
    }
    return bool(keep), dbg

