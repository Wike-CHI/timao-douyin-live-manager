/**
 * 初次启动向导 - 本地化模式
 * 
 * 引导用户配置AI服务商API Key和模型映射
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card as AntCard,
  Steps,
  Button,
  Form,
  Input,
  Select,
  message,
  Space,
  Typography,
  Alert,
  Spin,
  Divider,
  Tag,
} from 'antd';
import {
  CheckCircleOutlined,
  CloudOutlined,
  SettingOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { fetchJsonWithAuth } from '../../services/http';

const { Title, Text, Paragraph } = Typography;
const Card = AntCard as any;

interface ProviderTemplate {
  name: string;
  base_url: string;
  models: string[];
  default_model: string;
}

interface ProviderConfig {
  provider_id: string;
  api_key: string;
  base_url?: string;
  default_model?: string;
  enabled: boolean;
}

interface FunctionModel {
  function_id: string;
  provider: string;
  model: string;
}

const SetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  
  // 服务商配置
  const [providerTemplates, setProviderTemplates] = useState<Record<string, ProviderTemplate>>({});
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [providerConfigs, setProviderConfigs] = useState<Record<string, ProviderConfig>>({});
  
  // 功能模型映射
  const [functionModels, setFunctionModels] = useState<Record<string, FunctionModel>>({
    'live_summary': { function_id: 'live_summary', provider: '', model: '' },
    'danmaku_analysis': { function_id: 'danmaku_analysis', provider: '', model: '' },
    'topic_suggestion': { function_id: 'topic_suggestion', provider: '', model: '' },
    'content_generation': { function_id: 'content_generation', provider: '', model: '' },
  });

  // 检查是否已初始化
  useEffect(() => {
    checkInitStatus();
  }, []);

  const checkInitStatus = async () => {
    try {
      setChecking(true);
      const response = await fetchJsonWithAuth('backend', '/api/bootstrap/status');
      const data = await response.json();
      
      if (data?.is_initialized) {
        // 已初始化，直接跳转到主页
        message.success('系统已配置完成');
        navigate('/dashboard');
        return;
      }
      
      // 加载服务商模板
      if (data?.provider_templates) {
        setProviderTemplates(data.provider_templates);
      }
    } catch (error: any) {
      console.error('检查初始化状态失败:', error);
      message.error('无法连接到后端服务，请检查服务是否启动');
    } finally {
      setChecking(false);
    }
  };

  // 步骤1：选择服务商
  const handleProviderSelect = (providers: string[]) => {
    setSelectedProviders(providers);
    
    // 初始化配置
    const newConfigs: Record<string, ProviderConfig> = {};
    providers.forEach(id => {
      if (!providerConfigs[id]) {
        const template = providerTemplates[id];
        newConfigs[id] = {
          provider_id: id,
          api_key: '',
          base_url: template?.base_url,
          default_model: template?.default_model,
          enabled: true,
        };
      } else {
        newConfigs[id] = providerConfigs[id];
      }
    });
    setProviderConfigs(newConfigs);
  };

  // 步骤2：配置API Key
  const handleProviderConfigChange = (providerId: string, field: string, value: string) => {
    setProviderConfigs(prev => ({
      ...prev,
      [providerId]: {
        ...prev[providerId],
        [field]: value,
      },
    }));
  };

  // 步骤3：配置功能模型
  const handleFunctionModelChange = (functionId: string, field: 'provider' | 'model', value: string) => {
    setFunctionModels(prev => ({
      ...prev,
      [functionId]: {
        ...prev[functionId],
        [field]: value,
      },
    }));
  };

  // 提交配置
  const handleFinish = async () => {
    try {
      setLoading(true);

      // 1. 配置服务商
      for (const providerId of selectedProviders) {
        const config = providerConfigs[providerId];
        if (!config.api_key) {
          message.error(`请填写 ${providerTemplates[providerId]?.name} 的API Key`);
          return;
        }

        await fetchJsonWithAuth('backend', '/api/bootstrap/provider', {
          method: 'POST',
          body: JSON.stringify(config),
        });
      }

      // 2. 配置功能模型
      const validFunctions = Object.values(functionModels).filter(
        f => f.provider && f.model
      );
      
      if (validFunctions.length === 0) {
        message.error('请至少配置一个功能的AI模型');
        return;
      }

      await fetchJsonWithAuth('backend', '/api/bootstrap/function-models/batch', {
        method: 'POST',
        body: JSON.stringify({
          function_models: validFunctions.reduce((acc, f) => {
            acc[f.function_id] = { provider: f.provider, model: f.model };
            return acc;
          }, {} as Record<string, { provider: string; model: string }>),
        }),
      });

      message.success('配置完成！正在启动...');
      
      // 跳转到主页
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (error: any) {
      console.error('配置失败:', error);
      const errorMsg = error.message || '配置失败，请重试';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: '选择服务商',
      icon: <CloudOutlined />,
    },
    {
      title: '配置API Key',
      icon: <SettingOutlined />,
    },
    {
      title: '配置功能',
      icon: <CheckCircleOutlined />,
    },
  ];

  const functionNames: Record<string, string> = {
    'live_summary': '直播总结',
    'danmaku_analysis': '弹幕分析',
    'topic_suggestion': '话题推荐',
    'content_generation': '内容生成',
  };

  if (checking) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="正在检查系统状态..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card
        style={{ maxWidth: 900, margin: '0 auto' } as React.CSSProperties}
        title={
          <Space direction="vertical" size={0}>
            <Title level={3} style={{ margin: 0 }}>
              <RocketOutlined /> 欢迎使用抖音直播管理系统
            </Title>
            <Text type="secondary">本地化版本 - 首次启动配置</Text>
          </Space>
        }
      >
        <Steps current={current} items={steps} style={{ marginBottom: 32 }} />

        {/* 步骤1：选择服务商 */}
        {current === 0 && (
          <div>
            <Alert
              message="选择AI服务商"
              description="请选择您要使用的AI服务商。您可以选择多个服务商，稍后为不同功能分配不同的模型。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form layout="vertical">
              <Form.Item label="可用服务商" required>
                <Select
                  mode="multiple"
                  placeholder="选择一个或多个服务商"
                  value={selectedProviders}
                  onChange={(values: string[]) => handleProviderSelect(values)}
                  style={{ width: '100%' }}
                  options={Object.entries(providerTemplates).map(([id, template]) => ({
                    label: `${template.name} (${id})`,
                    value: id
                  }))}
                />
              </Form.Item>

              {selectedProviders.length > 0 && (
                <Alert
                  message={`已选择 ${selectedProviders.length} 个服务商`}
                  description={selectedProviders.map(id => providerTemplates[id]?.name).join('、')}
                  type="success"
                  showIcon
                />
              )}
            </Form>

            <Divider />

            <Space>
              <Button
                type="primary"
                onClick={() => setCurrent(1)}
                disabled={selectedProviders.length === 0}
              >
                下一步
              </Button>
            </Space>
          </div>
        )}

        {/* 步骤2：配置API Key */}
        {current === 1 && (
          <div>
            <Alert
              message="配置API Key"
              description="请填写各个服务商的API Key。这些信息将保存在本地，不会上传到服务器。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form layout="vertical">
              {selectedProviders.map(providerId => {
                const template = providerTemplates[providerId];
                const config = providerConfigs[providerId];

                return (
                  <Card
                    key={providerId}
                    title={template?.name}
                    size="small"
                    style={{ marginBottom: 16 } as React.CSSProperties}
                  >
                    <Form.Item label="API Key" required>
                      <Input.Password
                        placeholder={`请输入${template?.name}的API Key`}
                        value={config?.api_key}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleProviderConfigChange(providerId, 'api_key', e.target.value)}
                      />
                    </Form.Item>

                    <Form.Item label="Base URL">
                      <Input
                        placeholder="默认使用官方地址"
                        value={config?.base_url}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleProviderConfigChange(providerId, 'base_url', e.target.value)}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        默认: {template?.base_url}
                      </Text>
                    </Form.Item>

                    <Form.Item label="默认模型">
                      <Select
                        placeholder="选择默认模型"
                        value={config?.default_model}
                        onChange={(value: string) => handleProviderConfigChange(providerId, 'default_model', value)}
                        options={template?.models.map(model => ({
                          label: model,
                          value: model
                        }))}
                      />
                    </Form.Item>
                  </Card>
                );
              })}
            </Form>

            <Divider />

            <Space>
              <Button onClick={() => setCurrent(0)}>上一步</Button>
              <Button
                type="primary"
                onClick={() => setCurrent(2)}
                disabled={!selectedProviders.every(id => providerConfigs[id]?.api_key)}
              >
                下一步
              </Button>
            </Space>
          </div>
        )}

        {/* 步骤3：配置功能模型 */}
        {current === 2 && (
          <div>
            <Alert
              message="配置功能模型"
              description="为不同的AI功能选择合适的模型。您可以为不同功能使用不同服务商的模型。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form layout="vertical">
              {Object.entries(functionModels).map(([functionId, config]) => (
                <Card
                  key={functionId}
                  title={functionNames[functionId]}
                  size="small"
                  style={{ marginBottom: 16 } as React.CSSProperties}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Form.Item label="服务商" style={{ marginBottom: 8 }}>
                      <Select
                        placeholder="选择服务商"
                        value={config.provider}
                        onChange={(value: string) => handleFunctionModelChange(functionId, 'provider', value)}
                        style={{ width: '100%' }}
                        options={selectedProviders.map(id => ({
                          label: providerTemplates[id]?.name,
                          value: id
                        }))}
                      />
                    </Form.Item>

                    {config.provider && (
                      <Form.Item label="模型" style={{ marginBottom: 0 }}>
                        <Select
                          placeholder="选择模型"
                          value={config.model}
                          onChange={(value: string) => handleFunctionModelChange(functionId, 'model', value)}
                          style={{ width: '100%' }}
                          options={providerTemplates[config.provider]?.models.map(model => ({
                            label: model,
                            value: model
                          }))}
                        />
                      </Form.Item>
                    )}
                  </Space>
                </Card>
              ))}
            </Form>

            <Divider />

            <Space>
              <Button onClick={() => setCurrent(1)}>上一步</Button>
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                loading={loading}
                onClick={handleFinish}
                disabled={!Object.values(functionModels).some(f => f.provider && f.model)}
              >
                完成配置
              </Button>
            </Space>
          </div>
        )}
      </Card>
    </div>
  );
};

export default SetupWizard;

