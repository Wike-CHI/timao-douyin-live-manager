import React, { useEffect, useState } from 'react';
                          import { getServiceUrl } from '../../services/apiConfig';

const FASTAPI_BASE_URL = getServiceUrl('main');

const HOTWORDS_PLACEHOLDER = '{ "replace": { "正确词": ["变体1", "变体2"] } }';

const ToolsPage: React.FC = () => {
  const [busy, setBusy] = useState(false);
  const [hotwords, setHotwords] = useState<any>({ replace: {} });
  const [message, setMessage] = useState<string | null>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [polling, setPolling] = useState<any>(null);
  const [selfTest, setSelfTest] = useState<{ backendOk?: boolean; modelOk?: boolean; wsOk?: boolean; details?: string } | null>(null);
  const [cleanPreview, setCleanPreview] = useState<string[] | null>(null);
  const [autoReload, setAutoReload] = useState<boolean>(true);
  const [runtimeInfo, setRuntimeInfo] = useState<any>(null);
  const [forcedDevice, setForcedDevice] = useState<string>('auto');
  const [prepareLog, setPrepareLog] = useState<string>('');
  const [prepareBusy, setPrepareBusy] = useState<boolean>(false);

  const fetchHotwords = async () => {
    try {             
      const resp = await fetch(`${FASTAPI_BASE_URL}/api/nlp/hotwords`);
      const data = await resp.json();
      setHotwords(data || { replace: {} });
    } catch (e) {
      setMessage('热词获取失败');
    }
  };

  useEffect(() => {
    fetchHotwords();
    void fetchRuntimeInfo();
  }, []);

  const preload = async (sizes: string[]) => {
    try {
      setBusy(true);
      setMessage(null);
      const resp = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/preload_models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sizes }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error((data as any)?.detail || '预下载失败');
      setMessage(`模型预下载任务完成：${(data as any)?.data?.ok?.join(', ') || ''}`);
      await fetchModelStatus();
    } catch (e: any) {
      setMessage(e?.message || '预下载失败');
    } finally {
      setBusy(false);
    }
  };

  const fetchModelStatus = async () => {
    try {
      const resp = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/models`);
      const data = await resp.json();
      setModelStatus(data || null);
    } catch (_error) {}
  };

  const fetchRuntimeInfo = async () => {
    try {
      const info = await (window as any).electronAPI?.getRuntimeInfo();
      if (info?.success) {
        setRuntimeInfo(info.info || null);
        if (info.info?.env?.LIVE_FORCE_DEVICE != null) {
          setForcedDevice(info.info.env.LIVE_FORCE_DEVICE || 'auto');
        }
      }
    } catch (e) {
      console.error('runtime info failed', e);
    }
  };

  const runSelfTest = async () => {
    setSelfTest(null);
    setMessage(null);
    const res: any = { backendOk: false, modelOk: false, wsOk: false, details: '' };
    try {
      // 1) 后端健康
      const r1 = await fetch(`${FASTAPI_BASE_URL}/health`);
      res.backendOk = r1.ok;
      // 2) 模型与 VAD 健康
      const r2 = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/health`);
      const d2 = await r2.json().catch(() => ({}));
      res.modelOk = !!(d2?.success);
      res.details = `模型: ${d2?.assets?.model_present ? 'OK' : '缺失'} · VAD: ${d2?.assets?.vad_present ? 'OK' : '缺失'}`;
      // 3) WebSocket 连通性（ping/pong）
      await new Promise<void>((resolve) => {
        let done = false;
        try {
          const wsUrl = FASTAPI_BASE_URL.replace(/^http/i, 'ws').replace(/\/$/, '') + '/api/live_audio/ws';
          const ws = new WebSocket(wsUrl);
          const timer = setTimeout(() => {
            if (!done) { try { ws.close(); } catch (_error) {} done = true; resolve(); }
          }, 2000);
          ws.onopen = () => {
            try { ws.send(JSON.stringify({ type: 'ping' })); } catch (_error) {}
          };
          ws.onmessage = (ev) => {
            try {
              const m = JSON.parse(ev.data);
              if (m?.type === 'pong') { res.wsOk = true; }
            } catch (_error) {}
          };
          ws.onclose = () => { if (!done) { clearTimeout(timer); done = true; resolve(); } };
          ws.onerror = () => { if (!done) { clearTimeout(timer); done = true; resolve(); } };
        } catch (_error) { resolve(); }
      });
    } catch (e: any) {
      res.details = e?.message || String(e);
    } finally {
      setSelfTest(res);
    }
  };

  const startPolling = () => {
    if (polling) return;
    const id = setInterval(fetchModelStatus, 2000);
    setPolling(id);
  };
  const stopPolling = () => {
    if (polling) { clearInterval(polling); setPolling(null); }
  };

  useEffect(() => {
    fetchModelStatus();
    startPolling();
    return () => stopPolling();
  }, []);

  const saveHotwords = async () => {
    try {
      setBusy(true);
      setMessage(null);
      const resp = await fetch(`${FASTAPI_BASE_URL}/api/nlp/hotwords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hotwords || { replace: {} }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error((data as any)?.detail || '保存失败');
      setMessage('热词已保存');
    } catch (e: any) {
      setMessage(e?.message || '保存失败');
    } finally {
      setBusy(false);
    }
  };

  const importJson = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      setHotwords(data);
      setMessage('已载入文件，点击“保存热词”生效');
    } catch (_error) {
      setMessage('文件解析失败');
    }
  };

  return (
    <div className="space-y-6">
      <div className="timao-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🖥️</span>
            运行环境（Torch / 设备）
          </h3>
          <div className="flex items-center gap-3 text-xs timao-support-text">
            <label htmlFor="forced-device-select" className="cursor-pointer">
              强制设备
            </label>
            <select
              id="forced-device-select"
              className="timao-select"
              value={forcedDevice}
              onChange={async (e) => {
                const value = e.target.value;
                setForcedDevice(value);
                try {
                  await (window as any).electronAPI?.setRuntimeDevice(value === 'auto' ? '' : value);
                  await fetchRuntimeInfo();
                  setMessage(`已设置强制设备为 ${value}`);
                } catch (err: any) {
                  setMessage(err?.message || '设置失败');
                }
              }}
            >
              <option value="auto">自动</option>
              <option value="cpu">CPU</option>
              <option value="cuda:0">GPU (cuda:0)</option>
            </select>
            <button
              className="timao-outline-btn text-[10px] px-2 py-0.5"
              disabled={prepareBusy}
              onClick={async () => {
                try {
                  setPrepareBusy(true);
                  setPrepareLog('');
                  const res = await (window as any).electronAPI?.runPrepareTorch();
                  if (res?.success) {
                    setPrepareLog(res.output || '准备完成');
                    setMessage('GPU 依赖准备完成');
                  } else {
                    setPrepareLog(res?.output || '执行失败');
                    setMessage('GPU 依赖准备失败');
                  }
                  await fetchRuntimeInfo();
                } catch (err: any) {
                  setPrepareLog(String(err));
                  setMessage('执行 prepare:torch 失败');
                } finally {
                  setPrepareBusy(false);
                }
              }}
            >{prepareBusy ? '执行中…' : '准备 GPU 依赖'}</button>
          </div>
        </div>
        <div className="text-xs timao-support-text space-y-1">
          <div>{runtimeInfo ? `OS: ${runtimeInfo.platform} · Node ${runtimeInfo.node} · Electron ${runtimeInfo.electron}` : '尚未获取运行信息'}</div>
          <div>{runtimeInfo?.torch ? `Torch ${runtimeInfo.torch.version} · CUDA ${runtimeInfo.torch.cuda ? 'YES' : 'NO'}` : 'Torch 信息未检测'}</div>
          {prepareLog ? (
            <pre className="mt-2 max-h-[160px] overflow-y-auto bg-slate-50 border rounded p-2 text-[11px]">{prepareLog}</pre>
          ) : null}
        </div>
      </div>

      <div className="timao-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🧹</span>
            缓存清理（安全）
          </h3>
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-2 text-xs timao-support-text">
              <input type="checkbox" checked={autoReload} onChange={(e) => setAutoReload(e.target.checked)} />
              <span>清理后自动刷新</span>
            </label>
            <button
              className="timao-outline-btn"
              title="预览将删除的缓存"
              onClick={async () => {
                try {
                  setBusy(true); setMessage(null);
                  const r = await fetch(`${FASTAPI_BASE_URL}/api/tools/clean_caches/preview`).then(r=>r.json());
                  setCleanPreview(Array.isArray(r?.removed) ? r.removed : []);
                  setMessage('已生成预览，见下方列表');
                } catch (error) {
                  setMessage(error instanceof Error ? error.message : '预览失败');
                }
                finally { setBusy(false); }
              }}
            >预览</button>
            <button
              className="timao-primary-btn"
              title="删除 Vite/构建缓存、pytest/ruff 缓存和 Python 字节码；不影响源码和依赖"
              onClick={async () => {
                try {
                  setBusy(true); setMessage(null);
                  const r = await fetch(`${FASTAPI_BASE_URL}/api/tools/clean_caches?apply=true`, { method: 'POST' }).then(r=>r.json());
                  setCleanPreview(Array.isArray(r?.removed) ? r.removed : []);
                  setMessage('清理完成');
                  if (autoReload) {
                    setTimeout(() => {
                      try {
                        window.location.reload();
                      } catch (_error) {}
                    }, 600);
                  }
                } catch (error) {
                  setMessage(error instanceof Error ? error.message : '清理失败');
                }
                finally { setBusy(false); }
              }}
            >一键清理</button>
          </div>
        </div>
        {cleanPreview && (
          <div className="rounded-xl border bg-white/80 p-3 max-h-[200px] overflow-y-auto">
            {cleanPreview.length === 0 ? (
              <div className="text-sm timao-support-text">暂无可清理项</div>
            ) : (
              <ul className="list-disc pl-5 text-xs text-slate-600">
                {cleanPreview.map((p, i) => (<li key={`${p}-${i}`}>{p}</li>))}
              </ul>
            )}
          </div>
        )}
        <div className="text-xs timao-support-text mt-2">只删除已知缓存与构建产物（Vite/pytest/ruff/__pycache__/pyc），不会删除源码、依赖、数据。</div>
      </div>
      <div className="timao-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🧪</span>
            自检 · 前后端 + 模型（Small+VAD）
          </h3>
          <button className="timao-primary-btn" onClick={runSelfTest} disabled={busy}>一键自检</button>
        </div>
        <div className="grid gap-2 md:grid-cols-3 text-sm">
          <div className="rounded-xl border p-3 bg-white/90">
            <div className="text-slate-500">后端连接</div>
            <div className={`mt-1 font-semibold ${selfTest?.backendOk ? 'text-emerald-600' : 'text-slate-400'}`}>{selfTest?.backendOk ? '可用' : '未检测'}</div>
          </div>
          <div className="rounded-xl border p-3 bg-white/90">
            <div className="text-slate-500">模型与VAD</div>
            <div className={`mt-1 font-semibold ${selfTest?.modelOk ? 'text-emerald-600' : 'text-slate-400'}`}>{selfTest?.modelOk ? '就绪' : '未检测'}</div>
            <div className="text-xs timao-support-text mt-1 truncate" title={selfTest?.details || ''}>{selfTest?.details || ''}</div>
          </div>
          <div className="rounded-xl border p-3 bg-white/90">
            <div className="text-slate-500">WebSocket</div>
            <div className={`mt-1 font-semibold ${selfTest?.wsOk ? 'text-emerald-600' : 'text-slate-400'}`}>{selfTest?.wsOk ? '可用' : '未检测'}</div>
          </div>
        </div>
        <div className="text-xs timao-support-text mt-2">说明：检测后端健康、模型与VAD资源、以及 WS ping/pong（无需开始转写）。</div>
      </div>
      <div className="timao-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🧠</span>
            识别引擎 · 模型管理
          </h3>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className="timao-primary-btn" onClick={() => preload(['small'])} disabled={busy}>预下载 · 轻量（Small）</button>
        </div>
        <div className="text-xs timao-support-text mt-2">提示：首次下载可能较慢，建议提前完成以免影响直播。</div>
        <div className="mt-3 rounded-xl border bg-white/80 p-3">
          <div className="text-sm font-medium text-slate-600 mb-2">缓存状态</div>
          <div className="grid gap-2 md:grid-cols-1 text-xs timao-support-text">
            {['small'].map(sz => {
              const st = modelStatus?.cache?.[sz];
              const busy = (modelStatus?.busy || []).includes(sz);
              return (
                <div key={sz} className="rounded-lg border p-2">
                  <div className="font-semibold text-slate-700 mb-1">{sz.toUpperCase()}</div>
                  <div>状态：{busy ? '下载中…' : (st?.cached ? '已下载' : '未下载')}</div>
                  <div>大小：{st?.bytes ? `${(st.bytes/1024/1024).toFixed(1)} MB` : '—'}</div>
                  <div className="truncate" title={st?.path || ''}>位置：{st?.path || '—'}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="timao-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🔤</span>
            热词管理（品牌/人名/地名等）
          </h3>
        </div>
        <div className="flex items-center gap-3 mb-3">
          <label htmlFor="hotwords-file" className="text-sm font-medium timao-support-text">
            导入热词 JSON
          </label>
          <input
            id="hotwords-file"
            type="file"
            accept="application/json"
            aria-describedby="hotwords-file-help"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                void importJson(file);
              }
            }}
          />
          <button className="timao-primary-btn" onClick={saveHotwords} disabled={busy}>保存热词</button>
          <button className="timao-outline-btn" onClick={async () => {
            try {
              setBusy(true); setMessage(null);
              const resp = await fetch(`${FASTAPI_BASE_URL}/api/nlp/hotwords/reset`, { method: 'POST' });
              const data = await resp.json();
              if (!resp.ok) throw new Error((data as any)?.detail || '重置失败');
              setMessage('已恢复默认热词');
              fetchHotwords();
            } catch (e: any) {
              setMessage(e?.message || '重置失败');
            } finally { setBusy(false); }
          }} disabled={busy}>恢复默认</button>
          <button className="timao-outline-btn" onClick={fetchHotwords} disabled={busy}>刷新</button>
        </div>
        <div id="hotwords-file-help" className="text-xs timao-support-text mb-2">可直接编辑 JSON：正确词 → 变体列表</div>
        <textarea
          id="hotwords-json-editor"
          className="timao-input w-full h-64 font-mono text-xs"
          aria-label="热词JSON编辑器"
          title="热词JSON"
          placeholder={HOTWORDS_PLACEHOLDER}
          value={JSON.stringify(hotwords, null, 2)}
          onChange={(e) => {
            try {
              const v = JSON.parse(e.target.value);
              setHotwords(v);
            } catch (_error) {
              // ignore until valid
            }
          }}
        />
      </div>

      {message ? (
        <div className="rounded-xl border border-purple-200 bg-purple-50 px-4 py-3 text-sm text-purple-700">{message}</div>
      ) : null}
    </div>
  );
};

export default ToolsPage;
