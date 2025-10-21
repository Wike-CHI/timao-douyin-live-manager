# Live Audio Tuning Cheatsheet

This note collects the knobs introduced for SenseVoice Small + VAD so ops engineers can adapt to noisy livestreams without editing code.

## VAD And Chunking

- `LIVE_VAD_CHUNK_SEC` (0.2-2.0, default = profile preset)  
  Controls the FFT chunk size that feeds the ASR.
- `LIVE_VAD_MIN_RMS` (0.001-0.2, default = profile preset)  
  Raise this when background music is loud; lower it for very quiet presenters.
- `LIVE_VAD_MIN_SPEECH_SEC` / `LIVE_VAD_MIN_SILENCE_SEC` (0.2-2.5)  
  *Increase* both to reduce "行行行" style short snippets; decrease for ultra-low latency.
- `LIVE_VAD_HANGOVER_SEC` (0.1-1.5)  
  How long we keep buffering after energy drops, useful for preserving sentence endings.
- `LIVE_VAD_FORCE_FLUSH_SEC` (2.0-15.0) & `LIVE_VAD_FORCE_FLUSH_OVERLAP` (0.0-1.5)  
  Force emit long speech stretches; shrink the flush interval for faster turnaround.
- `LIVE_VAD_MIN_SENTENCE_CHARS` (0-128)  
  Hard floor before we treat a final chunk as “too short” and keep it as a partial delta.

All overrides are read at service start. Changing a profile (`fast` / `stable`) re-applies the env-based overrides automatically.

## Diarizer Behaviour

- `LIVE_DIARIZER_MAX_SPEAKERS` (1-4, default 2)  
  Higher values let the heuristic cluster more guests but need extra warm-up audio.
- `LIVE_DIARIZER_ENROLL_SEC` (1-20, default 4.0)  
  Amount of speech required before the first “host” cluster is locked in.
- `LIVE_DIARIZER_WARMUP_SEC` (0-20, default = 75% of `enroll_sec`)  
  Until we reach this many seconds of observed speech, `last_speaker` stays `unknown`.
- `LIVE_DIARIZER_SMOOTH` (0.05-0.6, default 0.2)  
  Larger values make cluster centroids adapt faster to new voices (but add jitter).

Remember to restart the FastAPI process after tweaking these env variables so the diarizer is re-instantiated.

## Text Noise Filter

- `LIVE_TEXT_NOISE_FILTER` (0/1, default 1) toggles the new short-text filter.
- `LIVE_TEXT_NOISE_MIN_CHARS` (1-12, default 3)  
  Sentences made only of filler characters under this length will be dropped.
- `LIVE_TEXT_NOISE_REPEAT` (2-10, default 3)  
  If all characters repeat beyond this limit (e.g. "行行行行行"), the segment is discarded.

Filtered segments are not persisted and never reach the Electron UI, reducing clutter such as "嗯嗯嗯" or pure laughter.
