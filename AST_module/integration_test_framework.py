#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AST服务集成测试框架
提供完整的端到端测试功能，验证增强版AST服务的实际性能
"""

import asyncio
import time
import json
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

from enhanced_ast_service import EnhancedASTService
from enhanced_transcription_result import (
    EnhancedTranscriptionResult,
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown
)
from performance_benchmark import PerformanceBenchmark, BenchmarkResult, RealTimePerformanceMonitor
from config_manager import EnhancedConfigManager


@dataclass
class TestScenario:
    """测试场景定义"""
    name: str
    description: str
    audio_samples: List[Dict[str, Any]]
    expected_metrics: Dict[str, float]
    test_duration_minutes: int
    concurrent_users: int
    success_criteria: Dict[str, float]


@dataclass
class IntegrationTestResult:
    """集成测试结果"""
    scenario_name: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    total_samples_processed: int
    success_count: int
    failure_count: int
    average_accuracy: float
    average_confidence: float
    average_processing_time_ms: float
    peak_memory_usage_mb: float
    average_cpu_usage_percent: float
    error_messages: List[str]
    performance_summary: Dict[str, Any]
    meets_success_criteria: bool


class IntegrationTestFramework:
    """集成测试框架主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化集成测试框架
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = EnhancedConfigManager()
        self.ast_service = None
        self.performance_benchmark = None
        self.performance_monitor = RealTimePerformanceMonitor()
        
        # 测试结果存储
        self.test_results = []
        self.test_reports_dir = Path("test_reports")
        self.test_reports_dir.mkdir(exist_ok=True)
        
        # 初始化测试场景
        self.test_scenarios = self._initialize_test_scenarios()
    
    async def initialize_services(self):
        """初始化测试服务"""
        try:
            self.logger.info("初始化增强版AST服务...")
            self.ast_service = EnhancedASTService()
            
            # 等待服务初始化完成
            await asyncio.sleep(2.0)
            
            self.performance_benchmark = PerformanceBenchmark(self.ast_service)
            self.logger.info("服务初始化完成")
            
        except Exception as e:
            self.logger.error(f"服务初始化失败: {e}")
            raise
    
    def _initialize_test_scenarios(self) -> List[TestScenario]:
        """初始化测试场景"""
        scenarios = []
        
        # 场景1: 情感博主日常直播场景
        emotion_scenario = TestScenario(
            name="情感博主日常直播",
            description="模拟情感博主在日常直播中的语音转录需求",
            audio_samples=self._generate_emotion_samples(),
            expected_metrics={
                "accuracy": 0.85,
                "confidence": 0.80,
                "processing_time_ms": 1500
            },
            test_duration_minutes=15,
            concurrent_users=3,
            success_criteria={
                "accuracy_threshold": 0.80,
                "confidence_threshold": 0.75,
                "processing_time_threshold_ms": 2000,
                "success_rate_threshold": 0.90
            }
        )
        scenarios.append(emotion_scenario)
        
        # 场景2: 产品推荐高强度场景
        product_scenario = TestScenario(
            name="产品推荐高强度",
            description="高强度产品推荐场景，语速快，专业词汇多",
            audio_samples=self._generate_product_samples(),
            expected_metrics={
                "accuracy": 0.88,
                "confidence": 0.85,
                "processing_time_ms": 1200
            },
            test_duration_minutes=20,
            concurrent_users=5,
            success_criteria={
                "accuracy_threshold": 0.82,
                "confidence_threshold": 0.78,
                "processing_time_threshold_ms": 1800,
                "success_rate_threshold": 0.85
            }
        )
        scenarios.append(product_scenario)
        
        # 场景3: 长时间连续直播场景
        endurance_scenario = TestScenario(
            name="长时间连续直播",
            description="模拟3小时连续直播的耐久性测试",
            audio_samples=self._generate_mixed_samples(),
            expected_metrics={
                "accuracy": 0.82,
                "confidence": 0.78,
                "processing_time_ms": 1800
            },
            test_duration_minutes=180,  # 3小时
            concurrent_users=2,
            success_criteria={
                "accuracy_threshold": 0.75,
                "confidence_threshold": 0.70,
                "processing_time_threshold_ms": 2500,
                "success_rate_threshold": 0.85,
                "memory_leak_threshold_mb": 500  # 内存泄漏阈值
            }
        )
        scenarios.append(endurance_scenario)
        
        # 场景4: 噪声环境压力测试
        noise_scenario = TestScenario(
            name="噪声环境压力测试",
            description="各种噪声干扰下的识别能力测试",
            audio_samples=self._generate_noise_samples(),
            expected_metrics={
                "accuracy": 0.70,
                "confidence": 0.65,
                "processing_time_ms": 2000
            },
            test_duration_minutes=30,
            concurrent_users=4,
            success_criteria={
                "accuracy_threshold": 0.60,
                "confidence_threshold": 0.55,
                "processing_time_threshold_ms": 3000,
                "success_rate_threshold": 0.75
            }
        )
        scenarios.append(noise_scenario)
        
        return scenarios
    
    def _generate_emotion_samples(self) -> List[Dict[str, Any]]:
        """生成情感表达测试样本"""
        return [
            {
                "audio_data": self._create_mock_audio(3.0, "emotion_high"),
                "expected_text": "宝贝们今天这个口红颜色真的太美了",
                "category": "emotional_expression",
                "difficulty": "medium"
            },
            {
                "audio_data": self._create_mock_audio(2.5, "emotion_medium"),
                "expected_text": "家人们觉得这个眼影盘怎么样",
                "category": "emotional_interaction",
                "difficulty": "easy"
            },
            {
                "audio_data": self._create_mock_audio(4.0, "emotion_excited"),
                "expected_text": "天哪这个粉底液的遮瑕效果也太好了吧",
                "category": "emotional_excitement",
                "difficulty": "medium"
            }
        ]
    
    def _generate_product_samples(self) -> List[Dict[str, Any]]:
        """生成产品介绍测试样本"""
        return [
            {
                "audio_data": self._create_mock_audio(4.5, "product_detailed"),
                "expected_text": "这款精华液含有烟酰胺和透明质酸双重成分",
                "category": "product_specification",
                "difficulty": "hard"
            },
            {
                "audio_data": self._create_mock_audio(3.5, "product_benefit"),
                "expected_text": "坚持使用一个月皮肤会变得更加光滑细腻",
                "category": "product_benefit",
                "difficulty": "medium"
            },
            {
                "audio_data": self._create_mock_audio(2.8, "product_price"),
                "expected_text": "现在下单只需要二百九十八元包邮",
                "category": "product_pricing",
                "difficulty": "easy"
            }
        ]
    
    def _generate_mixed_samples(self) -> List[Dict[str, Any]]:
        """生成混合场景测试样本"""
        emotion_samples = self._generate_emotion_samples()
        product_samples = self._generate_product_samples()
        
        interaction_samples = [
            {
                "audio_data": self._create_mock_audio(2.2, "interaction"),
                "expected_text": "有问题的小仙女们可以私信我",
                "category": "user_interaction",
                "difficulty": "easy"
            },
            {
                "audio_data": self._create_mock_audio(3.2, "guidance"),
                "expected_text": "想要购买的话点击下方橙色按钮",
                "category": "purchase_guidance",
                "difficulty": "medium"
            }
        ]
        
        return emotion_samples + product_samples + interaction_samples
    
    def _generate_noise_samples(self) -> List[Dict[str, Any]]:
        """生成噪声环境测试样本"""
        return [
            {
                "audio_data": self._create_mock_audio(3.0, "background_music"),
                "expected_text": "今天给大家推荐几款好用的护肤品",
                "category": "background_noise",
                "difficulty": "hard"
            },
            {
                "audio_data": self._create_mock_audio(2.8, "echo_effect"),
                "expected_text": "这个价格真的很优惠大家要抓紧",
                "category": "echo_interference",
                "difficulty": "hard"
            },
            {
                "audio_data": self._create_mock_audio(3.5, "crowd_noise"),
                "expected_text": "感谢大家的支持和关注爱你们",
                "category": "crowd_background",
                "difficulty": "medium"
            }
        ]
    
    def _create_mock_audio(self, duration: float, audio_type: str) -> bytes:
        """
        创建模拟音频数据
        
        Args:
            duration: 音频时长
            audio_type: 音频类型
        
        Returns:
            音频数据字节
        """
        sample_rate = 16000
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        
        # 根据音频类型生成不同特征的信号
        if "emotion" in audio_type:
            # 情感语音：频率变化更大
            base_freq = 250
            signal = (
                0.6 * np.sin(2 * np.pi * base_freq * t) *
                (1 + 0.4 * np.sin(2 * np.pi * 3 * t))
            )
        elif "product" in audio_type:
            # 产品介绍：更稳定的频率
            base_freq = 200
            signal = 0.5 * np.sin(2 * np.pi * base_freq * t)
        elif "noise" in audio_type or "background" in audio_type:
            # 噪声环境：添加更多干扰
            base_freq = 220
            signal = 0.4 * np.sin(2 * np.pi * base_freq * t)
            noise = np.random.normal(0, 0.3, samples)
            signal = signal + noise
        else:
            # 默认信号
            base_freq = 215
            signal = 0.5 * np.sin(2 * np.pi * base_freq * t)
        
        # 归一化和量化
        signal = np.clip(signal, -1.0, 1.0)
        audio_data = (signal * 32767).astype(np.int16)
        
        return audio_data.tobytes()
    
    async def run_scenario_test(self, scenario: TestScenario) -> IntegrationTestResult:
        """
        运行单个测试场景
        
        Args:
            scenario: 测试场景
        
        Returns:
            集成测试结果
        """
        self.logger.info(f"开始执行测试场景: {scenario.name}")
        
        start_time = datetime.now()
        total_samples = 0
        success_count = 0
        failure_count = 0
        error_messages = []
        accuracy_scores = []
        confidence_scores = []
        processing_times = []
        
        # 启动性能监控
        self.performance_monitor.start_monitoring()
        
        try:
            # 计算测试结束时间
            end_time = start_time + timedelta(minutes=scenario.test_duration_minutes)
            
            # 创建并发任务
            async def single_user_simulation():
                """单用户模拟"""
                user_success = 0
                user_failure = 0
                user_errors = []
                
                while datetime.now() < end_time:
                    try:
                        # 随机选择音频样本
                        sample = scenario.audio_samples[
                            np.random.randint(0, len(scenario.audio_samples))
                        ]
                        
                        # 执行转录
                        start_processing = time.time()
                        if self.ast_service is not None:
                            result = await self.ast_service.transcribe_audio(
                                audio_data=sample["audio_data"],
                                session_id=f"test_{int(time.time())}_{np.random.randint(1000, 9999)}",
                                room_id=f"scenario_{scenario.name}",
                                enable_enhancements=True
                            )
                        else:
                            raise RuntimeError("AST服务未初始化")
                        end_processing = time.time()
                        
                        processing_time = (end_processing - start_processing) * 1000
                        processing_times.append(processing_time)
                        
                        # 计算准确率
                        accuracy = self._calculate_text_similarity(
                            sample["expected_text"],
                            result.text
                        )
                        accuracy_scores.append(accuracy)
                        confidence_scores.append(result.confidence)
                        
                        user_success += 1
                        
                    except Exception as e:
                        user_failure += 1
                        error_msg = f"用户模拟错误: {str(e)}"
                        user_errors.append(error_msg)
                        self.logger.error(error_msg)
                    
                    # 模拟用户间隔
                    await asyncio.sleep(np.random.uniform(0.5, 2.0))
                
                return user_success, user_failure, user_errors
            
            # 启动并发用户
            tasks = [
                single_user_simulation() 
                for _ in range(scenario.concurrent_users)
            ]
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 汇总结果
            for result in results:
                if isinstance(result, Exception):
                    error_messages.append(f"并发任务异常: {str(result)}")
                    continue
                
                if isinstance(result, tuple) and len(result) == 3:
                    user_success, user_failure, user_errors = result
                    success_count += user_success
                    failure_count += user_failure
                    error_messages.extend(user_errors)
            
            total_samples = success_count + failure_count
            
        finally:
            # 停止性能监控
            self.performance_monitor.stop_monitoring()
        
        # 计算性能指标
        actual_end_time = datetime.now()
        total_duration = (actual_end_time - start_time).total_seconds()
        
        avg_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0.0
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        avg_processing_time = np.mean(processing_times) if processing_times else 0.0
        
        # 获取性能监控数据
        performance_summary = self.performance_monitor.get_metrics_summary(
            duration_minutes=scenario.test_duration_minutes
        )
        
        peak_memory = performance_summary.get("memory", {}).get("max", 0.0)
        avg_cpu = performance_summary.get("cpu", {}).get("avg", 0.0)
        
        # 评估是否满足成功标准
        meets_criteria = self._evaluate_success_criteria(
            scenario.success_criteria,
            float(avg_accuracy),
            float(avg_confidence),
            float(avg_processing_time),
            success_count / total_samples if total_samples > 0 else 0.0,
            peak_memory
        )
        
        result = IntegrationTestResult(
            scenario_name=scenario.name,
            start_time=start_time,
            end_time=actual_end_time,
            total_duration_seconds=total_duration,
            total_samples_processed=total_samples,
            success_count=success_count,
            failure_count=failure_count,
            average_accuracy=float(avg_accuracy),
            average_confidence=float(avg_confidence),
            average_processing_time_ms=float(avg_processing_time),
            peak_memory_usage_mb=peak_memory,
            average_cpu_usage_percent=avg_cpu,
            error_messages=error_messages,
            performance_summary=performance_summary,
            meets_success_criteria=meets_criteria
        )
        
        self.test_results.append(result)
        self.logger.info(f"测试场景 '{scenario.name}' 完成")
        
        return result
    
    def _calculate_text_similarity(self, expected: str, actual: str) -> float:
        """
        计算文本相似度
        
        Args:
            expected: 期望文本
            actual: 实际文本
        
        Returns:
            相似度分数 (0.0-1.0)
        """
        if not expected or not actual:
            return 0.0 if expected != actual else 1.0
        
        # 简单的词汇匹配计算
        expected_words = set(expected.split())
        actual_words = set(actual.split())
        
        if len(expected_words) == 0:
            return 1.0 if len(actual_words) == 0 else 0.0
        
        intersection = expected_words.intersection(actual_words)
        return len(intersection) / len(expected_words)
    
    def _evaluate_success_criteria(self,
                                  criteria: Dict[str, float],
                                  accuracy: float,
                                  confidence: float,
                                  processing_time: float,
                                  success_rate: float,
                                  peak_memory: float) -> bool:
        """
        评估是否满足成功标准
        
        Args:
            criteria: 成功标准
            accuracy: 平均准确率
            confidence: 平均置信度
            processing_time: 平均处理时间
            success_rate: 成功率
            peak_memory: 峰值内存使用
        
        Returns:
            是否满足标准
        """
        checks = []
        
        if "accuracy_threshold" in criteria:
            checks.append(accuracy >= criteria["accuracy_threshold"])
        
        if "confidence_threshold" in criteria:
            checks.append(confidence >= criteria["confidence_threshold"])
        
        if "processing_time_threshold_ms" in criteria:
            checks.append(processing_time <= criteria["processing_time_threshold_ms"])
        
        if "success_rate_threshold" in criteria:
            checks.append(success_rate >= criteria["success_rate_threshold"])
        
        if "memory_leak_threshold_mb" in criteria:
            checks.append(peak_memory <= criteria["memory_leak_threshold_mb"])
        
        return all(checks)
    
    async def run_full_test_suite(self) -> List[IntegrationTestResult]:
        """
        运行完整测试套件
        
        Returns:
            所有测试结果
        """
        self.logger.info("开始执行完整集成测试套件...")
        
        # 初始化服务
        await self.initialize_services()
        
        # 依次执行每个场景
        for scenario in self.test_scenarios:
            try:
                await self.run_scenario_test(scenario)
                
                # 场景间休息
                self.logger.info(f"场景 '{scenario.name}' 完成，休息30秒...")
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"场景 '{scenario.name}' 执行失败: {e}")
                self.logger.error(traceback.format_exc())
        
        # 生成测试报告
        self._generate_test_report()
        
        self.logger.info("完整集成测试套件执行完成")
        return self.test_results
    
    def _generate_test_report(self):
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.test_reports_dir / f"integration_test_report_{timestamp}.json"
        
        # 准备报告数据
        report_data = {
            "test_suite_info": {
                "execution_time": datetime.now().isoformat(),
                "total_scenarios": len(self.test_scenarios),
                "total_test_results": len(self.test_results)
            },
            "scenarios": [
                {
                    "name": scenario.name,
                    "description": scenario.description,
                    "expected_metrics": scenario.expected_metrics,
                    "success_criteria": scenario.success_criteria
                }
                for scenario in self.test_scenarios
            ],
            "test_results": [
                asdict(result) for result in self.test_results
            ],
            "summary": self._generate_summary()
        }
        
        # 写入JSON报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 生成可读的文本报告
        text_report = self._generate_text_report()
        text_report_file = self.test_reports_dir / f"integration_test_report_{timestamp}.txt"
        
        with open(text_report_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        self.logger.info(f"测试报告已生成: {report_file}")
        self.logger.info(f"文本报告已生成: {text_report_file}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        if not self.test_results:
            return {}
        
        total_samples = sum(r.total_samples_processed for r in self.test_results)
        total_success = sum(r.success_count for r in self.test_results)
        total_failures = sum(r.failure_count for r in self.test_results)
        
        avg_accuracy = np.mean([r.average_accuracy for r in self.test_results])
        avg_confidence = np.mean([r.average_confidence for r in self.test_results])
        avg_processing_time = np.mean([r.average_processing_time_ms for r in self.test_results])
        
        scenarios_passed = sum(1 for r in self.test_results if r.meets_success_criteria)
        
        return {
            "overall_success_rate": total_success / total_samples if total_samples > 0 else 0.0,
            "total_samples_processed": total_samples,
            "total_successful_samples": total_success,
            "total_failed_samples": total_failures,
            "average_accuracy": avg_accuracy,
            "average_confidence": avg_confidence,
            "average_processing_time_ms": avg_processing_time,
            "scenarios_passed": scenarios_passed,
            "scenarios_total": len(self.test_results),
            "scenarios_pass_rate": scenarios_passed / len(self.test_results) if self.test_results else 0.0
        }
    
    def _generate_text_report(self) -> str:
        """生成可读的文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("AST语音转录算法 - 集成测试报告")
        lines.append("=" * 80)
        lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 摘要信息
        summary = self._generate_summary()
        lines.append("测试摘要:")
        lines.append("-" * 40)
        lines.append(f"总处理样本数: {summary.get('total_samples_processed', 0)}")
        lines.append(f"成功样本数: {summary.get('total_successful_samples', 0)}")
        lines.append(f"失败样本数: {summary.get('total_failed_samples', 0)}")
        lines.append(f"整体成功率: {summary.get('overall_success_rate', 0):.3f}")
        lines.append(f"平均准确率: {summary.get('average_accuracy', 0):.3f}")
        lines.append(f"平均置信度: {summary.get('average_confidence', 0):.3f}")
        lines.append(f"平均处理时间: {summary.get('average_processing_time_ms', 0):.2f}ms")
        lines.append(f"通过场景数: {summary.get('scenarios_passed', 0)}/{summary.get('scenarios_total', 0)}")
        lines.append("")
        
        # 各场景详细结果
        for result in self.test_results:
            lines.append(f"场景: {result.scenario_name}")
            lines.append("-" * 50)
            lines.append(f"测试时长: {result.total_duration_seconds:.1f}秒")
            lines.append(f"处理样本: {result.total_samples_processed}")
            lines.append(f"成功率: {(result.success_count / result.total_samples_processed * 100):.2f}%" 
                        if result.total_samples_processed > 0 else "成功率: 0%")
            lines.append(f"平均准确率: {result.average_accuracy:.3f}")
            lines.append(f"平均置信度: {result.average_confidence:.3f}")
            lines.append(f"平均处理时间: {result.average_processing_time_ms:.2f}ms")
            lines.append(f"峰值内存使用: {result.peak_memory_usage_mb:.2f}MB")
            lines.append(f"平均CPU使用: {result.average_cpu_usage_percent:.2f}%")
            lines.append(f"满足成功标准: {'✅ 是' if result.meets_success_criteria else '❌ 否'}")
            
            if result.error_messages:
                lines.append(f"错误信息数量: {len(result.error_messages)}")
            
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


if __name__ == "__main__":
    async def main():
        """主测试程序"""
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('integration_test.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # 创建测试框架
        test_framework = IntegrationTestFramework()
        
        try:
            # 运行完整测试套件
            results = await test_framework.run_full_test_suite()
            
            # 输出简要结果
            print("\n" + "=" * 60)
            print("集成测试执行完成")
            print("-" * 60)
            
            for result in results:
                status = "✅ 通过" if result.meets_success_criteria else "❌ 失败"
                print(f"{result.scenario_name}: {status}")
                print(f"  准确率: {result.average_accuracy:.3f}")
                print(f"  置信度: {result.average_confidence:.3f}")
                print(f"  处理时间: {result.average_processing_time_ms:.2f}ms")
                print()
                
        except Exception as e:
            print(f"测试执行失败: {e}")
            logging.error(f"测试执行失败: {e}")
            logging.error(traceback.format_exc())