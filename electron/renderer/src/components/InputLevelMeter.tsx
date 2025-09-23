import { useEffect, useRef, useState } from 'react';

// Lightweight input level meter using Web Audio API. It only runs in renderer,
// does not affect backend capture. The goal is to让用户直观看到是否在录到声音。

const clamp = (v: number, min = 0, max = 1) => Math.max(min, Math.min(max, v));

const InputLevelMeter = () => {
  const [level, setLevel] = useState(0);
  const rafRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    let audioCtx: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let source: MediaStreamAudioSourceNode | null = null;

    const start = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 1024;
        source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);
        const buf = new Uint8Array(analyser.frequencyBinCount);

        const tick = () => {
          if (!analyser) return;
          analyser.getByteTimeDomainData(buf);
          // Compute rough RMS in [0,1]
          let sum = 0;
          for (let i = 0; i < buf.length; i++) {
            const v = (buf[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / buf.length);
          setLevel(clamp(rms * 2));
          rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
      } catch (e) {
        // Ignore permission errors; meter will stay at 0
        console.warn('Mic meter unavailable:', e);
      }
    };

    start();
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks()?.forEach((t) => t.stop());
      if (audioCtx) audioCtx.close();
    };
  }, []);

  return (
    <div className="w-full flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-emerald-400 to-amber-400 transition-[width] duration-75"
          style={{ width: `${Math.round(level * 100)}%` }}
        />
      </div>
      <div className="text-xs text-slate-500 w-10 text-right">{Math.round(level * 100)}%</div>
    </div>
  );
};

export default InputLevelMeter;

