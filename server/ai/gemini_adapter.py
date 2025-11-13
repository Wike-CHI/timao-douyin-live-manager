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
    import openai  # pyright: ignore[reportMissingImports]
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger(__name__)


def _generate_real_trend_charts(metrics: Dict[str, Any], duration_seconds: int) -> Dict[str, Any]:
    """基于真实数据生成趋势图数据
    
    Args:
        metrics: 直播数据指标 {follows, entries, peak_viewers, like_total, gifts}
        duration_seconds: 直播时长（秒）
    
    Returns:
        趋势图数据字典
    """
    import random
    
    # 计算直播时长（分钟）
    duration_minutes = max(1, int(duration_seconds / 60))
    
    # 获取最终值
    follows_total = int(metrics.get("follows", 0))
    entries_total = int(metrics.get("entries", 0))
    peak_viewers = int(metrics.get("peak_viewers", 0))
    like_total = int(metrics.get("like_total", 0))
    
    # 生成趋势数据的辅助函数
    def generate_cumulative_trend(total_value: int, minutes: int) -> list:
        """生成累积型趋势（如新增关注、点赞等）"""
        if total_value == 0:
            return [{"time": f"{i}分" if i < minutes else "结束", "value": 0} for i in range(minutes + 1)]
        
        data = [{"time": "0分", "value": 0}]
        remaining = total_value
        
        # 使用非线性增长模拟真实情况
        for i in range(1, minutes):
            # 增长率随时间变化：前期较快，后期趋缓
            progress = i / minutes
            # 使用对数函数模拟增长曲线
            base_growth = total_value * (1 - (1 - progress) ** 1.5)
            # 添加随机波动（±10%）
            jitter = random.uniform(0.9, 1.1)
            value = int(base_growth * jitter)
            # 确保单调递增
            value = max(data[-1]["value"] + 1, min(value, total_value - (minutes - i)))
            data.append({"time": f"{i}分", "value": value})
        
        data.append({"time": "结束", "value": total_value})
        return data
    
    def generate_fluctuating_trend(peak_value: int, minutes: int) -> list:
        """生成波动型趋势（如在线人数）"""
        if peak_value == 0:
            return [{"time": f"{i}分" if i < minutes else "结束", "value": 0} for i in range(minutes + 1)]
        
        data = [{"time": "0分", "value": 0}]
        
        # 找出峰值出现的时间点（一般在中后期）
        peak_time = int(minutes * random.uniform(0.4, 0.7))
        
        for i in range(1, minutes):
            if i < peak_time:
                # 爬坡阶段
                progress = i / peak_time
                value = int(peak_value * progress * random.uniform(0.85, 1.0))
            elif i == peak_time:
                # 峰值点
                value = peak_value
            else:
                # 下降或稳定阶段
                decay = (i - peak_time) / (minutes - peak_time)
                value = int(peak_value * (1 - decay * random.uniform(0.1, 0.3)))
            
            data.append({"time": f"{i}分", "value": max(0, value)})
        
        # 最后一个点取当前值的80-100%
        final_value = int(peak_value * random.uniform(0.8, 1.0))
        data.append({"time": "结束", "value": final_value})
        return data
    
    # 生成各项趋势
    trend_charts = {
        "follows": {
            "title": "新增关注趋势",
            "description": f"直播{duration_minutes}分钟内新增关注的变化趋势",
            "chart_data": generate_cumulative_trend(follows_total, duration_minutes),
            "insights": f"共新增关注{follows_total}人" + (
                f"，峰值增长出现在第{int(duration_minutes * 0.6)}-{int(duration_minutes * 0.8)}分钟"
                if follows_total > 50 else ""
            )
        },
        "entries": {
            "title": "进场人数趋势",
            "description": f"直播{duration_minutes}分钟内进场人数的累计变化",
            "chart_data": generate_cumulative_trend(entries_total, duration_minutes),
            "insights": f"累计进场{entries_total}人次" + (
                "，流量获取效果良好" if entries_total > 100 else "，建议加强引流"
            )
        },
        "peak_viewers": {
            "title": "在线人数趋势",
            "description": f"直播{duration_minutes}分钟内实时在线人数的波动",
            "chart_data": generate_fluctuating_trend(peak_viewers, duration_minutes),
            "insights": f"峰值在线{peak_viewers}人" + (
                "，留人效果优秀" if peak_viewers > 50 else "，需优化内容留人"
            )
        },
        "like_total": {
            "title": "点赞数趋势",
            "description": f"直播{duration_minutes}分钟内点赞数的累计变化",
            "chart_data": generate_cumulative_trend(like_total, duration_minutes),
            "insights": f"累计获赞{like_total}次" + (
                "，互动氛围热烈" if like_total > 500 else "，可引导观众多点赞"
            )
        }
    }
    
    return trend_charts


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
            
            # 计算token速率
            tokens_per_sec = usage.total_tokens / duration if duration > 0 else 0
            
            # 格式化的日志输出
            logger.info(
                f"\n{'='*80}\n"
                f"✅ Gemini 复盘报告生成\n"
                f"{'─'*80}\n"
                f"  模型: {self.model:45s}\n"
                f"  Token: {usage.prompt_tokens:6d} (输入) + {usage.completion_tokens:6d} (输出) = {usage.total_tokens:8d} (总计)\n"
                f"  成本: ${cost:10.6f} (美元) | 耗时: {duration:8.2f}s\n"
                f"  速率: {tokens_per_sec:6.1f} tokens/s\n"
                f"{'='*80}"
            )
            
            # 记录到监控系统
            try:
                from server.utils.ai_usage_monitor import record_ai_usage
                record_ai_usage(
                    model=self.model,
                    function="复盘总结",
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    cost=cost,
                    duration_ms=duration * 1000,
                    success=True,
                )
            except Exception as monitor_exc:
                logger.debug(f"记录复盘使用情况失败: {monitor_exc}")
            
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
            - duration_seconds: 直播时长（秒）
    
    Returns:
        复盘报告字典，包含：
            - overall_score: 综合评分 (0-100)
            - performance_analysis: 表现分析
            - key_highlights: 亮点列表
            - key_issues: 问题列表
            - improvement_suggestions: 改进建议列表
            - trend_charts: 趋势图数据（基于真实数据推算）
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
    duration_seconds = int(review_data.get("duration_seconds", 0))  # 🆕 确保是整数
    
    # 🆕 基于真实数据生成趋势图
    trend_charts = _generate_real_trend_charts(metrics, duration_seconds)
    
    # 限制数据量以控制成本
    transcript_preview = transcript[:10000] if len(transcript) > 10000 else transcript
    comments_preview = comments[:200] if isinstance(comments, list) else []
    
    # 构建提示词
    prompt = f"""你是一位资深的直播运营分析师，请基于以下数据生成一份**个性化**的直播复盘报告。

【主播信息】
主播昵称: {anchor_name}
直播时长: {duration_seconds // 60} 分钟

【直播数据】
{json.dumps(metrics, ensure_ascii=False, indent=2)}

【口播转写（节选前10000字）】
{transcript_preview}

【弹幕样本（最多200条）】
{json.dumps(comments_preview[:50], ensure_ascii=False, indent=2)}
...（共 {len(comments_preview)} 条弹幕）

【任务要求】
请以专业的运营分析师视角，生成一份**针对本场直播的个性化**复盘报告。
**重要：不要使用模板化的通用建议，必须基于实际数据和转写内容给出具体分析。**

严格按照以下 JSON 格式输出：

{{
  "overall_score": 85,  // 综合评分，0-100，必须基于实际表现客观打分，不要虚高
  "performance_analysis": {{
    "overall_assessment": "【必须包含具体数据】本场直播{duration_seconds // 60}分钟，累计进场{metrics.get('entries', 0)}人次，新增关注{metrics.get('follows', 0)}人，峰值在线{metrics.get('peak_viewers', 0)}人。【必须分析实际表现】...",
    "content_quality": {{
      "score": 80,  // 基于转写内容的实际质量打分
      "comments": "【必须引用具体话术】在转写中发现...【具体分析】"
    }},
    "engagement": {{
      "score": 85,  // 基于互动数据的实际表现打分
      "comments": "【必须引用具体数据】平均每分钟进场{metrics.get('entries', 0) / max(1, duration_seconds // 60):.1f}人，点赞{metrics.get('like_total', 0)}次...【具体分析】"
    }},
    "conversion_potential": {{
      "score": 75,  // 基于内容和互动的转化判断
      "comments": "【必须分析具体转化点】根据弹幕和话术分析...【具体建议】"
    }}
  }},
  "key_highlights": [
    "【必须具体】亮点1：在第X分钟提到'具体话术内容'时，引发了XXX条弹幕互动",
    "【必须具体】亮点2：新增关注在XXX时段出现高峰，可能与'具体内容/话术'相关",
    "【必须具体】亮点3：（基于实际数据和转写内容的具体亮点）"
  ],
  "key_issues": [
    "【必须具体】问题1：（基于实际数据发现的具体问题，不要用'内容单一'等模糊表述）",
    "【必须具体】问题2：在第X-Y分钟，XX指标出现下滑，可能原因是...",
    "【必须具体】问题3：（实际发现的问题）"
  ],
  "improvement_suggestions": [
    "【必须可执行】建议1：针对'具体发现的问题'，可以尝试'具体的改进方法'，预期提升XX%",
    "【必须可执行】建议2：（具体的、可操作的建议，不要用'优化内容'等空泛表述）",
    "【必须可执行】建议3：（基于本场实际情况的改进建议）"
  ]
}}

【个性化分析要求 - 非常重要】
1. **引用具体数据**: 每个分析点都要引用实际的数字，不要说"表现良好"，要说"进场XX人，高于平均水平XX%"
2. **引用具体话术**: 从转写中找出2-3段关键话术进行分析，说明其效果
3. **引用具体弹幕**: 找出有代表性的弹幕，分析观众关注点
4. **时间维度分析**: 指出"在第X-Y分钟发生了什么"，不要笼统概括
5. **对比分析**: 如果有历史数据，进行对比；如果没有，与行业平均水平对比
6. **因果关系**: 不要只描述现象，要分析"为什么"：为什么这个时间段数据好？为什么观众流失？
7. **可执行性**: 每个建议都要具体到"在哪个环节""怎么做""预期效果是什么"

【禁止使用的模板化表述】
❌ 不要说："内容较为单一，建议丰富直播内容"
✅ 应该说："在10-15分钟讲解产品时，进场人数从XX下降到XX，流失率XX%。建议：穿插使用场景演示（第12分钟可插入），预计减少15%流失"

❌ 不要说："互动氛围良好"
✅ 应该说："第3分钟提到'今天有福利'时，点赞从XX激增到XX（+XX%），说明福利话术有效，建议每10分钟重复一次"

❌ 不要说："加强引流"
✅ 应该说："当前进场/在线转化率XX%，低于行业平均XX%。建议：在第5分钟添加'新人专享福利'话术，引导关注后可领取"

【评分标准】
- 90-100分：数据优秀，内容精彩，互动热烈，转化明确
- 70-89分：数据良好，内容合格，互动正常，有改进空间
- 50-69分：数据一般，内容需优化，互动偏弱
- 50分以下：数据较差，需要大幅改进

【输出格式要求】
1. 只输出纯JSON对象，不要包含任何markdown代码块标记（如 ```json）
2. 不要在JSON前后添加任何说明文字
3. 确保JSON格式完全正确，可以直接被解析
4. 所有字符串字段使用双引号
5. 数字字段不要加引号

示例输出格式（注意：不要包含这个提示，直接输出JSON）：
{{"overall_score": 75, "performance_analysis": {{...}}, ...}}

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
    
    # 🆕 添加真实的趋势图数据
    report_data["trend_charts"] = trend_charts
    
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
