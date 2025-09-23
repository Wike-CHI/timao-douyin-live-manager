interface LoginPayload {
  email: string;
  password: string;
}

interface RegisterPayload {
  email: string;
  password: string;
  nickname: string;
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockLogin = async (payload: LoginPayload) => {
  await delay(800);
  if (!payload.email || !payload.password) {
    throw new Error('请输入邮箱和密码');
  }
  return {
    success: true,
    token: 'mock-token',
    user: {
      id: 'user-1',
      email: payload.email,
      nickname: '提猫主播',
    },
    isPaid: false,
  };
};

export const mockRegister = async (payload: RegisterPayload) => {
  await delay(1000);
  if (!payload.email || !payload.password || !payload.nickname) {
    throw new Error('请填写完整信息');
  }
  return {
    success: true,
    user: {
      id: 'user-new',
      email: payload.email,
      nickname: payload.nickname,
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
