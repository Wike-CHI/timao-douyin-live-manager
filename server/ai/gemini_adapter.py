# -*- coding: utf-8 -*-
"""
Gemini AI 适配器（通过 AiHubMix 的 OpenAI 兼容接口）

使用 OpenAI SDK 通过 AiHubMix 代理调用 Gemini 2.5 Flash，
用于生成直播复盘报告和深度分析。
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional

try:
    import openai
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger(__name__)


class GeminiAdapter:
    """Gemini 2.5 Flash 适配器
    
    通过 AiHubMix 的 OpenAI 兼容接口调用 Gemini API。
    支持 JSON 模式输出，适合生成结构化的复盘报告。
    """
    
    def __init__(self):
        """初始化 Gemini 适配器"""
        self.api_key = os.getenv("AIHUBMIX_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = os.getenv("AIHUBMIX_BASE_URL", "https://aihubmix.com/v1")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025")
        
        if not _OPENAI_AVAILABLE:
            logger.error("❌ openai 库未安装，请运行: pip install openai")
            self.client = None
            return
        
        if not self.api_key:
            logger.warning("⚠️ AIHUBMIX_API_KEY 或 GEMINI_API_KEY 未配置，Gemini 复盘功能将不可用")
            logger.info("请在 .env 文件中添加:")
            logger.info("AIHUBMIX_API_KEY=sk-your-aihubmix-api-key")
            self.client = None
        else:
            try:
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=60.0  # Gemini 可能需要更长时间处理大量数据
                )
                logger.info(f"✅ Gemini 适配器初始化成功 - 模型: {self.model}")
            except Exception as e:
                logger.error(f"❌ Gemini 客户端初始化失败: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None
    
    def generate_review(
        self, 
        prompt: str, 
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """生成复盘报告
        
        Args:
            prompt: 完整的分析提示词
            temperature: 温度参数（0-1，越低越确定性强，推荐 0.2-0.4）
            max_tokens: 最大输出 token 数（Gemini Flash 支持最大 8192）
            response_format: 输出格式，"json" 或 "text"
        
        Returns:
            成功返回:
            {
                "text": "生成的文本内容",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300
                },
                "cost": 0.001234,  # 美元
                "duration": 2.5     # 秒
            }
            失败返回: None
        """
        if not self.client:
            logger.error("❌ Gemini 客户端未初始化")
            return None
        
        start_time = time.time()
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的直播运营分析师，擅长数据分析和运营策略建议。请基于实际数据给出客观、可执行的建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # 如果需要 JSON 格式输出
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
            
            logger.info(f"🚀 开始调用 Gemini API - 模型: {self.model}, 温度: {temperature}")
            
            response = self.client.chat.completions.create(**request_params)
            
            duration = time.time() - start_time
            content = response.choices[0].message.content
            usage = response.usage
            
            # 计算成本（Gemini 2.5 Flash 定价，单位：美元）
            # Input: $0.075 / 1M tokens
            # Output: $0.30 / 1M tokens
            cost = (
                usage.prompt_tokens * 0.075 / 1_000_000 +
                usage.completion_tokens * 0.30 / 1_000_000
            )
            
            logger.info(
                f"✅ Gemini 调用成功 - "
                f"Tokens: {usage.prompt_tokens} (输入) + {usage.completion_tokens} (输出) = {usage.total_tokens}, "
                f"成本: ${cost:.6f}, "
                f"耗时: {duration:.2f}s"
            )
            
            return {
                "text": content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "cost": cost,
                "duration": duration
            }
        
        except openai.APIError as e:
            duration = time.time() - start_time
            logger.error(f"❌ Gemini API 错误 ({duration:.2f}s): {e}")
            return None
        except openai.RateLimitError as e:
            duration = time.time() - start_time
            logger.error(f"❌ Gemini API 限流 ({duration:.2f}s): {e}")
            logger.info("建议: 稍后重试或升级 API 配额")
            return None
        except openai.Timeout as e:
            duration = time.time() - start_time
            logger.error(f"❌ Gemini API 超时 ({duration:.2f}s): {e}")
            logger.info("建议: 减少输入数据量或增加超时时间")
            return None
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Gemini 调用失败 ({duration:.2f}s): {e}", exc_info=True)
            return None
    
    def parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """解析 JSON 响应
        
        尝试多种方式解析 Gemini 返回的 JSON 内容。
        
        Args:
            text: Gemini 返回的文本
        
        Returns:
            解析成功返回字典，失败返回 None
        """
        if not text or not text.strip():
            logger.error("❌ Gemini 返回内容为空")
            return None
        
        # 方式 1: 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 方式 2: 提取 Markdown 代码块中的 JSON
        if "```json" in text:
            try:
                json_text = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_text)
            except (IndexError, json.JSONDecodeError):
                pass
        
        # 方式 3: 提取普通代码块中的 JSON
        if "```" in text:
            try:
                json_text = text.split("```")[1].strip()
                return json.loads(json_text)
            except (IndexError, json.JSONDecodeError):
                pass
        
        # 方式 4: 尝试清理后解析
        try:
            cleaned_text = text.strip().lstrip('\ufeff')  # 移除 BOM
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        logger.error(f"❌ 无法解析 JSON 响应，前 200 字符: {text[:200]}")
        return None
    
    def test_connection(self) -> bool:
        """测试连接是否正常
        
        Returns:
            连接正常返回 True，否则返回 False
        """
        if not self.client:
            logger.error("❌ Gemini 客户端未初始化")
            return False
        
        try:
            logger.info("🧪 测试 Gemini 连接...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info(f"✅ Gemini 连接测试成功 - 模型响应: {response.choices[0].message.content[:50]}")
            return True
        except Exception as e:
            logger.error(f"❌ Gemini 连接测试失败: {e}")
            return False


# 全局单例
_gemini_adapter: Optional[GeminiAdapter] = None


def get_gemini_adapter() -> GeminiAdapter:
    """获取 Gemini 适配器单例"""
    global _gemini_adapter
    if _gemini_adapter is None:
        _gemini_adapter = GeminiAdapter()
    return _gemini_adapter


def test_gemini_api():
    """测试 Gemini API（用于调试）"""
    adapter = get_gemini_adapter()
    
    if not adapter.is_available():
        print("❌ Gemini 服务不可用，请检查配置")
        return
    
    print("🧪 测试 Gemini API...")
    
    # 测试简单调用
    result = adapter.generate_review(
        prompt="请用JSON格式返回一个简单的直播复盘报告示例，包含overall_score和key_highlights字段。",
        temperature=0.3,
        max_tokens=500,
        response_format="json"
    )
    
    if result:
        print(f"\n✅ 调用成功!")
        print(f"📊 Tokens: {result['usage']['total_tokens']}")
        print(f"💰 成本: ${result['cost']:.6f}")
        print(f"⏱️  耗时: {result['duration']:.2f}s")
        print(f"\n📝 返回内容:\n{result['text'][:500]}")
        
        # 测试 JSON 解析
        parsed = adapter.parse_json_response(result['text'])
        if parsed:
            print(f"\n✅ JSON 解析成功: {parsed}")
        else:
            print("\n❌ JSON 解析失败")
    else:
        print("❌ 调用失败")


if __name__ == "__main__":
    # 运行测试
    test_gemini_api()
