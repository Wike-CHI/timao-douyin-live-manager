import {
  List,
  Datagrid,
  TextField,
  EmailField,
  BooleanField,
  DateField,
  FilterForm,
  SearchInput,
  SelectInput,
  BooleanInput,
  CreateButton,
  TopToolbar,
  ExportButton,
  useListContext,
} from 'react-admin';
import { Chip } from '@mui/material';

// 角色选项
const roleChoices = [
  { id: 'user', name: '普通用户' },
  { id: 'streamer', name: '主播' },
  { id: 'assistant', name: '助理' },
  { id: 'admin', name: '管理员' },
  { id: 'super_admin', name: '超级管理员' },
];

// 状态选项
const statusChoices = [
  { id: true, name: '激活' },
  { id: false, name: '未激活' },
];

// 自定义过滤器
const UserFilter = () => (
  <FilterForm>
    <SearchInput source="search" alwaysOn placeholder="搜索用户名、邮箱、手机号" />
    <SelectInput source="filter.role" choices={roleChoices} label="角色" />
    <SelectInput source="filter.is_active" choices={statusChoices} label="状态" />
    <BooleanInput source="filter.is_verified" label="已验证" />
  </FilterForm>
);

// 角色显示组件
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
      size="small"
    />
  );
};

// 列表工具栏
const ListActions = () => (
  <TopToolbar>
    <CreateButton />
    <ExportButton />
  </TopToolbar>
);

export const UserList = () => {
  return (
    <List
      filters={<UserFilter />}
      actions={<ListActions />}
      sort={{ field: 'id', order: 'DESC' }}
    >
      <Datagrid rowClick="show">
        <TextField source="id" />
        <TextField source="username" label="用户名" />
        <EmailField source="email" />
        <TextField source="nickname" label="昵称" />
        <TextField source="phone" label="手机号" />
        <RoleField label="角色" />
        <BooleanField source="is_active" label="激活" />
        <BooleanField source="is_verified" label="已验证" />
        <DateField source="last_login_at" label="最后登录" showTime />
        <DateField source="created_at" label="注册时间" showTime />
      </Datagrid>
    </List>
  );
};

