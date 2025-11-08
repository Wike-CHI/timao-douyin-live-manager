import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Box,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import { Title } from 'react-admin';

interface FunctionConfig {
  provider: string;
  model: string;
}

interface FunctionConfigs {
  [key: string]: FunctionConfig;
}

const FUNCTION_NAMES: { [key: string]: string } = {
  live_analysis: '直播分析',
  style_profile: '氛围情绪识别',
  script_generation: '话术生成',
  live_review: '直播复盘',
  chat_focus: '聊天焦点摘要',
  topic_generation: '智能话题生成',
};

export const FunctionList: React.FC = () => {
  const [configs, setConfigs] = useState<FunctionConfigs>({});
  const [providers, setProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialog, setEditDialog] = useState(false);
  const [editFunction, setEditFunction] = useState('');
  const [editProvider, setEditProvider] = useState('');
  const [editModel, setEditModel] = useState('');
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      
      // 获取功能配置
      const configResponse = await fetch('http://127.0.0.1:15000/api/ai_gateway/functions', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!configResponse.ok) {
        throw new Error('获取配置失败');
      }

      const configData = await configResponse.json();
      setConfigs(configData.function_configs);

      // 获取服务商列表
      const providerResponse = await fetch('http://127.0.0.1:15000/api/ai_gateway/providers', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!providerResponse.ok) {
        throw new Error('获取服务商失败');
      }

      const providerData = await providerResponse.json();
      setProviders(Object.keys(providerData.providers));
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchModels = async (provider: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`http://127.0.0.1:15000/api/ai_gateway/models/${provider}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取模型失败');
      }

      const data = await response.json();
      setAvailableModels(data.models);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const openEditDialog = (functionKey: string) => {
    const config = configs[functionKey];
    setEditFunction(functionKey);
    setEditProvider(config.provider);
    setEditModel(config.model);
    fetchModels(config.provider);
    setEditDialog(true);
  };

  const handleProviderChange = (provider: string) => {
    setEditProvider(provider);
    setEditModel('');
    fetchModels(provider);
  };

  const handleUpdate = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        `http://127.0.0.1:15000/api/ai_gateway/functions/${editFunction}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            function: editFunction,
            provider: editProvider,
            model: editModel,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('更新失败');
      }

      setEditDialog(false);
      fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <div>
      <Title title="AI网关 - 功能配置" />

      <Alert severity="info" sx={{ mb: 3 }}>
        为不同的AI功能配置专用的服务商和模型，实现最佳性能和成本控制
      </Alert>

      <Grid container spacing={2}>
        {Object.entries(configs).map(([functionKey, config]) => (
          <Grid item xs={12} md={6} lg={4} key={functionKey}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {FUNCTION_NAMES[functionKey] || functionKey}
                </Typography>

                <Box my={2}>
                  <Typography variant="body2" color="text.secondary">
                    服务商: <strong>{config.provider}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    模型: <strong>{config.model}</strong>
                  </Typography>
                </Box>

                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  onClick={() => openEditDialog(functionKey)}
                >
                  修改配置
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 编辑对话框 */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          修改配置: {FUNCTION_NAMES[editFunction] || editFunction}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="服务商"
            value={editProvider}
            onChange={(e) => handleProviderChange(e.target.value)}
            fullWidth
            margin="normal"
            select
          >
            {providers.map((provider) => (
              <MenuItem key={provider} value={provider}>
                {provider.toUpperCase()}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="模型"
            value={editModel}
            onChange={(e) => setEditModel(e.target.value)}
            fullWidth
            margin="normal"
            select
            disabled={!editProvider || availableModels.length === 0}
          >
            {availableModels.map((model) => (
              <MenuItem key={model} value={model}>
                {model}
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>取消</Button>
          <Button onClick={handleUpdate} variant="contained" disabled={!editProvider || !editModel}>
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
