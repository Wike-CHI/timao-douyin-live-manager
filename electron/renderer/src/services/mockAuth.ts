interface LoginPayload {
  email: string;
  password: string;
}

interface RegisterPayload {
  email: string;
  password: string;
  nickname: string;
}

// 导入类型
import type { UserInfo, LoginResponse, RegisterResponse } from './auth';

// 简易内存态，模拟首次免费使用
let mockFirstFreeUsed = false;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockLogin = async (payload: LoginPayload): Promise<LoginResponse> => {
  await delay(800);
  if (!payload.email || !payload.password) {
    throw new Error('请输入邮箱和密码');
  }
  return {
    success: true,
    token: 'mock-token',
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 86400, // 24小时
    user: {
      id: 1,
      username: 'mockuser',
      email: payload.email,
      nickname: '提猫主播',
      role: 'user',
      status: 'active',
      email_verified: true,
      phone_verified: false,
      created_at: new Date().toISOString(),
    },
    isPaid: false,
    firstFreeUsed: mockFirstFreeUsed,
  };
};

export const mockRegister = async (payload: RegisterPayload): Promise<RegisterResponse> => {
  await delay(1000);
  if (!payload.email || !payload.password || !payload.nickname) {
    throw new Error('请填写完整信息');
  }
  // 注册后重置首次免费状态
  mockFirstFreeUsed = false;
  return {
    success: true,
    user: {
      id: 2,
      username: 'mockuser',
      email: payload.email,
      nickname: payload.nickname,
      role: 'user',
      status: 'active',
      email_verified: true,
      phone_verified: false,
      created_at: new Date().toISOString(),
    },
  };
};

export const mockPaymentUpload = async (file: File) => {
  await delay(1200);
  if (!file) {
    throw new Error('请上传收款截图');
  }
  return {
    success: true,
    status: 'PENDING_REVIEW' as const,
    message: '已提交审核，预计 5 秒内完成',
  };
};

export const mockPaymentPoll = async () => {
  await delay(2000);
  const approved = Math.random() > 0.2;
  return {
    success: approved,
    status: approved ? 'APPROVED' : 'REJECTED',
    message: approved ? '支付已验证，感谢支持！' : '截图识别失败，请重新上传',
  };
};

export const mockUseFirstFree = async () => {
  await delay(300);
  if (mockFirstFreeUsed) return { success: false, message: '首次免费已使用' };
  mockFirstFreeUsed = true;
  return { success: true, firstFreeUsed: true };
};