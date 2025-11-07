import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { Title } from 'react-admin';

interface SystemHealth {
  database: string;
  expired_subscriptions: number;
  pending_payments: number;
  timestamp: string;
}

interface Activity {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  level: string;
  category: string;
  ip_address?: string;
  created_at: string;
  details?: any;
}

export const SystemMonitor: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [securityEvents, setSecurityEvents] = useState<Activity[]>([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30 * 1000); // 每30秒刷新
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9030';

      // 获取系统健康状态
      const healthRes = await fetch(`${baseUrl}/api/admin/system/health`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (healthRes.ok) {
        const data = await healthRes.json();
        setHealth(data);
      }

      // 获取最近活动
      const activitiesRes = await fetch(`${baseUrl}/api/admin/activities/recent?limit=20`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (activitiesRes.ok) {
        const data = await activitiesRes.json();
        setActivities(data || []);
      }

      // 获取安全事件
      const securityRes = await fetch(`${baseUrl}/api/admin/security/events?hours=24&limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (securityRes.ok) {
        const data = await securityRes.json();
        setSecurityEvents(data || []);
      }
    } catch (error) {
      console.error('获取系统监控数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHealthStatus = () => {
    if (!health) return { icon: <WarningIcon />, color: 'warning', text: '未知' };
    if (health.database === 'healthy') {
      return { icon: <CheckCircleIcon />, color: 'success', text: '正常' };
    }
    return { icon: <ErrorIcon />, color: 'error', text: '异常' };
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'info': return 'info';
      case 'warning': return 'warning';
      case 'error': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const statusInfo = getHealthStatus();

  return (
    <div>
      <Title title="系统监控" />
      
      <Grid container spacing={3}>
        {/* 系统健康状态 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Box mr={2} color={`${statusInfo.color}.main`}>
                {statusInfo.icon}
              </Box>
              <Typography variant="h6">
                系统健康状态: {statusInfo.text}
              </Typography>
            </Box>
            
            {health && (
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        数据库状态
                      </Typography>
                      <Typography variant="h6">
                        <Chip 
                          label={health.database} 
                          color={health.database === 'healthy' ? 'success' : 'error'}
                          size="small"
                        />
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        过期订阅
                      </Typography>
                      <Typography variant="h6">
                        {health.expired_subscriptions} 个
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        待处理支付
                      </Typography>
                      <Typography variant="h6">
                        {health.pending_payments} 个
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* 安全事件 */}
        {securityEvents.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                安全事件 (最近24小时)
              </Typography>
              <Alert severity="warning" sx={{ mb: 2 }}>
                发现 {securityEvents.length} 个安全相关事件
              </Alert>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>时间</TableCell>
                      <TableCell>用户ID</TableCell>
                      <TableCell>操作</TableCell>
                      <TableCell>级别</TableCell>
                      <TableCell>IP地址</TableCell>
                      <TableCell>详情</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {securityEvents.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell>
                          {new Date(event.created_at).toLocaleString('zh-CN')}
                        </TableCell>
                        <TableCell>{event.user_id || '-'}</TableCell>
                        <TableCell>{event.action}</TableCell>
                        <TableCell>
                          <Chip 
                            label={event.level} 
                            color={getLevelColor(event.level)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{event.ip_address || '-'}</TableCell>
                        <TableCell>
                          {event.details ? JSON.stringify(event.details).substring(0, 50) : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        )}

        {/* 最近活动 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              最近活动
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>时间</TableCell>
                    <TableCell>用户</TableCell>
                    <TableCell>操作</TableCell>
                    <TableCell>资源类型</TableCell>
                    <TableCell>资源ID</TableCell>
                    <TableCell>类别</TableCell>
                    <TableCell>IP地址</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activities.map((activity) => (
                    <TableRow key={activity.id}>
                      <TableCell>
                        {new Date(activity.created_at).toLocaleString('zh-CN')}
                      </TableCell>
                      <TableCell>{activity.user_id}</TableCell>
                      <TableCell>{activity.action}</TableCell>
                      <TableCell>
                        <Chip label={activity.resource_type} size="small" />
                      </TableCell>
                      <TableCell>{activity.resource_id || '-'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={activity.category} 
                          color={getLevelColor(activity.level)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{activity.ip_address || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};
