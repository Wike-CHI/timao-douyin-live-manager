import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { startLiveReport, stopLiveReport, getLiveReportStatus, generateLiveReport } from '../../services/liveReport';

type Metrics = {
  follows?: number;
  entries?: number;
  peak_viewers?: number;
  like_total?: number;
  gifts?: Record<string, number>;
};

const FASTAPI_BASE_URL = (import.meta.env?.VITE_FASTAPI_URL as string | undefined) || 'http://127.0.0.1:8090';

const ReportsPage: React.FC = () => {
  const [liveInput, setLiveInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [artifacts, setArtifacts] = useState<{ comments?: string; transcript?: string; report?: string } | null>(null);
  const pollTimerRef = useRef<any>(null);

  const isActive = !!status;
  const metrics: Metrics = status?.metrics || {};

  const start = async () => {
    try {
      setBusy(true); setError(null);
      const input = liveInput.trim();
      if (!input) throw new Error('请填写直播地址或直播间ID');
      const idMatch = input.match(/live\.douyin\.com\/([A-Za-z0-9_\-]+)/);
      const liveId = idMatch ? idMatch[1] : input;
      const liveUrl = idMatch ? input : `https://live.douyin.com/${liveId}`;
      await startLiveReport(liveUrl, 30, FASTAPI_BASE_URL);
      await refresh();
      startPolling();
    } catch (e: any) {
      setError(e?.message || '启动录制失败');
    } finally {
      setBusy(false);
    }
  };

  const stop = async () => {
    try {
      setBusy(true); setError(null);
      await stopLiveReport(FASTAPI_BASE_URL);
      await refresh();
      stopPolling();
    } catch (e: any) {
      setError(e?.message || '停止录制失败');
    } finally {
      setBusy(false);
    }
  };

  const generate = async () => {
    try {
      setBusy(true); setError(null);
      const res = await generateLiveReport(FASTAPI_BASE_URL);
      setArtifacts(res?.data || null);
    } catch (e: any) {
      setError(e?.message || '生成报告失败');
    } finally {
      setBusy(false);
    }
  };

  const refresh = useCallback(async () => {
    try {
      const r = await getLiveReportStatus(FASTAPI_BASE_URL);
      setStatus(r?.status || null);
    } catch { /* ignore */ }
  }, []);

  const startPolling = () => {
    if (pollTimerRef.current) return;
    pollTimerRef.current = setInterval(refresh, 2000);
  };
  const stopPolling = () => {
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
  };

  useEffect(() => { refresh(); return () => stopPolling(); }, [refresh]);

  const giftList = useMemo(() => {
    const gifts = metrics?.gifts || {};
    return Object.entries(gifts).sort((a, b) => (b[1] as number) - (a[1] as number));
  }, [metrics]);

  return (
    <div className="space-y-6">
      <div className="timao-soft-card flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <div className="text-4xl">🧾</div>
          <div>
            <div className="text-lg font-semibold text-purple-600">整场复盘 · 录制与报告</div>
            <div className="text-sm timao-support-text">{isActive ? '录制中' : '未开始'}</div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={liveInput}
            onChange={(e) => setLiveInput(e.target.value)}
            className="timao-input w-64 text-sm"
            placeholder="直播地址或ID (https://live.douyin.com/xxxx)"
            disabled={isActive || busy}
            aria-label="直播地址或ID"
            title="直播地址或ID"
          />
          <button className="timao-primary-btn" onClick={start} disabled={busy || isActive}>开始录制</button>
          <button className="timao-outline-btn" onClick={stop} disabled={busy || !isActive}>停止</button>
          <button className="timao-outline-btn" onClick={generate} disabled={busy}>生成报告</button>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] lg:grid-cols-[1fr_1fr]">
        <section className="timao-card">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-purple-600">直播数据</h3>
            <div className="text-xs timao-support-text">{status?.session_id || '—'}</div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="timao-soft-card">新增关注 <div className="text-lg font-semibold text-purple-600">{metrics?.follows ?? 0}</div></div>
            <div className="timao-soft-card">进场人数 <div className="text-lg font-semibold text-purple-600">{metrics?.entries ?? 0}</div></div>
            <div className="timao-soft-card">最高在线 <div className="text-lg font-semibold text-purple-600">{metrics?.peak_viewers ?? 0}</div></div>
            <div className="timao-soft-card">新增点赞 <div className="text-lg font-semibold text-purple-600">{metrics?.like_total ?? 0}</div></div>
          </div>
          <div className="mt-4">
            <div className="text-sm text-slate-500 mb-2">礼物统计</div>
            <div className="max-h-[220px] overflow-y-auto pr-1">
              {giftList.length === 0 ? (
                <div className="timao-outline-card text-xs timao-support-text">暂无礼物数据</div>
              ) : (
                <table className="w-full text-sm">
                  <thead><tr><th className="text-left">礼物</th><th className="text-left">数量</th></tr></thead>
                  <tbody>
                    {giftList.map(([name, cnt]) => (
                      <tr key={name}><td>{name}</td><td>{cnt as number}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </section>

        <section className="timao-card">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-purple-600">片段与产物</h3>
            <div className="text-xs timao-support-text">分段 {status?.segments?.length ?? 0} · 间隔 {Math.round((status?.segment_seconds ?? 0)/60)} 分钟</div>
          </div>
          <div className="timao-soft-card text-xs timao-support-text">
            <div>录制目录：{status?.recording_dir || '—'} {status?.recording_dir ? (
              <button className="timao-outline-btn text-[10px] px-2 py-0.5 ml-2" onClick={() => { try { (window as any).electronAPI?.openPath(status.recording_dir as string); } catch {} }}>打开</button>
            ) : null}</div>
          </div>
          {artifacts ? (
            <div className="mt-3 timao-soft-card text-xs timao-support-text">
              <div>· 弹幕：{artifacts.comments || '—'}</div>
              <div>· 转写：{artifacts.transcript || '—'}</div>
              <div className="flex items-center gap-2">· 报告：{artifacts.report || '—'} {artifacts.report ? (
                <button className="timao-outline-btn text-[10px] px-2 py-0.5" onClick={() => { try { (window as any).electronAPI?.openPath(artifacts.report as string); } catch {} }}>打开</button>
              ) : null}</div>
            </div>
          ) : null}
          <div className="text-xs timao-support-text mt-2">说明：录制整场直播音频（分段），离线转写并汇总弹幕；调用 Qwen3-Max 生成 AI 复盘报告。</div>
        </section>
      </div>
    </div>
  );
};

export default ReportsPage;

