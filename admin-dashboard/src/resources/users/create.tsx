import {
  Create,
  SimpleForm,
  TextInput,
  PasswordInput,
  SelectInput,
  required,
  minLength,
  email,
} from 'react-admin';

const roleChoices = [
  { id: 'user', name: '普通用户' },
  { id: 'streamer', name: '主播' },
  { id: 'assistant', name: '助理' },
  { id: 'admin', name: '管理员' },
  { id: 'super_admin', name: '超级管理员' },
];

export const UserCreate = () => {
  return (
    <Create>
      <SimpleForm>
        <TextInput
          source="username"
          label="用户名"
          validate={[required(), minLength(3)]}
          helperText="用户名长度至少3个字符"
        />
        <TextInput
          source="email"
          label="邮箱"
          type="email"
          validate={[required(), email()]}
        />
        <PasswordInput
          source="password"
          label="密码"
          validate={[required(), minLength(8)]}
          helperText="密码长度至少8个字符"
        />
        <TextInput
          source="nickname"
          label="昵称"
          fullWidth
        />
        <TextInput
          source="phone"
          label="手机号"
          fullWidth
        />
        <SelectInput
          source="role"
          label="角色"
          choices={roleChoices}
          defaultValue="user"
          validate={required()}
        />
      </SimpleForm>
    </Create>
  );
};

