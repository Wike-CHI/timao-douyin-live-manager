# 管理后台系统任务清单

## 阶段 1: 基础搭建

### 1.1 项目初始化

- [ ] 创建 React Admin 项目
- [ ] 安装所有依赖包
- [ ] 配置 TypeScript
- [ ] 配置 Vite 和代理
- [ ] 设置项目目录结构

### 1.2 认证系统

- [ ] 实现 `authProvider.ts`
  - [ ] login 方法
  - [ ] logout 方法
  - [ ] checkAuth 方法
  - [ ] getPermissions 方法
  - [ ] getIdentity 方法
- [ ] 测试登录流程

### 1.3 数据提供者

- [ ] 实现 `dataProvider.ts`
  - [ ] getList
  - [ ] getOne
  - [ ] create
  - [ ] update
  - [ ] delete
- [ ] 处理分页、过滤、排序
- [ ] 错误处理

### 1.4 基础布局

- [ ] 创建 `AppLayout.tsx`
- [ ] 配置菜单
- [ ] 设置主题
- [ ] 响应式布局

---

## 阶段 2: 用户管理

### 2.1 用户列表

- [ ] 创建 `resources/users/list.tsx`
- [ ] 实现表格显示
- [ ] 实现搜索功能
- [ ] 实现过滤功能（角色、状态、时间）
- [ ] 实现排序功能
- [ ] 实现分页
- [ ] 添加批量操作（激活/停用/删除）

### 2.2 用户详情

- [ ] 创建 `resources/users/show.tsx`
- [ ] 基本信息标签页
- [ ] 订阅信息标签页
- [ ] 使用统计标签页
- [ ] 操作记录标签页

### 2.3 创建用户

- [ ] 创建 `resources/users/create.tsx`
- [ ] 表单验证
- [ ] 提交处理
- [ ] 成功提示

### 2.4 编辑用户

- [ ] 创建 `resources/users/edit.tsx`
- [ ] 加载现有数据
- [ ] 表单编辑
- [ ] 重置密码功能
- [ ] 锁定/解锁功能

### 2.5 后端API

- [ ] 扩展 `GET /api/admin/users`（列表）
- [ ] 扩展 `GET /api/admin/users/:id`（详情）
- [ ] 实现 `POST /api/admin/users`（创建）
- [ ] 实现 `PUT /api/admin/users/:id`（更新）
- [ ] 实现 `DELETE /api/admin/users/:id`（删除）
- [ ] 实现 `POST /api/admin/users/:id/lock`（锁定）
- [ ] 实现 `POST /api/admin/users/:id/unlock`（解锁）

---

## 阶段 3: 支付管理

### 3.1 支付列表

- [ ] 创建 `resources/payments/list.tsx`
- [ ] 表格显示
- [ ] 过滤（状态、支付方式、时间范围）
- [ ] 搜索（订单号、用户）
- [ ] 快速操作按钮

### 3.2 支付详情

- [ ] 创建 `resources/payments/show.tsx`
- [ ] 订单信息显示
- [ ] 用户信息显示
- [ ] 退款信息显示
- [ ] 发票信息显示

### 3.3 支付操作

- [ ] 创建 `RefundDialog.tsx`（退款对话框）
- [ ] 创建 `MarkPaidDialog.tsx`（标记已支付）
- [ ] 创建 `InvoiceDialog.tsx`（发票管理）

### 3.4 后端API

- [ ] 实现 `GET /api/admin/payments`（列表）
- [ ] 实现 `GET /api/admin/payments/:id`（详情）
- [ ] 实现 `POST /api/admin/payments/:id/mark-paid`
- [ ] 实现 `POST /api/admin/payments/:id/refund`
- [ ] 实现 `GET /api/admin/payments/export`（导出）

---

## 阶段 4: 订阅套餐管理

### 4.1 套餐列表

- [ ] 创建 `resources/plans/list.tsx`
- [ ] 卡片式或表格式展示
- [ ] 显示订阅用户数
- [ ] 启用/停用切换

### 4.2 套餐详情

- [ ] 创建 `resources/plans/show.tsx`
- [ ] 基本信息显示
- [ ] 价格信息显示
- [ ] 功能限制显示
- [ ] 订阅统计显示

### 4.3 创建套餐

- [ ] 创建 `resources/plans/create.tsx`
- [ ] 基本信息表单
- [ ] 价格设置表单
- [ ] 功能限制表单
- [ ] 功能列表编辑器（`PlanFeaturesEditor.tsx`）
- [ ] JSON格式验证

### 4.4 编辑套餐

- [ ] 创建 `resources/plans/edit.tsx`
- [ ] 复用创建表单逻辑
- [ ] 加载现有数据
- [ ] 更新处理

### 4.5 后端API

- [ ] 实现 `GET /api/admin/plans`（列表）
- [ ] 实现 `GET /api/admin/plans/:id`（详情）
- [ ] 实现 `POST /api/admin/plans`（创建）
- [ ] 实现 `PUT /api/admin/plans/:id`（更新）
- [ ] 实现 `DELETE /api/admin/plans/:id`（删除）
- [ ] 检查套餐使用情况

---

## 阶段 5: AI监控

### 5.1 AI使用统计页面

- [ ] 创建 `resources/analytics/AIUsageStats.tsx`
- [ ] 实时统计卡片
- [ ] Token消耗趋势图（Recharts LineChart）
- [ ] 按模型统计饼图（PieChart）
- [ ] 按功能统计柱状图（BarChart）
- [ ] 成本分析表格

### 5.2 AI网关管理

- [ ] 创建 `resources/ai-gateway/GatewayStatus.tsx`
- [ ] 当前配置显示
- [ ] 可以控制AI分析和AI话术生成和直播间氛围与情绪识别和复盘功能的各个AI调用，将每个服务的AI API调用分离 比如AI分析和话术生成和直播间氛围与情绪识别用qwen3max，复盘功能用gemini flash 2.5 preview。或者是AI分析用deepseek 话术生成用qwen3max 直播间氛围与情绪识别用豆包1.6 复盘功能用gemini flash2.5 preview。各个功能的AI配置
- [ ] 服务商列表
- [ ] 切换服务商表单
- [ ] 注册/编辑服务商对话框

### 5.3 后端API（复用现有）

- [ ] 确认 `GET /api/ai_gateway/status` 可用
- [ ] 确认 `GET /api/ai_usage/stats/*` 可用
- [ ] 如需要，扩展统计API

---

## 阶段 6: 在线用户统计

### 6.1 在线用户页面

- [ ] 创建 `resources/analytics/OnlineUsers.tsx`
- [ ] 实时在线人数卡片
- [ ] 在线用户趋势图（24小时/7天）
- [ ] 活跃会话列表表格
- [ ] 会话详情对话框
- [ ] 强制断开功能

### 6.2 WebSocket连接管理

- [ ] 在后端实现连接跟踪
  - [ ] 连接时记录到Redis
  - [ ] 断开时清理
  - [ ] 定期清理过期连接
- [ ] 实现查询接口

### 6.3 后端API

- [ ] 实现 `GET /api/admin/online-users/count`
- [ ] 实现 `GET /api/admin/sessions/active`
- [ ] 实现 `POST /api/admin/sessions/:id/disconnect`

---

## 阶段 7: 流水统计

### 7.1 收入统计页面

- [ ] 创建 `resources/analytics/RevenueStats.tsx`
- [ ] 收入概览卡片（总/今日/本月）
- [ ] 收入趋势图（按天/周/月）
- [ ] 支付方式分布饼图
- [ ] 套餐收入对比柱状图

### 7.2 财务报表

- [ ] 创建报表导出功能
- [ ] CSV导出
- [ ] Excel导出
- [ ] PDF导出（可选）

### 7.3 后端API

- [ ] 实现 `GET /api/admin/revenue/stats`
- [ ] 实现 `GET /api/admin/revenue/payments`
- [ ] 实现 `GET /api/admin/revenue/export`

---

## 阶段 8: 仪表板

### 8.1 主仪表板

- [ ] 创建 `resources/analytics/Dashboard.tsx`
- [ ] 关键指标卡片
- [ ] 收入趋势图表
- [ ] Token消耗图表
- [ ] 套餐分布图表
- [ ] 实时数据更新（轮询或WebSocket）

---

## 阶段 9: 优化和测试

### 9.1 性能优化

- [ ] 实现数据缓存（React Query）
- [ ] 虚拟滚动（大数据量列表）
- [ ] 懒加载（图表组件）
- [ ] 代码分割

### 9.2 响应式设计

- [ ] 移动端适配
- [ ] 平板适配
- [ ] 测试不同屏幕尺寸

### 9.3 测试

- [ ] 单元测试（关键组件）
- [ ] 集成测试（API调用）
- [ ] E2E测试（关键流程）

### 9.4 文档

- [ ] 用户使用文档
- [ ] API文档完善
- [ ] 部署文档

---

## 阶段 10: 部署

### 10.1 构建

- [ ] 配置生产环境构建
- [ ] 优化打包体积
- [ ] 设置环境变量

### 10.2 部署

- [ ] 静态文件部署（Nginx）
- [ ] 或集成到Electron应用
- [ ] 配置反向代理

---

## 优先级标记

- **P0** - 必须完成（核心功能）
- **P1** - 重要（增强体验）
- **P2** - 可选（锦上添花）

### P0 任务

- 阶段1全部
- 阶段2全部
- 阶段3（支付列表和详情）
- 阶段4（套餐CRUD）
- 阶段5（AI使用统计基础）
- 阶段8（基础仪表板）

### P1 任务

- 阶段3（支付操作）
- 阶段5（AI网关管理）
- 阶段6（在线用户统计）
- 阶段7（流水统计）

### P2 任务

- 阶段9（优化和测试）
- 阶段7（财务报表导出）
- 高级图表分析

---

**文档版本**：v1.0
**创建日期**：2025-11-02
