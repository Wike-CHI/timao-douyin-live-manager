import {
  List,
  Datagrid,
  TextField,
  NumberField,
  DateField,
  FunctionField,
  SearchInput,
  SelectInput,
  ExportButton,
  TopToolbar,
} from 'react-admin';
import { Chip } from '@mui/material';

const paymentFilters = [
  <SearchInput key="search" source="q" placeholder="搜索用户/订单号" alwaysOn />,
  <SelectInput
    key="status"
    source="status"
    label="支付状态"
    choices={[
      { id: 'pending', name: '待支付' },
      { id: 'completed', name: '已完成' },
      { id: 'failed', name: '失败' },
      { id: 'cancelled', name: '已取消' },
      { id: 'refunded', name: '已退款' },
    ]}
  />,
  <SelectInput
    key="payment_method"
    source="payment_method"
    label="支付方式"
    choices={[
      { id: 'wechat', name: '微信支付' },
      { id: 'alipay', name: '支付宝' },
      { id: 'balance', name: '余额支付' },
    ]}
  />,
];

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

  return <Chip label={statusInfo.label} color={statusInfo.color as any} size="small" />;
};

const PaymentMethodField = ({ record }: any) => {
  const methodMap: Record<string, string> = {
    wechat: '微信支付',
    alipay: '支付宝',
    balance: '余额支付',
  };

  return <span>{methodMap[record?.payment_method] || record?.payment_method}</span>;
};

const ListActions = () => (
  <TopToolbar>
    <ExportButton />
  </TopToolbar>
);

export const PaymentList = () => {
  return (
    <List
      filters={paymentFilters}
      actions={<ListActions />}
      perPage={25}
      sort={{ field: 'created_at', order: 'DESC' }}
    >
      <Datagrid rowClick="show" bulkActionButtons={false}>
        <TextField source="id" label="ID" />
        <TextField source="order_no" label="订单号" />
        <TextField source="user.username" label="用户" />
        <NumberField
          source="amount"
          label="金额"
          options={{ style: 'currency', currency: 'CNY' }}
        />
        <FunctionField
          label="支付方式"
          render={(record: any) => <PaymentMethodField record={record} />}
        />
        <FunctionField
          label="状态"
          render={(record: any) => <PaymentStatusField record={record} />}
        />
        <DateField source="created_at" label="创建时间" showTime />
        <DateField source="paid_at" label="支付时间" showTime />
      </Datagrid>
    </List>
  );
};
