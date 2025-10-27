import React, { useState, useEffect } from 'react';

interface UsageStats {
  total_calls: number;
  total_tokens: number;
  total_cost: number;
  success_rate: number;
  by_model: Record<string, {
    calls: number;
    tokens: number;
    cost: number;
  }>;
  by_function: Record<string, {
    calls: number;
    tokens: number;
    cost: number;
  }>;
  by_user: Record<string, {
    calls: number;
    tokens: number;
    cost: number;
  }>;
  by_anchor: Record<string, {
    calls: number;
    tokens: number;
    cost: number;
  }>;
}

interface DashboardData {
  today_stats: UsageStats;
  monthly_stats: UsageStats;
  top_users: Array<{
    user_id: string;
    total_tokens: number;
    total_cost: number;
    call_count: number;
  }>;
  cost_trend: Array<{
    date: string;
    cost: number;
  }>;
  model_distribution: Record<string, number>;
  function_distribution: Record<string, number>;
}

interface ModelPricing {
  [key: string]: {
    input_price: number;
    output_price: number;
    unit: string;
    description: string;
  };
}

const AIUsagePage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [modelPricing, setModelPricing] = useState<ModelPricing>({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [alert, setAlert] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [reportDays, setReportDays] = useState(7);
  const [exportLoading, setExportLoading] = useState(false);

  const API_BASE = 'http://127.0.0.1:10090';

  useEffect(() => {
    loadDashboard();
    loadModelPricing();
  }, []);

  const showAlert = (message: string, type: 'success' | 'error') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 5000);
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/ai_usage/dashboard`);
      const data = await res.json();
      setDashboardData(data);
    } catch (error) {
      console.error('加载仪表板失败:', error);
      showAlert('加载仪表板失败: ' + (error as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadModelPricing = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ai_usage/models/pricing`);
      const data = await res.json();
      setModelPricing(data.pricing || {});
    } catch (error) {
      console.error('加载定价信息失败:', error);
    }
  };

  const exportReport = async () => {
    try {
      setExportLoading(true);
      const res = await fetch(`${API_BASE}/api/ai_usage/export_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: reportDays })
      });
      
      const data = await res.json();
      if (data.success) {
        showAlert(`✓ 报告导出成功: ${data.file_path}`, 'success');
        
        // 下载文件
        const downloadRes = await fetch(`${API_BASE}/api/ai_usage/download_report`);
        const blob = await downloadRes.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai_usage_report_${reportDays}days.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        showAlert('✗ 导出失败', 'error');
      }
    } catch (error) {
      showAlert('导出失败: ' + (error as Error).message, 'error');
    } finally {
      setExportLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `¥${amount.toFixed(4)}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const renderStatsCard = (title: string, stats: UsageStats, color: string) => (
    <div className={`bg-gradient-to-r ${color} text-white p-6 rounded-xl shadow-lg`}>
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold">{formatNumber(stats.total_calls)}</div>
          <div className="text-sm opacity-90">总调用次数</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{formatNumber(stats.total_tokens)}</div>
          <div className="text-sm opacity-90">总Token数</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{formatCurrency(stats.total_cost)}</div>
          <div className="text-sm opacity-90">总费用</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{(stats.success_rate * 100).toFixed(1)}%</div>
          <div className="text-sm opacity-90">成功率</div>
        </div>
      </div>
    </div>
  );

  const renderDistributionChart = (title: string, data: Record<string, number>, color: string) => {
    const total = Object.values(data).reduce((sum, val) => sum + val, 0);
    const sortedData = Object.entries(data)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    return (
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
        <div className="space-y-3">
          {sortedData.map(([key, value]) => {
            const percentage = total > 0 ? (value / total) * 100 : 0;
            return (
              <div key={key} className="flex items-center">
                <div className="w-24 text-sm text-gray-600 truncate">{key}</div>
                <div className="flex-1 mx-3">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className={`${color} h-2 rounded-full transition-all duration-300`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
                <div className="w-16 text-sm text-gray-600 text-right">
                  {percentage.toFixed(1)}%
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-5">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <div className="bg-white/95 p-8 rounded-2xl shadow-xl mb-5 text-center">
          <h1 className="text-3xl font-bold text-blue-600 mb-3">📊 AI 使用监控</h1>
          <p className="text-gray-600">实时监控 AI 服务使用情况和成本分析</p>
        </div>

        {/* 警告信息 */}
        {alert && (
          <div className={`p-4 rounded-lg mb-5 ${
            alert.type === 'success' 
              ? 'bg-green-100 text-green-800 border border-green-300' 
              : 'bg-red-100 text-red-800 border border-red-300'
          }`}>
            {alert.message}
          </div>
        )}

        {/* 标签页导航 */}
        <div className="bg-white/95 p-2 rounded-2xl shadow-xl mb-5">
          <div className="flex space-x-2">
            {[
              { id: 'dashboard', label: '📊 仪表板', icon: '📊' },
              { id: 'pricing', label: '💰 定价信息', icon: '💰' },
              { id: 'export', label: '📤 导出报告', icon: '📤' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* 仪表板标签页 */}
        {activeTab === 'dashboard' && dashboardData && (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {renderStatsCard('📅 今日统计', dashboardData.today_stats, 'from-blue-500 to-blue-600')}
              {renderStatsCard('📊 本月统计', dashboardData.monthly_stats, 'from-purple-500 to-purple-600')}
            </div>

            {/* 分布图表 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {renderDistributionChart('🤖 模型使用分布', dashboardData.model_distribution, 'bg-blue-500')}
              {renderDistributionChart('⚙️ 功能使用分布', dashboardData.function_distribution, 'bg-purple-500')}
            </div>

            {/* 费用趋势 */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">📈 7日费用趋势</h3>
              <div className="space-y-2">
                {dashboardData.cost_trend.map((item, index) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600">{item.date}</span>
                    <span className="font-semibold text-blue-600">{formatCurrency(item.cost)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 用户排行 */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">👥 用户使用排行</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">用户ID</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">调用次数</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">Token数</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">费用</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.top_users.map((user, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 text-gray-800">{user.user_id}</td>
                        <td className="py-3 px-4 text-right text-gray-600">{formatNumber(user.call_count)}</td>
                        <td className="py-3 px-4 text-right text-gray-600">{formatNumber(user.total_tokens)}</td>
                        <td className="py-3 px-4 text-right font-semibold text-blue-600">{formatCurrency(user.total_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 定价信息标签页 */}
        {activeTab === 'pricing' && (
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-6">💰 AI 模型定价信息</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(modelPricing).map(([model, pricing]) => (
                <div key={model} className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-shadow">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">{model}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">输入价格:</span>
                      <span className="font-semibold">¥{pricing.input_price}/{pricing.unit}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">输出价格:</span>
                      <span className="font-semibold">¥{pricing.output_price}/{pricing.unit}</span>
                    </div>
                    <div className="pt-2 border-t border-gray-100">
                      <p className="text-gray-600 text-xs">{pricing.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 导出报告标签页 */}
        {activeTab === 'export' && (
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-6">📤 导出使用报告</h2>
            <div className="max-w-md mx-auto space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择天数</label>
                <select
                  value={reportDays}
                  onChange={(e) => setReportDays(Number(e.target.value))}
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value={1}>最近 1 天</option>
                  <option value={7}>最近 7 天</option>
                  <option value={30}>最近 30 天</option>
                  <option value={90}>最近 90 天</option>
                </select>
              </div>
              <button
                onClick={exportReport}
                disabled={exportLoading}
                className={`w-full py-3 px-6 rounded-lg font-medium transition-all ${
                  exportLoading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:shadow-lg'
                } text-white`}
              >
                {exportLoading ? '⏳ 导出中...' : '📥 导出 Excel 报告'}
              </button>
              <div className="text-center text-sm text-gray-600">
                <p>报告将包含详细的使用统计、费用分析和用户数据</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIUsagePage;