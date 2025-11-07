import {
  List,
  Datagrid,
  TextField,
  NumberField,
  BooleanField,
  FunctionField,
  SearchInput,
  SelectInput,
  CreateButton,
  ExportButton,
  TopToolbar,
} from 'react-admin';
import { Chip } from '@mui/material';

const planFilters = [
  <SearchInput key="search" source="q" placeholder="搜索套餐名称" alwaysOn />,
  <SelectInput
    key="plan_type"
    source="plan_type"
    label="套餐类型"
    choices={[
      { id: 'free', name: '免费' },
      { id: 'basic', name: '基础' },
      { id: 'professional', name: '专业' },
      { id: 'enterprise', name: '企业' },
    ]}
    alwaysOn
  />,
  <SelectInput
    key="is_active"
    source="is_active"
    label="状态"
    choices={[
      { id: 'true', name: '启用' },
      { id: 'false', name: '禁用' },
    ]}
  />,
];

const ListActions = () => (
  <TopToolbar>
    <CreateButton />
    <ExportButton />
  </TopToolbar>
);

const PlanTypeField = ({ record }: any) => {
  const typeMap: Record<string, { label: string; color: string }> = {
    free: { label: '免费', color: 'default' },
    basic: { label: '基础', color: 'primary' },
    professional: { label: '专业', color: 'success' },
    enterprise: { label: '企业', color: 'error' },
  };

  const type = record?.plan_type || 'free';
  const typeInfo = typeMap[type] || typeMap['free'];

  return <Chip label={typeInfo.label} color={typeInfo.color as any} size="small" />;
};

const BillingCycleField = ({ record }: any) => {
  const cycleMap: Record<string, string> = {
    monthly: '月付',
    quarterly: '季付',
    yearly: '年付',
    lifetime: '终身',
  };

  return <>{cycleMap[record?.billing_cycle] || record?.billing_cycle}</>;
};

export const PlanList = () => {
  return (
    <List
      filters={planFilters}
      actions={<ListActions />}
      sort={{ field: 'created_at', order: 'DESC' }}
      perPage={25}
    >
      <Datagrid rowClick="show" bulkActionButtons={false}>
        <TextField source="id" label="ID" />
        <TextField source="name" label="套餐名称" />
        <FunctionField
          label="类型"
          render={(record: any) => <PlanTypeField record={record} />}
        />
        <NumberField
          source="price"
          label="价格"
          options={{ style: 'currency', currency: 'CNY' }}
        />
        <FunctionField
          label="计费周期"
          render={(record: any) => <BillingCycleField record={record} />}
        />
        <NumberField source="duration_days" label="有效天数" />
        <NumberField source="ai_quota" label="AI配额" />
        <BooleanField source="is_active" label="启用" />
        <TextField source="description" label="描述" />
      </Datagrid>
    </List>
  );
};
