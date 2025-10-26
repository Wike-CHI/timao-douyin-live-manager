"""
AI API 使用量监控与计费系统
监控所有 AI 调用的 Token 使用量和费用
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """单次 API 调用记录"""
    timestamp: float
    user_id: Optional[str]
    anchor_id: Optional[str]
    session_id: Optional[str]
    model: str
    function: str  # 功能：实时分析、话术生成、问答等
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    duration_ms: float
    success: bool
    error_msg: Optional[str] = None


@dataclass
class UsageSummary:
    """使用量汇总"""
    period: str  # hourly, daily, monthly
    start_time: float
    end_time: float
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    by_model: Dict[str, Dict[str, Any]]
    by_function: Dict[str, Dict[str, Any]]
    by_user: Dict[str, Dict[str, Any]]
    by_anchor: Dict[str, Dict[str, Any]]


class ModelPricing:
    """AI 模型定价配置"""
    
    # Qwen 系列定价（元/1K tokens）
    QWEN_PRICING = {
        "qwen-max": {
            "input": 0.02,
            "output": 0.06,
            "display_name": "通义千问-Max"
        },
        "qwen3-max": {
            "input": 0.02,
            "output": 0.06,
            "display_name": "通义千问3-Max"
        },
        "qwen-plus": {
            "input": 0.004,
            "output": 0.012,
            "display_name": "通义千问-Plus"
        },
        "qwen-turbo": {
            "input": 0.002,
            "output": 0.006,
            "display_name": "通义千问-Turbo"
        },
    }
    
    # OpenAI 系列定价（元/1K tokens）
    OPENAI_PRICING = {
        "gpt-4": {
            "input": 0.21,
            "output": 0.42,
            "display_name": "GPT-4"
        },
        "gpt-4-turbo": {
            "input": 0.07,
            "output": 0.21,
            "display_name": "GPT-4 Turbo"
        },
        "gpt-4o": {
            "input": 0.035,
            "output": 0.105,
            "display_name": "GPT-4o"
        },
        "gpt-4o-mini": {
            "input": 0.001,
            "output": 0.004,
            "display_name": "GPT-4o Mini"
        },
        "gpt-3.5-turbo": {
            "input": 0.0035,
            "output": 0.007,
            "display_name": "GPT-3.5 Turbo"
        },
    }
    
    # DeepSeek 系列定价（元/1K tokens）
    DEEPSEEK_PRICING = {
        "deepseek-chat": {
            "input": 0.001,
            "output": 0.002,
            "display_name": "DeepSeek-Chat"
        },
        "deepseek-coder": {
            "input": 0.001,
            "output": 0.002,
            "display_name": "DeepSeek-Coder"
        },
    }
    
    # 字节豆包系列定价（元/1K tokens）
    DOUBAO_PRICING = {
        "doubao-pro-32k": {
            "input": 0.008,
            "output": 0.008,
            "display_name": "豆包-Pro-32K"
        },
        "doubao-lite-32k": {
            "input": 0.003,
            "output": 0.003,
            "display_name": "豆包-Lite-32K"
        },
    }
    
    # ChatGLM 系列定价（元/1K tokens）
    GLM_PRICING = {
        "glm-4": {
            "input": 0.10,
            "output": 0.10,
            "display_name": "ChatGLM-4"
        },
        "glm-4-flash": {
            "input": 0.0,
            "output": 0.0,
            "display_name": "ChatGLM-4-Flash (免费)"
        },
        "glm-3-turbo": {
            "input": 0.005,
            "output": 0.005,
            "display_name": "ChatGLM-3-Turbo"
        },
    }
    
    # 合并所有定价
    ALL_PRICING = {
        **QWEN_PRICING,
        **OPENAI_PRICING,
        **DEEPSEEK_PRICING,
        **DOUBAO_PRICING,
        **GLM_PRICING,
    }
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算单次调用费用"""
        pricing = cls.ALL_PRICING.get(model)
        if not pricing:
            # 未知模型，使用 Qwen-Plus 价格作为默认
            logger.warning(f"未知模型 {model}，使用默认定价")
            pricing = cls.QWEN_PRICING["qwen-plus"]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)
    
    @classmethod
    def get_model_display_name(cls, model: str) -> str:
        """获取模型显示名称"""
        pricing = cls.ALL_PRICING.get(model)
        return pricing["display_name"] if pricing else model
    
    @classmethod
    def get_pricing(cls, model: str) -> Optional[Dict[str, Any]]:
        """获取模型定价信息"""
        return cls.ALL_PRICING.get(model)


class AIUsageMonitor:
    """AI 使用量监控器"""
    
    def __init__(self, data_dir: Path = None):
        """
        初始化监控器
        
        Args:
            data_dir: 数据存储目录，默认为 records/ai_usage
        """
        self.data_dir = data_dir or Path("records") / "ai_usage"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存（最近 1000 条记录）
        self._records: List[UsageRecord] = []
        self._max_cache_size = 1000
        
        # 当前会话统计
        self._session_stats = defaultdict(lambda: {
            "calls": 0,
            "tokens": 0,
            "cost": 0.0
        })
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 加载今日记录
        self._load_today_records()
        
        logger.info(f"AI 使用量监控器已启动，数据目录: {self.data_dir}")
    
    def record_usage(
        self,
        model: str,
        function: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool = True,
        user_id: Optional[str] = None,
        anchor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        error_msg: Optional[str] = None
    ) -> UsageRecord:
        """
        记录一次 API 调用
        
        Args:
            model: 模型名称
            function: 功能名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
            duration_ms: 调用耗时（毫秒）
            success: 是否成功
            user_id: 用户 ID
            anchor_id: 主播 ID
            session_id: 会话 ID
            error_msg: 错误信息
            
        Returns:
            UsageRecord: 使用记录
        """
        total_tokens = input_tokens + output_tokens
        cost = ModelPricing.calculate_cost(model, input_tokens, output_tokens)
        
        record = UsageRecord(
            timestamp=time.time(),
            user_id=user_id,
            anchor_id=anchor_id,
            session_id=session_id,
            model=model,
            function=function,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            duration_ms=duration_ms,
            success=success,
            error_msg=error_msg
        )
        
        with self._lock:
            # 添加到缓存
            self._records.append(record)
            if len(self._records) > self._max_cache_size:
                self._records.pop(0)
            
            # 更新会话统计
            if session_id:
                stats = self._session_stats[session_id]
                stats["calls"] += 1
                stats["tokens"] += total_tokens
                stats["cost"] += cost
            
            # 持久化到文件
            self._save_record(record)
        
        logger.info(
            f"AI 调用记录: {function}({model}) | "
            f"Tokens: {input_tokens}+{output_tokens}={total_tokens} | "
            f"Cost: ¥{cost:.4f} | "
            f"Duration: {duration_ms:.0f}ms"
        )
        
        return record
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计"""
        with self._lock:
            return dict(self._session_stats.get(session_id, {}))
    
    def get_hourly_summary(self, hours_ago: int = 0) -> UsageSummary:
        """获取小时汇总"""
        now = datetime.now()
        target_hour = now - timedelta(hours=hours_ago)
        start = target_hour.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        return self._generate_summary(
            period="hourly",
            start_time=start.timestamp(),
            end_time=end.timestamp()
        )
    
    def get_daily_summary(self, days_ago: int = 0) -> UsageSummary:
        """获取每日汇总"""
        now = datetime.now()
        target_day = now - timedelta(days=days_ago)
        start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        return self._generate_summary(
            period="daily",
            start_time=start.timestamp(),
            end_time=end.timestamp()
        )
    
    def get_monthly_summary(self, year: int = None, month: int = None) -> UsageSummary:
        """获取月度汇总"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        return self._generate_summary(
            period="monthly",
            start_time=start.timestamp(),
            end_time=end.timestamp()
        )
    
    def get_top_users(self, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """获取 Token 消耗最多的用户"""
        records = self._get_recent_records(days=days)
        user_stats = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "calls": 0})
        
        for record in records:
            if record.user_id:
                stats = user_stats[record.user_id]
                stats["tokens"] += record.total_tokens
                stats["cost"] += record.cost
                stats["calls"] += 1
        
        sorted_users = sorted(
            user_stats.items(),
            key=lambda x: x[1]["tokens"],
            reverse=True
        )
        
        return [
            {"user_id": uid, **stats}
            for uid, stats in sorted_users[:limit]
        ]
    
    def get_cost_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取成本趋势（按天）"""
        records = self._get_recent_records(days=days)
        daily_cost = defaultdict(float)
        
        for record in records:
            date_str = datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d")
            daily_cost[date_str] += record.cost
        
        sorted_dates = sorted(daily_cost.keys())
        return [
            {"date": date, "cost": round(daily_cost[date], 2)}
            for date in sorted_dates
        ]
    
    def export_report(self, output_path: Path = None, days: int = 7) -> Path:
        """导出使用报告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"usage_report_{timestamp}.json"
        
        summary = self.get_daily_summary(days_ago=0)
        top_users = self.get_top_users(days=days)
        cost_trend = self.get_cost_trend(days=days)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "today_summary": asdict(summary),
            "top_users": top_users,
            "cost_trend": cost_trend,
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"使用报告已导出: {output_path}")
        return output_path
    
    def _generate_summary(
        self,
        period: str,
        start_time: float,
        end_time: float
    ) -> UsageSummary:
        """生成使用汇总"""
        records = [
            r for r in self._get_records_in_range(start_time, end_time)
        ]
        
        total_calls = len(records)
        successful_calls = sum(1 for r in records if r.success)
        failed_calls = total_calls - successful_calls
        
        total_input_tokens = sum(r.input_tokens for r in records)
        total_output_tokens = sum(r.output_tokens for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        total_cost = sum(r.cost for r in records)
        
        # 按模型统计
        by_model = defaultdict(lambda: {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0
        })
        for r in records:
            stats = by_model[r.model]
            stats["calls"] += 1
            stats["input_tokens"] += r.input_tokens
            stats["output_tokens"] += r.output_tokens
            stats["total_tokens"] += r.total_tokens
            stats["cost"] += r.cost
        
        # 按功能统计
        by_function = defaultdict(lambda: {
            "calls": 0,
            "total_tokens": 0,
            "cost": 0.0
        })
        for r in records:
            stats = by_function[r.function]
            stats["calls"] += 1
            stats["total_tokens"] += r.total_tokens
            stats["cost"] += r.cost
        
        # 按用户统计
        by_user = defaultdict(lambda: {
            "calls": 0,
            "total_tokens": 0,
            "cost": 0.0
        })
        for r in records:
            if r.user_id:
                stats = by_user[r.user_id]
                stats["calls"] += 1
                stats["total_tokens"] += r.total_tokens
                stats["cost"] += r.cost
        
        # 按主播统计
        by_anchor = defaultdict(lambda: {
            "calls": 0,
            "total_tokens": 0,
            "cost": 0.0
        })
        for r in records:
            if r.anchor_id:
                stats = by_anchor[r.anchor_id]
                stats["calls"] += 1
                stats["total_tokens"] += r.total_tokens
                stats["cost"] += r.cost
        
        return UsageSummary(
            period=period,
            start_time=start_time,
            end_time=end_time,
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 2),
            by_model=dict(by_model),
            by_function=dict(by_function),
            by_user=dict(by_user),
            by_anchor=dict(by_anchor)
        )
    
    def _save_record(self, record: UsageRecord):
        """保存记录到文件"""
        date_str = datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d")
        file_path = self.data_dir / f"usage_{date_str}.jsonl"
        
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error(f"保存使用记录失败: {exc}")
    
    def _load_today_records(self):
        """加载今日记录到缓存"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.data_dir / f"usage_{date_str}.jsonl"
        
        if not file_path.exists():
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        record = UsageRecord(**data)
                        self._records.append(record)
            
            logger.info(f"加载今日记录: {len(self._records)} 条")
        except Exception as exc:
            logger.error(f"加载今日记录失败: {exc}")
    
    def _get_records_in_range(
        self,
        start_time: float,
        end_time: float
    ) -> List[UsageRecord]:
        """获取时间范围内的记录"""
        # 从内存缓存获取
        records = [
            r for r in self._records
            if start_time <= r.timestamp < end_time
        ]
        
        # 如果缓存不够，从文件加载
        if not records or records[0].timestamp > start_time:
            records = self._load_records_from_files(start_time, end_time)
        
        return records
    
    def _load_records_from_files(
        self,
        start_time: float,
        end_time: float
    ) -> List[UsageRecord]:
        """从文件加载记录"""
        start_date = datetime.fromtimestamp(start_time)
        end_date = datetime.fromtimestamp(end_time)
        
        records = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            file_path = self.data_dir / f"usage_{date_str}.jsonl"
            
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                data = json.loads(line)
                                record = UsageRecord(**data)
                                if start_time <= record.timestamp < end_time:
                                    records.append(record)
                except Exception as exc:
                    logger.error(f"加载文件 {file_path} 失败: {exc}")
            
            current_date += timedelta(days=1)
        
        return records
    
    def _get_recent_records(self, days: int) -> List[UsageRecord]:
        """获取最近 N 天的记录"""
        end_time = time.time()
        start_time = end_time - (days * 24 * 3600)
        return self._get_records_in_range(start_time, end_time)


# 全局单例
_monitor_instance: Optional[AIUsageMonitor] = None


def get_usage_monitor() -> AIUsageMonitor:
    """获取全局监控器实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AIUsageMonitor()
    return _monitor_instance


def record_ai_usage(
    model: str,
    function: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: float,
    **kwargs
) -> UsageRecord:
    """便捷方法：记录 AI 使用"""
    monitor = get_usage_monitor()
    return monitor.record_usage(
        model=model,
        function=function,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        **kwargs
    )
