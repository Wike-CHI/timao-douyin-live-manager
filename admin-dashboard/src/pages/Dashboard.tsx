import { Card, CardContent, Typography, Grid, Box, CircularProgress } from '@mui/material';
import { useNotify } from 'react-admin';
import { useEffect, useState } from 'react';
import PeopleIcon from '@mui/icons-material/People';
import PaymentIcon from '@mui/icons-material/Payment';
import SubscriptionsIcon from '@mui/icons-material/Subscriptions';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';

interface SystemStats {
  users: {
    total: number;
    active: number;
    new_today: number;
    new_week: number;
    new_month: number;
  };
  subscriptions: {
    total: number;
    active: number;
  };
  payments: {
    total: number;
    completed: number;
    success_rate: number;
  };
  revenue: {
    total: number;
    today: number;
    week: number;
    month: number;
  };
}

export const Dashboard = () => {
  const notify = useNotify();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:15000';
        const token = localStorage.getItem('token');
        
        const response = await fetch(`${API_BASE}/api/admin/stats`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) {
          throw new Error('获取统计数据失败');
        }
        
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('获取统计数据失败:', error);
        notify('获取统计数据失败', { type: 'error' });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    
    // 每30秒刷新一次
    const interval = setInterval(fetchStats, 30000);
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
    <Box>
      <Typography variant="h4" gutterBottom>
        仪表板
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography color="textSecondary">
                  总用户数
                </Typography>
              </Box>
              <Typography variant="h4">
                {stats?.users.total || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                活跃: {stats?.users.active || 0} | 今日新增: {stats?.users.new_today || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PaymentIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography color="textSecondary">
                  总支付数
                </Typography>
              </Box>
              <Typography variant="h4">
                {stats?.payments.total || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                成功: {stats?.payments.completed || 0} ({((stats?.payments.success_rate || 0) * 100).toFixed(1)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SubscriptionsIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography color="textSecondary">
                  订阅总数
                </Typography>
              </Box>
              <Typography variant="h4">
                {stats?.subscriptions.total || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                活跃订阅: {stats?.subscriptions.active || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AttachMoneyIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography color="textSecondary">
                  总收入
                </Typography>
              </Box>
              <Typography variant="h4">
                ¥{(stats?.revenue.total || 0).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                本月: ¥{(stats?.revenue.month || 0).toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          欢迎使用管理后台
        </Typography>
        <Typography variant="body1" color="text.secondary">
          数据每30秒自动刷新。当前用户管理模块已完整实现，其他模块正在开发中。
        </Typography>
      </Box>
    </Box>
  );
};

