# AI网关2.0重构实施计划 - Phase 1

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构AI网关，集成GLM-5和MiniMax M2.5系列模型，实现智能路由和思考模式支持

**Architecture:** 创建新的ai_gateway_v2.py，保留旧网关以支持回退；添加GLM-5和MiniMax提供商；实现ThinkingMode管理器；构建SmartRouter智能路由引擎

**Tech Stack:** Python 3.10+, OpenAI SDK, SQLite, pytest

**Design Doc:** docs/plans/2025-02-17-ai-architecture-redesign.md

---

## Task 1: 环境准备和依赖安装

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example`

**Step 1: 添加新依赖到requirements.txt**

在 `requirements.txt` 末尾添加：

```txt
# AI Gateway 2.0 新增依赖
# GLM-5 和 MiniMax 已通过 OpenAI SDK 兼容，无需额外依赖
```

**Step 2: 更新.env.example添加新环境变量**

在 `.env.example` 的 AI 服务商配置部分添加：

```bash
# ==================== 智谱 GLM-5 配置 ====================
GLM_API_KEY=your-glm-api-key-here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# ==================== MiniMax M2.5 配置 ====================
MINIMAX_API_KEY=your-minimax-api-key-here
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

**Step 3: 验证文件修改**

```bash
git diff requirements.txt .env.example
```

Expected: 看到新增的环境变量配置

**Step 4: 提交环境配置**

```bash
git add requirements.txt .env.example
git commit -m "chore: add GLM-5 and MiniMax environment configuration"
```

---

## Task 2: 创建ThinkingMode管理器

**Files:**
- Create: `server/ai/thinking_mode.py`
- Create: `tests/ai/test_thinking_mode.py`

**Step 1: 编写ThinkingMode测试**

创建 `tests/ai/test_thinking_mode.py`：

```python
"""测试思考模式管理器"""
import pytest
from server.ai.thinking_mode import ThinkingMode


def test_enable_for_glm5_adds_thinking_parameter():
    """测试为GLM-5启用思考模式"""
    kwargs = {"temperature": 0.7}
    result = ThinkingMode.enable_for_glm5(kwargs)

    assert "thinking" in result
    assert result["thinking"]["type"] == "enabled"
    assert result["temperature"] == 0.7  # 保留原有参数


def test_enable_for_minimax_adds_reasoning_split():
    """测试为MiniMax启用思考分离"""
    kwargs = {"temperature": 0.5}
    result = ThinkingMode.enable_for_minimax(kwargs)

    assert "extra_body" in result
    assert result["extra_body"]["reasoning_split"] is True
    assert result["temperature"] == 0.5


def test_parse_glm5_thinking_response():
    """测试解析GLM-5的思考响应"""
    # 模拟GLM-5响应对象
    class MockMessage:
        reasoning_content = "思考过程内容"
        content = "最终输出内容"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "glm")

    assert result["reasoning"] == "思考过程内容"
    assert result["content"] == "最终输出内容"


def test_parse_minimax_thinking_response():
    """测试解析MiniMax的思考响应"""
    # 模拟MiniMax响应对象
    class MockMessage:
        reasoning_details = [{"text": "推理步骤1"}, {"text": "推理步骤2"}]
        content = "最终答案"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "minimax")

    assert result["reasoning"] == "推理步骤1推理步骤2"
    assert result["content"] == "最终答案"


def test_parse_response_without_thinking():
    """测试解析不包含思考过程的响应"""
    class MockMessage:
        content = "普通响应"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "unknown_provider")

    assert result["reasoning"] == ""
    assert result["content"] == "普通响应"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/ai/test_thinking_mode.py -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'server.ai.thinking_mode'

**Step 3: 实现ThinkingMode类**

创建 `server/ai/thinking_mode.py`：

```python
"""思考模式管理器

支持GLM-5和MiniMax的思考模式
"""
from typing import Any, Dict


class ThinkingMode:
    """思考模式管理器"""

    @staticmethod
    def enable_for_glm5(kwargs: dict) -> dict:
        """为GLM-5启用深度思考模式

        Args:
            kwargs: 原始请求参数

        Returns:
            添加了thinking参数的请求参数
        """
        kwargs["thinking"] = {"type": "enabled"}
        return kwargs

    @staticmethod
    def enable_for_minimax(kwargs: dict) -> dict:
        """为MiniMax启用思考分离模式

        Args:
            kwargs: 原始请求参数

        Returns:
            添加了extra_body参数的请求参数
        """
        kwargs["extra_body"] = {"reasoning_split": True}
        return kwargs

    @staticmethod
    def parse_thinking_response(response: Any, provider: str) -> Dict[str, str]:
        """解析包含思考过程的响应

        Args:
            response: API响应对象
            provider: 服务商名称（'glm' 或 'minimax'）

        Returns:
            包含 reasoning 和 content 的字典
        """
        choice = response.choices[0]

        if provider == "glm":
            # GLM-5: reasoning_content + content
            return {
                "reasoning": getattr(choice.message, 'reasoning_content', ''),
                "content": choice.message.content,
            }
        elif provider == "minimax":
            # MiniMax: reasoning_details + content
            reasoning_text = ""
            if hasattr(choice.message, 'reasoning_details'):
                reasoning_text = "".join(
                    detail.get("text", "")
                    for detail in choice.message.reasoning_details
                )
            return {
                "reasoning": reasoning_text,
                "content": choice.message.content,
            }

        # 默认返回空推理
        return {"reasoning": "", "content": choice.message.content}
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/ai/test_thinking_mode.py -v
```

Expected: PASS - 所有测试通过

**Step 5: 提交ThinkingMode实现**

```bash
git add server/ai/thinking_mode.py tests/ai/test_thinking_mode.py
git commit -m "feat: add ThinkingMode manager for GLM-5 and MiniMax"
```

---

## Task 3: 创建功能级模型配置

**Files:**
- Create: `server/ai/function_models.py`
- Create: `tests/ai/test_function_models.py`

**Step 1: 编写功能级模型配置测试**

创建 `tests/ai/test_function_models.py`：

```python
"""测试功能级模型配置"""
import pytest
from server.ai.function_models import (
    FUNCTION_MODELS,
    get_function_model,
    get_all_function_models
)


def test_function_models_structure():
    """测试功能模型配置结构"""
    assert "live_analysis" in FUNCTION_MODELS
    assert "style_profile" in FUNCTION_MODELS
    assert "script_generation" in FUNCTION_MODELS
    assert "live_review" in FUNCTION_MODELS


def test_live_analysis_uses_minimax_highspeed():
    """测试实时分析使用MiniMax highspeed"""
    config = get_function_model("live_analysis")

    assert config["provider"] == "minimax"
    assert config["model"] == "MiniMax-M2.5-highspeed"
    assert config["enable_thinking"] is False


def test_style_profile_uses_glm5():
    """测试风格画像使用GLM-5"""
    config = get_function_model("style_profile")

    assert config["provider"] == "glm"
    assert config["model"] == "glm-5"
    assert config["enable_thinking"] is True


def test_get_all_function_models_returns_copy():
    """测试获取所有配置返回副本"""
    all_models = get_all_function_models()

    # 修改返回的副本不应影响原始配置
    all_models["test"] = {"provider": "test"}
    assert "test" not in FUNCTION_MODELS


def test_get_function_model_unknown_returns_default():
    """测试未知功能返回默认配置"""
    config = get_function_model("unknown_function")

    assert config["provider"] == "minimax"
    assert config["model"] == "MiniMax-M2.5-highspeed"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/ai/test_function_models.py -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现功能级模型配置**

创建 `server/ai/function_models.py`：

```python
"""功能级模型配置

为不同功能指定最优的模型配置
"""
from typing import Any, Dict, Optional

# 功能级模型配置
# 只使用GLM-5和MiniMax系列
FUNCTION_MODELS: Dict[str, Dict[str, Any]] = {
    "live_analysis": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",  # 极速版，100 TPS
        "enable_thinking": False,           # 实时分析不需要思考过程
        "reason": "高速输出，降低延迟"
    },
    "style_profile": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "面向Agent优化，深度分析风格"
    },
    "script_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "深度思考提升话术质量"
    },
    "live_review": {
        "provider": "minimax",
        "model": "MiniMax-M2.5",            # 复盘用标准版
        "enable_thinking": True,
        "reason": "204K大上下文，支持长复盘"
    },
    "reflection": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，评估分析质量"
    },
    "chat_focus": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",
        "enable_thinking": False,
        "reason": "快速摘要，降低延迟"
    },
    "topic_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，生成智能话题"
    }
}

# 默认配置（MiniMax highspeed性价比最高）
DEFAULT_CONFIG = {
    "provider": "minimax",
    "model": "MiniMax-M2.5-highspeed",
    "enable_thinking": False,
    "reason": "默认配置，性价比最高"
}


def get_function_model(function_name: str) -> Dict[str, Any]:
    """获取指定功能的模型配置

    Args:
        function_name: 功能名称

    Returns:
        模型配置字典
    """
    return FUNCTION_MODELS.get(function_name, DEFAULT_CONFIG).copy()


def get_all_function_models() -> Dict[str, Dict[str, Any]]:
    """获取所有功能模型配置的副本

    Returns:
        所有功能配置的副本
    """
    return FUNCTION_MODELS.copy()
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/ai/test_function_models.py -v
```

Expected: PASS

**Step 5: 提交功能模型配置**

```bash
git add server/ai/function_models.py tests/ai/test_function_models.py
git commit -m "feat: add function-level model configuration"
```

---

## Task 4: 创建AI Gateway 2.0基础框架

**Files:**
- Create: `server/ai/ai_gateway_v2.py`
- Create: `tests/ai/test_ai_gateway_v2.py`

**Step 1: 编写AI Gateway 2.0基础测试**

创建 `tests/ai/test_ai_gateway_v2.py`：

```python
"""测试AI Gateway 2.0"""
import pytest
from unittest.mock import Mock, patch
from server.ai.ai_gateway_v2 import AIGatewayV2


def test_gateway_initializes_without_providers():
    """测试网关初始化时无服务商"""
    gateway = AIGatewayV2()

    assert gateway.providers == {}
    assert gateway.clients == {}


@patch.dict('os.environ', {
    'GLM_API_KEY': 'test-glm-key',
    'MINIMAX_API_KEY': 'test-minimax-key'
})
def test_gateway_loads_glm_and_minimax_from_env():
    """测试从环境变量加载GLM和MiniMax配置"""
    gateway = AIGatewayV2()

    assert "glm" in gateway.providers
    assert "minimax" in gateway.providers
    assert gateway.providers["glm"].api_key == "test-glm-key"
    assert gateway.providers["minimax"].api_key == "test-minimax-key"


def test_register_glm5_provider():
    """测试注册GLM-5服务商"""
    gateway = AIGatewayV2()

    gateway.register_provider(
        provider="glm",
        api_key="test-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-5"
    )

    assert "glm" in gateway.providers
    assert gateway.providers["glm"].default_model == "glm-5"


def test_register_minimax_provider():
    """测试注册MiniMax服务商"""
    gateway = AIGatewayV2()

    gateway.register_provider(
        provider="minimax",
        api_key="test-key",
        base_url="https://api.minimaxi.com/v1",
        default_model="MiniMax-M2.5-highspeed",
        models=["MiniMax-M2.5", "MiniMax-M2.5-highspeed"]
    )

    assert "minimax" in gateway.providers
    assert "MiniMax-M2.5" in gateway.providers["minimax"].models


def test_switch_provider():
    """测试切换服务商"""
    gateway = AIGatewayV2()
    gateway.register_provider("glm", "key1", "url1", "glm-5")
    gateway.register_provider("minimax", "key2", "url2", "MiniMax-M2.5")

    gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

    assert gateway.current_provider == "minimax"
    assert gateway.current_model == "MiniMax-M2.5-highspeed"


def test_switch_to_unknown_provider_raises_error():
    """测试切换到未注册的服务商抛出错误"""
    gateway = AIGatewayV2()

    with pytest.raises(ValueError, match="未注册的服务商"):
        gateway.switch_provider("unknown", "model")
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/ai/test_ai_gateway_v2.py::test_gateway_initializes_without_providers -v
```

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现AI Gateway 2.0基础框架**

创建 `server/ai/ai_gateway_v2.py`：

```python
"""AI模型控制网关 2.0

统一管理GLM-5和MiniMax服务商，支持：
- 智能路由
- 思考模式
- 流式输出
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI服务商枚举"""
    GLM = "glm"           # 智谱GLM-5
    MINIMAX = "minimax"   # MiniMax M2.5系列


@dataclass
class ProviderConfig:
    """服务商配置"""
    provider: AIProvider
    api_key: str
    base_url: str
    default_model: str
    models: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        if not self.models:
            self.models = [self.default_model]


class AIGatewayV2:
    """AI模型控制网关 2.0（单例模式）"""

    _instance: Optional[AIGatewayV2] = None

    def __init__(self):
        """初始化网关"""
        self.providers: Dict[str, ProviderConfig] = {}
        self.clients: Dict[str, OpenAI] = {}
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None

        # 从环境变量加载配置
        self._load_from_env()

    @classmethod
    def get_instance(cls) -> AIGatewayV2:
        """获取网关单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 加载GLM-5
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key:
            self.register_provider(
                provider="glm",
                api_key=glm_key,
                base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                default_model="glm-5",
            )
            logger.info("✅ GLM-5已注册")

        # 加载MiniMax
        minimax_key = os.getenv("MINIMAX_API_KEY")
        if minimax_key:
            self.register_provider(
                provider="minimax",
                api_key=minimax_key,
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
                default_model="MiniMax-M2.5-highspeed",
                models=[
                    "MiniMax-M2.5",
                    "MiniMax-M2.5-highspeed",
                    "MiniMax-M2.1",
                    "MiniMax-M2.1-highspeed",
                    "MiniMax-M2",
                ]
            )
            logger.info("✅ MiniMax M2.5已注册")

    def register_provider(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        default_model: str,
        models: Optional[List[str]] = None,
        enabled: bool = True,
    ) -> None:
        """注册一个服务商

        Args:
            provider: 服务商名称 (glm/minimax)
            api_key: API密钥
            base_url: API基础URL
            default_model: 默认模型
            models: 支持的模型列表
            enabled: 是否启用
        """
        provider = provider.lower()

        config = ProviderConfig(
            provider=AIProvider(provider),
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            models=models or [],
            enabled=enabled,
        )

        self.providers[provider] = config

        # 创建OpenAI客户端
        if OpenAI and enabled:
            try:
                self.clients[provider] = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info(f"AI服务商已注册: {provider} (模型: {config.default_model})")
            except Exception as e:
                logger.error(f"创建 {provider} 客户端失败: {e}")
                config.enabled = False

    def switch_provider(
        self,
        provider: str,
        model: Optional[str] = None,
    ) -> None:
        """切换当前服务商和模型

        Args:
            provider: 服务商名称
            model: 模型名称（为空则使用该服务商的默认模型）

        Raises:
            ValueError: 服务商未注册或已禁用
        """
        provider = provider.lower()

        if provider not in self.providers:
            raise ValueError(f"未注册的服务商: {provider}")

        config = self.providers[provider]
        if not config.enabled:
            raise ValueError(f"服务商已禁用: {provider}")

        self.current_provider = provider
        self.current_model = model or config.default_model

        logger.info(f"已切换至: {provider} / {self.current_model}")


# 便捷函数
def get_gateway() -> AIGatewayV2:
    """获取网关实例"""
    return AIGatewayV2.get_instance()
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/ai/test_ai_gateway_v2.py -v
```

Expected: PASS（部分测试）

**Step 5: 提交Gateway 2.0基础框架**

```bash
git add server/ai/ai_gateway_v2.py tests/ai/test_ai_gateway_v2.py
git commit -m "feat: implement AI Gateway 2.0 basic framework"
```

---

## Task 5: 实现智能路由引擎

**Files:**
- Modify: `server/ai/ai_gateway_v2.py`
- Create: `tests/ai/test_smart_router.py`

**Step 1: 编写智能路由测试**

创建 `tests/ai/test_smart_router.py`：

```python
"""测试智能路由引擎"""
import pytest
from server.ai.ai_gateway_v2 import AIGatewayV2


@pytest.fixture
def gateway():
    """创建配置好的网关实例"""
    g = AIGatewayV2()
    g.register_provider("glm", "key", "url", "glm-5")
    g.register_provider("minimax", "key", "url", "MiniMax-M2.5-highspeed")
    return g


def test_route_live_analysis_to_minimax_highspeed(gateway):
    """测试实时分析路由到MiniMax highspeed"""
    model = gateway.smart_route("live_analysis", {"latency": "fast"})

    assert model == "minimax:MiniMax-M2.5-highspeed"


def test_route_style_profile_to_glm5(gateway):
    """测试风格画像路由到GLM-5"""
    model = gateway.smart_route("style_profile", {})

    assert model == "glm:glm-5"


def test_route_script_generation_to_glm5(gateway):
    """测试话术生成路由到GLM-5"""
    model = gateway.smart_route("script_generation", {})

    assert model == "glm:glm-5"


def test_route_live_review_to_minimax(gateway):
    """测试复盘总结路由到MiniMax标准版"""
    model = gateway.smart_route("live_review", {})

    assert model == "minimax:MiniMax-M2.5"


def test_route_reflection_to_glm5(gateway):
    """测试反思路由到GLM-5"""
    model = gateway.smart_route("reflection", {})

    assert model == "glm:glm-5"


def test_route_unknown_to_default(gateway):
    """测试未知任务路由到默认模型"""
    model = gateway.smart_route("unknown_task", {})

    assert model == "minimax:MiniMax-M2.5-highspeed"
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/ai/test_smart_router.py -v
```

Expected: FAIL - AttributeError: 'AIGatewayV2' object has no attribute 'smart_route'

**Step 3: 实现智能路由引擎**

在 `server/ai/ai_gateway_v2.py` 的 `AIGatewayV2` 类中添加：

```python
    def smart_route(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """智能路由 - 只在GLM-5和MiniMax之间选择

        Args:
            task_type: 任务类型（live_analysis/style_profile等）
            requirements: 任务需求（latency/quality等）

        Returns:
            格式为 "provider:model" 的字符串
        """
        # 实时分析任务 → MiniMax highspeed（100 TPS）
        if task_type == "live_analysis":
            latency = requirements.get("latency", "normal")
            if latency == "fast":
                return "minimax:MiniMax-M2.5-highspeed"
            else:
                return "minimax:MiniMax-M2.5"

        # Agent工作流任务 → GLM-5（专为Agent打造）
        elif task_type in ["style_profile", "script_generation", "topic_generation"]:
            return "glm:glm-5"

        # 反思和推理任务 → GLM-5（深度思考）
        elif task_type == "reflection":
            return "glm:glm-5"

        # 复盘总结 → MiniMax M2.5（大上下文204K）
        elif task_type == "live_review":
            return "minimax:MiniMax-M2.5"

        # 快速摘要 → MiniMax highspeed
        elif task_type == "chat_focus":
            return "minimax:MiniMax-M2.5-highspeed"

        # 默认：MiniMax highspeed（性价比最高）
        return "minimax:MiniMax-M2.5-highspeed"
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/ai/test_smart_router.py -v
```

Expected: PASS

**Step 5: 提交智能路由实现**

```bash
git add server/ai/ai_gateway_v2.py tests/ai/test_smart_router.py
git commit -m "feat: implement smart routing engine"
```

---

## 后续任务（继续Phase 1）

这个计划会持续包含：

- Task 6: 实现带思考模式的chat_completion
- Task 7: 实现流式输出支持
- Task 8: 集成测试 - GLM-5真实调用
- Task 9: 集成测试 - MiniMax真实调用
- Task 10: 更新现有代码使用Gateway 2.0
- Task 11: 性能测试和优化
- Task 12: 文档更新

**（由于篇幅限制，Task 6-12 的详细步骤将在执行时继续展开）**

---

## 执行说明

**重要提示：**

1. **严格TDD流程**: 每个任务都遵循"写测试→失败→写代码→通过→提交"的循环
2. **频繁提交**: 每个小步骤完成后立即提交
3. **独立测试**: 确保每个Task可以独立测试和验证
4. **回滚安全**: 如果某个Task失败，可以安全回滚到上一个Task

**质量标准：**

- 所有测试必须通过
- 代码覆盖率 > 80%
- 遵循PEP 8规范
- 包含完整的docstring

**下一步：**

选择执行方式后，将逐步执行每个Task。
