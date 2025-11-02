# 管理后台系统实现指南

## 快速开始

### 1. 项目初始化

```bash
# 创建新的React项目（使用Vite）
npm create vite@latest admin-dashboard -- --template react-ts

cd admin-dashboard

# 安装依赖
npm install react-admin ra-data-simple-rest
npm install @mui/material @emotion/react @emotion/styled
npm install recharts react-hook-form yup @hookform/resolvers
npm install axios
npm install @mui/icons-material
```

### 2. 项目配置

#### package.json
```json
{
  "name": "admin-dashboard",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-admin": "^4.15.0",
    "ra-data-simple-rest": "^4.1.0",
    "@mui/material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "recharts": "^2.8.0",
    "react-hook-form": "^7.47.0",
    "yup": "^1.3.0",
    "axios": "^1.5.0"
  }
}
```

#### vite.config.ts
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9019',
        changeOrigin: true,
      },
    },
  },
});
```

### 3. 基础结构

#### src/App.tsx
```typescript
import { Admin, Resource, Layout } from 'react-admin';
import { dataProvider } from './dataProvider';
import { authProvider } from './authProvider';
import { UserList, UserShow, UserCreate, UserEdit } from './resources/users';
import { PaymentList, PaymentShow } from './resources/payments';
import { PlanList, PlanShow, PlanCreate, PlanEdit } from './resources/plans';
import { Dashboard } from './resources/analytics/Dashboard';

function App() {
  return (
    <Admin
      dataProvider={dataProvider}
      authProvider={authProvider}
      dashboard={Dashboard}
      layout={MyLayout}
    >
      <Resource
        name="users"
        list={UserList}
        show={UserShow}
        create={UserCreate}
        edit={UserEdit}
      />
      <Resource
        name="payments"
        list={PaymentList}
        show={PaymentShow}
      />
      <Resource
        name="plans"
        list={PlanList}
        show={PlanShow}
        create={PlanCreate}
        edit={PlanEdit}
      />
    </Admin>
  );
}

export default App;
```

---

## 实现步骤

### 阶段 1: 基础搭建（Week 1）

1. ✅ 项目初始化和依赖安装
2. ✅ 配置路由和基础布局
3. ✅ 实现认证提供者
4. ✅ 实现数据提供者（对接后端API）
5. ✅ 创建基础资源页面（用户列表）

### 阶段 2: 核心功能（Week 2-3）

1. ✅ 用户管理完整CRUD
2. ✅ 支付管理（列表、详情、退款）
3. ✅ 套餐管理完整CRUD
4. ✅ 基础统计图表

### 阶段 3: 高级功能（Week 4）

1. ✅ AI监控页面
2. ✅ 在线用户统计
3. ✅ 流水统计
4. ✅ 报表导出

### 阶段 4: 优化和测试（Week 5）

1. ✅ 性能优化
2. ✅ 响应式适配
3. ✅ 测试编写
4. ✅ 文档完善

---

## 后端API扩展

需要在现有后端添加以下API端点：

### 1. 扩展 Admin API

文件：`server/app/api/admin.py`

添加端点：
- `/api/admin/users` - 用户列表（支持过滤、排序、分页）
- `/api/admin/users/:id` - 用户详情
- `/api/admin/payments` - 支付列表
- `/api/admin/payments/:id/mark-paid` - 手动标记已支付
- `/api/admin/payments/:id/refund` - 退款
- `/api/admin/plans` - 套餐CRUD
- `/api/admin/ai/usage/stats` - AI使用统计
- `/api/admin/online-users/count` - 在线用户数
- `/api/admin/sessions/active` - 活跃会话
- `/api/admin/revenue/stats` - 收入统计

### 2. WebSocket连接管理

跟踪WebSocket连接：
- 连接时记录到Redis或内存
- 断开时清理
- 提供查询接口

---

## 部署

### 开发环境

```bash
# 启动后端（已存在）
npm run dev

# 启动管理后台（新项目）
cd admin-dashboard
npm run dev
```

访问：http://localhost:3000

### 生产环境

```bash
# 构建
npm run build

# 部署到静态服务器（Nginx等）
# 或集成到现有Electron应用
```

---

## 常见问题

### Q1: 如何自定义Data Provider？

A: 继承 `ra-data-simple-rest` 或实现 `DataProvider` 接口，覆盖需要自定义的方法。

### Q2: 如何添加自定义操作？

A: 在资源页面中使用 `<Button>` 组件，调用自定义API端点。

### Q3: 如何处理文件上传？

A: 使用 `<FileInput>` 组件，配合后端文件上传API。

### Q4: 如何实现实时数据更新？

A: 使用 WebSocket 或 Server-Sent Events (SSE)，配合 React Query 的 `refetchInterval`。

---

## 参考资源

- [react-admin 官方文档](https://marmelab.com/react-admin/)
- [Material-UI 文档](https://mui.com/)
- [Recharts 文档](https://recharts.org/)
- [React Hook Form 文档](https://react-hook-form.com/)

---

**文档版本**：v1.0  
**创建日期**：2025-11-02

