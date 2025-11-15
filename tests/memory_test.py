#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存优化测试脚本
审查人：叶维哲

用于验证内存优化方案的效果：
1. 监控服务长时间运行的内存使用
2. 验证内存清理机制的有效性
3. 检查服务重启次数
"""

import time
import requests
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MemoryTestMonitor:
    """内存测试监控器"""
    
    def __init__(self, api_base_url: str = "http://localhost:8081"):
        self.api_base_url = api_base_url
        self.snapshots: List[Dict[str, Any]] = []
        
    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        try:
            response = requests.get(f"{self.api_base_url}/api/model/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"获取模型状态失败: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取模型状态异常: {e}")
            return {}
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存监控状态"""
        try:
            response = requests.get(f"{self.api_base_url}/api/model/memory-status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"获取内存状态失败: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取内存状态异常: {e}")
            return {}
    
    def get_system_memory(self) -> Dict[str, float]:
        """获取系统内存使用"""
        try:
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total / 1024 / 1024,
                "available_mb": mem.available / 1024 / 1024,
                "used_mb": mem.used / 1024 / 1024,
                "percent": mem.percent
            }
        except Exception as e:
            logger.error(f"获取系统内存异常: {e}")
            return {}
    
    def take_snapshot(self) -> Dict[str, Any]:
        """获取内存快照"""
        snapshot = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_status": self.get_model_status(),
            "memory_status": self.get_memory_status(),
            "system_memory": self.get_system_memory()
        }
        self.snapshots.append(snapshot)
        return snapshot
    
    def log_snapshot(self, snapshot: Dict[str, Any]):
        """记录快照日志"""
        sys_mem = snapshot.get("system_memory", {})
        mem_status = snapshot.get("memory_status", {})
        monitor_status = mem_status.get("monitor_status", {})
        current_memory = monitor_status.get("current_memory", {})
        
        logger.info("=" * 80)
        logger.info(f"时间: {snapshot['timestamp']}")
        logger.info(f"系统内存: 总计{sys_mem.get('total_mb', 0):.0f}MB, "
                   f"已用{sys_mem.get('used_mb', 0):.0f}MB ({sys_mem.get('percent', 0):.1f}%), "
                   f"可用{sys_mem.get('available_mb', 0):.0f}MB")
        
        if current_memory:
            logger.info(f"进程内存: {current_memory.get('memory_mb', 0):.0f}MB "
                       f"({current_memory.get('memory_percent', 0):.1f}%)")
            logger.info(f"GC次数: {monitor_status.get('gc_count', 0)}")
        
        logger.info("=" * 80)
    
    def analyze_memory_trend(self):
        """分析内存趋势"""
        if len(self.snapshots) < 2:
            logger.info("快照数量不足，无法分析趋势")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("内存趋势分析")
        logger.info("=" * 80)
        
        # 提取进程内存数据
        memory_data = []
        for snapshot in self.snapshots:
            mem_status = snapshot.get("memory_status", {})
            monitor_status = mem_status.get("monitor_status", {})
            current_memory = monitor_status.get("current_memory", {})
            if current_memory:
                memory_data.append({
                    "timestamp": snapshot["timestamp"],
                    "memory_mb": current_memory.get("memory_mb", 0)
                })
        
        if len(memory_data) < 2:
            logger.info("进程内存数据不足，无法分析")
            return
        
        # 计算统计信息
        memories = [d["memory_mb"] for d in memory_data]
        avg_memory = sum(memories) / len(memories)
        min_memory = min(memories)
        max_memory = max(memories)
        
        logger.info(f"快照数量: {len(memory_data)}")
        logger.info(f"平均内存: {avg_memory:.0f}MB")
        logger.info(f"最小内存: {min_memory:.0f}MB")
        logger.info(f"最大内存: {max_memory:.0f}MB")
        logger.info(f"内存波动: {max_memory - min_memory:.0f}MB")
        
        # 检查内存是否在合理范围
        if avg_memory < 2800:
            logger.info("✅ 内存使用偏低，运行良好")
        elif avg_memory < 3800:
            logger.info("✅ 内存使用正常，在预期范围内")
        elif avg_memory < 4500:
            logger.warning("⚠️ 内存使用偏高，需要关注")
        else:
            logger.error("❌ 内存使用超标，可能触发PM2重启")
        
        # 检查内存趋势
        first_half = memories[:len(memories)//2]
        second_half = memories[len(memories)//2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:
            logger.warning(f"⚠️ 内存持续增长: 前半段{avg_first:.0f}MB -> 后半段{avg_second:.0f}MB")
        elif avg_second < avg_first * 0.9:
            logger.info(f"✅ 内存清理有效: 前半段{avg_first:.0f}MB -> 后半段{avg_second:.0f}MB")
        else:
            logger.info(f"✅ 内存使用稳定: 前半段{avg_first:.0f}MB -> 后半段{avg_second:.0f}MB")
        
        logger.info("=" * 80 + "\n")
    
    def run_continuous_test(self, duration_minutes: int = 120, interval_seconds: int = 60):
        """运行持续测试
        
        Args:
            duration_minutes: 测试持续时间（分钟）
            interval_seconds: 快照间隔（秒）
        """
        logger.info(f"开始内存持续测试: 持续{duration_minutes}分钟, 每{interval_seconds}秒采样")
        logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        
        try:
            while time.time() < end_time:
                snapshot = self.take_snapshot()
                self.log_snapshot(snapshot)
                
                # 计算剩余时间
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                logger.info(f"已运行: {elapsed/60:.1f}分钟, 剩余: {remaining/60:.1f}分钟\n")
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("\n测试被用户中断")
        
        logger.info("\n测试完成，开始分析...")
        self.analyze_memory_trend()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="内存优化测试脚本")
    parser.add_argument("--duration", type=int, default=120, help="测试持续时间（分钟），默认120分钟")
    parser.add_argument("--interval", type=int, default=60, help="快照间隔（秒），默认60秒")
    parser.add_argument("--api-url", type=str, default="http://localhost:8081", help="API地址")
    
    args = parser.parse_args()
    
    monitor = MemoryTestMonitor(api_base_url=args.api_url)
    
    # 检查服务是否可用
    logger.info("检查服务状态...")
    status = monitor.get_model_status()
    if not status:
        logger.error("❌ 无法连接到服务，请确保服务已启动")
        return
    
    logger.info("✅ 服务连接成功，开始测试\n")
    
    # 运行测试
    monitor.run_continuous_test(
        duration_minutes=args.duration,
        interval_seconds=args.interval
    )


if __name__ == "__main__":
    main()

