# -*- coding: utf-8 -*-
"""
性能监控服务
监控Redis、MySQL连接池、内存使用等关键指标
"""

import asyncio
import logging
import os
import psutil
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # MySQL连接池
    mysql_active_connections: int = 0
    mysql_pool_size: int = 0
    mysql_max_overflow: int = 0
    mysql_pool_usage_pct: float = 0.0
    
    # Redis
    redis_connected: bool = False
    redis_memory_used_mb: float = 0.0
    redis_memory_peak_mb: float = 0.0
    redis_keys_count: int = 0
    redis_hit_rate: float = 0.0
    
    # 系统内存
    process_memory_mb: float = 0.0
    process_memory_pct: float = 0.0
    system_memory_available_mb: float = 0.0
    system_memory_pct: float = 0.0
    
    # 时间戳
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    
    # 告警标志
    alerts: list = field(default_factory=list)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._enabled: bool = bool(int(os.getenv("MONITOR_ENABLED", "1")))
        self._interval: float = float(os.getenv("MONITOR_INTERVAL", "30.0"))  # 30秒
        self._task: Optional[asyncio.Task] = None
        self._current_metrics: Optional[PerformanceMetrics] = None
        self._process = psutil.Process()
        
        # 告警阈值
        self._mysql_conn_warning: int = int(os.getenv("MYSQL_CONN_WARNING", "45"))
        self._redis_memory_warning_mb: float = float(os.getenv("REDIS_MEMORY_WARNING_MB", "1800"))
        self._process_memory_warning_mb: float = float(os.getenv("PROCESS_MEMORY_WARNING_MB", "4000"))
    
    async def start(self) -> Dict[str, Any]:
        """启动监控"""
        if not self._enabled:
            return {"success": False, "message": "监控未启用"}
        
        if self._task and not self._task.done():
            return {"success": True, "message": "监控已在运行"}
        
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ 性能监控已启动")
        return {"success": True}
    
    async def stop(self) -> Dict[str, Any]:
        """停止监控"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("✅ 性能监控已停止")
        return {"success": True}
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前指标"""
        return self._current_metrics
    
    async def _monitor_loop(self):
        """监控循环"""
        try:
            while True:
                await asyncio.sleep(self._interval)
                await self._collect_metrics()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"监控循环异常: {e}", exc_info=True)
    
    async def _collect_metrics(self):
        """收集性能指标"""
        try:
            metrics = PerformanceMetrics()
            
            # 1. MySQL连接池指标
            try:
                # 本地服务不使用数据库
        # from ..database import get_db_engine
                engine = get_db_engine()
                if engine:
                    pool = engine.pool
                    metrics.mysql_active_connections = pool.checkedout()
                    metrics.mysql_pool_size = pool.size()
                    metrics.mysql_max_overflow = pool.overflow()
                    total_capacity = pool.size() + pool.overflow()
                    if total_capacity > 0:
                        metrics.mysql_pool_usage_pct = (metrics.mysql_active_connections / total_capacity) * 100
                    
                    # 告警检查
                    if metrics.mysql_active_connections >= self._mysql_conn_warning:
                        metrics.alerts.append({
                            "type": "mysql_connection",
                            "level": "warning",
                            "message": f"MySQL连接数过高: {metrics.mysql_active_connections}/{total_capacity}"
                        })
            except Exception as e:
                logger.warning(f"收集MySQL指标失败: {e}")
            
            # 2. Redis指标
            # 本地服务不使用Redis
            # try:
            #     from server.utils.redis_manager import get_redis
            #     redis_mgr = get_redis()
                if redis_mgr and redis_mgr.ping():
                    metrics.redis_connected = True
                    
                    # Redis内存使用（通过INFO命令获取，如果支持）
                    try:
                        info = redis_mgr._client.info("memory") if hasattr(redis_mgr, '_client') and redis_mgr._client else {}
                        if info:
                            metrics.redis_memory_used_mb = info.get("used_memory", 0) / (1024 * 1024)
                            metrics.redis_memory_peak_mb = info.get("used_memory_peak", 0) / (1024 * 1024)
                        
                        # 键数量（估算）
                        stats = redis_mgr._client.info("keyspace") if hasattr(redis_mgr, '_client') and redis_mgr._client else {}
                        for db_key, db_info in stats.items():
                            if isinstance(db_info, dict):
                                metrics.redis_keys_count += db_info.get("keys", 0)
                        
                        # 缓存命中率（通过stats计算）
                        stats_info = redis_mgr._client.info("stats") if hasattr(redis_mgr, '_client') and redis_mgr._client else {}
                        hits = stats_info.get("keyspace_hits", 0)
                        misses = stats_info.get("keyspace_misses", 0)
                        total = hits + misses
                        if total > 0:
                            metrics.redis_hit_rate = (hits / total) * 100
                    except:
                        pass
                    
                    # 告警检查
                    if metrics.redis_memory_used_mb >= self._redis_memory_warning_mb:
                        metrics.alerts.append({
                            "type": "redis_memory",
                            "level": "warning",
                            "message": f"Redis内存使用过高: {metrics.redis_memory_used_mb:.1f}MB"
                        })
            except Exception as e:
                logger.warning(f"收集Redis指标失败: {e}")
            
            # 3. 进程内存指标
            try:
                mem_info = self._process.memory_info()
                metrics.process_memory_mb = mem_info.rss / (1024 * 1024)
                metrics.process_memory_pct = self._process.memory_percent()
                
                # 系统内存
                sys_mem = psutil.virtual_memory()
                metrics.system_memory_available_mb = sys_mem.available / (1024 * 1024)
                metrics.system_memory_pct = sys_mem.percent
                
                # 告警检查
                if metrics.process_memory_mb >= self._process_memory_warning_mb:
                    metrics.alerts.append({
                        "type": "process_memory",
                        "level": "warning",
                        "message": f"进程内存使用过高: {metrics.process_memory_mb:.1f}MB"
                    })
            except Exception as e:
                logger.warning(f"收集内存指标失败: {e}")
            
            # 保存当前指标
            self._current_metrics = metrics
            
            # 输出监控日志
            logger.info(
                f"📊 性能监控 | MySQL连接: {metrics.mysql_active_connections}/{metrics.mysql_pool_size + metrics.mysql_max_overflow} "
                f"({metrics.mysql_pool_usage_pct:.1f}%) | Redis: {'✅' if metrics.redis_connected else '❌'} "
                f"{metrics.redis_memory_used_mb:.1f}MB ({metrics.redis_keys_count}键) | "
                f"进程内存: {metrics.process_memory_mb:.1f}MB ({metrics.process_memory_pct:.1f}%)"
            )
            
            # 输出告警
            for alert in metrics.alerts:
                logger.warning(f"⚠️ {alert['message']}")
            
            # 🆕 将指标写入Redis（供前端查询）
            # 本地服务不使用Redis
            # try:
            #     from server.utils.redis_manager import get_redis
            #     import json
            #     redis_mgr = get_redis()
                if redis_mgr:
                    metrics_dict = {
                        "mysql_active_connections": metrics.mysql_active_connections,
                        "mysql_pool_size": metrics.mysql_pool_size,
                        "mysql_pool_usage_pct": round(metrics.mysql_pool_usage_pct, 2),
                        "redis_connected": metrics.redis_connected,
                        "redis_memory_used_mb": round(metrics.redis_memory_used_mb, 2),
                        "redis_keys_count": metrics.redis_keys_count,
                        "redis_hit_rate": round(metrics.redis_hit_rate, 2),
                        "process_memory_mb": round(metrics.process_memory_mb, 2),
                        "process_memory_pct": round(metrics.process_memory_pct, 2),
                        "system_memory_pct": round(metrics.system_memory_pct, 2),
                        "timestamp": metrics.timestamp,
                        "alerts": metrics.alerts
                    }
                    redis_mgr.set("system:performance:latest", json.dumps(metrics_dict, ensure_ascii=False), ttl=120)
            except Exception as e:
                logger.debug(f"写入监控指标到Redis失败: {e}")
        
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}", exc_info=True)


# 全局单例
_monitor_instance: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance


async def init_performance_monitor():
    """初始化并启动性能监控"""
    monitor = get_performance_monitor()
    await monitor.start()


async def stop_performance_monitor():
    """停止性能监控"""
    monitor = get_performance_monitor()
    await monitor.stop()

