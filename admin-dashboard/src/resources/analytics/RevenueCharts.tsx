import React, { useState, useEffect } from 'react';
import {
  Typography,
  Grid,
  Box,
  CircularProgress,
  ToggleButtonGroup,
  ToggleButton,
  Paper,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Title } from 'react-admin';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const RevenueCharts: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7' | '30' | '90'>('30');
  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [userGrowthData, setUserGrowthData] = useState<any[]>([]);
  const [planDistribution, setPlanDistribution] = useState<any[]>([]);
  const [paymentMethodStats, setPaymentMethodStats] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // 每5分钟刷新
    return () => clearInterval(interval);
  }, [period]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9030';

      // 获取收入趋势
      const revenueRes = await fetch(`${baseUrl}/api/admin/charts/revenue?days=${period}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (revenueRes.ok) {
        const data = await revenueRes.json();
        setRevenueData(data.data || []);
      }

      // 获取用户增长
      const userGrowthRes = await fetch(`${baseUrl}/api/admin/charts/user-growth?days=${period}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (userGrowthRes.ok) {
        const data = await userGrowthRes.json();
        setUserGrowthData(data.data || []);
      }

      // 获取套餐分布
      const planRes = await fetch(`${baseUrl}/api/admin/stats/plan-distribution`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (planRes.ok) {
        const data = await planRes.json();
        setPlanDistribution(data.map((item: any) => ({
          name: item.plan_name,
          value: item.active_count,
        })));
      }

      // 获取支付方式统计
      const paymentRes = await fetch(`${baseUrl}/api/admin/stats/payment-methods`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (paymentRes.ok) {
        const data = await paymentRes.json();
        setPaymentMethodStats(data.map((item: any) => ({
          name: item.payment_method,
          amount: item.total_amount,
          count: item.count,
        })));
      }
    } catch (error) {
      console.error('获取图表数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (_event: React.MouseEvent<HTMLElement>, newPeriod: '7' | '30' | '90' | null) => {
    if (newPeriod !== null) {
      setPeriod(newPeriod);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Title title="收入统计分析" />
      
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h5">数据分析看板</Typography>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={handlePeriodChange}
          size="small"
        >
          <ToggleButton value="7">近7天</ToggleButton>
          <ToggleButton value="30">近30天</ToggleButton>
          <ToggleButton value="90">近90天</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Grid container spacing={3}>
        {/* 收入趋势图 */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              收入趋势
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="amount" 
                  stroke="#8884d8" 
                  name="收入金额"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#82ca9d" 
                  name="订单数"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 套餐分布饼图 */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              套餐分布
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={planDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {planDistribution.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 用户增长趋势 */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              用户增长趋势
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={userGrowthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="new_users" fill="#8884d8" name="新增用户" />
                <Bar dataKey="total_users" fill="#82ca9d" name="总用户数" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 支付方式统计 */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              支付方式统计
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={paymentMethodStats} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} />
                <Tooltip />
                <Legend />
                <Bar dataKey="amount" fill="#8884d8" name="总金额" />
                <Bar dataKey="count" fill="#82ca9d" name="订单数" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};
