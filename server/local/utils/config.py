"""
提猫直播助手 - 配置管理模块
负责应用配置的加载、验证和管理
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = None):
        """初始化配置"""
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'config.json'
        )
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            # AI服务配置
            'ai_service': 'deepseek',
            'ai_api_key': '',
            'ai_base_url': '',
            'ai_model': '',
            
            # 抖音配置
            'douyin_room_id': '',
            'douyin_cookie': '',
            
            # 应用配置
            'max_comments': 1000,
            'hot_words_limit': 50,
            'script_generation_interval': 300,
            'comment_fetch_interval': 5,
            
            # 缓存配置
            'enable_cache': True,
            'cache_ttl': 300,
            'max_memory_usage': 512,
            
            # 日志配置
            'log_level': 'INFO',
            'log_file': 'logs/app.log',
            'max_log_size': 10,
            
            # 调试配置
            'debug_mode': False,
            'mock_data': False
        }
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    print(f"配置已从 {self.config_file} 加载")
            else:
                print(f"配置文件 {self.config_file} 不存在，使用默认配置")
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config.copy()
    
    def validate(self) -> bool:
        """验证配置"""
        required_keys = ['ai_service', 'douyin_room_id']
        
        for key in required_keys:
            if not self.config.get(key):
                print(f"配置项 {key} 不能为空")
                return False
        
        return True