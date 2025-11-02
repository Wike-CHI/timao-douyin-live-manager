# 管理后台系统设计文档

## 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────┐
│            React Admin Dashboard                 │
│  (Material-UI + React Admin + Data Provider)   │
└──────────────────┬──────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────┐
│         FastAPI Backend (现有)                   │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │ Auth API │ Payment  │ User API │ Admin API│ │
│  │          │ API      │          │ (扩展)   │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Database (MySQL)                    │
│  ┌──────┬─────────┬─────────┬─────────┬──────┐ │
│  │Users │Payments │Plans    │Sessions │AI    │ │
│  │      │         │         │         │Usage │ │
│  └──────┴─────────┴─────────┴─────────┴──────┘ │
└──────────────────────────────────────────────────┘
```

### 2. 技术选型

#### 前端
- **react-admin** v4.x：快速构建管理界面
- **Material-UI** (MUI) v5：UI组件库
- **TypeScript**：类型安全
- **React Query**：数据获取和缓存
- **Recharts**：图表可视化
- **React Hook Form**：表单管理

#### 后端
- **FastAPI**：现有框架
- **SQLAlchemy**：ORM
- **Pydantic**：数据验证
- **JWT**：身份认证

---

## 目录结构

```
admin-dashboard/
├── public/
│   └── index.html
├── src/
│   ├── App.tsx                    # 主应用入口
│   ├── AppLayout.tsx             # 布局组件
│   ├── authProvider.ts           # 认证提供者
│   ├── dataProvider.ts           # 数据提供者（API对接）
│   ├── resources/                # 资源模块
│   │   ├── users/
│   │   │   ├── list.tsx
│   │   │   ├── show.tsx
│   │   │   ├── create.tsx
│   │   │   ├── edit.tsx
│   │   │   └── UserFilters.tsx
│   │   ├── payments/
│   │   │   ├── list.tsx
│   │   │   ├── show.tsx
│   │   │   └── RefundDialog.tsx
│   │   ├── plans/
│   │   │   ├── list.tsx
│   │   │   ├── show.tsx
│   │   │   ├── create.tsx
│   │   │   ├── edit.tsx
│   │   │   └── PlanFeaturesEditor.tsx
│   │   └── analytics/
│   │       ├── Dashboard.tsx
│   │       ├── AIUsageStats.tsx
│   │       ├── RevenueStats.tsx
│   │       └── OnlineUsers.tsx
│   ├── components/               # 共享组件
│   │   ├── charts/
│   │   │   ├── LineChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   └── PieChart.tsx
│   │   ├── filters/
│   │   └── actions/
│   ├── utils/                    # 工具函数
│   │   ├── api.ts               # API客户端
│   │   ├── date.ts              # 日期处理
│   │   └── format.ts            # 格式化
│   └── types/                    # TypeScript类型
│       ├── user.ts
│       ├── payment.ts
│       ├── plan.ts
│       └── api.ts
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 数据模型设计

### 1. API响应格式

所有API遵循RESTful规范，响应格式统一：

```typescript
// 列表响应
interface ListResponse<T> {
  data: T[];
  total: number;
  page: number;
  perPage: number;
}

// 单个资源响应
interface ResourceResponse<T> {
  data: T;
}

// 错误响应
interface ErrorResponse {
  error: {
    message: string;
    code?: string;
    details?: any;
  };
}
```

### 2. 核心实体类型

#### User
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  nickname?: string;
  avatar_url?: string;
  role: 'user' | 'streamer' | 'assistant' | 'admin' | 'super_admin';
  status: 'active' | 'inactive' | 'suspended' | 'banned';
  email_verified: boolean;
  phone_verified: boolean;
  login_count: number;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  
  // 关联数据（详情页）
  subscription?: UserSubscription;
  active_sessions?: number;
}
```

#### Payment
```typescript
interface Payment {
  id: number;
  order_no: string;
  user_id: number;
  user?: {
    username: string;
    email: string;
  };
  subscription_id?: number;
  amount: number;
  currency: string;
  payment_method: 'alipay' | 'wechat' | 'bank_card' | 'paypal' | 'stripe';
  status: 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled';
  third_party_order_id?: string;
  paid_at?: string;
  refunded_at?: string;
  refund_reason?: string;
  invoice_requested: boolean;
  created_at: string;
}
```

#### SubscriptionPlan
```typescript
interface SubscriptionPlan {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  plan_type: 'free' | 'basic' | 'premium' | 'enterprise';
  price: number;
  currency: string;
  original_price?: number;
  billing_cycle: number; // 天数
  max_streams?: number;
  max_storage_gb?: number;
  max_ai_requests?: number;
  max_export_count?: number;
  features: string[]; // JSON数组或字符串
  is_active: boolean;
  is_popular: boolean;
  sort_order: number;
  subscription_count?: number; // 使用该套餐的用户数
  created_at: string;
  updated_at: string;
}
```

---

## 页面设计

### 1. 仪表板（Dashboard）

```
┌─────────────────────────────────────────────────┐
│  📊 仪表板                                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 总用户数 │ │ 在线用户 │ │ 今日收入 │        │
│  │  1,234   │ │   456    │ │  ¥12,345 │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ 📈 收入趋势（最近30天）                   │  │
│  │  [Line Chart]                            │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────┐ ┌──────────────────┐    │
│  │ 💰 Token消耗     │ │ 📦 套餐分布       │    │
│  │  [Pie Chart]     │ │  [Bar Chart]      │    │
│  └──────────────────┘ └──────────────────┘    │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 2. 用户管理页面

#### 2.1 用户列表
```typescript
<Resource
  name="users"
  list={UserList}
  show={UserShow}
  create={UserCreate}
  edit={UserEdit}
/>
```

**功能**：
- 表格显示：ID、用户名、邮箱、角色、状态、注册时间、最后登录
- 搜索：用户名、邮箱、手机号
- 过滤：角色、状态、注册时间范围
- 批量操作：批量激活/停用、批量删除（软删除）

#### 2.2 用户详情
```typescript
<TabbedShowLayout>
  <Tab label="基本信息">
    <TextField source="username" />
    <TextField source="email" />
    {/* ... */}
  </Tab>
  <Tab label="订阅信息">
    <SubscriptionInfo />
  </Tab>
  <Tab label="使用统计">
    <UserStats />
  </Tab>
  <Tab label="操作记录">
    <AuditLogs />
  </Tab>
</TabbedShowLayout>
```

### 3. 支付管理页面

#### 3.1 支付列表
- 表格列：订单号、用户、金额、状态、支付方式、时间
- 快速操作：查看详情、退款、标记已支付

#### 3.2 支付详情
- 订单信息卡片
- 用户信息
- 退款操作（如有）
- 发票管理

### 4. 订阅套餐管理

#### 4.1 套餐列表
- 卡片式或表格式展示
- 显示：名称、类型、价格、状态、订阅用户数

#### 4.2 套餐编辑表单
```typescript
<SimpleForm>
  <TextInput source="name" />
  <TextInput source="display_name" />
  <SelectInput source="plan_type" choices={PLAN_TYPES} />
  <NumberInput source="price" />
  <NumberInput source="billing_cycle" />
  
  {/* 功能限制 */}
  <SectionTitle label="功能限制" />
  <NumberInput source="max_streams" />
  <NumberInput source="max_storage_gb" />
  <NumberInput source="max_ai_requests" />
  
  {/* 功能列表 */}
  <ArrayInput source="features">
    <TextInput />
  </ArrayInput>
</SimpleForm>
```

### 5. AI监控页面

#### 5.1 AI使用统计
- 实时统计卡片（当前小时、今日）
- Token消耗趋势图（按小时/天）
- 按模型统计饼图
- 按功能统计柱状图
- 成本分析表格

#### 5.2 AI网关管理
- 当前配置显示
- 服务商列表
- 切换服务商表单
- 注册/编辑服务商对话框

### 6. 在线用户统计

- 实时在线人数卡片
- 在线用户趋势图（24小时/7天）
- 活跃会话列表表格
- 会话详情对话框

### 7. 流水统计

- 收入概览卡片（总/今日/本月）
- 收入趋势图（按天/周/月）
- 支付方式分布
- 套餐收入对比
- 财务报表导出

---

## API设计

### 1. 用户管理API

```typescript
// 获取用户列表
GET /api/admin/users
Query: {
  page?: number;
  perPage?: number;
  filter?: {
    role?: string;
    status?: string;
    search?: string;
    created_from?: string;
    created_to?: string;
  };
  sort?: string; // "id" | "-id" | "created_at" | "-created_at"
}

// 获取用户详情
GET /api/admin/users/:id

// 创建用户
POST /api/admin/users
Body: {
  username: string;
  email: string;
  password: string;
  role?: string;
  status?: string;
  // ...
}

// 更新用户
PUT /api/admin/users/:id
Body: Partial<User>

// 删除用户（软删除）
DELETE /api/admin/users/:id
```

### 2. 支付管理API

```typescript
// 获取支付列表
GET /api/admin/payments
Query: {
  page?: number;
  perPage?: number;
  filter?: {
    status?: string;
    payment_method?: string;
    user_id?: number;
    date_from?: string;
    date_to?: string;
  };
}

// 获取支付详情
GET /api/admin/payments/:id

// 标记已支付（手动）
POST /api/admin/payments/:id/mark-paid
Body: {
  third_party_order_id?: string;
  notes?: string;
}

// 退款
POST /api/admin/payments/:id/refund
Body: {
  reason: string;
  amount?: number; // 部分退款
}
```

### 3. 套餐管理API

```typescript
// 获取套餐列表
GET /api/admin/plans

// 获取套餐详情
GET /api/admin/plans/:id

// 创建套餐
POST /api/admin/plans
Body: SubscriptionPlan

// 更新套餐
PUT /api/admin/plans/:id
Body: Partial<SubscriptionPlan>

// 删除套餐
DELETE /api/admin/plans/:id
```

### 4. AI监控API

```typescript
// 获取AI使用统计
GET /api/admin/ai/usage/stats
Query: {
  period?: 'hour' | 'day' | 'week' | 'month';
  start_date?: string;
  end_date?: string;
}

// 获取Token消耗详情
GET /api/admin/ai/usage/tokens
Query: {
  group_by?: 'model' | 'function' | 'user';
  // ...
}

// 获取成本分析
GET /api/admin/ai/usage/cost
```

### 5. 在线用户API

```typescript
// 获取在线用户数
GET /api/admin/online-users/count

// 获取活跃会话列表
GET /api/admin/sessions/active

// 强制断开会话
POST /api/admin/sessions/:id/disconnect
```

### 6. 流水统计API

```typescript
// 获取收入统计
GET /api/admin/revenue/stats
Query: {
  period?: 'day' | 'week' | 'month' | 'year';
  start_date?: string;
  end_date?: string;
}

// 获取支付统计
GET /api/admin/revenue/payments

// 导出财务报表
GET /api/admin/revenue/export
Query: {
  format: 'csv' | 'excel' | 'pdf';
  start_date: string;
  end_date: string;
}
```

---

## 认证和权限

### 1. 认证流程

```typescript
// authProvider.ts
const authProvider = {
  login: async ({ username, password }) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    if (response.ok) {
      const { access_token } = await response.json();
      localStorage.setItem('token', access_token);
      return Promise.resolve();
    }
    return Promise.reject();
  },
  
  logout: () => {
    localStorage.removeItem('token');
    return Promise.resolve();
  },
  
  checkAuth: () => {
    return localStorage.getItem('token')
      ? Promise.resolve()
      : Promise.reject();
  },
  
  getPermissions: async () => {
    const response = await fetch('/api/auth/me');
    const user = await response.json();
    return user.role === 'admin' || user.role === 'super_admin'
      ? Promise.resolve()
      : Promise.reject();
  },
};
```

### 2. 权限控制

```typescript
// 资源级别的权限控制
<Resource
  name="users"
  options={{
    permissions: {
      list: ['admin', 'super_admin'],
      create: ['super_admin'],
      edit: ['admin', 'super_admin'],
      delete: ['super_admin'],
    },
  }}
/>
```

---

## 数据提供者（Data Provider）

```typescript
// dataProvider.ts
import { DataProvider } from 'react-admin';

const dataProvider: DataProvider = {
  getList: async (resource, params) => {
    const { page, perPage, filter, sort } = params;
    const query = new URLSearchParams({
      page: page.toString(),
      perPage: perPage.toString(),
      ...(filter && { filter: JSON.stringify(filter) }),
      ...(sort && { sort: `${sort.field},${sort.order}` }),
    });
    
    const response = await fetch(
      `/api/admin/${resource}?${query}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );
    
    const data = await response.json();
    return {
      data: data.items,
      total: data.total,
    };
  },
  
  getOne: async (resource, params) => {
    // ...
  },
  
  create: async (resource, params) => {
    // ...
  },
  
  update: async (resource, params) => {
    // ...
  },
  
  delete: async (resource, params) => {
    // ...
  },
};
```

---

## 响应式设计

### 断点设置
- **移动端**：< 600px
- **平板**：600px - 960px
- **桌面**：> 960px

### 移动端适配
- 列表改为卡片式布局
- 表格改为可横向滚动
- 侧边栏改为抽屉式
- 图表自适应宽度

---

## 性能优化

### 1. 数据缓存
- 使用 React Query 缓存API响应
- 设置合理的缓存时间（统计数据5分钟，静态数据30分钟）

### 2. 虚拟滚动
- 大数据量列表使用虚拟滚动（react-window）

### 3. 懒加载
- 图表组件按需加载
- 详情页关联数据延迟加载

### 4. 分页和过滤
- 服务器端分页
- 服务器端过滤和排序

---

## 测试策略

### 1. 单元测试
- 组件测试（React Testing Library）
- 工具函数测试

### 2. 集成测试
- API集成测试
- 表单提交流程测试

### 3. E2E测试
- 关键流程测试（创建用户、处理退款等）
- 使用 Playwright 或 Cypress

---

**文档版本**：v1.0  
**创建日期**：2025-11-02  
**最后更新**：2025-11-02

