# 需求文档 - API 接口和数据类型一致性检查

## 介绍

对提猫直播助手项目进行全面的 API 接口和数据类型一致性检查，确保前后端接口定义、数据模型、类型定义完全匹配，提升系统可维护性和减少运行时错误。

## 项目背景

- **后端技术栈**: Python + FastAPI + Pydantic + SQLAlchemy
- **前端技术栈**: TypeScript + React + Electron
- **当前问题**: 
  - 前后端接口定义可能存在不一致
  - 数据类型定义可能存在差异
  - 缺少统一的 API 契约文档

## 需求

### 需求 1 - API 接口一致性检查

**用户故事：** 作为开发人员，我需要确保前后端 API 接口定义完全一致，以避免集成问题和运行时错误。

#### 验收标准

1. **接口路径一致性**: When 后端定义了 API 路由时，the 系统 shall 确保前端调用的路径与后端完全匹配。
2. **HTTP 方法一致性**: When 后端定义了 HTTP 方法（GET/POST/PUT/DELETE）时，the 系统 shall 确保前端使用相同的方法。
3. **请求参数一致性**: When 后端定义了请求参数时，the 系统 shall 确保前端发送的参数名称、类型、必填性与后端期望完全一致。
4. **响应数据一致性**: When 后端返回响应数据时，the 系统 shall 确保前端期望的响应结构与后端返回的结构完全一致。

### 需求 2 - 数据类型深度检查

**用户故事：** 作为开发人员，我需要确保前后端数据类型定义在细节上完全一致，包括可选性、默认值、验证规则等。

#### 验收标准

1. **字段类型匹配**: When 后端定义字段类型为 `str/int/bool/datetime` 时，the 系统 shall 确保前端类型为 `string/number/boolean/Date`。
2. **可选性匹配**: When 后端字段为 `Optional[T]` 时，the 系统 shall 确保前端字段为 `T | null | undefined`。
3. **默认值匹配**: When 后端字段有默认值时，the 系统 shall 记录并验证前端是否需要相应的默认值处理。
4. **验证规则一致**: When 后端使用 Pydantic 验证器时，the 系统 shall 确保前端有相应的验证逻辑或文档说明。
5. **嵌套对象一致**: When 数据包含嵌套对象时，the 系统 shall 递归检查嵌套层级的类型一致性。

### 需求 3 - 分层检查覆盖

**用户故事：** 作为项目管理员，我需要对不同重要程度的 API 模块进行分层检查，确保关键模块优先级最高。

#### 验收标准

1. **层级 1 - 核心业务**: When 检查核心业务模块（认证、订阅、支付、用户）时，the 系统 shall 进行最严格的深度检查。
2. **层级 2 - 功能模块**: When 检查功能模块（抖音、音频转写、直播复盘）时，the 系统 shall 进行完整的深度检查。
3. **层级 3 - 辅助模块**: When 检查辅助模块（AI网关、工具、健康检查）时，the 系统 shall 进行基本的一致性检查。

### 需求 4 - 问题识别和报告

**用户故事：** 作为开发人员，我需要清晰的问题报告，明确指出哪些接口存在不一致，具体是什么问题。

#### 验收标准

1. **问题清单表格**: When 发现不一致问题时，the 系统 shall 生成包含以下信息的表格：
   - 模块名称
   - 接口路径
   - 问题类型（路径/方法/参数/响应）
   - 后端定义
   - 前端定义
   - 严重程度（高/中/低）
   
2. **问题分类统计**: When 生成报告时，the 系统 shall 提供问题分类统计（如：路径不一致 3 个，类型不匹配 5 个）。

3. **优先级排序**: When 发现多个问题时，the 系统 shall 按严重程度和影响范围排序。

### 需求 5 - 自动修复方案

**用户故事：** 作为开发人员，我需要针对发现的问题获得具体的修复建议和代码示例。

#### 验收标准

1. **修复建议文档**: When 发现不一致问题时，the 系统 shall 生成包含以下内容的修复方案：
   - 问题描述
   - 建议的修复方式
   - 修复代码示例（前端/后端）
   - 修复优先级
   
2. **可执行修复脚本**: When 问题可以自动修复时，the 系统 shall 提供可执行的修复脚本或代码补丁。

### 需求 6 - API 契约文档生成

**用户故事：** 作为团队成员，我需要一份统一的 API 契约文档，作为前后端开发的标准参考。

#### 验收标准

1. **OpenAPI 规范**: When 生成契约文档时，the 系统 shall 输出符合 OpenAPI 3.0 规范的文档。

2. **TypeScript 类型定义**: When 生成契约文档时，the 系统 shall 输出完整的 TypeScript 类型定义文件。

3. **数据模型映射表**: When 生成契约文档时，the 系统 shall 提供前后端数据模型的对应映射表。

4. **使用示例**: When 生成契约文档时，the 系统 shall 为每个接口提供请求/响应示例。

## 模块检查范围

### 层级 1：核心业务接口（必查）
1. **认证模块** (`/api/auth`)
   - 登录接口 (POST /api/auth/login)
   - 注册接口 (POST /api/auth/register)
   - 令牌刷新 (POST /api/auth/refresh)
   - 用户信息 (GET /api/auth/me)

2. **订阅模块** (`/api/subscription`)
   - 获取套餐列表 (GET /api/subscription/plans)
   - 获取用户订阅 (GET /api/subscription/current)
   - 创建订阅 (POST /api/subscription/subscribe)

3. **支付模块** (`/api/payment`)
   - 获取套餐 (GET /api/payment/plans)
   - 创建订单 (POST /api/payment/create)
   - 支付回调 (POST /api/payment/webhook)

### 层级 2：功能接口（重要）
4. **抖音模块** (`/api/douyin`)
   - 启动监控 (POST /api/douyin/start)
   - 停止监控 (POST /api/douyin/stop)
   - 获取状态 (GET /api/douyin/status)

5. **音频转写模块** (`/api/live_audio`)
   - 启动转写 (POST /api/live_audio/start)
   - 停止转写 (POST /api/live_audio/stop)
   - 获取状态 (GET /api/live_audio/status)

6. **直播复盘模块** (`/api/live_report`, `/api/live/review`)
   - 启动录制 (POST /api/live_report/start)
   - 生成报告 (POST /api/live_report/generate)
   - 获取报告 (GET /api/live/review/reports)

7. **AI 服务模块** (`/api/ai_live`, `/api/ai_scripts`)
   - 启动 AI 分析 (POST /api/ai_live/start)
   - 生成话术 (POST /api/ai_scripts/generate)

### 层级 3：辅助接口（可选）
8. **AI 网关模块** (`/api/ai_gateway`)
   - 注册服务商
   - 切换服务商
   - 获取配置

9. **管理员模块** (`/api/admin`)
   - 用户管理
   - 系统配置

10. **工具模块** (`/api/tools`, `/api/bootstrap`)
    - 健康检查
    - 资源自检

## 输出交付物

1. **完整规范文档**
   - `specs/api-consistency-check/requirements.md` - 本文档
   - `specs/api-consistency-check/design.md` - 技术方案设计
   - `specs/api-consistency-check/tasks.md` - 任务拆分

2. **检查报告**
   - `specs/api-consistency-check/audit-report.md` - 详细检查报告
   - `specs/api-consistency-check/issues-table.md` - 问题清单表格

3. **修复方案**
   - `specs/api-consistency-check/fix-plan.md` - 修复方案文档
   - `specs/api-consistency-check/fix-examples.md` - 修复代码示例

4. **API 契约**
   - `specs/api-consistency-check/api-contract.yaml` - OpenAPI 规范
   - `specs/api-consistency-check/types-contract.d.ts` - TypeScript 类型定义
   - `specs/api-consistency-check/model-mapping.md` - 数据模型映射表

## 成功标准

1. ✅ 所有 3 个层级的 API 接口完成深度检查
2. ✅ 识别并记录所有不一致问题
3. ✅ 生成完整的问题清单和修复方案
4. ✅ 输出统一的 API 契约文档
5. ✅ 提供可执行的修复建议

