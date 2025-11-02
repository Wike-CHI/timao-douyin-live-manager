
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { startLiveReport, stopLiveReport, getLiveReportStatus, generateLiveReport } from '../../services/liveReport';
import type { ReviewData, ReportArtifacts } from '../../services/liveReport';
import ReviewReportPage from './ReviewReportPage';

type Metrics = {
  follows?: number;
  entries?: number;
  peak_viewers?: number;
  like_total?: number;
  gifts?: Record<string, number>;
};

const FASTAPI_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9019';

const ReportsPage: React.FC = () => {
  const [liveInput, setLiveInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [artifacts, setArtifacts] = useState<ReportArtifacts | null>(null);
  const [showReview, setShowReview] = useState(false);
  const [hasStopped, setHasStopped] = useState(false); // 标记是否已停止录制
  const [historyReports, setHistoryReports] = useState<any[]>([]); // 历史报告列表
  const [showHistory, setShowHistory] = useState(false); // 是否显示历史记录
  const pollTimerRef = useRef<any>(null);

  const isActive = !!status;
  const hasRecordedSession = hasStopped && !artifacts; // 有已停止但未生成报告的会话
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
      setHasStopped(false); // 重置停止状态
      setArtifacts(null); // 清空之前的报告
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
      setHasStopped(true); // 标记已停止
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
      setHasStopped(false); // 生成报告后重置状态
      
      // 🆕 刷新历史报告列表
      await loadHistory();
      
      // 如果有复盘数据，自动展示复盘页面
      if (res?.data?.review_data) {
        setShowReview(true);
      }
    } catch (e: any) {
      setError(e?.message || '生成报告失败');
    } finally {
      setBusy(false);
    }
  };

  const viewReview = async (reportPath: string) => {
    try {
      setBusy(true); setError(null);
      // 调用新的 API 接口加载历史报告
      const encodedPath = encodeURIComponent(reportPath);
      const res = await fetch(`${FASTAPI_BASE_URL}/api/report/live/review/${encodedPath}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data?.data?.review_data) {
        // 更新 artifacts 的 review_data 并展示
        setArtifacts(prev => ({
          ...(prev || {}),
          review_data: data.data.review_data
        }));
        setShowReview(true);
      } else {
        throw new Error('复盘数据格式错误');
      }
    } catch (e: any) {
      setError(e?.message || '加载复盘数据失败');
    } finally {
      setBusy(false);
    }
  };

  // 加载历史报告列表
  const loadHistory = async () => {
    try {
      const res = await fetch(`${FASTAPI_BASE_URL}/api/live/review/list/recent?limit=20`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data?.success && data?.data) {
        // 🆕 过滤掉测试报告（room_id 包含 test 的）
        const filteredReports = data.data.filter((report: any) => {
          const isTestModel = report.ai_model === 'test-model';
          const isTestRoom = report.room_id && report.room_id.toLowerCase().includes('test');
          return !isTestModel && !isTestRoom;
        });
        setHistoryReports(filteredReports);
      }
    } catch (e: any) {
      console.error('加载历史报告失败:', e);
    }
  };

  // 删除历史报告
  const deleteHistoryReport = async (reportId: number) => {
    if (!confirm('确定要删除这个报告吗？删除后无法恢复。')) {
      return;
    }
    
    try {
      setBusy(true); setError(null);
      const res = await fetch(`${FASTAPI_BASE_URL}/api/live/review/${reportId}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `HTTP ${res.status}`);
      }
      // 删除成功后刷新列表
      await loadHistory();
      setError(null);
    } catch (e: any) {
      setError(e?.message || '删除报告失败');
    } finally {
      setBusy(false);
    }
  };

  // 根据报告ID查看历史报告
  const viewHistoryReport = async (reportId: number) => {
    try {
      setBusy(true); setError(null);
      // 获取报告详情（使用新的 API）
      const res = await fetch(`${FASTAPI_BASE_URL}/api/live/review/report/${reportId}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data?.success && data?.data) {
        // 构造 ReviewData 格式
        const reportData = data.data;
        const reviewData: ReviewData = {
          session_id: reportData.session_id,
          room_id: reportData.session?.room_id,
          anchor_name: reportData.session?.title || reportData.session?.room_id, // 使用 title 或 room_id
          started_at: reportData.session?.started_at ? new Date(reportData.session.started_at).getTime() : undefined,
          ended_at: reportData.session?.ended_at ? new Date(reportData.session.ended_at).getTime() : undefined,
          duration_seconds: reportData.session?.duration,
          comments_count: reportData.session?.comment_count || 0,
          transcript: '', // 历史报告没有原始转写文本
          ai_summary: {
            overall_score: reportData.overall_score,
            performance_analysis: reportData.performance_analysis,
            key_highlights: reportData.key_highlights,
            key_issues: reportData.key_issues,
            improvement_suggestions: reportData.improvement_suggestions,
            gemini_metadata: {
              model: reportData.ai_model,
              cost: reportData.generation_cost,
              tokens: reportData.generation_tokens,
              duration: reportData.generation_duration
            }
          },
          metrics: {
            total_viewers: reportData.session?.total_viewers,
            peak_viewers: reportData.session?.peak_viewers,
            comment_count: reportData.session?.comment_count
          },
          // 重要：添加 trend_charts 数据
          trend_charts: reportData.trend_charts
        };
        
        setArtifacts({ review_data: reviewData });
        setShowReview(true);
        setShowHistory(false); // 关闭历史列表
      } else {
        throw new Error('报告数据格式错误');
      }
    } catch (e: any) {
      setError(e?.message || '加载历史报告失败');
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

  useEffect(() => { 
    refresh(); 
    loadHistory(); // 加载历史记录
    return () => stopPolling(); 
  }, [refresh]);

  const giftList = useMemo(() => {
    const gifts = metrics?.gifts || {};
    return Object.entries(gifts).sort((a, b) => (b[1] as number) - (a[1] as number));
  }, [metrics]);

  // 如果正在展示历史记录列表
  if (showHistory) {
    return (
      <div className="space-y-6">
        <div className="timao-soft-card flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📚</div>
            <div>
              <div className="text-lg font-semibold text-purple-600">历史复盘报告</div>
              <div className="text-sm timao-support-text">最近 {historyReports.length} 条记录</div>
            </div>
          </div>
          <button
            className="timao-outline-btn px-4 py-2"
            onClick={() => setShowHistory(false)}
          >
            ← 返回
          </button>
        </div>

        {historyReports.length === 0 ? (
          <div className="timao-card text-center py-12">
            <div className="text-4xl mb-4">📭</div>
            <div className="text-gray-500">暂无历史报告</div>
            <div className="text-sm text-gray-400 mt-2">开始录制并生成报告后会显示在这里</div>
          </div>
        ) : (
          <div className="grid gap-4">
            {historyReports.map((report) => (
              <div key={report.id} className="timao-card hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">📊</span>
                      <div>
                        <div className="font-semibold text-purple-600">
                          {report.title || `房间 ${report.room_id}`}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(report.generated_at).toLocaleString('zh-CN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false
                          })}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      {report.overall_score !== undefined && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">评分:</span>
                          <span className="font-bold text-purple-600 text-lg">
                            {report.overall_score}/100
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">状态:</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          report.status === 'completed' 
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {report.status === 'completed' ? '已完成' : report.status}
                        </span>
                      </div>
                      {report.ai_model && (
                        <div className="text-xs text-gray-500">
                          🤖 {report.ai_model}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      className="timao-primary-btn px-6 py-2.5 flex items-center gap-2 disabled:opacity-50"
                      onClick={() => viewHistoryReport(report.id)}
                      disabled={busy}
                    >
                      {busy ? <span className="animate-spin">⏳</span> : <span>👁️</span>}
                      <span>查看报告</span>
                    </button>
                    <button
                      className="timao-outline-btn px-4 py-2.5 text-red-600 hover:bg-red-50 hover:border-red-300 flex items-center gap-2 disabled:opacity-50"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteHistoryReport(report.id);
                      }}
                      disabled={busy}
                      title="删除报告"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 如果正在展示复盘报告，渲染复盘页面
  if (showReview && artifacts?.review_data) {
    return (
      <ReviewReportPage
        reviewData={artifacts.review_data}
        onClose={() => setShowReview(false)}
      />
    );
  }

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
          <button
            className="timao-outline-btn px-4 py-2 flex items-center gap-2 hover:bg-purple-50 transition-colors"
            onClick={() => {
              loadHistory();
              setShowHistory(true);
            }}
            title="查看历史报告"
          >
            <span>📚</span>
            <span>历史记录</span>
            {historyReports.length > 0 && (
              <span className="ml-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                {historyReports.length}
              </span>
            )}
          </button>
          <input
            value={liveInput}
            onChange={(e) => setLiveInput(e.target.value)}
            className="timao-input w-72 text-sm"
            placeholder="直播地址或ID (https://live.douyin.com/xxxx)"
            disabled={isActive || busy || hasRecordedSession}
            aria-label="直播地址或ID"
            title="直播地址或ID"
          />
          <button 
            className="timao-primary-btn flex items-center gap-2 px-5 py-2 shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
            onClick={start} 
            disabled={busy || isActive || hasRecordedSession}
            title={hasRecordedSession ? "请先生成报告" : "开始录制"}
          >
            {busy ? <span className="animate-spin">⏳</span> : <span>🎬</span>}
            <span>开始录制</span>
          </button>
          <button 
            className="timao-outline-btn flex items-center gap-2 px-4 py-2 hover:bg-red-50 hover:border-red-300 hover:text-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
            onClick={stop} 
            disabled={busy || !isActive}
          >
            {busy ? <span className="animate-spin">⏳</span> : <span>⏹️</span>}
            <span>停止</span>
          </button>
          <button 
            className="timao-outline-btn flex items-center gap-2 px-4 py-2 hover:bg-green-50 hover:border-green-400 hover:text-green-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
            onClick={generate} 
            disabled={busy || !hasRecordedSession}
            title={hasRecordedSession ? "点击生成报告" : "请先录制并停止"}
          >
            {busy ? <span className="animate-spin">⏳</span> : <span>✨</span>}
            <span>生成报告</span>
          </button>
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
            <div className="flex items-center justify-between">
              <span>录制目录：{status?.recording_dir || '—'}</span>
              {status?.recording_dir && (
                <button 
                  className="timao-outline-btn text-xs px-3 py-1 ml-2 flex items-center gap-1 hover:bg-purple-50 transition-colors" 
                  onClick={() => { try { (window as any).electronAPI?.openPath(status.recording_dir as string); } catch {} }}
                >
                  <span>📂</span>
                  <span>打开</span>
                </button>
              )}
            </div>
          </div>
          {artifacts ? (
            <div className="mt-3 space-y-3">
              <div className="timao-soft-card text-xs timao-support-text space-y-1">
                <div>· 弹幕文件：{artifacts.comments || '—'}</div>
                <div>· 转写文本：{artifacts.transcript || '—'}</div>
                <div>· 报告文件：{artifacts.report || '—'}</div>
              </div>
              
              {artifacts.report && (
                <div className="flex items-center gap-3 pt-2">
                  <button 
                    className="timao-outline-btn text-sm px-4 py-2 flex items-center gap-2 hover:bg-purple-50 transition-colors" 
                    onClick={() => { try { (window as any).electronAPI?.openPath(artifacts.report as string); } catch {} }}
                  >
                    <span>📁</span>
                    <span>打开文件</span>
                  </button>
                  <button 
                    className="timao-primary-btn text-sm px-6 py-2.5 flex items-center gap-2 shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium" 
                    onClick={() => viewReview(artifacts.report as string)}
                    disabled={busy}
                  >
                    {busy ? <span className="animate-spin">⏳</span> : <span>🎯</span>}
                    <span>{busy ? '加载中...' : '查看 AI 复盘报告'}</span>
                  </button>
                </div>
              )}
            </div>
          ) : null}
          <div className="text-xs timao-support-text mt-2">说明：录制整场直播音频（分段），离线转写并汇总弹幕；调用 Gemini 2.5 Flash 生成 AI 复盘报告（超低成本，约 $0.0001/次）。</div>
        </section>
      </div>
    </div>
  );
};

export default ReportsPage;

