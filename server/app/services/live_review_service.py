# -*- coding: utf-8 -*-
"""
直播复盘服务

负责在直播结束后生成完整的复盘分析报告，包括：
- 数据聚合（弹幕、转写、事件）
- 调用 Gemini AI 进行深度分析
- 保存结构化报告到数据库
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from ...ai.ai_gateway import get_gateway
from ..models.live_review import LiveReviewReport
from ..models.live import LiveSession

logger = logging.getLogger(__name__)


class LiveReviewService:
    """直播复盘服务"""
    
    def __init__(self):
        self.gateway = get_gateway()
        self.persist_root = os.getenv("PERSIST_ROOT", "records/live_logs")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025")
    
    def _is_gemini_available(self) -> bool:
        """检查 Gemini 服务是否可用"""
        try:
            providers = self.gateway.list_providers()
            return "gemini" in providers and providers["gemini"].get("enabled", False)
        except Exception:
            return False
    
    def generate_review(self, session_id: int, db: Session) -> Optional[LiveReviewReport]:
        """生成直播复盘报告
        
        Args:
            session_id: 直播会话 ID
            db: 数据库会话
        
        Returns:
            LiveReviewReport 对象或 None
        """
        if not self._is_gemini_available():
            logger.error("❌ Gemini 服务不可用，无法生成复盘报告")
            logger.info("请在 .env 文件中配置 AIHUBMIX_API_KEY")
            return None
        
        # 查询直播会话
        session = db.query(LiveSession).filter(LiveSession.id == session_id).first()
        if not session:
            logger.error(f"❌ 直播会话不存在: session_id={session_id}")
            return None
        
        if session.status != "ended":
            logger.warning(f"⚠️ 直播尚未结束，无法生成复盘: session_id={session_id}, status={session.status}")
            return None
        
        # 检查是否已存在报告
        existing_report = db.query(LiveReviewReport).filter(
            LiveReviewReport.session_id == session_id
        ).first()
        if existing_report:
            logger.info(f"ℹ️ 复盘报告已存在，将重新生成: session_id={session_id}")
            db.delete(existing_report)
            db.flush()
        
        logger.info(f"🚀 开始生成复盘报告: session_id={session_id}, room_id={session.room_id}")
        
        # 1. 加载直播数据
        context_data = self._load_session_data(session)
        
        # 2. 构建 Prompt
        prompt = self._build_review_prompt(session, context_data)
        
        # 3. 通过 AIGateway 调用 Gemini
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
        
        try:
            ai_response = self.gateway.chat_completion(
                messages=messages,
                provider="gemini",
                model=self.gemini_model,
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            
            if not ai_response.success:
                logger.error(f"❌ Gemini 调用失败: {ai_response.error}")
                report = LiveReviewReport(
                    session_id=session_id,
                    status="failed",
                    error_message=f"Gemini API 调用失败: {ai_response.error}",
                    ai_model=self.gemini_model
                )
                db.add(report)
                db.commit()
                return None
            
            response_text = ai_response.content
            response_usage = ai_response.usage
            response_cost = ai_response.cost
            response_duration = ai_response.duration_ms / 1000.0  # 转换为秒
            
        except Exception as e:
            logger.error(f"❌ Gemini 调用异常: {e}", exc_info=True)
            report = LiveReviewReport(
                session_id=session_id,
                status="failed",
                error_message=f"Gemini API 调用异常: {str(e)}",
                ai_model=self.gemini_model
            )
            db.add(report)
            db.commit()
            return None
        
        # 4. 解析响应
        result = self._parse_json_response(response_text)
        if not result:
            logger.error("❌ 无法解析 Gemini 响应为 JSON")
            # 保存原始文本作为降级方案
            report = LiveReviewReport(
                session_id=session_id,
                full_report_text=response_text,
                status="completed",
                ai_model=self.gemini_model,
                generation_cost=response_cost,
                generation_tokens=response_usage.get("total_tokens", 0),
                generation_duration=response_duration
            )
            db.add(report)
            db.commit()
            logger.warning("⚠️ 已保存原始文本报告（未结构化）")
            return report
        
        # 5. 保存报告到数据库
        report = LiveReviewReport(
            session_id=session_id,
            overall_score=result.get("overall_score", 0),
            performance_analysis=result.get("performance_analysis", {}),
            key_highlights=result.get("key_highlights", []),
            key_issues=result.get("key_issues", []),
            improvement_suggestions=result.get("improvement_suggestions", []),
            full_report_text=self._format_markdown_report(result),
            status="completed",
            ai_model=self.gemini_model,
            generation_cost=response_cost,
            generation_tokens=response_usage.get("total_tokens", 0),
            generation_duration=response_duration
        )
        
        db.add(report)
        db.flush()
        
        # 6. 更新 session 的 AI 使用记录
        session.ai_usage_count += 1
        session.ai_usage_tokens += response_usage.get("total_tokens", 0)
        session.ai_usage_cost += float(response_cost)
        
        db.commit()
        
        logger.info(
            f"✅ 复盘报告生成成功: report_id={report.id}, "
            f"score={report.overall_score}, "
            f"cost=${report.generation_cost:.6f}, "
            f"duration={report.generation_duration:.2f}s"
        )
        
        return report
    
    def _load_session_data(self, session: LiveSession) -> Dict[str, Any]:
        """加载直播数据文件
        
        从 records/live_logs/ 目录加载弹幕、转写、事件数据
        
        Args:
            session: LiveSession 对象
        
        Returns:
            {
                "comments": List[Dict],  # 弹幕列表
                "transcript": str,       # 转写文本
                "events": List[Dict]     # 事件列表
            }
        """
        data = {
            "comments": [],
            "transcript": "",
            "events": [],
            "comments_summary": {},
            "transcript_summary": {}
        }
        
        # 读取弹幕文件
        if session.comment_file and Path(session.comment_file).exists():
            try:
                with open(session.comment_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    data["comments"] = [json.loads(line) for line in lines if line.strip()]
                    logger.info(f"✅ 加载弹幕数据: {len(data['comments'])} 条")
            except Exception as e:
                logger.warning(f"⚠️ 读取弹幕文件失败: {e}")
        else:
            logger.warning(f"⚠️ 弹幕文件不存在: {session.comment_file}")
        
        # 读取转写文件
        if session.transcript_file and Path(session.transcript_file).exists():
            try:
                with open(session.transcript_file, 'r', encoding='utf-8') as f:
                    data["transcript"] = f.read()
                    logger.info(f"✅ 加载转写数据: {len(data['transcript'])} 字符")
            except Exception as e:
                logger.warning(f"⚠️ 读取转写文件失败: {e}")
        else:
            logger.warning(f"⚠️ 转写文件不存在: {session.transcript_file}")
        
        # 如果没有具体文件路径，尝试从默认路径加载
        if not data["comments"] and not data["transcript"]:
            data = self._load_from_default_path(session)
        
        # 生成摘要（避免 Prompt 过长）
        data["comments_summary"] = self._summarize_comments(data["comments"])
        data["transcript_summary"] = self._summarize_transcript(data["transcript"])
        
        return data
    
    def _load_from_default_path(self, session: LiveSession) -> Dict[str, Any]:
        """从默认路径加载数据"""
        data = {"comments": [], "transcript": "", "events": []}
        
        # records/live_logs/<room_id>/<date>/
        if session.start_time:
            date_str = session.start_time.strftime("%Y-%m-%d")
            base_path = Path(self.persist_root) / session.room_id / date_str
            
            if base_path.exists():
                # 查找弹幕文件
                comment_files = list(base_path.glob("comments_*.jsonl"))
                if comment_files:
                    try:
                        with open(comment_files[0], 'r', encoding='utf-8') as f:
                            data["comments"] = [json.loads(line) for line in f if line.strip()]
                            logger.info(f"✅ 从默认路径加载弹幕: {len(data['comments'])} 条")
                    except Exception as e:
                        logger.warning(f"⚠️ 从默认路径读取弹幕失败: {e}")
                
                # 查找转写文件
                transcript_files = list(base_path.glob("transcript_*.txt"))
                if transcript_files:
                    try:
                        with open(transcript_files[0], 'r', encoding='utf-8') as f:
                            data["transcript"] = f.read()
                            logger.info(f"✅ 从默认路径加载转写: {len(data['transcript'])} 字符")
                    except Exception as e:
                        logger.warning(f"⚠️ 从默认路径读取转写失败: {e}")
        
        return data
    
    def _summarize_comments(self, comments: List[Dict]) -> Dict[str, Any]:
        """弹幕摘要
        
        提取前100条、热门评论、高价值用户等
        """
        if not comments:
            return {
                "total": 0,
                "sample": [],
                "hot_users": []
            }
        
        # 取前100条作为样本
        sample = comments[:100]
        
        # 统计活跃用户
        user_counts = {}
        for comment in comments:
            user = comment.get("user") or comment.get("nickname") or "匿名"
            user_counts[user] = user_counts.get(user, 0) + 1
        
        # 取前10名活跃用户
        hot_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total": len(comments),
            "sample": sample,
            "hot_users": [{"user": u, "count": c} for u, c in hot_users]
        }
    
    def _summarize_transcript(self, transcript: str) -> Dict[str, Any]:
        """转写摘要
        
        提取关键片段（首尾各500字）
        """
        if not transcript:
            return {
                "total_chars": 0,
                "opening": "",
                "closing": ""
            }
        
        return {
            "total_chars": len(transcript),
            "opening": transcript[:500] if len(transcript) > 500 else transcript,
            "closing": transcript[-500:] if len(transcript) > 500 else ""
        }
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """解析 JSON 响应（从 GeminiAdapter 移植）
        
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
    
    def _build_review_prompt(self, session: LiveSession, data: Dict[str, Any]) -> str:
        """构建 Gemini 分析 Prompt
        
        包含直播基本数据、弹幕样本、转写片段等
        """
        # 格式化弹幕样本
        comments_text = "\n".join([
            f"{i+1}. {c.get('user', '匿名')}: {c.get('text', c.get('content', ''))}"
            for i, c in enumerate(data["comments_summary"].get("sample", [])[:50])
        ])
        
        # 格式化活跃用户
        hot_users_text = "\n".join([
            f"- {u['user']}: {u['count']} 条评论"
            for u in data["comments_summary"].get("hot_users", [])[:10]
        ])
        
        # 构建 Prompt
        prompt = f"""你是一位资深的直播运营分析师，请对以下直播数据进行**全面复盘分析**，并给出未来改进建议。

# 直播基本信息
- **直播平台**: {session.platform}
- **直播间ID**: {session.room_id}
- **直播标题**: {session.title or "（无标题）"}
- **开始时间**: {session.start_time.strftime("%Y-%m-%d %H:%M:%S") if session.start_time else "未知"}
- **结束时间**: {session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else "未知"}
- **直播时长**: {session.duration // 60} 分钟 {session.duration % 60} 秒
- **总观看人数**: {session.total_viewers}
- **峰值在线**: {session.peak_viewers}
- **平均在线**: {session.avg_viewers}
- **评论数**: {session.comment_count}
- **点赞数**: {session.like_count}
- **礼物数**: {session.gift_count}（价值 ¥{session.gift_value}）

# 主播口播内容（语音转写片段）
## 开场片段：
```
{data["transcript_summary"].get("opening", "（无转写数据）")}
```

## 结尾片段：
```
{data["transcript_summary"].get("closing", "")}
```

**转写总字数**: {data["transcript_summary"].get("total_chars", 0)}

# 观众弹幕样本（前 50 条）
{comments_text or "（无弹幕数据）"}

**弹幕总数**: {data["comments_summary"].get("total", 0)}

# 活跃观众 TOP 10
{hot_users_text or "（无数据）"}

---

# 分析要求

请严格按照以下 JSON 结构输出分析结果（**只返回JSON，不要包含任何其他文字说明**）：

{{
  "overall_score": 75,  // 综合评分 0-100，基于数据客观评估
  "performance_analysis": {{
    "engagement": {{
      "score": 80,  // 互动表现评分 0-100
      "highlights": ["互动频繁", "回复及时"],  // 亮点（2-5个）
      "issues": ["中途冷场10分钟"]  // 问题（0-3个）
    }},
    "content_quality": {{
      "score": 70,  // 内容质量评分 0-100
      "highlights": ["产品讲解清晰"],
      "issues": ["话题重复", "缺少新鲜感"]
    }},
    "conversion": {{
      "score": 65,  // 转化潜力评分 0-100
      "signals": ["询价多但成交少", "缺少限时优惠"]  // 转化信号（2-5个）
    }}
  }},
  "key_highlights": [
    "开场3分钟吸引观众，在线人数快速增长",
    "20:15 在线人数达到峰值 {session.peak_viewers} 人",
    "20:32 收到单笔最大礼物 ¥{session.gift_value / session.gift_count if session.gift_count > 0 else 0:.2f}"
  ],  // 3-5个亮点时刻
  "key_issues": [
    "中途网络波动导致卡顿",
    "话题切换过于突然，观众跟不上节奏",
    "结尾草率，未做好告别和预告"
  ],  // 2-5个主要问题
  "improvement_suggestions": [
    {{
      "priority": "high",  // high/medium/low
      "category": "互动技巧",
      "action": "增加观众提问环节，每15分钟主动邀请观众留言",
      "expected_impact": "提升留存率和参与度"
    }},
    {{
      "priority": "medium",
      "category": "内容规划",
      "action": "提前准备3-5个备用话题和产品卖点",
      "expected_impact": "避免冷场，保持节奏"
    }},
    {{
      "priority": "medium",
      "category": "技术准备",
      "action": "直播前测试网络，准备 4G 热点备用",
      "expected_impact": "减少技术故障"
    }},
    {{
      "priority": "low",
      "category": "营销策略",
      "action": "设置限时优惠和互动游戏，提升转化",
      "expected_impact": "增加成交机会"
    }}
  ]  // 4-6条建议，按优先级排序
}}

**评分说明**：
- 90-100分：优秀，超出预期
- 80-89分：良好，符合预期
- 70-79分：合格，有提升空间
- 60-69分：待改进，存在明显问题
- <60分：较差，需要重点改进

**注意事项**：
1. 评分要客观，基于实际数据（观看人数、互动量、时长等）
2. 亮点和问题要具体，尽量关联时间点或数据
3. 建议要可执行，避免空话套话
4. 优先级 high（立即改进）、medium（短期优化）、low（长期提升）
5. **只返回 JSON，不要有其他解释性文字**
"""
        
        return prompt
    
    def _format_markdown_report(self, result: Dict[str, Any]) -> str:
        """将 JSON 结果格式化为 Markdown 报告
        
        Args:
            result: Gemini 返回的结构化数据
        
        Returns:
            Markdown 格式的报告文本
        """
        md = f"""# 📊 直播复盘报告

## 综合评分：{result.get('overall_score', 0)} / 100

"""
        
        # 评分等级
        score = result.get('overall_score', 0)
        if score >= 90:
            md += "**等级**：⭐⭐⭐⭐⭐ 优秀\n\n"
        elif score >= 80:
            md += "**等级**：⭐⭐⭐⭐ 良好\n\n"
        elif score >= 70:
            md += "**等级**：⭐⭐⭐ 合格\n\n"
        elif score >= 60:
            md += "**等级**：⭐⭐ 待改进\n\n"
        else:
            md += "**等级**：⭐ 需重点改进\n\n"
        
        md += "---\n\n"
        
        # 亮点时刻
        md += "## ✨ 亮点时刻\n\n"
        for highlight in result.get("key_highlights", []):
            md += f"- {highlight}\n"
        md += "\n"
        
        # 主要问题
        md += "## ⚠️ 主要问题\n\n"
        issues = result.get("key_issues", [])
        if issues:
            for issue in issues:
                md += f"- {issue}\n"
        else:
            md += "- 暂无明显问题\n"
        md += "\n"
        
        # 表现分析
        md += "## 📈 表现分析\n\n"
        perf = result.get("performance_analysis", {})
        
        for category, data in perf.items():
            category_name = {
                "engagement": "互动表现",
                "content_quality": "内容质量",
                "conversion": "转化潜力"
            }.get(category, category)
            
            score = data.get('score', 0)
            md += f"### {category_name} ({score}/100)\n\n"
            
            if data.get("highlights"):
                md += "**亮点**：\n"
                for h in data["highlights"]:
                    md += f"- ✅ {h}\n"
            
            if data.get("issues"):
                md += "\n**问题**：\n"
                for i in data["issues"]:
                    md += f"- ❌ {i}\n"
            
            if data.get("signals"):
                md += "\n**信号**：\n"
                for s in data["signals"]:
                    md += f"- 📊 {s}\n"
            
            md += "\n"
        
        # 改进建议
        md += "## 💡 改进建议\n\n"
        suggestions = result.get("improvement_suggestions", [])
        
        # 按优先级分组
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        medium_priority = [s for s in suggestions if s.get("priority") == "medium"]
        low_priority = [s for s in suggestions if s.get("priority") == "low"]
        
        if high_priority:
            md += "### 🔴 高优先级（立即改进）\n\n"
            for sug in high_priority:
                md += f"**{sug.get('category', '其他')}**\n"
                md += f"- **行动**：{sug.get('action', '')}\n"
                md += f"- **预期效果**：{sug.get('expected_impact', '')}\n\n"
        
        if medium_priority:
            md += "### 🟡 中优先级（短期优化）\n\n"
            for sug in medium_priority:
                md += f"**{sug.get('category', '其他')}**\n"
                md += f"- **行动**：{sug.get('action', '')}\n"
                md += f"- **预期效果**：{sug.get('expected_impact', '')}\n\n"
        
        if low_priority:
            md += "### 🟢 低优先级（长期提升）\n\n"
            for sug in low_priority:
                md += f"**{sug.get('category', '其他')}**\n"
                md += f"- **行动**：{sug.get('action', '')}\n"
                md += f"- **预期效果**：{sug.get('expected_impact', '')}\n\n"
        
        # 结尾
        md += "---\n\n"
        md += f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        md += f"*由 Gemini 2.5 Flash 提供技术支持*\n"
        
        return md


# 全局单例
_live_review_service: Optional[LiveReviewService] = None


def get_live_review_service() -> LiveReviewService:
    """获取直播复盘服务单例"""
    global _live_review_service
    if _live_review_service is None:
        _live_review_service = LiveReviewService()
    return _live_review_service
