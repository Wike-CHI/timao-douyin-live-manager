import React, { useState, useEffect } from 'react';

interface Provider {
  provider: string;
  enabled: boolean;
  default_model: string;
  base_url: string;
  models: string[];
}

interface CurrentConfig {
  provider: string;
  model: string;
  base_url: string;
}

interface StatusData {
  current: CurrentConfig;
  providers: Record<string, Provider>;
}

const AIGatewayPage: React.FC = () => {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [testResponse, setTestResponse] = useState<string>('');
  const [showTestResponse, setShowTestResponse] = useState(false);

  // 表单状态
  const [switchProvider, setSwitchProvider] = useState('');
  const [switchModel, setSwitchModel] = useState('');
  const [regProvider, setRegProvider] = useState('qwen');
  const [regApiKey, setRegApiKey] = useState('');
  const [regBaseUrl, setRegBaseUrl] = useState('');
  const [regModel, setRegModel] = useState('');
  const [updateProvider, setUpdateProvider] = useState('');
  const [updateApiKey, setUpdateApiKey] = useState('');
  const [testMessage, setTestMessage] = useState('你好，请用一句话介绍你自己');

  const API_BASE = 'http://127.0.0.1:9019';

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/ai_gateway/status`);
      const data = await res.json();
      setStatusData(data);
      setSwitchProvider(data.current.provider || '');
    } catch (error) {
      console.error('加载失败:', error);
      showAlert('加载配置失败: ' + (error as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const showAlert = (message: string, type: 'success' | 'error') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleSwitchProvider = async () => {
    if (!switchProvider) {
      showAlert('请选择服务商', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/ai_gateway/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          provider: switchProvider, 
          model: switchModel || null 
        })
      });
      
      const data = await res.json();
      if (data.success) {
        showAlert('✓ ' + data.message, 'success');
        loadStatus();
      } else {
        showAlert('✗ ' + data.message, 'error');
      }
    } catch (error) {
      showAlert('切换失败: ' + (error as Error).message, 'error');
    }
  };

  const handleRegisterProvider = async () => {
    if (!regApiKey) {
      showAlert('请输入 API Key', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/ai_gateway/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: regProvider,
          api_key: regApiKey,
          base_url: regBaseUrl || null,
          default_model: regModel || null
        })
      });
      
      const data = await res.json();
      if (data.success) {
        showAlert('✓ ' + data.message, 'success');
        setRegApiKey('');
        setRegBaseUrl('');
        setRegModel('');
        loadStatus();
      } else {
        showAlert('✗ 注册失败', 'error');
      }
    } catch (error) {
      showAlert('注册失败: ' + (error as Error).message, 'error');
    }
  };

  const handleUpdateApiKey = async () => {
    if (!updateProvider || !updateApiKey) {
      showAlert('请选择服务商并输入新的 API Key', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/ai_gateway/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: updateProvider,
          api_key: updateApiKey
        })
      });
      
      const data = await res.json();
      if (data.success) {
        showAlert('✓ API Key 更新成功', 'success');
        setUpdateApiKey('');
        loadStatus();
      } else {
        showAlert('✗ 更新失败', 'error');
      }
    } catch (error) {
      showAlert('更新失败: ' + (error as Error).message, 'error');
    }
  };

  const handleTestChat = async () => {
    if (!testMessage) {
      showAlert('请输入测试消息', 'error');
      return;
    }

    setShowTestResponse(true);
    setTestResponse('⏳ 调用中...');

    try {
      const res = await fetch(`${API_BASE}/api/ai_gateway/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: testMessage }],
          temperature: 0.3,
          max_tokens: 100
        })
      });
      
      const data = await res.json();
      if (data.success) {
        setTestResponse(`✓ 调用成功！\n\n响应: ${data.response}\n\n统计:\n- 输入 Token: ${data.usage?.input_tokens || 0}\n- 输出 Token: ${data.usage?.output_tokens || 0}\n- 费用: ¥${data.usage?.cost || 0}`);
      } else {
        setTestResponse(`✗ 调用失败: ${data.message}`);
      }
    } catch (error) {
      setTestResponse(`✗ 调用失败: ${(error as Error).message}`);
    }
  };

  const handleDeleteProvider = async (providerName: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (!confirm(`确定要删除服务商 "${providerName}" 吗？`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/ai_gateway/providers/${providerName}`, {
        method: 'DELETE'
      });
      
      const data = await res.json();
      if (data.success) {
        showAlert('✓ 删除成功', 'success');
        loadStatus();
      } else {
        showAlert('✗ 删除失败', 'error');
      }
    } catch (error) {
      showAlert('删除失败: ' + (error as Error).message, 'error');
    }
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
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="bg-white/95 p-8 rounded-2xl shadow-xl mb-5 text-center">
          <h1 className="text-3xl font-bold text-blue-600 mb-3">🚀 AI 模型网关管理</h1>
          <p className="text-gray-600">统一管理多个 AI 服务商，一键切换模型</p>
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

        {/* 当前配置 */}
        <div className="bg-white/95 p-6 rounded-2xl shadow-xl mb-5">
          <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
            📊 当前配置
          </h2>
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-5 rounded-xl">
            <h3 className="text-lg font-medium mb-4">✨ 当前使用</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-white/20">
                <span className="font-medium opacity-90">服务商</span>
                <span className="bg-white/20 px-3 py-1 rounded font-mono">
                  {statusData?.current.provider || '未配置'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/20">
                <span className="font-medium opacity-90">模型</span>
                <span className="bg-white/20 px-3 py-1 rounded font-mono">
                  {statusData?.current.model || '未配置'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="font-medium opacity-90">API地址</span>
                <span className="bg-white/20 px-3 py-1 rounded font-mono text-sm">
                  {statusData?.current.base_url || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 已注册的服务商 */}
        <div className="bg-white/95 p-6 rounded-2xl shadow-xl mb-5">
          <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
            🌐 已注册的服务商
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {statusData?.providers && Object.keys(statusData.providers).length > 0 ? (
              Object.entries(statusData.providers).map(([name, config]) => (
                <div
                  key={name}
                  className={`relative border-2 rounded-xl p-4 transition-all cursor-pointer hover:shadow-lg ${
                    config.enabled 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-300 bg-gray-50'
                  }`}
                >
                  <button
                    onClick={(e) => handleDeleteProvider(name, e)}
                    className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                  >
                    ✕ 删除
                  </button>
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold text-gray-800">{config.provider}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      config.enabled 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {config.enabled ? '✓ 启用' : '✗ 禁用'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <div><strong>默认模型:</strong> {config.default_model}</div>
                    <div><strong>API:</strong> {config.base_url}</div>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {config.models.map((model) => (
                      <span
                        key={model}
                        className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs"
                      >
                        {model}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full text-center text-gray-500 py-8">
                暂无已注册的服务商
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* 切换服务商 */}
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
              🔄 切换服务商
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择服务商</label>
                <select
                  value={switchProvider}
                  onChange={(e) => {
                    setSwitchProvider(e.target.value);
                    setSwitchModel('');
                  }}
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value="">请选择...</option>
                  {statusData?.providers && Object.entries(statusData.providers).map(([name, config]) => (
                    <option key={name} value={name}>{config.provider}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择模型（可选）</label>
                <select
                  value={switchModel}
                  onChange={(e) => setSwitchModel(e.target.value)}
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value="">使用默认模型</option>
                  {switchProvider && statusData?.providers[switchProvider]?.models.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleSwitchProvider}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:shadow-lg transition-all"
              >
                切换
              </button>
            </div>
          </div>

          {/* 注册新服务商 */}
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
              ➕ 注册新服务商
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">服务商</label>
                <select
                  value={regProvider}
                  onChange={(e) => setRegProvider(e.target.value)}
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value="qwen">通义千问 (Qwen)</option>
                  <option value="openai">OpenAI</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="doubao">字节豆包</option>
                  <option value="glm">智谱 ChatGLM</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                <input
                  type="password"
                  value={regApiKey}
                  onChange={(e) => setRegApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Base URL（可选）</label>
                <input
                  type="text"
                  value={regBaseUrl}
                  onChange={(e) => setRegBaseUrl(e.target.value)}
                  placeholder="留空使用默认值"
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">默认模型（可选）</label>
                <input
                  type="text"
                  value={regModel}
                  onChange={(e) => setRegModel(e.target.value)}
                  placeholder="留空使用默认值"
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>
              <button
                onClick={handleRegisterProvider}
                className="w-full bg-green-500 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-600 transition-colors"
              >
                注册
              </button>
            </div>
          </div>

          {/* 更新 API Key */}
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
              🔑 更新 API Key
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择服务商</label>
                <select
                  value={updateProvider}
                  onChange={(e) => setUpdateProvider(e.target.value)}
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value="">请选择...</option>
                  {statusData?.providers && Object.entries(statusData.providers).map(([name, config]) => (
                    <option key={name} value={name}>{config.provider}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">新的 API Key</label>
                <input
                  type="password"
                  value={updateApiKey}
                  onChange={(e) => setUpdateApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>
              <button
                onClick={handleUpdateApiKey}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:shadow-lg transition-all"
              >
                更新 API Key
              </button>
            </div>
          </div>

          {/* 测试调用 */}
          <div className="bg-white/95 p-6 rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-blue-600 mb-4 border-b-2 border-gray-100 pb-2">
              🧪 测试调用
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">测试消息</label>
                <input
                  type="text"
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  placeholder="输入测试消息"
                  className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>
              <button
                onClick={handleTestChat}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:shadow-lg transition-all"
              >
                测试当前配置
              </button>
              {showTestResponse && (
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {testResponse}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIGatewayPage;