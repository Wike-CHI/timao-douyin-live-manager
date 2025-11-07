# 提猫直播助手 - 管理后台系统

基于 React Admin 4 构建的现代化管理后台，提供用户管理、支付管理、订阅套餐管理、AI成本监控等核心功能。

## ✨ 功能特性

### ✅ 已实现模块

#### 🎛️ 仪表板
- 实时数据展示（用户/支付/订阅/收入统计）
- 自动刷新机制（每30秒）
- Material-UI 图标美化
- 响应式布局

#### 👥 用户管理
- **列表页**: 搜索、筛选（角色/状态）、分页、导出CSV
- **详情页**: 4个Tab页（基本信息/订阅信息/使用统计/操作记录）
- **创建页**: 表单验证、角色分配
- **编辑页**: 信息修改、角色管理、重置密码
- **角色类型**: user, streamer, assistant, admin, super_admin
- **状态管理**: 激活/未激活/暂停/封禁

#### 💳 支付管理
- **列表页**: 搜索订单号/用户、筛选状态和支付方式
- **详情页**: 支付信息、交易详情、关联订阅
- **状态展示**: 待支付/已完成/失败/已取消/已退款

#### 📦 订阅套餐管理
- **列表页**: 搜索套餐名、筛选类型和状态
- **详情页**: 基本信息/功能权限/时间信息
- **创建页**: 完整表单验证、配额设置
- **编辑页**: 支持所有字段修改
- **套餐类型**: free, basic, professional, enterprise
- **计费周期**: monthly, quarterly, yearly, lifetime

#### 🤖 AI成本监控
- 总成本/Token数/请求数/平均成本统计
- 按提供商/模型统计表格
- 成本趋势分析（最近10天）
- 自动刷新（每分钟）

#### 📊 数据分析
- **收入趋势图**: 折线图展示收入金额和订单数
- **用户增长图**: 柱状图显示新增用户和总用户数
- **套餐分布图**: 饼图展示各套餐订阅分布
- **支付方式统计**: 横向柱状图对比各支付方式
- **时间筛选**: 支持7/30/90天数据查看
- **自动刷新**: 每5分钟更新数据

#### 🔍 系统监控
- **健康检查**: 数据库状态、过期订阅、待处理支付
- **安全事件**: 最近24小时安全相关事件监控
- **活动记录**: 实时展示系统操作日志
- **自动刷新**: 每30秒更新监控数据
- **可视化状态**: 彩色图标和标签显示系统状态

#### 📝 审计日志
- **全面查询**: 搜索操作、资源类型等关键信息
- **多维筛选**: 级别筛选(Info/Warning/Error/Critical)
- **分类筛选**: 认证/用户/支付/订阅/系统
- **分页展示**: 支持10/25/50/100条每页
- **详细信息**: IP地址、用户代理、操作详情

### ⏳ 规划中模块

- 🟢 在线用户实时监控（WebSocket）
- 🔌 AI网关配置管理

## 🚀 快速开始

### 环境要求

- Node.js >= 16
- npm >= 8

### 安装依赖

```bash
npm install
```

### 配置后端地址

创建 `.env` 文件：

```env
VITE_FASTAPI_URL=http://127.0.0.1:9030
```

### 开发模式

```bash
npm run dev
```

默认访问：http://localhost:10050

如果端口被占用，Vite 会自动尝试下一个端口（10051, 10052...）

### 构建生产版本

```bash
npm run build
```

构建产物位于 `dist/` 目录。

## 🔐 登录凭据

**默认管理员账户:**
- 用户名: `tc1102Admin`
- 密码: `xjystimao1115`

> ⚠️ 生产环境请务必修改默认密码！

## 📁 项目结构

```
admin-dashboard/
├── src/
│   ├── App.tsx                 # 主应用入口
│   ├── authProvider.ts         # 认证提供者
│   ├── dataProvider.ts         # 数据提供者
│   ├── AppLayout.tsx           # 布局组件
│   ├── pages/
│   │   ├── Dashboard.tsx       # 仪表板
│   │   └── LoginPage.tsx       # 登录页
│   └── resources/
│       ├── users/              # 用户管理
│       │   ├── list.tsx
│       │   ├── show.tsx
│       │   ├── create.tsx
│       │   └── edit.tsx
│       ├── payments/           # 支付管理
│       │   ├── list.tsx
│       │   └── show.tsx
│       ├── plans/              # 订阅套餐
│       │   ├── list.tsx
│       │   ├── show.tsx
│       │   ├── create.tsx
│       │   └── edit.tsx
│       └── ai-monitoring/      # AI监控
│           └── CostStats.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 🛠️ 技术栈

### 核心框架
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite 5** - 构建工具

### UI 组件库
- **React Admin 4.15** - 管理后台框架
- **Material-UI 5** - UI 组件库
- **React Router 6** - 路由管理
- **Recharts 2.15** - 数据可视化图表库

### 数据交互
- **ra-data-simple-rest** - REST API 适配器
- **Fetch API** - HTTP 请求

### 开发工具
- **ESLint** - 代码检查
- **TypeScript** - 类型检查

## 🔌 后端 API 要求

管理后台需要配合 FastAPI 后端使用，后端需要提供以下 API 端点：

### 认证 API
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新令牌

### 管理 API (需要 admin 权限)
- `GET /api/admin/users` - 用户列表
- `POST /api/admin/users` - 创建用户
- `GET /api/admin/users/{id}` - 用户详情
- `PUT /api/admin/users/{id}` - 更新用户
- `DELETE /api/admin/users/{id}` - 删除用户
- `GET /api/admin/stats` - 系统统计
- `GET /api/admin/payments` - 支付列表
- `GET /api/admin/payments/{id}` - 支付详情
- `GET /api/admin/plans` - 套餐列表
- `POST /api/admin/plans` - 创建套餐
- `PUT /api/admin/plans/{id}` - 更新套餐
- `DELETE /api/admin/plans/{id}` - 删除套餐
- `GET /api/admin/ai/costs` - AI成本统计
- `GET /api/admin/charts/revenue` - 收入趋势
- `GET /api/admin/charts/user-growth` - 用户增长
- `GET /api/admin/stats/plan-distribution` - 套餐分布
- `GET /api/admin/stats/payment-methods` - 支付方式统计
- `GET /api/admin/system/health` - 系统健康状态
- `GET /api/admin/activities/recent` - 最近活动
- `GET /api/admin/security/events` - 安全事件

## 📊 完成度统计

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 🎛️ 仪表板 | 100% | 实时数据展示 |
| 👥 用户管理 | 100% | 完整 CRUD + 高级功能 |
| 💳 支付管理 | 95% | 查看功能完整，缺退款 |
| 📦 订阅套餐 | 100% | 完整 CRUD |
| 🤖 AI监控 | 100% | 成本统计完整 |
| � 数据分析 | 100% | 4种图表完整实现 |
| � 系统监控 | 100% | 健康检查+活动监控 |
| 📝 审计日志 | 100% | 查询筛选完整 |
| 🟢 在线用户 | 0% | 待开发 |
| 🔌 AI网关 | 50% | 后端完整，前端待开发 |

**总体完成度: 85%**

## 🎨 特色功能

### 彩色状态标签
- 角色标签：不同颜色区分用户角色
- 状态标签：直观展示账户状态
- 支付状态：清晰的支付流程可视化

### 实时数据
- 仪表板每 30 秒自动刷新
- AI 监控每 60 秒自动更新
- 加载状态友好提示

### 搜索与筛选
- 所有列表页支持搜索
- 多维度筛选（角色/状态/类型）
- 分页展示，性能优化

### 响应式设计
- 适配桌面端和平板
- Grid 布局自适应
- Material-UI 主题定制

## 🔧 开发说明

### 添加新模块

1. 在 `src/resources/` 下创建新目录
2. 实现 list/show/create/edit 组件
3. 在 `App.tsx` 中注册 Resource
4. 在 `AppLayout.tsx` 菜单中添加入口

### 自定义主题

在 `App.tsx` 的 `theme` 配置中修改：

```typescript
theme={{
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
}}
```

## 📝 更新日志

### v1.1.0 (2025-11-07)
- ✅ 新增数据分析模块
  - 收入趋势折线图
  - 用户增长柱状图
  - 套餐分布饼图
  - 支付方式统计
  - 7/30/90天时间筛选
- ✅ 新增系统监控模块
  - 系统健康状态检查
  - 安全事件监控
  - 活动记录展示
- ✅ 新增审计日志模块
  - 审计日志查询
  - 多维度筛选
  - 分页展示
- ✅ 安装Recharts图表库
- ✅ 优化菜单导航结构

### v1.0.0 (2025-11-07)
- ✅ 完成用户管理模块
- ✅ 完成支付管理模块
- ✅ 完成订阅套餐管理模块
- ✅ 完成 AI 成本监控模块
- ✅ 完成仪表板实时数据展示
- ✅ 添加 TypeScript 类型定义
- ✅ 集成 Material-UI 5

## 📄 License

MIT

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

