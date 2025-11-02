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
                    "content": "你是一位资深的直播运营分析师，擅长数据分析和运营策略建议。请基于实际数据给出客观、可执行的建议。你必须严格返回JSON格式，不要添加任何markdown标记或其他文字说明。"
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
        except json.JSONDecodeError as e:
            logger.debug(f"方式1失败: {e}")
        
        # 方式 2: 提取 Markdown 代码块中的 JSON
        if "```json" in text:
            try:
                json_text = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_text)
            except (IndexError, json.JSONDecodeError) as e:
                logger.debug(f"方式2失败: {e}")
        
        # 方式 3: 提取普通代码块中的 JSON
        if "```" in text:
            try:
                parts = text.split("```")
                for i in range(1, len(parts), 2):  # 代码块在奇数索引
                    json_text = parts[i].strip()
                    # 移除可能的语言标识符
                    if json_text.startswith('json\n'):
                        json_text = json_text[5:]
                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.debug(f"方式3失败: {e}")
        
        # 方式 4: 尝试清理后解析（移除BOM、空格、换行）
        try:
            cleaned_text = text.strip().lstrip('\ufeff').lstrip('\n').rstrip('\n')
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.debug(f"方式4失败: {e}")
        
        # 方式 5: 查找第一个 { 和最后一个 }，尝试提取JSON对象
        try:
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                json_text = text[first_brace:last_brace + 1]
                return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.debug(f"方式5失败: {e}")
        
        # 全部失败，记录详细错误
        logger.error(f"❌ 无法解析 JSON 响应")
        logger.error(f"原始响应长度: {len(text)} 字符")
        logger.error(f"前 500 字符:\n{text[:500]}")
        if len(text) > 500:
            logger.error(f"后 500 字符:\n{text[-500:]}")
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
  ],
  "trend_charts": {{
    "follows": {{
      "title": "新增关注趋势",
      "description": "根据实际数据分析新增关注的变化趋势（每分钟采样）",
      "chart_data": [
        {{"time": "0分", "value": 0}},
        {{"time": "1分", "value": 5}},
        {{"time": "2分", "value": 12}},
        {{"time": "3分", "value": 25}},
        {{"time": "4分", "value": 45}},
        {{"time": "5分", "value": 68}},
        {{"time": "...更多分钟", "value": "..."}},
        {{"time": "结束", "value": 200}}
      ],
      "insights": "在第X-Y分钟出现增长高峰，可能与某个爆点话题相关"
    }},
    "entries": {{
      "title": "进场人数趋势",
      "description": "直播间进场人数随时间的变化（每分钟采样）",
      "chart_data": [
        {{"time": "0分", "value": 0}},
        {{"time": "1分", "value": 15}},
        {{"time": "2分", "value": 35}},
        {{"time": "3分", "value": 60}},
        {{"time": "4分", "value": 90}},
        {{"time": "5分", "value": 125}},
        {{"time": "...更多分钟", "value": "..."}},
        {{"time": "结束", "value": 350}}
      ],
      "insights": "进场人数持续增长，直播初期引流效果良好"
    }},
    "peak_viewers": {{
      "title": "在线人数趋势",
      "description": "实时在线人数的波动情况（每分钟采样）",
      "chart_data": [
        {{"time": "0分", "value": 0}},
        {{"time": "1分", "value": 12}},
        {{"time": "2分", "value": 28}},
        {{"time": "3分", "value": 45}},
        {{"time": "4分", "value": 67}},
        {{"time": "5分", "value": 85}},
        {{"time": "...更多分钟", "value": "..."}},
        {{"time": "结束", "value": 90}}
      ],
      "insights": "第X分钟达到峰值XXX人，后期有所回落，需优化留人策略"
    }},
    "like_total": {{
      "title": "点赞数趋势",
      "description": "直播间点赞数累计变化（每分钟采样）",
      "chart_data": [
        {{"time": "0分", "value": 0}},
        {{"time": "1分", "value": 50}},
        {{"time": "2分", "value": 120}},
        {{"time": "3分", "value": 210}},
        {{"time": "4分", "value": 350}},
        {{"time": "5分", "value": 520}},
        {{"time": "...更多分钟", "value": "..."}},
        {{"time": "结束", "value": 2000}}
      ],
      "insights": "点赞增长稳定，互动氛围良好"
    }}
  }}
}}

【重要说明 - 图表数据生成规则】
1. **采样频率**: 每1分钟采集一次数据点（不是5分钟！）
2. **数据点数量**: 根据直播时长生成相应数量的数据点
   - 例如：10分钟直播 = 10个数据点（0分、1分、2分...9分、结束）
   - 例如：30分钟直播 = 30个数据点（0分、1分、2分...29分、结束）
3. **时间格式**: 使用 "X分" 格式，最后一个点用 "结束"
4. **数值合理性**:
   - 最后一个时间点的 value 必须等于【直播数据】中的实际最终值
   - 中间数据点要符合真实增长规律（不要线性增长，要有波动）
   - 新增类指标（关注、点赞）：应该是累加的，持续增长
   - 瞬时类指标（在线人数）：可以有起伏波动
5. **数据真实性**: 
   - 如果某个指标实际值为0，图表所有数据点都应该是0
   - 不要虚构数据，基于实际最终值进行合理推算
6. **洞察价值**: insights 必须指出关键转折点、峰值、异常波动等

【示例说明】
假设直播时长15分钟，新增关注200人：
- 应该生成15个数据点：0分(0) → 1分(8) → 2分(18) → ... → 14分(185) → 结束(200)
- 数值增长要有快慢变化，不要平均分配
- 找出增长最快的时间段并在 insights 中说明

【分析要点】
1. 客观评分：基于实际数据和转写内容，不要盲目打高分
2. 具体分析：引用具体的数据或话术片段支撑观点
3. 可执行建议：给出明确的改进方向和操作步骤
4. 运营导向：关注转化、留存、互动等关键指标
5. 数据真实：图表数据必须基于实际指标推算，不要虚构

【输出格式要求】
1. 只输出纯JSON对象，不要包含任何markdown代码块标记（如 ```json）
2. 不要在JSON前后添加任何说明文字
3. 确保JSON格式完全正确，可以直接被解析
4. 所有字符串字段使用双引号
5. 数字字段不要加引号

示例输出格式（注意：不要包含这个提示，直接输出JSON）：
{{"overall_score": 85, "performance_analysis": {{...}}, ...}}

现在开始输出JSON："""
    
    # 调用 Gemini
    logger.info(f"📊 准备数据 - 转写: {len(transcript)} 字符, 弹幕: {len(comments_preview)} 条")
    logger.info(f"🚀 开始调用 Gemini 生成复盘报告...")
    
    result = adapter.generate_review(
        prompt=prompt,
        temperature=0.3,
        max_tokens=4096,  # 增加token限制，确保完整输出
        response_format="json"
    )
    
    if not result:
        logger.error("❌ Gemini API 调用返回 None")
        raise RuntimeError("Gemini API 调用失败，请检查网络连接和API密钥")
    
    logger.info(f"✅ Gemini 响应接收成功，长度: {len(result['text'])} 字符")
    
    # 解析 JSON 响应
    report_data = adapter.parse_json_response(result["text"])
    if not report_data:
        # 保存原始响应用于调试
        error_msg = f"Gemini 返回的 JSON 格式无效。响应长度: {len(result['text'])} 字符"
        logger.error(f"❌ {error_msg}")
        logger.error(f"完整响应内容:\n{result['text']}")
        
        # 提供降级方案：返回基本结构
        logger.warning("⚠️ 使用降级方案：返回基本报告结构")
        report_data = {
            "overall_score": 0,
            "performance_analysis": {
                "overall_assessment": "AI分析失败，无法生成完整报告。原因：JSON解析错误。",
                "content_quality": {"score": 0, "comments": "解析失败"},
                "engagement": {"score": 0, "comments": "解析失败"},
                "conversion_potential": {"score": 0, "comments": "解析失败"}
            },
            "key_highlights": ["AI分析遇到问题，请重试或联系技术支持"],
            "key_issues": ["JSON解析失败"],
            "improvement_suggestions": ["请检查网络连接和API配置"],
            "error": error_msg,
            "raw_response_preview": result["text"][:1000]  # 保存前1000字符用于调试
        }
    
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
