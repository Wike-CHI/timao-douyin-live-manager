export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  nickname?: string;
  full_name?: string;
  avatar_url?: string;
  role: 'user' | 'streamer' | 'assistant' | 'admin' | 'super_admin';
  status?: 'active' | 'inactive' | 'suspended' | 'banned';
  is_active: boolean;
  is_verified: boolean;
  email_verified?: boolean;
  phone_verified?: boolean;
  login_count?: number;
  last_login_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface UserDetail {
  user: User;
  subscriptions?: any[];
  payments?: any[];
  audit_logs?: any[];
  stats?: {
    total_subscriptions?: number;
    total_payments?: number;
    total_spent?: number;
    last_login?: string;
    registration_date?: string;
    active_sessions?: number;
  };
}

