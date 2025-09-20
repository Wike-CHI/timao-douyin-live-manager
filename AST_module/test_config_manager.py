#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器测试模块
测试配置加载、验证、缓存等功能的正确性
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from config_manager import EnhancedConfigManager, ConfigValidator, ConfigCache


class TestConfigManager(unittest.TestCase):
    """配置管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = EnhancedConfigManager(enable_cache=True)
        
        # 创建测试配置文件
        self.test_algorithm_config = {
            "audio_processing": {
                "sample_rate": 16000,
                "chunk_size": 1024,
                "spectral_gate": {
                    "enabled": True,
                    "stationary_threshold": 0.5,
                    "non_stationary_threshold": 0.3
                }
            },
            "confidence_calculation": {
                "base_weight": 0.4,
                "acoustic_weight": 0.3,
                "linguistic_weight": 0.3,
                "min_confidence_threshold": 0.6
            }
        }
        
        self.test_emotion_vocabulary = {
            "emotional_expressions": ["开心", "激动", "惊喜"],
            "product_keywords": ["口红", "眼影", "粉底"],
            "interaction_phrases": ["宝贝们", "家人们", "小仙女们"]
        }
        
        # 写入测试文件
        self.algorithm_config_path = os.path.join(self.temp_dir, "algorithm_config.json")
        self.emotion_vocab_path = os.path.join(self.temp_dir, "emotion_vocabulary.json")
        
        with open(self.algorithm_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_algorithm_config, f, ensure_ascii=False, indent=2)
            
        with open(self.emotion_vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_emotion_vocabulary, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_algorithm_config_success(self):
        """测试成功加载算法配置"""
        with patch.object(self.config_manager, '_get_config_path') as mock_path:
            mock_path.return_value = self.algorithm_config_path
            
            config = self.config_manager.load_algorithm_config()
            
            self.assertIsNotNone(config)
            self.assertEqual(config['audio_processing']['sample_rate'], 16000)
            self.assertTrue(config['audio_processing']['spectral_gate']['enabled'])
            self.assertEqual(config['confidence_calculation']['base_weight'], 0.4)
    
    def test_load_emotion_vocabulary_success(self):
        """测试成功加载情感词库"""
        with patch.object(self.config_manager, '_get_config_path') as mock_path:
            mock_path.return_value = self.emotion_vocab_path
            
            vocab = self.config_manager.load_emotion_vocabulary()
            
            self.assertIsNotNone(vocab)
            self.assertIn("emotional_expressions", vocab)
            self.assertIn("开心", vocab["emotional_expressions"])
            self.assertIn("口红", vocab["product_keywords"])
    
    def test_config_validation(self):
        """测试配置验证功能"""
        validator = ConfigValidator()
        
        # 测试有效配置
        self.assertTrue(validator.validate_algorithm_config(self.test_algorithm_config))
        self.assertTrue(validator.validate_emotion_vocabulary(self.test_emotion_vocabulary))
        
        # 测试无效配置
        invalid_config = {"invalid": "config"}
        self.assertFalse(validator.validate_algorithm_config(invalid_config))
        self.assertFalse(validator.validate_emotion_vocabulary(invalid_config))
    
    def test_config_cache(self):
        """测试配置缓存功能"""
        cache = ConfigCache()
        
        # 测试缓存存储和获取
        test_data = {"test": "data"}
        cache.set("test_key", test_data)
        
        cached_data = cache.get("test_key")
        self.assertEqual(cached_data, test_data)
        
        # 测试缓存过期
        cache.set("expired_key", test_data)
        import time
        time.sleep(0.2)
        
        expired_data = cache.get("expired_key")
        self.assertIsNone(expired_data)
    
    def test_file_not_found_handling(self):
        """测试文件不存在的处理"""
        with patch.object(self.config_manager, '_get_config_path') as mock_path:
            mock_path.return_value = "non_existent_file.json"
            
            with self.assertRaises(FileNotFoundError):
                self.config_manager.load_algorithm_config()
    
    def test_invalid_json_handling(self):
        """测试无效JSON文件的处理"""
        invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write("invalid json content")
        
        with patch.object(self.config_manager, '_get_config_path') as mock_path:
            mock_path.return_value = invalid_json_path
            
            with self.assertRaises(json.JSONDecodeError):
                self.config_manager.load_algorithm_config()
    
    def test_cache_disabled(self):
        """测试禁用缓存的情况"""
        config_manager_no_cache = EnhancedConfigManager(enable_cache=False)
        self.assertIsNone(config_manager_no_cache.cache)
    
    def test_force_reload(self):
        """测试强制重新加载配置"""
        with patch.object(self.config_manager, '_get_config_path') as mock_path:
            mock_path.return_value = self.algorithm_config_path
            
            # 首次加载
            config1 = self.config_manager.load_algorithm_config()
            
            # 修改配置文件
            modified_config = self.test_algorithm_config.copy()
            modified_config['audio_processing']['sample_rate'] = 44100
            
            with open(self.algorithm_config_path, 'w', encoding='utf-8') as f:
                json.dump(modified_config, f, ensure_ascii=False, indent=2)
            
            # 强制重新加载
            config2 = self.config_manager.load_algorithm_config(force_reload=True)
            
            self.assertEqual(config2['audio_processing']['sample_rate'], 44100)


class TestAccuracyBenchmark(unittest.TestCase):
    """准确率基准测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_audio_samples = [
            {
                "audio_file": "test_emotion_1.wav",
                "expected_text": "宝贝们今天这个口红真的超级好看",
                "expected_confidence": 0.85,
                "scenario": "情感表达"
            },
            {
                "audio_file": "test_product_1.wav", 
                "expected_text": "这款粉底液遮瑕效果特别棒",
                "expected_confidence": 0.80,
                "scenario": "产品介绍"
            },
            {
                "audio_file": "test_interaction_1.wav",
                "expected_text": "有想要的小仙女们可以点击下方链接",
                "expected_confidence": 0.78,
                "scenario": "互动引导"
            }
        ]
    
    def test_accuracy_calculation(self):
        """测试准确率计算"""
        # 模拟转录结果
        actual_results = [
            {"text": "宝贝们今天这个口红真的超级好看", "confidence": 0.87},
            {"text": "这款粉底液遮瑕效果特别好", "confidence": 0.82},  # 部分匹配
            {"text": "有想要的小仙女们可以点击下方链接", "confidence": 0.79}
        ]
        
        # 计算准确率指标
        word_accuracy = self._calculate_word_accuracy(
            [sample["expected_text"] for sample in self.test_audio_samples],
            [result["text"] for result in actual_results]
        )
        
        confidence_accuracy = self._calculate_confidence_accuracy(
            [sample["expected_confidence"] for sample in self.test_audio_samples],
            [result["confidence"] for result in actual_results]
        )
        
        self.assertGreater(word_accuracy, 0.8)  # 要求词汇准确率>80%
        self.assertGreater(confidence_accuracy, 0.9)  # 要求置信度准确率>90%
    
    def _calculate_word_accuracy(self, expected_texts, actual_texts):
        """计算词汇准确率"""
        total_accuracy = 0
        for expected, actual in zip(expected_texts, actual_texts):
            expected_words = set(expected.split())
            actual_words = set(actual.split())
            
            if len(expected_words) == 0:
                accuracy = 1.0 if len(actual_words) == 0 else 0.0
            else:
                intersection = expected_words.intersection(actual_words)
                accuracy = len(intersection) / len(expected_words)
            
            total_accuracy += accuracy
        
        return total_accuracy / len(expected_texts) if expected_texts else 0
    
    def _calculate_confidence_accuracy(self, expected_confidences, actual_confidences):
        """计算置信度准确率"""
        total_accuracy = 0
        for expected, actual in zip(expected_confidences, actual_confidences):
            # 允许10%的误差范围
            accuracy = 1.0 if abs(expected - actual) <= 0.1 else 0.0
            total_accuracy += accuracy
        
        return total_accuracy / len(expected_confidences) if expected_confidences else 0


if __name__ == '__main__':
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加配置管理器测试
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConfigManager))
    
    # 添加准确率基准测试
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestAccuracyBenchmark))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print(f"测试完成: 运行 {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"{'='*50}")