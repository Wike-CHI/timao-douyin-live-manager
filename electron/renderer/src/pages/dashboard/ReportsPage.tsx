
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { 
  startLiveReport, 
  stopLiveReport, 
  pauseLiveReport, 
  resumeLiveReport, 
  getResumableSession, 
  getLiveReportStatus, 
  generateLiveReport 
} from '../../services/liveReport';
import type { ReviewData, ReportArtifacts } from '../../services/liveReport';
import ReviewReportPage from './ReviewReportPage';

type Metrics = {
  follows?: number;
  entries?: number;
  peak_viewers?: number;
  like_total?: number;
  gifts?: Record<string, number>;
};

const FASTAPI_BASE_URL = import.meta.env?.VITE_FASTAPI_URL as string || 'http://127.0.0.1:9030'; // 默认端口改为 9030，避免 Windows 端口排除范围 8930-9029

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
  // 🆕 恢复会话相关状态
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const [resumableSession, setResumableSession] = useState<any>(null);
  const pollTimerRef = useRef<any>(null);
  // 🆕 多选删除相关状态
  const [selectedReports, setSelectedReports] = useState<Set<string>>(new Set()); // 选中的报告session_id集合
  const [isSelectMode, setIsSelectMode] = useState(false); // 是否处于选择模式

  const isActive = !!status;
  const hasRecordedSession = hasStopped && !artifacts; // 有已停止但未生成报告的会话
  const isPaused = status?.status === 'paused'; // 🆕 是否处于暂停状态
  const isRecording = status?.status === 'recording'; // 🆕 是否正在录制
  const metrics: Metrics = status?.metrics || {};
  
  // 🆕 调试日志
  React.useEffect(() => {
    if (status) {
      console.log('📊 [ReportsPage] 当前 status 更新:', status);
      console.log('📊 [ReportsPage] 当前 metrics:', metrics);
      console.log('📊 [ReportsPage] follows:', metrics?.follows);
      console.log('📊 [ReportsPage] entries:', metrics?.entries);
    }
  }, [status, metrics]);

  // 🆕 计算已录制时长
  const getRecordedDuration = () => {
    if (!status) return '—';
    const startedAt = status.started_at;
    const now = Date.now();
    const pausedAt = status.paused_at;
    const stoppedAt = status.stopped_at;
    
    let durationMs = 0;
    if (isRecording) {
      // 正在录制中
      durationMs = now - startedAt;
    } else if (isPaused && pausedAt) {
      // 已暂停
      durationMs = pausedAt - startedAt;
    } else if (hasStopped && stoppedAt) {
      // 已停止
      durationMs = stoppedAt - startedAt;
    }
    
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}分${seconds}秒`;
  };

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
      // 🆕 开始新录制时清理所有状态
      setHasStopped(false);
      setArtifacts(null);
      setShowReview(false);
      setShowHistory(false);
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

  // 🆕 暂停录制
  const pause = async () => {
    try {
      setBusy(true); setError(null);
      await pauseLiveReport(FASTAPI_BASE_URL);
      await refresh();
      stopPolling(); // 暂停后停止轮询
      setError(null);
    } catch (e: any) {
      setError(e?.message || '暂停录制失败');
    } finally {
      setBusy(false);
    }
  };

  // 🆕 继续录制
  const resume = async () => {
    try {
      setBusy(true); setError(null);
      await resumeLiveReport(FASTAPI_BASE_URL);
      await refresh();
      startPolling(); // 继续后重新启动轮询
      setError(null);
    } catch (e: any) {
      setError(e?.message || '继续录制失败');
    } finally {
      setBusy(false);
    }
  };

  // 🆕 恢复会话(从暂停或录制状态恢复)
  const resumeSession = async () => {
    if (!resumableSession) return;
    
    try {
      setBusy(true); setError(null);
      setShowResumeDialog(false);
      
      // 如果会话是暂停状态,调用 resume API
      if (resumableSession.status === 'paused') {
        await resumeLiveReport(FASTAPI_BASE_URL);
        startPolling();
      } else {
        // 如果会话是录制状态(意外退出),只需刷新状态
        await refresh();
        startPolling();
      }
      
      setError(null);
    } catch (e: any) {
      setError(e?.message || '恢复会话失败');
      setShowResumeDialog(true); // 失败时重新显示对话框
    } finally {
      setBusy(false);
    }
  };

  // 🆕 放弃恢复会话
  const discardSession = async () => {
    if (!resumableSession) return;
    
    try {
      setBusy(true); setError(null);
      setShowResumeDialog(false);
      
      // 调用 stop API 清除会话
      await stopLiveReport(FASTAPI_BASE_URL);
      await refresh();
      
      setResumableSession(null);
      setError(null);
    } catch (e: any) {
      setError(e?.message || '清除会话失败');
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
      
      // 🆕 刷新历史报告列表（后台更新）
      await loadHistory();
      
      // 🆕 如果有复盘数据，直接展示复盘页面
      if (res?.data?.review_data) {
        setShowReview(true);
        setShowHistory(false);
        console.log('✅ 报告已生成，自动显示复盘页面');
      } else {
        // 如果没有复盘数据，跳转到历史记录
        setShowHistory(true);
        setShowReview(false);
        console.log('⚠️ 没有复盘数据，跳转到历史记录');
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
      console.log('🔍 [loadHistory] 开始加载历史记录...');
      console.log('🔍 [loadHistory] API URL:', `${FASTAPI_BASE_URL}/api/report/live/history?limit=20`);
      
      // 🆕 改为调用基于本地文件系统的 API
      const res = await fetch(`${FASTAPI_BASE_URL}/api/report/live/history?limit=20`);
      console.log('🔍 [loadHistory] 响应状态:', res.status, res.statusText);
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('❌ [loadHistory] API错误:', errorText);
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }
      
      const data = await res.json();
      console.log('📚 [loadHistory] 原始响应数据:', data);
      console.log('📚 [loadHistory] data.success:', data?.success);
      console.log('📚 [loadHistory] data.data类型:', Array.isArray(data?.data) ? 'Array' : typeof data?.data);
      console.log('📚 [loadHistory] data.data长度:', data?.data?.length);
      
      if (data?.success && data?.data) {
        // 🆕 过滤掉测试报告（room_id 包含 test 的）
        const filteredReports = data.data.filter((report: any) => {
          const isTestModel = report.ai_model === 'test-model';
          const isTestRoom = report.room_id && report.room_id.toLowerCase().includes('test');
          const shouldFilter = isTestModel || isTestRoom;
          if (shouldFilter) {
            console.log('🔍 [loadHistory] 过滤掉测试报告:', report.session_id);
          }
          return !shouldFilter;
        });
        console.log('📚 [loadHistory] 过滤前数量:', data.data.length);
        console.log('📚 [loadHistory] 过滤后数量:', filteredReports.length);
        console.log('📚 [loadHistory] 设置历史记录状态...');
        setHistoryReports(filteredReports);
        console.log('✅ [loadHistory] 历史记录加载完成');
      } else {
        console.warn('⚠️ [loadHistory] 数据格式不正确:', { success: data?.success, hasData: !!data?.data });
      }
    } catch (e: any) {
      console.error('❌ [loadHistory] 加载历史报告失败:', e);
      console.error('❌ [loadHistory] 错误堆栈:', e.stack);
    }
  };

  // 删除历史报告
  // 删除历史报告（基于本地文件系统）
  const deleteHistoryReport = async (sessionId: string) => {
    if (!confirm('确定要删除这个报告吗？删除后无法恢复。')) {
      return;
    }
    
    try {
      setBusy(true); setError(null);
      
      // 🆕 调用基于本地文件系统的删除 API
      const res = await fetch(`${FASTAPI_BASE_URL}/api/report/live/history/${encodeURIComponent(sessionId)}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `HTTP ${res.status}`);
      }
      
            // 删除成功后刷新列表
      await loadHistory();
      console.log('✅ 报告已删除，历史记录已刷新');
      
    } catch (e: any) {
      setError(e?.message || '删除报告失败');
    } finally {
      setBusy(false);
    }
  };

  // 🆕 切换选择模式
  const toggleSelectMode = () => {
    setIsSelectMode(!isSelectMode);
    setSelectedReports(new Set()); // 切换模式时清空选择
  };

  // 🆕 切换单个报告的选择状态
  const toggleReportSelection = (sessionId: string) => {
    const newSelected = new Set(selectedReports);
    if (newSelected.has(sessionId)) {
      newSelected.delete(sessionId);
    } else {
      newSelected.add(sessionId);
    }
    setSelectedReports(newSelected);
  };

  // 🆕 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedReports.size === historyReports.length) {
      // 当前全选，则取消全选
      setSelectedReports(new Set());
    } else {
      // 否则全选
      const allIds = new Set(historyReports.map(r => r.session_id));
      setSelectedReports(allIds);
    }
  };

  // 🆕 批量删除选中的报告
  const deleteSelectedReports = async () => {
    if (selectedReports.size === 0) {
      alert('请先选择要删除的报告');
      return;
    }

    if (!confirm(`确定要删除选中的 ${selectedReports.size} 个报告吗？删除后无法恢复。`)) {
      return;
    }

    try {
      setBusy(true);
      setError(null);

      // 并行删除所有选中的报告
      const deletePromises = Array.from(selectedReports).map(sessionId =>
        fetch(`${FASTAPI_BASE_URL}/api/report/live/history/${encodeURIComponent(sessionId)}`, {
          method: 'DELETE'
        }).then(res => {
          if (!res.ok) {
            throw new Error(`删除 ${sessionId} 失败: HTTP ${res.status}`);
          }
          return sessionId;
        })
      );

      const results = await Promise.allSettled(deletePromises);
      
      // 统计成功和失败的数量
      const succeeded = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;

      // 刷新列表
      await loadHistory();
      
      // 清空选择并退出选择模式
      setSelectedReports(new Set());
      setIsSelectMode(false);

      if (failed > 0) {
        setError(`删除完成：成功 ${succeeded} 个，失败 ${failed} 个`);
      } else {
        console.log(`✅ 成功删除 ${succeeded} 个报告`);
      }

    } catch (e: any) {
      setError(e?.message || '批量删除失败');
    } finally {
      setBusy(false);
    }
  };

  // 根据报告ID查看历史报告
  const viewHistoryReport = async (reportPath: string) => {
    try {
      setBusy(true); setError(null);
      
      // 🆕 直接使用 viewReview 函数加载本地报告
      await viewReview(reportPath);
      
      // 关闭历史列表，显示复盘报告
      setShowHistory(false);
      
    } catch (e: any) {
      setError(e?.message || '查看历史报告失败');
    } finally {
      setBusy(false);
    }
  };

  const refresh = useCallback(async () => {
    try {
      const r = await getLiveReportStatus(FASTAPI_BASE_URL);
      console.log('📊 [ReportsPage] refresh 获取到的数据:', r);
      console.log('📊 [ReportsPage] status:', r?.status);
      console.log('📊 [ReportsPage] metrics:', r?.status?.metrics);
      setStatus(r?.status || null);
    } catch (e) {
      console.error('❌ [ReportsPage] refresh 失败:', e);
    }
  }, []);

  const startPolling = () => {
    if (pollTimerRef.current) return;
    pollTimerRef.current = setInterval(refresh, 2000); // 🔧 从1秒改为2秒，降低轮询频率
  };
  const stopPolling = () => {
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
  };

  useEffect(() => { 
    refresh(); 
    loadHistory(); // 加载历史记录
    
    // 🆕 检查是否有可恢复的会话
    const checkResumableSession = async () => {
      try {
        const res = await getResumableSession(FASTAPI_BASE_URL);
        if (res?.success && res?.data) {
          setResumableSession(res.data);
          setShowResumeDialog(true);
        }
      } catch (e) {
        console.error('检查可恢复会话失败:', e);
      }
    };
    checkResumableSession();
    
    // 🆕 检查是否有活动会话，如果有则启动轮询
    const checkActiveSession = async () => {
      try {
        const r = await getLiveReportStatus(FASTAPI_BASE_URL);
        if (r?.status && (r.status.status === 'recording' || r.status.status === 'paused')) {
          startPolling();
        }
      } catch (e) {
        console.error('检查活动会话失败:', e);
      }
    };
    checkActiveSession();
    
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
              <div className="text-sm timao-support-text">
                最近 {historyReports.length} 条记录
                {isSelectMode && selectedReports.size > 0 && (
                  <span className="ml-2 text-purple-600">（已选择 {selectedReports.size} 项）</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* 🆕 多选模式切换按钮 */}
            {historyReports.length > 0 && (
              <>
                {isSelectMode ? (
                  <>
                    {/* 全选/取消全选按钮 */}
                    <button
                      className="timao-outline-btn px-3 py-2 text-sm"
                      onClick={toggleSelectAll}
                      disabled={busy}
                    >
                      {selectedReports.size === historyReports.length ? '取消全选' : '全选'}
                    </button>
                    {/* 批量删除按钮 */}
                    <button
                      className="timao-outline-btn px-3 py-2 text-sm text-red-600 hover:bg-red-50 hover:border-red-300"
                      onClick={deleteSelectedReports}
                      disabled={busy || selectedReports.size === 0}
                    >
                      {busy ? '删除中...' : `删除选中 (${selectedReports.size})`}
                    </button>
                    {/* 取消选择按钮 */}
                    <button
                      className="timao-outline-btn px-3 py-2 text-sm"
                      onClick={toggleSelectMode}
                      disabled={busy}
                    >
                      取消
                    </button>
                  </>
                ) : (
                  <button
                    className="timao-outline-btn px-3 py-2 text-sm"
                    onClick={toggleSelectMode}
                    disabled={busy}
                  >
                    多选删除
                  </button>
                )}
              </>
            )}
            <button
              className="timao-outline-btn px-4 py-2"
              onClick={() => {
                setShowHistory(false);
                // 🆕 返回主页面时清理状态
                setArtifacts(null);
                setHasStopped(false);
                setError(null);
                setIsSelectMode(false);
                setSelectedReports(new Set());
              }}
            >
              ← 返回
            </button>
          </div>
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
              <div 
                key={report.session_id || report.report_path} 
                className={`timao-card hover:shadow-lg transition-all ${
                  isSelectMode && selectedReports.has(report.session_id) 
                    ? 'ring-2 ring-purple-500 bg-purple-50' 
                    : ''
                }`}
                onClick={() => {
                  if (isSelectMode) {
                    toggleReportSelection(report.session_id);
                  }
                }}
                style={{ cursor: isSelectMode ? 'pointer' : 'default' }}
              >
                <div className="flex items-center justify-between">
                  {/* 🆕 多选模式下显示复选框 */}
                  {isSelectMode && (
                    <div className="flex items-center mr-3">
                      <input
                        type="checkbox"
                        checked={selectedReports.has(report.session_id)}
                        onChange={() => toggleReportSelection(report.session_id)}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">📊</span>
                      <div>
                        <div className="font-semibold text-purple-600">
                          {report.title || report.anchor_name || `房间 ${report.room_id}`}
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
                  {/* 🆕 非选择模式下显示操作按钮 */}
                  {!isSelectMode && (
                    <div className="flex items-center gap-3">
                      <button
                        className="timao-primary-btn px-6 py-2.5 flex items-center gap-2 disabled:opacity-50"
                        onClick={(e) => {
                          e.stopPropagation();
                          viewHistoryReport(report.report_path);
                        }}
                        disabled={busy}
                      >
                        {busy ? <span className="animate-spin">⏳</span> : <span>👁️</span>}
                        <span>查看报告</span>
                      </button>
                      <button
                        className="timao-outline-btn px-4 py-2.5 text-red-600 hover:bg-red-50 hover:border-red-300 flex items-center gap-2 disabled:opacity-50"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteHistoryReport(report.session_id);
                        }}
                        disabled={busy}
                        title="删除报告"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
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
        onClose={() => {
          setShowReview(false);
          // 🆕 关闭报告时清理状态，允许开始新的录制
          setArtifacts(null);
          setHasStopped(false);
          setError(null);
        }}
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
            <div className="text-sm timao-support-text">
              {isPaused ? (
                <>
                  <span className="text-yellow-600 font-medium">⏸️ 已暂停</span>
                  <div className="text-xs text-gray-500 mt-1">{getRecordedDuration()}</div>
                </>
              ) : isRecording ? (
                <>
                  <span className="text-green-600 font-medium">🔴 录制中</span>
                  <div className="text-xs text-gray-500 mt-1">{getRecordedDuration()}</div>
                </>
              ) : (
                '未开始'
              )}
            </div>
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
          {/* 🆕 暂停/继续按钮 */}
          {isActive && (
            <button 
              className={`timao-outline-btn flex items-center gap-2 px-4 py-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                isPaused 
                  ? 'hover:bg-green-50 hover:border-green-400 hover:text-green-600'
                  : 'hover:bg-yellow-50 hover:border-yellow-400 hover:text-yellow-600'
              }`}
              onClick={isPaused ? resume : pause} 
              disabled={busy}
              title={isPaused ? "继续录制" : "暂停录制"}
            >
              {busy ? <span className="animate-spin">⏳</span> : isPaused ? <span>▶️</span> : <span>⏸️</span>}
              <span>{isPaused ? '继续' : '暂停'}</span>
            </button>
          )}
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

      {/* 🆕 恢复会话对话框 */}
      {showResumeDialog && resumableSession && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="timao-card max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🔄</span>
              <div>
                <h3 className="text-lg font-semibold text-purple-600">发现未完成的录制会话</h3>
                <p className="text-sm text-gray-500">检测到上次的录制会话未完成，是否继续？</p>
              </div>
            </div>
            <div className="timao-soft-card mb-4 space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-700">主播:</span>
                <span>{resumableSession.anchor_name || resumableSession.room_id}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-700">状态:</span>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  resumableSession.status === 'paused' 
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-green-100 text-green-700'
                }`}>
                  {resumableSession.status === 'paused' ? '已暂停' : '录制中'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-700">片段:</span>
                <span>{resumableSession.segments?.length || 0} 个</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-700">弹幕:</span>
                <span>{resumableSession.comments_count || 0} 条</span>
              </div>
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button 
                className="timao-outline-btn px-4 py-2 hover:bg-red-50 hover:border-red-300 hover:text-red-600 disabled:opacity-50"
                onClick={discardSession}
                disabled={busy}
              >
                {busy ? <span className="animate-spin">⏳</span> : '放弃'}
              </button>
              <button 
                className="timao-primary-btn px-6 py-2 disabled:opacity-50"
                onClick={resumeSession}
                disabled={busy}
              >
                {busy ? <span className="animate-spin">⏳</span> : '继续录制'}
              </button>
            </div>
          </div>
        </div>
      )}

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
            <div className="text-sm font-semibold text-gray-700 mb-3">礼物</div>
            <div className="max-h-[300px] overflow-y-auto pr-2">
              {giftList.length === 0 ? (
                <div className="timao-outline-card text-xs timao-support-text">暂无礼物数据</div>
              ) : (
                <div className="space-y-2">
                  {giftList.map(([name, cnt]) => {
                    const maxCount = Math.max(...giftList.map(([, c]) => c as number));
                    const percentage = maxCount > 0 ? ((cnt as number) / maxCount) * 100 : 0;
                    return (
                      <div key={name} className="timao-soft-card p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">{name}</span>
                          <span className="text-sm font-semibold text-purple-600">{cnt as number}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2.5 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="timao-card">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-purple-600">录制信息</h3>
            <div className="text-xs timao-support-text">
              {/* {isActive && `已录制: ${getRecordedDuration()}`} */}
            </div>
          </div>
          
          {/* 录制文件位置 */}
          <div className="timao-soft-card mb-3">
            <div className="text-sm font-medium text-gray-700 mb-2">📂 文件保存位置</div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600 break-all">{status?.recording_dir || '未开始录制'}</span>
              {status?.recording_dir && (
                <button 
                  className="timao-outline-btn text-xs px-3 py-1 ml-2 flex-shrink-0 flex items-center gap-1 hover:bg-purple-50 transition-colors" 
                  onClick={() => { try { (window as any).electronAPI?.openPath(status.recording_dir as string); } catch {} }}
                >
                  <span>📂</span>
                  <span>打开</span>
                </button>
              )}
            </div>
          </div>

          {/* 会话ID */}
          <div className="timao-soft-card text-xs text-gray-500">
            <div>会话ID: {status?.session_id || '—'}</div>
            <div className="mt-1">录制片段: {status?.segments?.length ?? 0} 个</div>
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
          <div className="text-xs timao-support-text mt-2">说明：录制整场直播音频（分段），离线转写并汇总弹幕。</div>
        </section>
      </div>
    </div>
  );
};

export default ReportsPage;

