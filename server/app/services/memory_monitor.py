#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存监控服务
定期检查服务内存使用，超过阈值时主动执行垃圾回收
"""

import asyncio
import gc
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None


logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """内存快照"""
    timestamp: float
    memory_mb: float
    memory_percent: float
    gc_count: int


@dataclass
class MemoryMonitorState:
    """内存监控状态"""
    enabled: bool = True
    check_interval_sec: int = 300  # 5分钟检查一次
    warning_threshold_mb: float = 3500  # 3.5GB警告
    critical_threshold_mb: float = 4000  # 4GB严重警告
    gc_count: int = 0
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    max_snapshots: int = 100  # 最多保留100个快照


class MemoryMonitor:
    """内存监控服务"""
    
    def __init__(self):
        self._state = MemoryMonitorState()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        if psutil is None:
            logger.warning("⚠️ psutil未安装，内存监控功能不可用")
            self._state.enabled = False
    
    def is_enabled(self) -> bool:
        """是否启用内存监控"""
        return self._state.enabled and psutil is not None
    
    async def start(self):
        """启动内存监控"""
        if not self.is_enabled():
            logger.warning("内存监控未启用或psutil不可用")
            return
        
        if self._task and not self._task.done():
            logger.warning("内存监控已在运行中")
            return
        
        self._stop_event.clear()
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ 内存监控服务已启动")
    
    async def stop(self):
        """停止内存监控"""
        if not self._task:
            return
        
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("🛑 内存监控服务已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info(f"🔍 内存监控循环已启动，检查间隔：{self._state.check_interval_sec}秒")
        
        while not self._stop_event.is_set():
            try:
                await self._check_memory()
            except Exception as e:
                logger.error(f"内存检查失败: {e}", exc_info=True)
            
            # 等待下次检查
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._state.check_interval_sec
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    async def _check_memory(self):
        """检查内存使用"""
        if not psutil:
            return
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # 记录快照
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                gc_count=self._state.gc_count
            )
            self._state.snapshots.append(snapshot)
            
            # 限制快照数量
            if len(self._state.snapshots) > self._state.max_snapshots:
                self._state.snapshots = self._state.snapshots[-self._state.max_snapshots:]
            
            # 检查阈值
            if memory_mb > self._state.critical_threshold_mb:
                logger.error(
                    f"❌ 内存占用严重: {memory_mb:.0f}MB ({memory_percent:.1f}%), "
                    f"超过临界阈值{self._state.critical_threshold_mb:.0f}MB，建议重启服务"
                )
                # 严重情况下执行垃圾回收
                await self._perform_gc()
            elif memory_mb > self._state.warning_threshold_mb:
                logger.warning(
                    f"⚠️ 内存占用较高: {memory_mb:.0f}MB ({memory_percent:.1f}%), "
                    f"超过警告阈值{self._state.warning_threshold_mb:.0f}MB"
                )
                # 警告情况下执行垃圾回收
                await self._perform_gc()
            else:
                logger.debug(
                    f"✅ 内存占用正常: {memory_mb:.0f}MB ({memory_percent:.1f}%)"
                )
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
    
    async def _perform_gc(self):
        """执行垃圾回收"""
        try:
            logger.info("🧹 开始执行垃圾回收...")
            
            # 在线程池中执行GC，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, gc.collect)
            
            self._state.gc_count += 1
            
            # GC后再次检查内存
            if psutil:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                logger.info(f"✅ 垃圾回收完成，当前内存: {memory_mb:.0f}MB (GC次数: {self._state.gc_count})")
        except Exception as e:
            logger.error(f"执行垃圾回收失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取内存监控状态"""
        if not self.is_enabled():
            return {
                "enabled": False,
                "reason": "psutil not available"
            }
        
        current_memory = None
        if psutil:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_percent = process.memory_percent()
                current_memory = {
                    "memory_mb": round(memory_mb, 2),
                    "memory_percent": round(memory_percent, 2)
                }
            except Exception:
                pass
        
        return {
            "enabled": self._state.enabled,
            "check_interval_sec": self._state.check_interval_sec,
            "warning_threshold_mb": self._state.warning_threshold_mb,
            "critical_threshold_mb": self._state.critical_threshold_mb,
            "gc_count": self._state.gc_count,
            "snapshots_count": len(self._state.snapshots),
            "current_memory": current_memory,
        }
    
    def get_recent_snapshots(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的内存快照"""
        snapshots = self._state.snapshots[-count:]
        return [
            {
                "timestamp": s.timestamp,
                "memory_mb": round(s.memory_mb, 2),
                "memory_percent": round(s.memory_percent, 2),
                "gc_count": s.gc_count,
            }
            for s in snapshots
        ]


# 全局实例
_memory_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """获取内存监控单例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor

