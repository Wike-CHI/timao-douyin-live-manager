# AI 网关科大讯飞 Lite 集成总结

## ✅ 完成内容

已成功将科大讯飞 Lite 模型集成到 AI 网关，并设置为所有功能的默认模型。

## 🔄 主要更改

### 1. AI 网关核心更改 (`server/ai/ai_gateway.py`)

#### 添加讯飞服务商枚举
```python
class AIProvider(str, Enum):
    XUNFEI = "xunfei"  # 科大讯飞星火
    # ... 其他服务商
```

#### 更新功能默认配置
所有功能默认使用讯飞 lite 模型：

```python
FUNCTION_MODELS = {
    "live_analysis": {
        "provider": "xunfei",  # 从 qwen 改为 xunfei
        "model": "lite"         # 从 qwen3-max 改为 lite
    },
    "style_profile": {
        "provider": "xunfei",  # 从 qwen 改为 xunfei
        "model": "lite"         # 从 qwen3-max 改为 lite
    },
    "script_generation": {
        "provider": "xunfei",  # 从 qwen 改为 xunfei
        "model": "lite"         # 从 qwen3-max 改为 lite
    },
    "live_review": {
        "provider": "xunfei",  # 从 gemini 改为 xunfei
        "model": "lite"         # 从 gemini-2.5-flash 改为 lite
    },
}
```

#### 添加讯飞配置模板
```python
PROVIDER_TEMPLATES = {
    AIProvider.XUNFEI: {
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "default_model": "lite",
        "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"],
    },
    # ... 其他服务商
}
```

#### 更新默认服务商
```python
# 从 qwen 改为 xunfei
primary_provider = os.getenv("AI_SERVICE", "xunfei").lower()
primary_model = os.getenv("AI_MODEL", "lite")
```

#### 添加环境变量加载
```python
def _load_additional_providers(self) -> None:
    # 科大讯飞（优先加载）
    xunfei_key = os.getenv("XUNFEI_API_KEY")
    if xunfei_key:
        self.register_provider(
            provider="xunfei",
            api_key=xunfei_key,
            base_url=os.getenv("XUNFEI_BASE_URL"),
            default_model=os.getenv("XUNFEI_MODEL", "lite"),
        )
```

#### 更新监控功能名称
```python
if provider == "xunfei":
    function_name = "实时分析"  # 讯飞主要用于实时分析和话术生成
```

### 2. 环境变量配置

#### 新增配置项
```bash
# 科大讯飞配置
XUNFEI_API_KEY=your_appid:your_api_secret
XUNFEI_BASE_URL=https://spark-api-open.xf-yun.com/v1
XUNFEI_MODEL=lite

# 或使用通用配置
AI_SERVICE=xunfei
AI_API_KEY=your_appid:your_api_secret
AI_MODEL=lite
```

#### 功能级别配置
```bash
AI_FUNCTION_LIVE_ANALYSIS_PROVIDER=xunfei
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite
AI_FUNCTION_STYLE_PROFILE_PROVIDER=xunfei
AI_FUNCTION_STYLE_PROFILE_MODEL=lite
AI_FUNCTION_SCRIPT_GENERATION_PROVIDER=xunfei
AI_FUNCTION_SCRIPT_GENERATION_MODEL=lite
AI_FUNCTION_LIVE_REVIEW_PROVIDER=xunfei
AI_FUNCTION_LIVE_REVIEW_MODEL=lite
```

## 📊 对比分析

### 更改前后对比

| 功能 | 更改前 | 更改后 |
|------|--------|--------|
| **AI分析** | qwen/qwen3-max | xunfei/lite |
| **风格画像** | qwen/qwen3-max | xunfei/lite |
| **话术生成** | qwen/qwen3-max | xunfei/lite |
| **复盘** | gemini/gemini-2.5-flash | xunfei/lite |

### 成本对比

以日均 1000 次调用，平均 250 tokens/次 为例：

| 场景 | 更改前 | 更改后 | 节省 |
|------|--------|--------|------|
| AI分析 (qwen3-max → lite) | ¥6.00 | ¥0.00 | 100% |
| 风格画像 (qwen3-max → lite) | ¥6.00 | ¥0.00 | 100% |
| 话术生成 (qwen3-max → lite) | ¥6.00 | ¥0.00 | 100% |
| 复盘 (gemini → lite) | ¥0.09 | ¥0.00 | 100% |
| **总计** | **¥18.09** | **¥0.00** | **100%** |

**月度节省：约 ¥543 元**

## 🎯 影响分析

### 正面影响

1. ✅ **零成本** - lite 模型完全免费
2. ✅ **统一管理** - 通过网关统一调用
3. ✅ **灵活切换** - 可随时切换到其他模型
4. ✅ **完整监控** - 自动记录所有调用

### 潜在风险

1. ⚠️ **性能差异** - lite 模型可能不如 qwen3-max 强大
2. ⚠️ **API 限制** - 免费模型可能有调用频率限制
3. ⚠️ **依赖单一服务商** - 所有功能依赖讯飞

### 缓解措施

1. ✅ **保留其他服务商** - 可配置多个备用服务商
2. ✅ **支持降级** - 失败时可切换到其他模型
3. ✅ **灵活配置** - 可按功能单独配置模型
4. ✅ **环境变量覆盖** - 可随时更改默认配置

## 🚀 使用方式

### 自动使用（推荐）

配置好环境变量后，所有 AI 功能自动使用讯飞 lite：

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()

# 使用功能标识，自动选择讯飞 lite
response = gateway.chat_completion(
    messages=[{"role": "user", "content": "分析直播间氛围"}],
    function="live_analysis"
)

print(f"服务商: {response.provider}")  # xunfei
print(f"模型: {response.model}")        # lite
print(f"成本: ¥{response.cost}")        # 0.00
```

### 临时切换模型

```python
# 临时使用讯飞的 V3.0 模型
response = gateway.chat_completion(
    messages=[...],
    provider="xunfei",
    model="generalv3"
)

# 临时使用其他服务商
response = gateway.chat_completion(
    messages=[...],
    provider="qwen",
    model="qwen-plus"
)
```

### 全局切换

```python
# 切换到其他服务商
gateway.switch_provider("qwen", "qwen-plus")

# 查看当前配置
config = gateway.get_current_config()
```

## 🔧 API 接口

### 查看网关状态

```bash
curl http://localhost:9019/api/ai_gateway/status
```

### 查看功能配置

```bash
# 所有功能
curl http://localhost:9019/api/ai_gateway/functions

# 特定功能
curl http://localhost:9019/api/ai_gateway/functions/live_analysis
```

### 更新功能配置

```bash
curl -X PUT http://localhost:9019/api/ai_gateway/functions/live_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "xunfei",
    "model": "generalv3"
  }'
```

### 切换服务商

```bash
curl -X POST http://localhost:9019/api/ai_gateway/switch \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "xunfei",
    "model": "lite"
  }'
```

## 🎓 最佳实践

### 1. 分级使用策略

```bash
# 高频功能使用免费模型
AI_FUNCTION_LIVE_ANALYSIS_MODEL=lite
AI_FUNCTION_SCRIPT_GENERATION_MODEL=lite

# 低频或重要功能使用高级模型
AI_FUNCTION_LIVE_REVIEW_PROVIDER=xunfei
AI_FUNCTION_LIVE_REVIEW_MODEL=generalv3
```

### 2. 多服务商配置

```bash
# 主服务商
AI_SERVICE=xunfei
AI_API_KEY=your_xunfei_key

# 备用服务商
QWEN_API_KEY=your_qwen_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### 3. 监控和预警

```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()
daily = monitor.get_daily_summary()

# 监控免费额度使用情况
if daily.total_calls > 10000:  # 假设每日限制
    logging.warning("接近免费额度上限，考虑切换模型")
```

## 🐛 故障排查

### 问题 1：讯飞未注册

**现象：**
```
无效的服务商: xunfei
```

**解决：**
1. 检查 `.env` 中的 `XUNFEI_API_KEY`
2. 重启服务
3. 查看日志确认注册成功

### 问题 2：功能未使用讯飞

**检查：**
```bash
# 查看功能配置
curl http://localhost:9019/api/ai_gateway/functions

# 查看当前服务商
curl http://localhost:9019/api/ai_gateway/status
```

**解决：**
```bash
# 手动更新功能配置
curl -X PUT http://localhost:9019/api/ai_gateway/functions/live_analysis \
  -H "Content-Type: application/json" \
  -d '{"provider": "xunfei", "model": "lite"}'
```

## 📝 迁移检查清单

- [ ] 配置 `XUNFEI_API_KEY` 环境变量
- [ ] 可选：配置其他备用服务商
- [ ] 重启服务使配置生效
- [ ] 验证网关状态：`GET /api/ai_gateway/status`
- [ ] 验证功能配置：`GET /api/ai_gateway/functions`
- [ ] 测试 AI 功能是否正常工作
- [ ] 监控调用成功率和响应时间
- [ ] 查看 Token 消耗统计

## 📚 相关文档

- [讯飞 Lite 完整文档](docs/AI处理工作流/讯飞星火Lite模型集成说明.md)
- [讯飞 Lite 快速开始](docs/AI处理工作流/讯飞Lite快速开始.md)
- [讯飞 Lite 使用示例](docs/AI处理工作流/讯飞Lite使用示例.md)
- [AI 网关讯飞集成](docs/AI处理工作流/AI网关讯飞集成说明.md)
- [集成完成说明](讯飞Lite集成完成说明.md)

## 🎊 总结

### 核心收益

1. ✅ **成本节省** - 每月节省约 ¥543 元（100% 节省）
2. ✅ **统一管理** - 通过网关统一管理所有 AI 调用
3. ✅ **灵活切换** - 支持随时切换服务商和模型
4. ✅ **完整监控** - 自动记录所有调用的 Token 和成本

### 技术优势

1. ✅ **向后兼容** - 保留所有原有功能和 API
2. ✅ **渐进迁移** - 支持按功能逐步迁移
3. ✅ **故障降级** - 失败时可自动或手动切换
4. ✅ **配置灵活** - 支持环境变量和 API 动态配置

### 下一步建议

1. 监控讯飞 lite 的性能表现
2. 对比 lite 与 qwen3-max 的输出质量
3. 根据实际使用情况优化配置
4. 考虑为重要功能使用高级模型

---

**集成完成！** 🎉 现在所有 AI 功能默认使用科大讯飞 Lite 模型，享受零成本 AI 服务！

