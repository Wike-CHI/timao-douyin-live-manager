import {
  Show,
  SimpleShowLayout,
  TextField,
  EmailField,
  BooleanField,
  DateField,
  TabbedShowLayout,
  Tab,
  FunctionField,
} from 'react-admin';
import { Chip, Box, Typography, Paper, Grid } from '@mui/material';

// 角色显示
const RoleField = ({ record }: any) => {
  const roleMap: Record<string, string> = {
    user: '普通用户',
    streamer: '主播',
    assistant: '助理',
    admin: '管理员',
    super_admin: '超级管理员',
  };
  
  const colorMap: Record<string, string> = {
    user: 'default',
    streamer: 'primary',
    assistant: 'info',
    admin: 'warning',
    super_admin: 'error',
  };
  
  return (
    <Chip
      label={roleMap[record?.role] || record?.role}
      color={colorMap[record?.role] as any || 'default'}
    />
  );
};

// 状态显示
const StatusField = ({ record }: any) => {
  const status = record?.status || (record?.is_active ? 'active' : 'inactive');
  const statusMap: Record<string, { label: string; color: string }> = {
    active: { label: '激活', color: 'success' },
    inactive: { label: '未激活', color: 'default' },
    suspended: { label: '暂停', color: 'warning' },
    banned: { label: '封禁', color: 'error' },
  };
  
  const statusInfo = statusMap[status] || statusMap['inactive'];
  
  return (
    <Chip
      label={statusInfo.label}
      color={statusInfo.color as any}
    />
  );
};

export const UserShow = () => {
  return (
    <Show>
      <TabbedShowLayout>
        <Tab label="基本信息">
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>用户信息</Typography>
                <TextField source="user.id" label="ID" />
                <TextField source="user.username" label="用户名" />
                <EmailField source="user.email" label="邮箱" />
                <TextField source="user.phone" label="手机号" />
                <TextField source="user.nickname" label="昵称" />
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>账户状态</Typography>
                <FunctionField
                  label="角色"
                  render={(record: any) => <RoleField record={record?.user || record} />}
                />
                <FunctionField
                  label="状态"
                  render={(record: any) => <StatusField record={record?.user || record} />}
                />
                <BooleanField source="user.is_active" label="激活" />
                <BooleanField source="user.is_verified" label="已验证" />
                <BooleanField source="user.email_verified" label="邮箱已验证" />
                <BooleanField source="user.phone_verified" label="手机已验证" />
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>登录信息</Typography>
                <TextField source="user.login_count" label="登录次数" />
                <DateField source="user.last_login_at" label="最后登录" showTime />
                <DateField source="user.created_at" label="注册时间" showTime />
                <DateField source="user.updated_at" label="更新时间" showTime />
              </Paper>
            </Grid>
          </Grid>
        </Tab>
        
        <Tab label="订阅信息">
          <FunctionField
            label="订阅列表"
            render={(record: any) => {
              const subscriptions = record?.subscriptions || [];
              if (subscriptions.length === 0) {
                return <Typography>暂无订阅</Typography>;
              }
              return (
                <Box>
                  {subscriptions.map((sub: any, index: number) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="subtitle1">
                        {sub.plan?.name || sub.name || `订阅 #${index + 1}`}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        状态: {sub.status || '未知'}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              );
            }}
          />
        </Tab>
        
        <Tab label="使用统计">
          <FunctionField
            label="统计信息"
            render={(record: any) => {
              const stats = record?.stats || {};
              return (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2">订阅统计</Typography>
                      <Typography>总订阅数: {stats.total_subscriptions || 0}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2">支付统计</Typography>
                      <Typography>总支付数: {stats.total_payments || 0}</Typography>
                      <Typography>总消费: ¥{stats.total_spent || 0}</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2">活跃会话</Typography>
                      <Typography>活跃会话数: {stats.active_sessions || 0}</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              );
            }}
          />
        </Tab>
        
        <Tab label="操作记录">
          <FunctionField
            label="审计日志"
            render={(record: any) => {
              const logs = record?.audit_logs || [];
              if (logs.length === 0) {
                return <Typography>暂无操作记录</Typography>;
              }
              return (
                <Box>
                  {logs.map((log: any, index: number) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="subtitle2">{log.action || '未知操作'}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {log.created_at || log.timestamp}
                      </Typography>
                      {log.description && (
                        <Typography variant="body2">{log.description}</Typography>
                      )}
                    </Paper>
                  ))}
                </Box>
              );
            }}
          />
        </Tab>
      </TabbedShowLayout>
    </Show>
  );
};

