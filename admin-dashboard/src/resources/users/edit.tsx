import {
  Edit,
  SimpleForm,
  TextInput,
  EmailInput,
  PasswordInput,
  SelectInput,
  BooleanInput,
  Toolbar,
  SaveButton,
  DeleteButton,
  useNotify,
  useRedirect,
  email,
  minLength,
} from 'react-admin';
import { Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import { useState } from 'react';

const roleChoices = [
  { id: 'user', name: '普通用户' },
  { id: 'streamer', name: '主播' },
  { id: 'assistant', name: '助理' },
  { id: 'admin', name: '管理员' },
  { id: 'super_admin', name: '超级管理员' },
];

const statusChoices = [
  { id: 'active', name: '激活' },
  { id: 'inactive', name: '未激活' },
  { id: 'suspended', name: '暂停' },
  { id: 'banned', name: '封禁' },
];

// 重置密码对话框
const ResetPasswordDialog = ({ open, onClose, userId }: { open: boolean; onClose: () => void; userId: number }) => {
  const [password, setPassword] = useState('');
  const notify = useNotify();
  
  const handleReset = async () => {
    if (!password || password.length < 8) {
      notify('密码长度至少8个字符', { type: 'error' });
      return;
    }
    
    try {
      const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9019';
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ password }),
      });
      
      if (response.ok) {
        notify('密码重置成功', { type: 'success' });
        onClose();
        setPassword('');
      } else {
        const error = await response.json();
        notify(error.detail || '密码重置失败', { type: 'error' });
      }
    } catch (error) {
      notify('密码重置失败', { type: 'error' });
    }
  };
  
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>重置密码</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          type="password"
          label="新密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          margin="normal"
          helperText="密码长度至少8个字符"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleReset} variant="contained">确定</Button>
      </DialogActions>
    </Dialog>
  );
};

// 自定义工具栏
const CustomToolbar = (props: any) => {
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const userId = props.record?.id || props.id;
  
  return (
    <>
      <Toolbar {...props}>
        <SaveButton />
        <DeleteButton />
        <Box sx={{ flex: 1 }} />
        <Button
          variant="outlined"
          color="warning"
          onClick={() => setResetPasswordOpen(true)}
        >
          重置密码
        </Button>
      </Toolbar>
      <ResetPasswordDialog
        open={resetPasswordOpen}
        onClose={() => setResetPasswordOpen(false)}
        userId={userId}
      />
    </>
  );
};

export const UserEdit = () => {
  return (
    <Edit>
      <SimpleForm toolbar={<CustomToolbar />}>
        <TextInput source="username" label="用户名" disabled />
        <EmailInput
          source="email"
          label="邮箱"
          validate={email()}
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
        />
        <SelectInput
          source="status"
          label="状态"
          choices={statusChoices}
        />
        <BooleanInput source="is_active" label="激活" />
        <BooleanInput source="is_verified" label="已验证" />
        <BooleanInput source="email_verified" label="邮箱已验证" />
        <BooleanInput source="phone_verified" label="手机已验证" />
      </SimpleForm>
    </Edit>
  );
};

