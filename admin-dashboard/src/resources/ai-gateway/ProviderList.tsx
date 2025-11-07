import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
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

interface ProviderConfig {
  provider: string;
  api_key: string;
  base_url: string;
  default_model: string;
  models: string[];
  enabled: boolean;
  timeout: number;
  max_retries: number;
}

interface GatewayStatus {
  current: {
    provider: string;
    model: string;
  };
  providers: { [key: string]: ProviderConfig };
  function_configs: { [key: string]: { provider: string; model: string } };
}

export const ProviderList: React.FC = () => {
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [switchDialog, setSwitchDialog] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://127.0.0.1:9030/api/ai_gateway/status', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取状态失败');
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSwitch = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://127.0.0.1:9030/api/ai_gateway/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider: selectedProvider,
          model: selectedModel || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('切换失败');
      }

      setSwitchDialog(false);
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const openSwitchDialog = (provider: string, model?: string) => {
    setSelectedProvider(provider);
    setSelectedModel(model || '');
    setSwitchDialog(true);
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

  if (!status) {
    return <Alert severity="warning">无数据</Alert>;
  }

  return (
    <div>
      <Title title="AI网关 - 服务商管理" />
      
      {/* 当前配置 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            当前配置
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <Chip
              label={`服务商: ${status.current.provider}`}
              color="primary"
              sx={{ fontSize: '1rem', padding: '20px 12px' }}
            />
            <Chip
              label={`模型: ${status.current.model}`}
              color="secondary"
              sx={{ fontSize: '1rem', padding: '20px 12px' }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* 服务商列表 */}
      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
        已注册服务商
      </Typography>
      <Grid container spacing={2}>
        {Object.entries(status.providers).map(([name, config]) => (
          <Grid item xs={12} md={6} lg={4} key={name}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{name.toUpperCase()}</Typography>
                  <Chip
                    label={config.enabled ? '已启用' : '已禁用'}
                    color={config.enabled ? 'success' : 'default'}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  默认模型: {config.default_model}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  超时: {config.timeout}s | 重试: {config.max_retries}次
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  API密钥: {config.api_key.substring(0, 8)}...
                </Typography>

                <Box mt={2}>
                  <Typography variant="caption" color="text.secondary">
                    支持的模型:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                    {config.models.map((model) => (
                      <Chip key={model} label={model} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>

                <Box mt={2} display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => openSwitchDialog(name, config.default_model)}
                    disabled={!config.enabled}
                  >
                    切换到此服务商
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 切换对话框 */}
      <Dialog open={switchDialog} onClose={() => setSwitchDialog(false)}>
        <DialogTitle>切换服务商</DialogTitle>
        <DialogContent>
          <TextField
            label="服务商"
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            fullWidth
            margin="normal"
            disabled
          />
          <TextField
            label="模型"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            fullWidth
            margin="normal"
            select
          >
            {status.providers[selectedProvider]?.models.map((model) => (
              <MenuItem key={model} value={model}>
                {model}
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwitchDialog(false)}>取消</Button>
          <Button onClick={handleSwitch} variant="contained">
            确认切换
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
