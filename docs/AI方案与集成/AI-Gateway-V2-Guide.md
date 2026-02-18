# AI Gateway V2 使用指南

## 概述

AI Gateway V2 是提猫直播助手的下一代AI网关，专为 GLM-5 和 MiniMax M2.5 系列模型设计。相比 V1 版本，V2 提供了更强的思考能力、更快的响应速度和更智能的路由功能。

### 核心特性

- **智能路由**: 根据任务类型自动选择最优模型
- **思考模式**: 支持 GLM-5 和 MiniMax 的深度思考能力
- **流式输出**: 实时流式响应，降低首字延迟
- **统一接口**: OpenAI 兼容的 API 接口
- **无缝迁移**: 与 V1 完全兼容，平滑升级

---

## 快速开始

### 1. 配置 API 密钥

在 `.env` 文件中配置：

```bash
# 智谱 GLM-5
GLM_API_KEY=your-glm-api-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# MiniMax M2.5 系列
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

> 获取 API Key:
> - GLM-5: https://open.bigmodel.cn
> - MiniMax: https://platform.minimaxi.com

### 2. 基础使用

```python
from server.ai.ai_gateway_v2 import get_gateway

# 获取网关实例
gateway = get_gateway()

# 切换到 GLM-5
gateway.switch_provider("glm")

# 发送请求
result = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}]
)
print(result["content"])
```

### 3. 启用思考模式

思考模式让 AI 先进行内部推理，然后给出回答。适用于复杂问题分析和创意生成。

```python
gateway.switch_provider("glm")

result = gateway.chat_completion(
    messages=[{"role": "user", "content": "请分析这个问题"}],
    enable_thinking=True
)

print("思考过程:", result["reasoning"])
print("回答:", result["content"])
```

### 4. 流式输出

流式输出可以实时接收响应，降低首字延迟。

```python
gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "讲个故事"}]
):
    print(chunk, end="", flush=True)
```

---

## 智能路由

AI Gateway V2 内置智能路由功能，根据任务类型自动选择最优模型。

### 路由策略

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| `live_analysis` | MiniMax-M2.5-highspeed | 100 TPS 极速输出，适合实时分析 |
| `style_profile` | GLM-5 | Agent 优化，深度分析用户风格 |
| `script_generation` | GLM-5 | 深度思考提升话术质量 |
| `live_review` | MiniMax-M2.5 | 204K 大上下文，完整复盘 |
| `reflection` | GLM-5 | 深度推理，反思改进 |
| `chat_focus` | MiniMax-M2.5-highspeed | 快速摘要，低延迟 |
| `topic_generation` | GLM-5 | 智能话题生成，创意性高 |

### 使用智能路由

```python
from server.ai.ai_gateway_v2 import get_gateway

gateway = get_gateway()

# 获取智能路由建议
route = gateway.smart_route("live_analysis", {"latency": "fast"})
# 返回: "minimax:MiniMax-M2.5-highspeed"

# 根据路由结果切换
provider, model = route.split(":")
gateway.switch_provider(provider, model)

# 或者直接使用智能路由调用
result = gateway.chat_completion_with_route(
    task_type="live_analysis",
    messages=[{"role": "user", "content": "分析这段弹幕"}],
    context={"latency": "fast"}
)
```

### 路由决策逻辑

智能路由考虑以下因素：

1. **任务类型**: 优先匹配预设规则
2. **延迟需求**: 低延迟场景选择 highspeed 模型
3. **上下文长度**: 大上下文选择 MiniMax
4. **推理深度**: 复杂推理选择 GLM-5

---

## 模型对比

### GLM-5 vs MiniMax M2.5

| 特性 | GLM-5 | MiniMax-M2.5 | MiniMax-M2.5-highspeed |
|-----|-------|--------------|------------------------|
| **思考模式** | 深度思考 | 思维分离 | 思维分离 |
| **上下文长度** | 65,536 tokens | 204,800 tokens | 204,800 tokens |
| **输出速度** | 标准 | 高速 | 100 TPS 极速 |
| **首字延迟** | ~2-3s | ~1.5-2s | ~1-2s |
| **适用场景** | Agent 工作流 | 大上下文需求 | 实时分析 |

### 价格对比

| 模型 | 输入价格 | 输出价格 |
|-----|---------|---------|
| GLM-5 | ¥0.001/1K tokens | ¥0.001/1K tokens |
| MiniMax-M2.5 | ¥0.0003/1K tokens | ¥0.001/1K tokens |
| MiniMax-M2.5-highspeed | ¥0.0003/1K tokens | ¥0.001/1K tokens |

---

## 思考模式详解

### 什么是思考模式？

思考模式让 AI 模型在进行回答之前，先进行内部推理。这个推理过程（reasoning）会被返回，让你了解 AI 的思考过程。

### GLM-5 思考模式

GLM-5 使用原生的深度思考能力：

```python
gateway.switch_provider("glm")

result = gateway.chat_completion(
    messages=[{"role": "user", "content": "分析这个直播间的用户画像"}],
    enable_thinking=True
)

# 返回结构
{
    "content": "基于弹幕数据分析...",
    "reasoning": "让我逐步分析这个问题...\n首先需要...",
    "model": "GLM-5",
    "provider": "glm",
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 500,
        "reasoning_tokens": 300
    }
}
```

### MiniMax 思考模式

MiniMax 使用思维分离技术：

```python
gateway.switch_provider("minimax")

result = gateway.chat_completion(
    messages=[{"role": "user", "content": "生成一个直播话术"}],
    enable_thinking=True
)

# 返回结构
{
    "content": "好的，这里是一个话术示例...",
    "reasoning": "思考: 用户需要一个直播话术...\n我考虑以下要点...",
    "model": "MiniMax-M2.5",
    "provider": "minimax"
}
```

### 何时使用思考模式？

推荐场景：
- 风格分析（`style_profile`）
- 话术生成（`script_generation`）
- 反思总结（`reflection`）
- 复杂问题分析

不推荐场景：
- 实时弹幕分析（`live_analysis`）- 增加延迟
- 快速摘要（`chat_focus`）- 不需要深度思考

---

## 流式输出

### 基础流式调用

```python
gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "讲个故事"}]
):
    print(chunk, end="", flush=True)
```

### 带思考模式的流式输出

```python
gateway.switch_provider("glm")

chunks = []
for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "分析这个问题"}],
    enable_thinking=True
):
    chunks.append(chunk)
    print(chunk, end="", flush=True)

# 完整响应
full_response = "".join(chunks)
```

### 流式输出的优势

- **降低首字延迟**: 用户更快看到响应
- **提升用户体验**: 实时显示内容
- **适合长输出**: 讲故事、生成话术等

---

## API 接口

### chat_completion

标准对话补全接口。

```python
result = gateway.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7,           # 可选，默认 0.7
    max_tokens=1000,          # 可选，默认自动
    enable_thinking=False     # 可选，是否启用思考模式
)

# 返回值
{
    "content": "...",
    "reasoning": "...",       # 仅当 enable_thinking=True
    "model": "GLM-5",
    "provider": "glm",
    "usage": {...}
}
```

### chat_completion_stream

流式对话补全接口。

```python
for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7,
    enable_thinking=False
):
    # chunk 是字符串片段
    print(chunk, end="", flush=True)
```

### switch_provider

切换服务商和模型。

```python
# 切换到 GLM-5
gateway.switch_provider("glm")

# 切换到 MiniMax 并指定模型
gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

# 支持的服务商
# - "glm": GLM-5
# - "minimax": MiniMax M2.5 系列
```

### smart_route

智能路由，根据任务类型推荐模型。

```python
route = gateway.smart_route(
    task_type="live_analysis",
    context={"latency": "fast"}
)

# 返回: "minimax:MiniMax-M2.5-highspeed"
```

### chat_completion_with_route

使用智能路由的对话补全。

```python
result = gateway.chat_completion_with_route(
    task_type="script_generation",
    messages=[{"role": "user", "content": "生成话术"}],
    enable_thinking=True
)
```

---

## 从 V1 迁移

AI Gateway V2 完全兼容 V1 的接口，可以平滑迁移。

### 兼容层使用

```python
# V1 代码（继续工作）
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()
response = gateway.chat_completion(messages=[...])

if response.success:
    content = response.content
    cost = response.cost
```

### 推荐迁移到 V2

```python
# V2 代码（推荐）
from server.ai.ai_gateway_v2 import get_gateway

gateway = get_gateway()
gateway.switch_provider("glm")

result = gateway.chat_completion(messages=[...])
content = result["content"]
# V2 提供更多功能：思考模式、流式输出、智能路由
```

### 主要区别

| 特性 | V1 | V2 |
|-----|----|----|
| 返回格式 | `AIResponse` 对象 | `dict` |
| 思考模式 | 不支持 | 支持 |
| 流式输出 | 有限支持 | 完整支持 |
| 智能路由 | 不支持 | 支持 |
| 服务商 | Qwen/OpenAI/DeepSeek等 | GLM-5/MiniMax |

---

## 错误处理

### 基础错误处理

```python
from server.ai.ai_gateway_v2 import get_gateway

gateway = get_gateway()

try:
    result = gateway.chat_completion(
        messages=[{"role": "user", "content": "你好"}]
    )
except ValueError as e:
    print(f"配置错误: {e}")
    # 示例: "未选择服务商，请先调用 switch_provider()"
except RuntimeError as e:
    print(f"API 调用失败: {e}")
    # 示例: "GLM API 调用失败: 401 Unauthorized"
except Exception as e:
    print(f"未知错误: {e}")
```

### 常见错误

#### 1. 未选择服务商

```
ValueError: 未选择服务商，请先调用 switch_provider()
```

**解决方法**:
```python
gateway.switch_provider("glm")
```

#### 2. API Key 无效

```
RuntimeError: GLM API 调用失败: 401 Unauthorized
```

**解决方法**: 检查 `.env` 中的 `GLM_API_KEY` 配置。

#### 3. 模型不可用

```
ValueError: 模型 'xxx' 不支持
```

**解决方法**: 使用支持的模型名称。

#### 4. 网络错误

```
RuntimeError: 连接超时
```

**解决方法**: 检查网络连接或代理设置。

---

## 性能测试

### 运行性能基准测试

```bash
# 设置 API Key
export GLM_API_KEY=your-key
export MINIMAX_API_KEY=your-key

# 运行测试
pytest tests/ai/performance/test_gateway_performance.py -v -s
```

### 性能指标

测试会评估以下指标：

- **首字延迟 (TTFT)**: 首个 token 返回时间
- **吞吐量 (TPS)**: 每秒输出 token 数
- **总延迟**: 完整响应时间
- **准确率**: 响应成功率

### 预期性能

| 模型 | 首字延迟 | 吞吐量 | 总延迟 (100 tokens) |
|-----|---------|-------|-------------------|
| GLM-5 | ~2-3s | ~20 TPS | ~7s |
| MiniMax-M2.5 | ~1.5-2s | ~40 TPS | ~4s |
| MiniMax-M2.5-highspeed | ~1-2s | ~100 TPS | ~2s |

---

## 集成测试

### GLM-5 集成测试

```bash
export GLM_API_KEY=your-key
pytest tests/ai/integration/test_glm5_integration.py -v
```

测试内容：
- 基础对话补全
- 思考模式
- 流式输出
- 错误处理

### MiniMax 集成测试

```bash
export MINIMAX_API_KEY=your-key
pytest tests/ai/integration/test_minimax_integration.py -v
```

测试内容：
- 基础对话补全
- 思考模式
- 流式输出
- 高速模型测试

### 运行所有集成测试

```bash
export GLM_API_KEY=your-key
export MINIMAX_API_KEY=your-key
pytest tests/ai/integration/ -v --tb=short
```

---

## 最佳实践

### 1. 选择合适的模型

```python
# 实时分析场景（低延迟）
gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

# 深度分析场景（高质量）
gateway.switch_provider("glm")

# 大上下文场景（长文本）
gateway.switch_provider("minimax", "MiniMax-M2.5")
```

### 2. 合理使用思考模式

```python
# 复杂问题 - 启用思考
result = gateway.chat_completion(
    messages=[{"role": "user", "content": "分析这个直播间"}],
    enable_thinking=True
)

# 简单问题 - 不启用
result = gateway.chat_completion(
    messages=[{"role": "user", "content": "翻译这段文字"}],
    enable_thinking=False
)
```

### 3. 流式输出优化用户体验

```python
# 长输出场景 - 使用流式
for chunk in gateway.chat_completion_stream(
    messages=[{"role": "user", "content": "讲个故事"}]
):
    # 实时显示给用户
    display_to_user(chunk)

# 短输出场景 - 使用标准调用
result = gateway.chat_completion(
    messages=[{"role": "user", "content": "总结这段话"}]
)
```

### 4. 使用智能路由

```python
# 让系统自动选择最优模型
result = gateway.chat_completion_with_route(
    task_type="live_analysis",
    messages=[{"role": "user", "content": "分析弹幕"}],
    context={"latency": "fast"}
)
```

### 5. 错误重试机制

```python
import time

def call_with_retry(gateway, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return gateway.chat_completion(messages=messages)
        except RuntimeError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

---

## 常见问题

### Q1: 如何选择 GLM-5 还是 MiniMax？

**A**:
- **实时分析**（弹幕、快速摘要）→ MiniMax-M2.5-highspeed
- **深度分析**（风格分析、话术生成）→ GLM-5
- **大上下文**（完整复盘、长文档）→ MiniMax-M2.5

### Q2: 思考模式会增加延迟吗？

**A**: 是的，思考模式会增加约 1-2 秒的延迟。建议仅在需要深度思考的场景启用。

### Q3: 流式输出的首字延迟是多少？

**A**:
- MiniMax-M2.5-highspeed: ~1-2 秒
- MiniMax-M2.5: ~1.5-2 秒
- GLM-5: ~2-3 秒

### Q4: 如何查看当前使用的模型？

```python
config = gateway.get_current_config()
print(f"服务商: {config['provider']}")
print(f"模型: {config['model']}")
```

### Q5: V1 和 V2 可以同时使用吗？

**A**: 可以，它们是完全独立的模块。但建议统一使用 V2 以获得更好的功能。

### Q6: 如何调试 API 调用？

**A**: 启用日志调试：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

或查看日志文件：
```bash
tail -f logs/ai_gateway_v2.log
```

---

## 更多资源

- [GLM-5 API 文档](https://docs.bigmodel.cn/cn/guide/models/text/glm-5)
- [MiniMax API 文档](https://platform.minimaxi.com/docs/api-reference/text-openai-api)
- [AI Gateway V1 使用指南](./AI_GATEWAY_GUIDE.md)
- [设计文档](../plans/2025-02-17-ai-architecture-redesign.md)

---

**文档更新**: 2025-02-18
**版本**: v2.0.0
**维护**: 提猫科技团队
