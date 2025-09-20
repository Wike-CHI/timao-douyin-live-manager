#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AST性能基准测试模块
测试增强版AST服务的性能指标和资源使用情况
"""

import time
import psutil
import threading
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging

from enhanced_ast_service import EnhancedASTService
from enhanced_transcription_result import (
    EnhancedTranscriptionResult,
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown
)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    processing_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    confidence_score: float
    accuracy_score: float
    throughput_samples_per_second: float
    error_rate_percent: float


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    test_name: str
    total_samples: int
    success_count: int
    failure_count: int
    avg_processing_time_ms: float
    max_processing_time_ms: float
    min_processing_time_ms: float
    avg_memory_usage_mb: float
    avg_cpu_usage_percent: float
    avg_confidence_score: float
    avg_accuracy_score: float
    throughput_samples_per_second: float
    error_rate_percent: float
    detailed_metrics: List[PerformanceMetrics]


class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self, enhanced_ast_service: EnhancedASTService):
        """
        初始化性能基准测试器
        
        Args:
            enhanced_ast_service: 增强版AST服务实例
        """
        self.ast_service = enhanced_ast_service
        self.logger = logging.getLogger(__name__)
        
        # 性能监控
        self.process = psutil.Process()
        self.metrics_lock = threading.Lock()
        self.current_metrics = []
        
        # 测试参数
        self.test_audio_samples = self._generate_test_audio_samples()
    
    def _generate_test_audio_samples(self) -> List[Dict[str, Any]]:
        """生成测试音频样本数据"""
        samples = []
        
        # 情感表达场景测试样本
        emotion_samples = [
            {
                "category": "emotion_expression",
                "audio_data": self._generate_mock_audio_data(duration=2.5),
                "expected_text": "宝贝们今天这个口红真的超级好看哦",
                "expected_confidence": 0.85,
                "scenario": "高情感强度表达"
            },
            {
                "category": "emotion_expression", 
                "audio_data": self._generate_mock_audio_data(duration=3.0),
                "expected_text": "家人们这个眼影盘颜色也太美了吧",
                "expected_confidence": 0.82,
                "scenario": "中等情感强度表达"
            }
        ]
        
        # 产品介绍场景测试样本
        product_samples = [
            {
                "category": "product_intro",
                "audio_data": self._generate_mock_audio_data(duration=4.0),
                "expected_text": "这款粉底液遮瑕效果特别棒而且不卡粉",
                "expected_confidence": 0.88,
                "scenario": "产品特性介绍"
            },
            {
                "category": "product_intro",
                "audio_data": self._generate_mock_audio_data(duration=3.5),
                "expected_text": "护肤品要选择适合自己肤质的产品",
                "expected_confidence": 0.90,
                "scenario": "专业建议说明"
            }
        ]
        
        # 互动引导场景测试样本
        interaction_samples = [
            {
                "category": "interaction",
                "audio_data": self._generate_mock_audio_data(duration=2.8),
                "expected_text": "有想要的小仙女们可以点击下方链接",
                "expected_confidence": 0.78,
                "scenario": "购买引导"
            },
            {
                "category": "interaction",
                "audio_data": self._generate_mock_audio_data(duration=2.2),
                "expected_text": "大家有什么问题可以在评论区留言",
                "expected_confidence": 0.80,
                "scenario": "互动邀请"
            }
        ]
        
        # 噪声干扰场景测试样本
        noise_samples = [
            {
                "category": "noisy_environment",
                "audio_data": self._generate_mock_audio_data(duration=3.0, noise_level=0.3),
                "expected_text": "今天直播间人气很旺谢谢大家支持",
                "expected_confidence": 0.65,
                "scenario": "背景噪声干扰"
            },
            {
                "category": "noisy_environment",
                "audio_data": self._generate_mock_audio_data(duration=2.5, noise_level=0.5),
                "expected_text": "这个价格真的很优惠机会难得",
                "expected_confidence": 0.55,
                "scenario": "高噪声环境"
            }
        ]
        
        # 语速变化场景测试样本
        speed_samples = [
            {
                "category": "fast_speech",
                "audio_data": self._generate_mock_audio_data(duration=1.8, speech_rate="fast"),
                "expected_text": "限时特价只有今天抓紧时间下单",
                "expected_confidence": 0.70,
                "scenario": "快速语音"
            },
            {
                "category": "slow_speech",
                "audio_data": self._generate_mock_audio_data(duration=4.5, speech_rate="slow"),
                "expected_text": "让我详细介绍一下这个产品的使用方法",
                "expected_confidence": 0.92,
                "scenario": "慢速清晰语音"
            }
        ]
        
        # 合并所有样本
        samples.extend(emotion_samples)
        samples.extend(product_samples)
        samples.extend(interaction_samples)
        samples.extend(noise_samples)
        samples.extend(speed_samples)
        
        return samples
    
    def _generate_mock_audio_data(self, 
                                 duration: float = 3.0,
                                 noise_level: float = 0.1,
                                 speech_rate: str = "normal") -> bytes:
        """
        生成模拟音频数据用于测试
        
        Args:
            duration: 音频时长（秒）
            noise_level: 噪声水平 (0.0-1.0)
            speech_rate: 语音速率 ("slow", "normal", "fast")
        
        Returns:
            模拟音频数据字节
        """
        # 音频参数
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # 生成基础信号（模拟语音频率特征）
        t = np.linspace(0, duration, samples)
        
        # 基础频率组合（模拟人声频谱）
        base_freq = 200  # 基频
        signal = (
            0.5 * np.sin(2 * np.pi * base_freq * t) +
            0.3 * np.sin(2 * np.pi * base_freq * 2 * t) +
            0.2 * np.sin(2 * np.pi * base_freq * 3 * t)
        )
        
        # 添加语音特征调制
        if speech_rate == "fast":
            signal = signal * (1 + 0.3 * np.sin(2 * np.pi * 5 * t))
        elif speech_rate == "slow":
            signal = signal * (1 + 0.2 * np.sin(2 * np.pi * 2 * t))
        
        # 添加噪声
        noise = np.random.normal(0, noise_level, samples)
        signal = signal + noise
        
        # 归一化和量化
        signal = np.clip(signal, -1.0, 1.0)
        audio_data = (signal * 32767).astype(np.int16)
        
        return audio_data.tobytes()
    
    async def run_single_sample_test(self, sample: Dict[str, Any]) -> PerformanceMetrics:
        """
        运行单个样本的性能测试
        
        Args:
            sample: 测试样本数据
        
        Returns:
            性能指标
        """
        # 记录开始时间和资源状态
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = self.process.cpu_percent()
        
        try:
            # 执行AST转录
            result = await self.ast_service.transcribe_audio(
                audio_data=sample["audio_data"],
                session_id=f"test_{int(time.time())}",
                room_id="benchmark_room",
                enable_enhancements=True
            )
            
            # 记录结束时间和资源状态
            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            end_cpu = self.process.cpu_percent()
            
            # 计算性能指标
            processing_time_ms = (end_time - start_time) * 1000
            memory_usage_mb = max(end_memory - start_memory, 0)
            cpu_usage_percent = (start_cpu + end_cpu) / 2
            
            # 计算准确率
            accuracy_score = self._calculate_accuracy(
                expected=sample["expected_text"],
                actual=result.text
            )
            
            return PerformanceMetrics(
                processing_time_ms=processing_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                confidence_score=result.confidence,
                accuracy_score=accuracy_score,
                throughput_samples_per_second=1000 / processing_time_ms,
                error_rate_percent=0.0
            )
            
        except Exception as e:
            self.logger.error(f"测试样本处理失败: {e}")
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000
            
            return PerformanceMetrics(
                processing_time_ms=processing_time_ms,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                confidence_score=0.0,
                accuracy_score=0.0,
                throughput_samples_per_second=0.0,
                error_rate_percent=100.0
            )
    
    def _calculate_accuracy(self, expected: str, actual: str) -> float:
        """
        计算转录准确率
        
        Args:
            expected: 期望文本
            actual: 实际转录文本
        
        Returns:
            准确率分数 (0.0-1.0)
        """
        if not expected or not actual:
            return 0.0 if expected != actual else 1.0
        
        # 分词比较
        expected_words = set(expected.split())
        actual_words = set(actual.split())
        
        if len(expected_words) == 0:
            return 1.0 if len(actual_words) == 0 else 0.0
        
        # 计算词汇匹配率
        intersection = expected_words.intersection(actual_words)
        accuracy = len(intersection) / len(expected_words)
        
        return accuracy
    
    async def run_accuracy_benchmark(self) -> BenchmarkResult:
        """
        运行准确率基准测试
        
        Returns:
            基准测试结果
        """
        self.logger.info("开始准确率基准测试...")
        
        metrics = []
        success_count = 0
        failure_count = 0
        
        for sample in self.test_audio_samples:
            try:
                metric = await self.run_single_sample_test(sample)
                metrics.append(metric)
                
                if metric.error_rate_percent == 0:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                self.logger.error(f"样本测试失败: {e}")
                failure_count += 1
        
        return self._generate_benchmark_result("准确率基准测试", metrics, success_count, failure_count)
    
    async def run_performance_benchmark(self, duration_minutes: int = 30) -> BenchmarkResult:
        """
        运行性能压力测试
        
        Args:
            duration_minutes: 测试持续时间（分钟）
        
        Returns:
            基准测试结果
        """
        self.logger.info(f"开始性能压力测试，持续时间: {duration_minutes}分钟...")
        
        metrics = []
        success_count = 0
        failure_count = 0
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            # 随机选择测试样本
            sample = self.test_audio_samples[np.random.randint(0, len(self.test_audio_samples))]
            
            try:
                metric = await self.run_single_sample_test(sample)
                metrics.append(metric)
                
                if metric.error_rate_percent == 0:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                self.logger.error(f"压力测试样本失败: {e}")
                failure_count += 1
            
            # 短暂休息避免过度占用资源
            await asyncio.sleep(0.1)
        
        return self._generate_benchmark_result("性能压力测试", metrics, success_count, failure_count)
    
    async def run_concurrent_benchmark(self, concurrent_users: int = 10) -> BenchmarkResult:
        """
        运行并发用户测试
        
        Args:
            concurrent_users: 并发用户数
        
        Returns:
            基准测试结果
        """
        self.logger.info(f"开始并发用户测试，并发数: {concurrent_users}...")
        
        async def concurrent_user_simulation():
            """模拟单个并发用户"""
            user_metrics = []
            for _ in range(5):  # 每个用户执行5次转录
                sample = self.test_audio_samples[np.random.randint(0, len(self.test_audio_samples))]
                metric = await self.run_single_sample_test(sample)
                user_metrics.append(metric)
                await asyncio.sleep(np.random.uniform(0.5, 2.0))  # 随机间隔
            return user_metrics
        
        # 启动并发任务
        tasks = [concurrent_user_simulation() for _ in range(concurrent_users)]
        all_user_metrics = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 汇总指标
        metrics = []
        success_count = 0
        failure_count = 0
        
        for user_metrics in all_user_metrics:
            if isinstance(user_metrics, Exception):
                failure_count += 5  # 假设每个用户5次测试
                continue
                
            if isinstance(user_metrics, list):
                for metric in user_metrics:
                    metrics.append(metric)
                    if metric.error_rate_percent == 0:
                        success_count += 1
                    else:
                        failure_count += 1
        
        return self._generate_benchmark_result("并发用户测试", metrics, success_count, failure_count)
    
    def _generate_benchmark_result(self, 
                                  test_name: str,
                                  metrics: List[PerformanceMetrics],
                                  success_count: int,
                                  failure_count: int) -> BenchmarkResult:
        """
        生成基准测试结果报告
        
        Args:
            test_name: 测试名称
            metrics: 性能指标列表
            success_count: 成功次数
            failure_count: 失败次数
        
        Returns:
            基准测试结果
        """
        if not metrics:
            return BenchmarkResult(
                test_name=test_name,
                total_samples=0,
                success_count=0,
                failure_count=failure_count,
                avg_processing_time_ms=0,
                max_processing_time_ms=0,
                min_processing_time_ms=0,
                avg_memory_usage_mb=0,
                avg_cpu_usage_percent=0,
                avg_confidence_score=0,
                avg_accuracy_score=0,
                throughput_samples_per_second=0,
                error_rate_percent=100.0,
                detailed_metrics=[]
            )
        
        # 计算统计指标
        processing_times = [m.processing_time_ms for m in metrics]
        memory_usages = [m.memory_usage_mb for m in metrics]
        cpu_usages = [m.cpu_usage_percent for m in metrics]
        confidence_scores = [m.confidence_score for m in metrics]
        accuracy_scores = [m.accuracy_score for m in metrics]
        throughputs = [m.throughput_samples_per_second for m in metrics]
        error_rates = [m.error_rate_percent for m in metrics]
        
        return BenchmarkResult(
            test_name=test_name,
            total_samples=len(metrics),
            success_count=success_count,
            failure_count=failure_count,
            avg_processing_time_ms=statistics.mean(processing_times),
            max_processing_time_ms=max(processing_times),
            min_processing_time_ms=min(processing_times),
            avg_memory_usage_mb=statistics.mean(memory_usages),
            avg_cpu_usage_percent=statistics.mean(cpu_usages),
            avg_confidence_score=statistics.mean(confidence_scores),
            avg_accuracy_score=statistics.mean(accuracy_scores),
            throughput_samples_per_second=statistics.mean(throughputs),
            error_rate_percent=(failure_count / (success_count + failure_count)) * 100 if (success_count + failure_count) > 0 else 0,
            detailed_metrics=metrics
        )
    
    def generate_performance_report(self, results: List[BenchmarkResult]) -> str:
        """
        生成性能测试报告
        
        Args:
            results: 基准测试结果列表
        
        Returns:
            格式化的性能报告
        """
        report = []
        report.append("\n" + "="*80)
        report.append("AST语音转录算法 - 性能基准测试报告")
        report.append("="*80)
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for result in results:
            report.append(f"测试项目: {result.test_name}")
            report.append("-"*50)
            report.append(f"总样本数: {result.total_samples}")
            report.append(f"成功: {result.success_count} | 失败: {result.failure_count}")
            report.append(f"成功率: {((result.success_count / result.total_samples) * 100):.2f}%")
            report.append("")
            
            report.append("性能指标:")
            report.append(f"  平均处理时间: {result.avg_processing_time_ms:.2f}ms")
            report.append(f"  最大处理时间: {result.max_processing_time_ms:.2f}ms")
            report.append(f"  最小处理时间: {result.min_processing_time_ms:.2f}ms")
            report.append(f"  平均内存使用: {result.avg_memory_usage_mb:.2f}MB")
            report.append(f"  平均CPU使用: {result.avg_cpu_usage_percent:.2f}%")
            report.append("")
            
            report.append("质量指标:")
            report.append(f"  平均置信度: {result.avg_confidence_score:.3f}")
            report.append(f"  平均准确率: {result.avg_accuracy_score:.3f}")
            report.append(f"  处理吞吐量: {result.throughput_samples_per_second:.2f} 样本/秒")
            report.append(f"  错误率: {result.error_rate_percent:.2f}%")
            report.append("")
            
            # 质量评估
            if result.avg_accuracy_score >= 0.8:
                report.append("✅ 准确率达标 (≥80%)")
            else:
                report.append("❌ 准确率未达标 (<80%)")
                
            if result.avg_confidence_score >= 0.7:
                report.append("✅ 置信度良好 (≥70%)")
            else:
                report.append("❌ 置信度偏低 (<70%)")
                
            if result.avg_processing_time_ms <= 2000:
                report.append("✅ 响应时间良好 (≤2000ms)")
            else:
                report.append("❌ 响应时间过长 (>2000ms)")
                
            report.append("\n")
        
        report.append("="*80)
        
        return "\n".join(report)


class RealTimePerformanceMonitor:
    """实时性能监控器"""
    
    def __init__(self, sampling_interval: float = 1.0):
        """
        初始化实时性能监控器
        
        Args:
            sampling_interval: 采样间隔（秒）
        """
        self.sampling_interval = sampling_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.metrics_history = []
        self.process = psutil.Process()
        
    def start_monitoring(self):
        """开始实时监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """停止实时监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统资源指标
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                timestamp = time.time()
                
                metric = {
                    "timestamp": timestamp,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "threads": self.process.num_threads()
                }
                
                self.metrics_history.append(metric)
                
                # 保持历史记录在合理范围内
                if len(self.metrics_history) > 3600:  # 保留1小时数据
                    self.metrics_history.pop(0)
                    
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                logging.error(f"性能监控错误: {e}")
                time.sleep(self.sampling_interval)
                
    def get_current_metrics(self) -> Dict[str, float]:
        """获取当前性能指标"""
        if not self.metrics_history:
            return {}
            
        latest = self.metrics_history[-1]
        return {
            "cpu_percent": latest["cpu_percent"],
            "memory_mb": latest["memory_mb"],
            "threads": latest["threads"]
        }
        
    def get_metrics_summary(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """获取指定时间段的性能指标摘要"""
        if not self.metrics_history:
            return {}
            
        # 过滤指定时间段的数据
        current_time = time.time()
        start_time = current_time - (duration_minutes * 60)
        
        filtered_metrics = [
            m for m in self.metrics_history 
            if m["timestamp"] >= start_time
        ]
        
        if not filtered_metrics:
            return {}
            
        # 计算统计指标
        cpu_values = [m["cpu_percent"] for m in filtered_metrics]
        memory_values = [m["memory_mb"] for m in filtered_metrics]
        
        return {
            "duration_minutes": duration_minutes,
            "sample_count": len(filtered_metrics),
            "cpu": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "std": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
            },
            "memory": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "std": statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            }
        }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        """主测试程序"""
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建增强版AST服务（需要实际实例）
        # ast_service = EnhancedASTService()
        # benchmark = PerformanceBenchmark(ast_service)
        
        print("AST语音转录算法性能基准测试")
        print("注意: 需要先初始化EnhancedASTService实例")
        print("")
        print("测试项目:")
        print("1. 准确率基准测试")
        print("2. 性能压力测试 (30分钟)")
        print("3. 并发用户测试 (10用户)")
        print("4. 实时性能监控")
        
        # 示例测试报告格式
        print("\n" + "="*80)
        print("示例测试报告格式:")
        print("-"*50)
        print("总样本数: 100")
        print("成功: 95 | 失败: 5")
        print("成功率: 95.00%")
        print("")
        print("性能指标:")
        print("  平均处理时间: 1250.30ms")
        print("  最大处理时间: 2100.50ms")
        print("  最小处理时间: 800.20ms")
        print("  平均内存使用: 45.60MB")
        print("  平均CPU使用: 25.30%")
        print("")
        print("质量指标:")
        print("  平均置信度: 0.825")
        print("  平均准确率: 0.890")
        print("  处理吞吐量: 0.80 样本/秒")
        print("  错误率: 5.00%")
        print("")
        print("✅ 准确率达标 (≥80%)")
        print("✅ 置信度良好 (≥70%)")
        print("✅ 响应时间良好 (≤2000ms)")
        print("="*80)
        
    # 运行主程序
    asyncio.run(main())