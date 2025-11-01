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


def generate_review_report(review_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成完整的直播复盘报告
    
    Args:
        review_data: 复盘数据，包含：
            - session_id: 会话ID
            - transcript: 完整转写文本
            - comments: 弹幕列表
            - anchor_name: 主播名称
            - metrics: 直播数据指标
    
    Returns:
        复盘报告字典，包含：
            - overall_score: 综合评分 (0-100)
            - performance_analysis: 表现分析
            - key_highlights: 亮点列表
            - key_issues: 问题列表
            - improvement_suggestions: 改进建议列表
            - ai_model: 使用的AI模型
            - generation_cost: 生成成本（美元）
            - generation_tokens: 消耗的token数
            - generation_duration: 生成耗时（秒）
    """
    adapter = get_gemini_adapter()
    
    if not adapter.is_available():
        raise RuntimeError("Gemini 服务不可用，请检查 AIHUBMIX_API_KEY 配置")
    
    # 准备数据
    transcript = review_data.get("transcript", "")
    comments = review_data.get("comments", [])
    anchor_name = review_data.get("anchor_name", "主播")
    metrics = review_data.get("metrics", {})
    
    # 限制数据量以控制成本
    transcript_preview = transcript[:10000] if len(transcript) > 10000 else transcript
    comments_preview = comments[:200] if isinstance(comments, list) else []
    
    # 构建提示词
    prompt = f"""你是一位资深的直播运营分析师，请基于以下数据生成一份详细的直播复盘报告。

【主播信息】
主播昵称: {anchor_name}

【直播数据】
{json.dumps(metrics, ensure_ascii=False, indent=2)}

【口播转写（节选前10000字）】
{transcript_preview}

【弹幕样本（最多200条）】
{json.dumps(comments_preview[:50], ensure_ascii=False, indent=2)}
...（共 {len(comments_preview)} 条弹幕）

【任务要求】
请以专业的运营分析师视角，生成一份结构化的复盘报告，严格按照以下 JSON 格式输出：

{{
  "overall_score": 85,  // 综合评分，0-100，综合考虑内容质量、互动效果、转化潜力等
  "performance_analysis": {{
    "overall_assessment": "本场直播整体表现...",  // 总体评价，100-200字
    "content_quality": {{
      "score": 80,
      "comments": "内容方面的分析..."
    }},
    "engagement": {{
      "score": 85,
      "comments": "互动效果分析..."
    }},
    "conversion_potential": {{
      "score": 75,
      "comments": "转化潜力分析..."
    }}
  }},
  "key_highlights": [
    "亮点1：具体描述本场直播的优秀表现",
    "亮点2：...",
    "亮点3：..."
  ],
  "key_issues": [
    "问题1：需要改进的具体问题",
    "问题2：...",
    "问题3：..."
  ],
  "improvement_suggestions": [
    "建议1：具体的、可执行的改进建议",
    "建议2：...",
    "建议3：..."
  ]
}}

【分析要点】
1. 客观评分：基于实际数据和转写内容，不要盲目打高分
2. 具体分析：引用具体的数据或话术片段支撑观点
3. 可执行建议：给出明确的改进方向和操作步骤
4. 运营导向：关注转化、留存、互动等关键指标

请只输出 JSON，不要其他解释文字。"""
    
    # 调用 Gemini
    logger.info(f"📊 准备数据 - 转写: {len(transcript)} 字符, 弹幕: {len(comments_preview)} 条")
    result = adapter.generate_review(
        prompt=prompt,
        temperature=0.3,
        max_tokens=3000,
        response_format="json"
    )
    
    if not result:
        raise RuntimeError("Gemini API 调用失败")
    
    # 解析 JSON 响应
    report_data = adapter.parse_json_response(result["text"])
    if not report_data:
        logger.error(f"❌ JSON 解析失败，原始响应: {result['text'][:500]}")
        raise RuntimeError("Gemini 返回的 JSON 格式无效")
    
    # 补充元数据
    report_data["ai_model"] = adapter.model
    report_data["generation_cost"] = result["cost"]
    report_data["generation_tokens"] = result["usage"]["total_tokens"]
    report_data["generation_duration"] = result["duration"]
    
    logger.info(
        f"✅ 复盘报告生成完成 - "
        f"评分: {report_data.get('overall_score', 0)}/100, "
        f"成本: ${result['cost']:.6f}, "
        f"耗时: {result['duration']:.2f}s"
    )
    
    return report_data


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
