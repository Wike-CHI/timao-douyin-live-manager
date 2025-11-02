# 管理后台系统 - 设置指南

## 阶段1完成 ✅

已创建的基础文件：

### 项目结构
```
admin-dashboard/
├── package.json          # 项目依赖配置
├── tsconfig.json         # TypeScript配置
├── vite.config.ts        # Vite构建配置
├── index.html            # HTML入口
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明
└── src/
    ├── main.tsx          # React入口
    ├── App.tsx           # 主应用组件
    ├── AppLayout.tsx     # 布局组件（含菜单）
    ├── authProvider.ts   # 认证提供者
    ├── dataProvider.ts   # 数据提供者（API对接）
    └── pages/
        ├── LoginPage.tsx # 登录页面
        └── Dashboard.tsx # 仪表板页面
```

## 安装和启动

### 1. 安装依赖

```bash
cd admin-dashboard
npm install
```

### 2. 配置环境变量（可选）

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

默认后端地址：`http://127.0.0.1:9019`

### 3. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:10050

### 4. 登录

使用管理员账号登录：
- 用户名/邮箱：你的管理员账号
- 密码：你的密码

**注意**：只有角色为 `admin` 或 `super_admin` 的用户可以登录。

## 已实现的功能

### ✅ 阶段1.1: 项目初始化
- [x] React Admin 项目结构
- [x] TypeScript 配置
- [x] Vite 配置（含API代理）
- [x] 项目目录结构

### ✅ 阶段1.2: 认证系统
- [x] `authProvider.ts` - 完整的认证逻辑
  - [x] login - 登录方法
  - [x] logout - 登出方法
  - [x] checkAuth - 检查认证状态
  - [x] checkError - 错误处理（401/403自动登出）
  - [x] getPermissions - 获取权限（仅管理员可访问）
  - [x] getIdentity - 获取用户身份

### ✅ 阶段1.3: 数据提供者
- [x] `dataProvider.ts` - RESTful API数据提供者
  - [x] getList - 获取列表（支持分页、排序、过滤）
  - [x] getOne - 获取单个资源
  - [x] getMany - 批量获取
  - [x] getManyReference - 关联资源获取
  - [x] create - 创建资源
  - [x] update - 更新资源
  - [x] updateMany - 批量更新
  - [x] delete - 删除资源
  - [x] deleteMany - 批量删除
  - [x] JWT Token自动添加
  - [x] 错误处理

### ✅ 阶段1.4: 基础布局
- [x] `AppLayout.tsx` - 自定义布局
  - [x] 侧边栏菜单
  - [x] 菜单项（仪表板、用户、支付、套餐、AI监控等）
  - [x] Material-UI图标
- [x] `LoginPage.tsx` - 登录页面
  - [x] 用户名/邮箱登录
  - [x] 密码输入
  - [x] 错误提示
  - [x] Material-UI样式
- [x] `Dashboard.tsx` - 仪表板页面
  - [x] 统计卡片布局
  - [x] 欢迎信息

## 下一步

### 阶段2: 用户管理（待实现）
- 用户列表
- 用户详情
- 创建/编辑/删除用户

### 阶段3: 支付管理（待实现）
- 支付记录列表
- 支付详情
- 退款处理

### 阶段4: 订阅套餐管理（待实现）
- 套餐列表
- 套餐CRUD
- 动态配置功能

## 注意事项

1. **后端API要求**：
   - 后端需要实现 `/api/admin/*` 接口
   - 接口需要支持分页、过滤、排序参数
   - 响应格式需要符合 react-admin 的要求

2. **认证要求**：
   - 后端 `/api/auth/login` 接口返回 `access_token`
   - 后端 `/api/auth/me` 接口返回用户信息（含 `role` 字段）
   - 只有 `admin` 或 `super_admin` 角色可以访问

3. **开发调试**：
   - 使用浏览器开发者工具查看网络请求
   - 检查后端日志以了解API调用情况
   - 查看浏览器控制台查看前端错误

## 常见问题

### Q: 登录后提示权限不足？
A: 检查用户角色是否为 `admin` 或 `super_admin`。

### Q: API请求失败？
A: 检查：
1. 后端服务是否运行在 `http://127.0.0.1:9019`
2. 后端是否实现了相应的 `/api/admin/*` 接口
3. 网络代理配置是否正确

### Q: TypeScript错误？
A: 运行 `npm install` 安装所有依赖，包括类型定义。

---

**阶段1完成时间**：2025-11-02

