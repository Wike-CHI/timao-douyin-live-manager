import React, { useState } from 'react';
import type { ReviewData, AIMetadata, AISummary } from '../../types/report';

interface ReviewReportPageProps {
  reviewData: ReviewData;
  onClose?: () => void;
}

// 折线图数据点接口
interface ChartDataPoint {
  time: string;
  value: number;
}

// 趋势图配置接口
interface TrendChart {
  title: string;
  description: string;
  chart_data: ChartDataPoint[];
  insights: string;
}

/**
 * 直播复盘报告展示页面
 * 展示 Gemini 生成的结构化复盘数据
 */
const ReviewReportPage: React.FC<ReviewReportPageProps> = ({ reviewData, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'metrics' | 'trends'>('overview');

  const { ai_summary, metrics, transcript, comments_count, duration_seconds, anchor_name, room_id } = reviewData;

  // 格式化时长
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '0分钟';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`;
    }
    return `${minutes}分钟`;
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  // 简单的折线图组件
  const LineChart: React.FC<{ data: ChartDataPoint[]; title: string; color?: string }> = ({ 
    data, 
    title,
    color = '#9333ea' // 默认紫色
  }) => {
    if (!data || data.length === 0) return null;

    const width = 600;
    const height = 300;
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    // 计算最大值和最小值
    const values = data.map(d => d.value);
    const maxValue = Math.max(...values, 1); // 至少为1，避免除以0
    const minValue = Math.min(...values, 0);
    const valueRange = maxValue - minValue || 1;

    // 生成路径点
    const points = data.map((point, index) => {
      const x = padding + (index / (data.length - 1)) * chartWidth;
      const y = padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;
      return { x, y, ...point };
    });

    // 生成 SVG 路径
    const pathData = points.map((p, i) => 
      `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`
    ).join(' ');

    // 生成填充区域路径
    const areaData = `${pathData} L ${points[points.length - 1].x},${height - padding} L ${padding},${height - padding} Z`;

    return (
      <div className="w-full">
        <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
          {/* 网格线 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
            const y = padding + chartHeight * (1 - ratio);
            const value = Math.round(minValue + valueRange * ratio);
            return (
              <g key={i}>
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                  strokeDasharray="4"
                />
                <text
                  x={padding - 10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="12"
                  fill="#6b7280"
                >
                  {value}
                </text>
              </g>
            );
          })}

          {/* 填充区域 */}
          <path
            d={areaData}
            fill={color}
            fillOpacity="0.1"
          />

          {/* 折线 */}
          <path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* 数据点 */}
          {points.map((point, index) => (
            <g key={index}>
              <circle
                cx={point.x}
                cy={point.y}
                r="5"
                fill="white"
                stroke={color}
                strokeWidth="3"
              />
              {/* X 轴标签 */}
              <text
                x={point.x}
                y={height - padding + 20}
                textAnchor="middle"
                fontSize="11"
                fill="#6b7280"
              >
                {point.time}
              </text>
              {/* 数值标签 */}
              <text
                x={point.x}
                y={point.y - 15}
                textAnchor="middle"
                fontSize="12"
                fontWeight="bold"
                fill={color}
              >
                {point.value}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // 获取趋势图数据
  const getTrendCharts = (): Record<string, TrendChart> | undefined => {
    // trend_charts 现在直接在 reviewData 顶层，不在 ai_summary 中
    return (reviewData as any)?.trend_charts || (ai_summary as any)?.trend_charts;
  };

  return (
    <div className="space-y-6">
      {/* 头部信息 */}
      <div className="timao-soft-card">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <span className="text-5xl">📊</span>
            <div>
              <h1 className="text-2xl font-bold text-purple-600">AI 复盘报告</h1>
              <div className="text-sm text-gray-600 mt-2 space-y-1">
                {room_id && <div>房间号: {room_id}</div>}
                {anchor_name && <div>主播: {anchor_name}</div>}
                <div>时长: {formatDuration(duration_seconds)}</div>
                <div>弹幕: {comments_count?.toLocaleString() || 0} 条</div>
                {reviewData.started_at && <div>开始: {formatTimestamp(reviewData.started_at)}</div>}
              </div>
            </div>
          </div>
          {onClose && (
            <button className="timao-outline-btn text-sm" onClick={onClose}>
              ← 返回
            </button>
          )}
        </div>

        {/* AI 成本信息 */}
        {ai_summary?.gemini_metadata && (
          <div className="mt-4 flex items-center gap-4 text-xs text-gray-500 bg-purple-50 rounded-lg px-4 py-2">
            <span>🤖 {ai_summary.gemini_metadata.model}</span>
            <span>Tokens: {ai_summary.gemini_metadata.tokens.toLocaleString()}</span>
            <span className="text-green-600 font-semibold">成本: ${ai_summary.gemini_metadata.cost.toFixed(6)}</span>
            <span>耗时: {ai_summary.gemini_metadata.duration.toFixed(2)}s</span>
          </div>
        )}
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-2">
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'overview'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('overview')}
        >
          📋 复盘概览
        </button>
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'trends'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('trends')}
        >
          📈 数据趋势
        </button>
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'transcript'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('transcript')}
        >
          📝 口播转写
        </button>
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'metrics'
              ? 'bg-purple-600 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('metrics')}
        >
          📊 数据总览
        </button>
      </div>

      {/* 内容区域 */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 错误提示 */}
          {ai_summary?.error && (
            <div className="timao-card bg-red-50 border-red-200">
              <div className="flex items-center gap-2 text-red-600">
                <span className="text-2xl">⚠️</span>
                <div>
                  <div className="font-semibold">AI 分析失败</div>
                  <div className="text-sm mt-1">{ai_summary.error}</div>
                </div>
              </div>
            </div>
          )}

          {/* 综合评分 */}
          {ai_summary?.overall_score !== undefined && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4 flex items-center gap-2">
                <span>⭐</span> 综合评分
              </h2>
              <div className="flex items-center gap-4">
                <div className="text-6xl font-bold text-purple-600">
                  {ai_summary.overall_score}
                </div>
                <div className="flex-1">
                  <div className="text-lg text-gray-600">/ 100 分</div>
                  <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
                    <div
                      className="bg-purple-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${ai_summary.overall_score}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 总体评价 */}
          {ai_summary?.performance_analysis?.overall_assessment && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4">💡 总体评价</h2>
              <div className="text-gray-700 leading-relaxed">
                {ai_summary.performance_analysis.overall_assessment}
              </div>
            </div>
          )}

          {/* 总结 */}
          {ai_summary?.summary && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4">📋 复盘总结</h2>
              <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {ai_summary.summary}
              </div>
            </div>
          )}

          {/* 亮点 */}
          {ai_summary?.highlight_points && ai_summary.highlight_points.length > 0 && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4 flex items-center gap-2">
                <span>✨</span> 关键亮点
              </h2>
              <div className="space-y-3">
                {ai_summary.highlight_points.map((point, idx) => (
                  <div
                    key={idx}
                    className="timao-soft-card bg-green-50 border-l-4 border-green-400 hover:bg-green-100 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-green-600 font-bold text-lg">{idx + 1}</span>
                      <div className="flex-1 text-gray-700">{point}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 问题/风险 */}
          {ai_summary?.risks && ai_summary.risks.length > 0 && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4 flex items-center gap-2">
                <span>⚠️</span> 需要改进
              </h2>
              <div className="space-y-3">
                {ai_summary.risks.map((risk, idx) => (
                  <div
                    key={idx}
                    className="timao-soft-card bg-orange-50 border-l-4 border-orange-400 hover:bg-orange-100 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-orange-600 font-bold text-lg">{idx + 1}</span>
                      <div className="flex-1 text-gray-700">{risk}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 改进建议 */}
          {ai_summary?.suggestions && ai_summary.suggestions.length > 0 && (
            <div className="timao-card">
              <h2 className="text-xl font-semibold text-purple-600 mb-4 flex items-center gap-2">
                <span>💡</span> 改进建议
              </h2>
              <div className="space-y-3">
                {ai_summary.suggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    className="timao-soft-card bg-blue-50 border-l-4 border-blue-400 hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-blue-600 font-bold text-lg">{idx + 1}</span>
                      <div className="flex-1 text-gray-700">{suggestion}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 数据趋势 Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {(() => {
            const trendCharts = getTrendCharts();
            if (!trendCharts || Object.keys(trendCharts).length === 0) {
              return (
                <div className="timao-card">
                  <div className="text-gray-500 text-center py-12">
                    <div className="text-4xl mb-4">📈</div>
                    <div>暂无趋势数据</div>
                    <div className="text-sm mt-2">Gemini 分析中未生成图表数据</div>
                  </div>
                </div>
              );
            }

            const chartColors = {
              follows: '#10b981', // 绿色
              entries: '#3b82f6', // 蓝色
              peak_viewers: '#f59e0b', // 橙色
              like_total: '#ec4899', // 粉色
            };

            const chartIcons = {
              follows: '👥',
              entries: '🚪',
              peak_viewers: '👀',
              like_total: '❤️',
            };

            return Object.entries(trendCharts).map(([key, chart]) => (
              <div key={key} className="timao-card">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">{chartIcons[key as keyof typeof chartIcons] || '📊'}</span>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-purple-600">{chart.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{chart.description}</p>
                  </div>
                </div>

                {/* 图表 */}
                <div className="timao-soft-card bg-gradient-to-br from-purple-50 to-blue-50 p-6">
                  <LineChart 
                    data={chart.chart_data} 
                    title={chart.title}
                    color={chartColors[key as keyof typeof chartColors] || '#9333ea'}
                  />
                </div>

                {/* 洞察 */}
                {chart.insights && (
                  <div className="mt-4 timao-soft-card bg-blue-50 border-l-4 border-blue-400">
                    <div className="flex items-start gap-3">
                      <span className="text-blue-600 text-xl">💡</span>
                      <div className="flex-1">
                        <div className="font-semibold text-blue-900 mb-1">数据洞察</div>
                        <div className="text-gray-700">{chart.insights}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ));
          })()}
        </div>
      )}

      {/* 转写 Tab */}
      {activeTab === 'transcript' && (
        <div className="timao-card">
          <h2 className="text-xl font-semibold text-purple-600 mb-4">📝 完整口播转写</h2>
          {transcript ? (
            <div className="timao-soft-card max-h-[600px] overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed font-sans">
                {transcript}
              </pre>
              <div className="mt-4 text-xs text-gray-500 border-t pt-2">
                共 {reviewData.transcript_chars?.toLocaleString()} 字符 · {reviewData.segments_count} 个片段
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-12">暂无转写内容</div>
          )}
        </div>
      )}

      {/* 指标 Tab */}
      {activeTab === 'metrics' && (
        <div className="timao-card">
          <h2 className="text-xl font-semibold text-purple-600 mb-4">📈 直播数据指标</h2>
          {metrics && Object.keys(metrics).length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(metrics).map(([key, value]) => (
                <div key={key} className="timao-soft-card">
                  <div className="text-sm text-gray-500 mb-1">
                    {key === 'follows' && '新增关注'}
                    {key === 'entries' && '进场人数'}
                    {key === 'peak_viewers' && '最高在线'}
                    {key === 'like_total' && '新增点赞'}
                    {!['follows', 'entries', 'peak_viewers', 'like_total'].includes(key) && key}
                  </div>
                  <div className="text-2xl font-bold text-purple-600">
                    {typeof value === 'object' ? JSON.stringify(value) : value?.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-12">暂无数据指标</div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReviewReportPage;
