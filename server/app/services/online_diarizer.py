"""
Lightweight online diarizer (no heavy embeddings):
- Extract simple spectral features per segment (band energy ratios, centroid, flatness)
- Online k-means (up to max_speakers) over segment-level features
- "Host" assignment: the first stable cluster observed in the initial enrollment seconds

This is a heuristic diarizer; it's not robust as x-vector/pyannote, but works as a
quick, no-download solution suitable for 1-2 main speakers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .audio_gate import _stft_mag, _band_energy, _spectral_centroid, _spectral_flatness


@dataclass
class Cluster:
    id: int
    center: np.ndarray
    count: int = 1
    total_dur: float = 0.0


@dataclass
class DiarizerState:
    clusters: Dict[int, Cluster] = field(default_factory=dict)
    next_id: int = 0
    host_cluster: Optional[int] = None
    enrolled_sec: float = 0.0


class OnlineDiarizer:
    def __init__(self, sr: int = 16000, max_speakers: int = 2, enroll_sec: float = 4.0, smooth: float = 0.2, single_speaker_mode: bool = False) -> None:
        self.sr = sr
        self.max_speakers = max(1, int(max_speakers))
        self.enroll_sec = max(0.0, float(enroll_sec))
        self.smooth = float(smooth)
        self.single_speaker_mode = single_speaker_mode
        self.state = DiarizerState()
        
        # 调整聚类阈值：单人模式使用更高的阈值，减少过度分割
        self.cluster_threshold = 1.2 if single_speaker_mode else 0.8

    def _feat(self, pcm16: bytes) -> np.ndarray:
        y = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
        mag = _stft_mag(y, n_fft=512, hop=160, win=400)
        if mag.shape[0] == 0:
            return np.zeros(6, dtype=np.float32)
        e_low = _band_energy(mag, self.sr, 0, 300)
        e_voice = _band_energy(mag, self.sr, 300, 3400)
        e_high = _band_energy(mag, self.sr, 3400, self.sr / 2)
        et = e_low + e_voice + e_high + 1e-12
        r_voice = e_voice / et
        r_high = e_high / et
        c = _spectral_centroid(mag, self.sr)
        f = _spectral_flatness(mag)
        # Add simple temporal stats
        rms = float(np.sqrt(np.mean(y * y) + 1e-12))
        dur = float(len(y) / self.sr)
        return np.array([r_voice, r_high, c / 4000.0, f, rms, min(1.0, dur / 3.0)], dtype=np.float32)

    def _dist(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(a - b))

    def _assign(self, x: np.ndarray) -> int:
        if not self.state.clusters:
            cid = self.state.next_id
            self.state.next_id += 1
            self.state.clusters[cid] = Cluster(cid, x.copy())
            return cid
        
        # 单人模式：强制使用第一个聚类，不创建新聚类
        if self.single_speaker_mode and len(self.state.clusters) >= 1:
            # 总是返回第一个聚类ID
            first_cid = min(self.state.clusters.keys())
            c = self.state.clusters[first_cid]
            c.center = (1.0 - self.smooth) * c.center + self.smooth * x
            c.count += 1
            return first_cid
        
        # find nearest cluster
        best_cid = None
        best_d = 1e9
        for cid, c in self.state.clusters.items():
            d = self._dist(x, c.center)
            if d < best_d:
                best_d = d
                best_cid = cid
        
        # threshold: if too far and we can add a new cluster
        # 使用动态阈值，单人模式使用更高的阈值
        if (best_d > self.cluster_threshold) and (len(self.state.clusters) < self.max_speakers):
            cid = self.state.next_id
            self.state.next_id += 1
            self.state.clusters[cid] = Cluster(cid, x.copy())
            return cid
        # update nearest
        assert best_cid is not None
        c = self.state.clusters[best_cid]
        c.center = (1.0 - self.smooth) * c.center + self.smooth * x
        c.count += 1
        return best_cid

    def feed(self, pcm16: bytes, seg_sec: float) -> Tuple[str, Dict[str, float]]:
        """Feed a segment; return (label, debug) where label in {host, guest, spk<N>}.
        seg_sec: duration seconds (for accounting)
        """
        x = self._feat(pcm16)
        cid = self._assign(x)
        # accounting
        self.state.clusters[cid].total_dur += float(seg_sec)
        self.state.enrolled_sec += float(seg_sec)
        
        # 单人模式：直接设置第一个聚类为主播
        if self.single_speaker_mode:
            if self.state.host_cluster is None:
                self.state.host_cluster = cid
            # 单人模式下始终返回主播标签
            label = "host"
        else:
            # 多人模式：原有逻辑
            # host selection during enrollment window: the first stable cluster
            if self.state.host_cluster is None and self.state.enrolled_sec <= self.enroll_sec:
                # pick cluster with largest total_dur so far
                if self.state.clusters[cid].total_dur >= 1.0:  # at least 1 sec observed
                    self.state.host_cluster = cid
            # label mapping
            if self.state.host_cluster is None:
                label = f"spk{cid}"
            else:
                if cid == self.state.host_cluster:
                    label = "host"
                else:
                    # assign guest if second most dominant
                    label = "guest"
        
        dbg = {
            "cluster": float(cid),
            "host_cluster": float(self.state.host_cluster) if self.state.host_cluster is not None else -1.0,
            "clusters": float(len(self.state.clusters)),
            "single_speaker_mode": self.single_speaker_mode,
            "cluster_threshold": self.cluster_threshold,
        }
        return label, dbg

    def total_observed_sec(self) -> float:
        """Return cumulative observed audio duration (seconds)."""
        return float(self.state.enrolled_sec)

    def is_ready(self, warmup_sec: Optional[float] = None) -> bool:
        """Return True once the diarizer has seen enough speech to separate speakers."""
        threshold = self.enroll_sec if warmup_sec is None else float(warmup_sec)
        return self.state.enrolled_sec >= max(0.0, threshold)
