#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理AST增强算法的配置和词库数据

主要功能:
1. 配置文件加载和验证
2. 词库数据管理
3. 运行时配置更新
4. 配置缓存和优化
5. 环境适配和部署配置
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import threading

# 配置文件路径
CONFIG_DIR = Path(__file__).parent / "config"
EMOTION_VOCAB_FILE = CONFIG_DIR / "emotion_vocabulary.json"
ALGORITHM_CONFIG_FILE = CONFIG_DIR / "algorithm_config.json"

@dataclass
class ConfigInfo:
    """配置信息"""
    version: str
    description: str
    last_updated: str
    file_path: str
    is_loaded: bool = False
    load_time: Optional[float] = None

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_emotion_vocabulary(self, config: Dict[str, Any]) -> bool:
        """验证情感词汇配置"""
        try:
            # 检查必需的顶级键
            required_keys = ["meta", "emotion_expressions", "product_vocabulary", 
                           "slang_vocabulary", "context_patterns"]
            for key in required_keys:
                if key not in config:
                    self.logger.error(f"缺少必需的配置键: {key}")
                    return False
            
            # 验证meta信息
            meta = config["meta"]
            if not all(k in meta for k in ["version", "description", "total_words"]):
                self.logger.error("meta信息不完整")
                return False
            
            # 验证情感表达词汇
            emotions = config["emotion_expressions"]
            for emotion_type, categories in emotions.items():
                for category, words in categories.items():
                    if not isinstance(words, list):
                        self.logger.error(f"情感词汇格式错误: {emotion_type}.{category}")
                        return False
                    
                    for word_info in words:
                        if not all(k in word_info for k in ["word", "frequency", "intensity"]):
                            self.logger.error(f"词汇信息不完整: {word_info}")
                            return False
                        
                        # 验证数值范围
                        if not (0.0 <= word_info["frequency"] <= 1.0):
                            self.logger.error(f"频率值超出范围: {word_info['frequency']}")
                            return False
                        
                        if not (0.0 <= word_info["intensity"] <= 1.0):
                            self.logger.error(f"强度值超出范围: {word_info['intensity']}")
                            return False
            
            self.logger.info("情感词汇配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"情感词汇配置验证失败: {e}")
            return False
    
    def validate_algorithm_config(self, config: Dict[str, Any]) -> bool:
        """验证算法配置"""
        try:
            # 检查必需的顶级键
            required_keys = ["meta", "audio_processing", "confidence_calculation", 
                           "emotion_analysis", "text_postprocessing", "adaptive_threshold"]
            for key in required_keys:
                if key not in config:
                    self.logger.error(f"缺少必需的配置键: {key}")
                    return False
            
            # 验证音频处理配置
            audio_config = config["audio_processing"]
            if audio_config["sample_rate"] not in [8000, 16000, 22050, 44100]:
                self.logger.warning(f"非标准采样率: {audio_config['sample_rate']}")
            
            # 验证置信度权重
            confidence_weights = config["confidence_calculation"]["weights"]
            total_weight = sum(confidence_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                self.logger.error(f"置信度权重总和不为1.0: {total_weight}")
                return False
            
            # 验证阈值配置
            threshold_config = config["adaptive_threshold"]
            if not (0.0 <= threshold_config["base_threshold"] <= 1.0):
                self.logger.error(f"基础阈值超出范围: {threshold_config['base_threshold']}")
                return False
            
            limits = threshold_config["adjustment_limits"]
            if limits["min_threshold"] >= limits["max_threshold"]:
                self.logger.error("阈值限制配置错误: min >= max")
                return False
            
            self.logger.info("算法配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"算法配置验证失败: {e}")
            return False

class ConfigCache:
    """配置缓存"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_count = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # 移除最少使用的项
                least_used = min(self.access_count.items(), key=lambda x: x[1])
                del self.cache[least_used[0]]
                del self.access_count[least_used[0]]
            
            self.cache[key] = value
            self.access_count[key] = 1
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()

class EnhancedConfigManager:
    """增强版配置管理器"""
    
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self.cache = ConfigCache() if enable_cache else None
        self.validator = ConfigValidator()
        
        # 配置信息
        self.config_info = {}
        self.loaded_configs = {}
        
        # 线程锁
        self.lock = threading.RLock()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("配置管理器已初始化")
        
        # 自动加载配置
        self._initialize_configs()
    
    def _initialize_configs(self):
        """初始化配置"""
        try:
            # 确保配置目录存在
            CONFIG_DIR.mkdir(exist_ok=True)
            
            # 加载情感词汇配置
            self.load_emotion_vocabulary()
            
            # 加载算法配置
            self.load_algorithm_config()
            
            self.logger.info("配置初始化完成")
            
        except Exception as e:
            self.logger.error(f"配置初始化失败: {e}")
    
    def load_emotion_vocabulary(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载情感词汇配置"""
        cache_key = "emotion_vocabulary"
        
        if not force_reload and self.enable_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        try:
            with self.lock:
                if not EMOTION_VOCAB_FILE.exists():
                    self.logger.error(f"情感词汇文件不存在: {EMOTION_VOCAB_FILE}")
                    return {}
                
                with open(EMOTION_VOCAB_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 验证配置
                if not self.validator.validate_emotion_vocabulary(config):
                    self.logger.error("情感词汇配置验证失败")
                    return {}
                
                # 更新配置信息
                self.config_info[cache_key] = ConfigInfo(
                    version=config["meta"]["version"],
                    description=config["meta"]["description"],
                    last_updated=config["meta"]["last_updated"],
                    file_path=str(EMOTION_VOCAB_FILE),
                    is_loaded=True,
                    load_time=self._get_current_time()
                )
                
                self.loaded_configs[cache_key] = config
                
                # 缓存配置
                if self.enable_cache and self.cache:
                    self.cache.set(cache_key, config)
                
                self.logger.info("情感词汇配置加载成功")
                return config
                
        except Exception as e:
            self.logger.error(f"加载情感词汇配置失败: {e}")
            return {}
    
    def load_algorithm_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载算法配置"""
        cache_key = "algorithm_config"
        
        if not force_reload and self.enable_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        try:
            with self.lock:
                if not ALGORITHM_CONFIG_FILE.exists():
                    self.logger.error(f"算法配置文件不存在: {ALGORITHM_CONFIG_FILE}")
                    return {}
                
                with open(ALGORITHM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 验证配置
                if not self.validator.validate_algorithm_config(config):
                    self.logger.error("算法配置验证失败")
                    return {}
                
                # 更新配置信息
                self.config_info[cache_key] = ConfigInfo(
                    version=config["meta"]["version"],
                    description=config["meta"]["description"],
                    last_updated=config["meta"]["last_updated"],
                    file_path=str(ALGORITHM_CONFIG_FILE),
                    is_loaded=True,
                    load_time=self._get_current_time()
                )
                
                self.loaded_configs[cache_key] = config
                
                # 缓存配置
                if self.enable_cache and self.cache:
                    self.cache.set(cache_key, config)
                
                self.logger.info("算法配置加载成功")
                return config
                
        except Exception as e:
            self.logger.error(f"加载算法配置失败: {e}")
            return {}
    
    def get_emotion_words(self, emotion_type: str, category: str = "high_frequency") -> List[Dict[str, Any]]:
        """获取指定情感类型的词汇"""
        config = self.load_emotion_vocabulary()
        if not config:
            return []
        
        try:
            return config["emotion_expressions"][emotion_type][category]
        except KeyError:
            self.logger.warning(f"未找到情感词汇: {emotion_type}.{category}")
            return []
    
    def get_product_vocabulary(self, category: str, subcategory: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取产品词汇"""
        config = self.load_emotion_vocabulary()
        if not config:
            return []
        
        try:
            if subcategory:
                return config["product_vocabulary"][category][subcategory]
            else:
                return config["product_vocabulary"][category]
        except KeyError:
            self.logger.warning(f"未找到产品词汇: {category}.{subcategory}")
            return []
    
    def get_slang_vocabulary(self, category: str = "popular_terms") -> List[Dict[str, Any]]:
        """获取网络用语词汇"""
        config = self.load_emotion_vocabulary()
        if not config:
            return []
        
        try:
            return config["slang_vocabulary"][category]
        except KeyError:
            self.logger.warning(f"未找到网络用语: {category}")
            return []
    
    def get_algorithm_config(self, section: Optional[str] = None) -> Union[Dict[str, Any], Any]:
        """获取算法配置"""
        config = self.load_algorithm_config()
        if not config:
            return {}
        
        if section:
            return config.get(section, {})
        return config
    
    def get_audio_processing_config(self) -> Dict[str, Any]:
        """获取音频处理配置"""
        return self.get_algorithm_config("audio_processing")
    
    def get_confidence_calculation_config(self) -> Dict[str, Any]:
        """获取置信度计算配置"""
        return self.get_algorithm_config("confidence_calculation")
    
    def get_emotion_analysis_config(self) -> Dict[str, Any]:
        """获取情感分析配置"""
        return self.get_algorithm_config("emotion_analysis")
    
    def get_text_postprocessing_config(self) -> Dict[str, Any]:
        """获取文本后处理配置"""
        return self.get_algorithm_config("text_postprocessing")
    
    def get_adaptive_threshold_config(self) -> Dict[str, Any]:
        """获取自适应阈值配置"""
        return self.get_algorithm_config("adaptive_threshold")
    
    def get_performance_targets(self) -> Dict[str, Any]:
        """获取性能目标配置"""
        return self.get_algorithm_config("performance_targets")
    
    def update_config(self, config_type: str, section: str, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            with self.lock:
                if config_type == "algorithm":
                    config = self.loaded_configs.get("algorithm_config", {})
                elif config_type == "vocabulary":
                    config = self.loaded_configs.get("emotion_vocabulary", {})
                else:
                    self.logger.error(f"未知配置类型: {config_type}")
                    return False
                
                if section in config:
                    config[section].update(updates)
                    self.logger.info(f"配置更新成功: {config_type}.{section}")
                    
                    # 清除缓存
                    if self.enable_cache and self.cache:
                        cache_key = f"{config_type}_config" if config_type == "algorithm" else "emotion_vocabulary"
                        self.cache.set(cache_key, config)
                    
                    return True
                else:
                    self.logger.error(f"配置节不存在: {section}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            return False
    
    def reload_all_configs(self) -> bool:
        """重新加载所有配置"""
        try:
            self.logger.info("开始重新加载所有配置")
            
            # 清除缓存
            if self.enable_cache and self.cache:
                self.cache.clear()
            
            # 重新加载配置
            emotion_config = self.load_emotion_vocabulary(force_reload=True)
            algorithm_config = self.load_algorithm_config(force_reload=True)
            
            success = bool(emotion_config and algorithm_config)
            
            if success:
                self.logger.info("所有配置重新加载成功")
            else:
                self.logger.error("配置重新加载失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, ConfigInfo]:
        """获取配置信息"""
        return self.config_info.copy()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self.enable_cache or not self.cache:
            return {"cache_enabled": False}
        
        return {
            "cache_enabled": True,
            "cache_size": len(self.cache.cache),
            "max_size": self.cache.max_size,
            "cache_keys": list(self.cache.cache.keys()),
            "access_counts": self.cache.access_count.copy()
        }
    
    def _get_current_time(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()

# 全局配置管理器实例
_config_manager = None
_config_manager_lock = threading.Lock()

def get_config_manager() -> EnhancedConfigManager:
    """获取全局配置管理器实例（单例模式）"""
    global _config_manager
    
    if _config_manager is None:
        with _config_manager_lock:
            if _config_manager is None:
                _config_manager = EnhancedConfigManager()
    
    return _config_manager

# 便捷函数
def get_emotion_words(emotion_type: str, category: str = "high_frequency") -> List[Dict[str, Any]]:
    """便捷函数：获取情感词汇"""
    return get_config_manager().get_emotion_words(emotion_type, category)

def get_algorithm_config(section: Optional[str] = None) -> Union[Dict[str, Any], Any]:
    """便捷函数：获取算法配置"""
    return get_config_manager().get_algorithm_config(section)

def reload_configs() -> bool:
    """便捷函数：重新加载配置"""
    return get_config_manager().reload_all_configs()

# 导出主要类和函数
__all__ = [
    'EnhancedConfigManager',
    'ConfigValidator',
    'ConfigCache',
    'ConfigInfo',
    'get_config_manager',
    'get_emotion_words',
    'get_algorithm_config',
    'reload_configs'
]