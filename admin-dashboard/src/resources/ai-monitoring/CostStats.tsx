import { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import { useNotify } from 'react-admin';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import MoneyIcon from '@mui/icons-material/Money';
import StorageIcon from '@mui/icons-material/Storage';

interface AICostData {
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  avg_cost_per_request: number;
  cost_by_provider: Array<{
    provider: string;
    model: string;
    total_cost: number;
    total_tokens: number;
    request_count: number;
  }>;
  cost_trend: Array<{
    date: string;
    cost: number;
    tokens: number;
    requests: number;
  }>;
}

export const AICostStats = () => {
  const notify = useNotify();
  const [data, setData] = useState<AICostData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9030';
        const token = localStorage.getItem('token');

        const response = await fetch(`${API_BASE}/api/admin/ai/costs`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('获取AI成本数据失败');
        }

        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('获取AI成本数据失败:', error);
        notify('获取AI成本数据失败', { type: 'error' });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // 每分钟刷新
    return () => clearInterval(interval);
  }, [notify]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI 成本监控
      </Typography>

      {/* 统计卡片 */}
      <Grid container spacing={3} sx={{ mt: 2, mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon sx={{ mr: 1, color: 'error.main' }} />
                <Typography color="textSecondary">总成本</Typography>
              </Box>
              <Typography variant="h4">¥{(data?.total_cost || 0).toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography color="textSecondary">总Token数</Typography>
              </Box>
              <Typography variant="h4">
                {((data?.total_tokens || 0) / 1000).toFixed(1)}K
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography color="textSecondary">总请求数</Typography>
              </Box>
              <Typography variant="h4">{data?.total_requests || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MoneyIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography color="textSecondary">平均请求成本</Typography>
              </Box>
              <Typography variant="h4">
                ¥{(data?.avg_cost_per_request || 0).toFixed(4)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 按提供商统计表格 */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            按提供商/模型统计
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>提供商</TableCell>
                  <TableCell>模型</TableCell>
                  <TableCell align="right">总成本</TableCell>
                  <TableCell align="right">Token数</TableCell>
                  <TableCell align="right">请求数</TableCell>
                  <TableCell align="right">平均成本</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.cost_by_provider?.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Chip label={item.provider} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{item.model}</TableCell>
                    <TableCell align="right">¥{item.total_cost.toFixed(2)}</TableCell>
                    <TableCell align="right">
                      {(item.total_tokens / 1000).toFixed(1)}K
                    </TableCell>
                    <TableCell align="right">{item.request_count}</TableCell>
                    <TableCell align="right">
                      ¥{(item.total_cost / item.request_count).toFixed(4)}
                    </TableCell>
                  </TableRow>
                ))}
                {(!data?.cost_by_provider || data.cost_by_provider.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="textSecondary">暂无数据</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* 成本趋势表格 */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            成本趋势
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>日期</TableCell>
                  <TableCell align="right">成本</TableCell>
                  <TableCell align="right">Token数</TableCell>
                  <TableCell align="right">请求数</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.cost_trend?.slice(0, 10).map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>{item.date}</TableCell>
                    <TableCell align="right">¥{item.cost.toFixed(2)}</TableCell>
                    <TableCell align="right">{(item.tokens / 1000).toFixed(1)}K</TableCell>
                    <TableCell align="right">{item.requests}</TableCell>
                  </TableRow>
                ))}
                {(!data?.cost_trend || data.cost_trend.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="textSecondary">暂无数据</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};
