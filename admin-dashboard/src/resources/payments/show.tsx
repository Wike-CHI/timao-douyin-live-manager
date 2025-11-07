import {
  Show,
  TabbedShowLayout,
  Tab,
  TextField,
  NumberField,
  DateField,
  FunctionField,
} from 'react-admin';
import { Chip, Typography, Paper, Grid } from '@mui/material';

const PaymentStatusField = ({ record }: any) => {
  const statusMap: Record<string, { label: string; color: string }> = {
    pending: { label: '待支付', color: 'warning' },
    completed: { label: '已完成', color: 'success' },
    failed: { label: '失败', color: 'error' },
    cancelled: { label: '已取消', color: 'default' },
    refunded: { label: '已退款', color: 'info' },
  };

  const status = record?.status || 'pending';
  const statusInfo = statusMap[status] || statusMap['pending'];

  return <Chip label={statusInfo.label} color={statusInfo.color as any} />;
};

export const PaymentShow = () => {
  return (
    <Show>
      <TabbedShowLayout>
        <Tab label="支付信息">
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  基本信息
                </Typography>
                <TextField source="id" label="支付ID" />
                <TextField source="order_no" label="订单号" />
                <TextField source="user.username" label="用户" />
                <TextField source="user.email" label="用户邮箱" />
                <NumberField
                  source="amount"
                  label="支付金额"
                  options={{ style: 'currency', currency: 'CNY' }}
                />
                <TextField source="payment_method" label="支付方式" />
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  状态信息
                </Typography>
                <FunctionField
                  label="支付状态"
                  render={(record: any) => <PaymentStatusField record={record} />}
                />
                <DateField source="created_at" label="创建时间" showTime />
                <DateField source="paid_at" label="支付时间" showTime />
                <DateField source="updated_at" label="更新时间" showTime />
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  交易详情
                </Typography>
                <TextField source="transaction_id" label="交易ID" />
                <TextField source="description" label="描述" />
                <FunctionField
                  label="备注"
                  render={(record: any) => (
                    <Typography variant="body2" color="text.secondary">
                      {record?.note || '无'}
                    </Typography>
                  )}
                />
              </Paper>
            </Grid>
          </Grid>
        </Tab>

        <Tab label="关联信息">
          <FunctionField
            label="订阅信息"
            render={(record: any) => {
              const subscription = record?.subscription;
              if (!subscription) {
                return <Typography>无关联订阅</Typography>;
              }
              return (
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle1">
                    订阅套餐: {subscription.plan?.name || '未知'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    状态: {subscription.status}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    开始时间: {subscription.start_date}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    结束时间: {subscription.end_date}
                  </Typography>
                </Paper>
              );
            }}
          />
        </Tab>
      </TabbedShowLayout>
    </Show>
  );
};
