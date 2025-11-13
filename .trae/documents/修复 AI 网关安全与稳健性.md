## 检查结论
- 路由挂载：AI 相关 API 已在 `server/app/main.py:226, 231-236` 挂载；CORS 及预检在 `server/app/main.py:139-168`。
- 网关核心：多提供商适配与功能模型映射见 `server/ai/ai_gateway.py:44-53, 96-121, 124-160, 182-262`；调用统一异常处理在 `server/ai/ai_gateway.py:582-632`。
- 主要问题：
  - 硬编码默认密钥并在启动注入环境：`server/utils/ai_defaults.py:14-27, 30-34`、`server/app/main.py:64`。
  - 向前端返回完整 `api_key`：`server/ai/ai_gateway.py:817`。
  - AI 路由缺少鉴权：`server/app/api/ai_gateway_api.py`、`ai_live.py`、`ai_scripts.py`、`ai_usage.py` 未接入认证依赖。
  - `timeout`、`max_retries` 未实际生效：定义在 `server/ai/ai_gateway.py:64-66`，调用处未应用。
  - 讯飞兼容与 Base URL 校验不足：`server/ai/ai_gateway.py:484-536, 593-603`。
  - SSE 流逻辑基本规范，阻塞风险取决于下游：`server/app/api/ai_live.py:63-78`、`server/app/services/ai_live_analyzer.py:346-358`。

## 修复计划（按优先级）
### 1) 移除默认密钥注入
- 删除或禁用 `server/utils/ai_defaults.py` 中密钥注入；在 `server/app/main.py:64` 处移除默认注入调用。
- 启动时校验必须的环境变量，不满足则禁用相关提供商并记录明确错误码。

### 2) 后端不回传敏感字段
- 修改 `server/ai/ai_gateway.py:817` 的 `list_providers()`，不返回 `api_key` 字段；如需显示，后端生成脱敏字符串而非原值。

### 3) 接入鉴权与授权
- 为以下路由添加认证依赖与角色校验：`/api/ai_gateway/*`、`/api/ai/live/*`、`/api/ai/scripts/*`、`/api/ai_usage/*`。
- 复用 `server/app/api/auth.py` 的验证方法（如 `get_current_user`），在各 `APIRouter` 端点增加 `dependencies=[Depends(...)]`。

### 4) 应用超时与重试
- 在网关实际调用处引入超时与重试：
  - OpenAI/兼容客户端：通过客户端配置或用 `httpx` 包装，使用 `ProviderConfig.timeout`、`max_retries`（参考 `server/ai/ai_gateway.py:300-314, 389-405, 582-632`）。
  - 对 5xx/网络错误进行指数退避重试；区分不可重试错误（如 4xx 参数问题）。

### 5) Provider/Model 启动校验
- 在启动阶段校验各 provider 的 `base_url`、`api_key`、`default_model` 是否有效；
- 对 `AI_FUNCTION_*` 映射做存在性校验，不合法时回退到 provider 模板或禁用功能。

### 6) 错误码与响应模型
- 为 `server/app/api/ai_gateway_api.py` 端点绑定响应模型；统一成功/失败结构与错误码（参数错误、鉴权失败、外部服务不可用）。
- 完善讯飞兼容处理与 Base URL 错误提示（失败即刻返回明确错误而非仅日志）。

### 7) 限流与配额
- 在 FastAPI 层引入用户级/会话级速率限制（每分钟请求数）与配额；
- 将 `server/utils/ai_usage_monitor.py` 的统计与限流策略打通，在入口拒绝过量调用。

### 8) 成本单位一致化
- 明确不同提供商的币种与费率，统一展示单位或在前端区分标识，避免误读（涉及 `server/utils/ai_usage_monitor.py:216-226`、`server/ai/gemini_adapter.py:248-256`）。

### 9) 验证与测试
- 编写测试用例：
  - 未鉴权访问被拒绝；敏感字段不在响应中；
  - 超时与重试策略触发与停止；Base URL/模型非法的错误码；
  - SSE 流启动与清理；实时分析在异常时的降级路径。
- 本地启动后用诊断脚本 `server/scripts/diagnose_ai_config.py` 校验配置可用性。

## 交付与回滚
- 分批提交，每项变更都附带单元测试；若外部服务异常，保留降级逻辑。
- 提供 feature flag 以便灰度启用鉴权与限流。