"""
DouyinLiveWebFetcher API封装 - 配置管理系统

本模块提供统一的配置管理功能，支持：
- JSON配置文件加载
- 环境变量覆盖
- 配置验证和默认值
- 运行时配置更新

配置优先级：环境变量 > JSON文件 > 默认值
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import asdict

from .models import (
    DouyinAPIConfig, DatabaseConfig, RedisConfig, 
    APIConfig, FetcherConfig, ErrorCode, ErrorInfo
)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为项目根目录的config.json
        """
        self.logger = logging.getLogger(__name__)
        
        # 确定配置文件路径
        if config_file is None:
            # 查找项目根目录的config.json
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_file = project_root / "config.json"
        
        self.config_file = Path(config_file)
        self._config: Optional[DouyinAPIConfig] = None
        self._file_config: Dict[str, Any] = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            # 加载JSON配置文件
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._file_config = json.load(f)
                self.logger.info(f"Loaded config from {self.config_file}")
            else:
                self.logger.warning(f"Config file not found: {self.config_file}")
                self._file_config = {}
            
            # 构建完整配置
            self._build_config()
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            # 使用默认配置
            self._config = DouyinAPIConfig()
    
    def _build_config(self) -> None:
        """构建完整配置，合并文件配置和环境变量"""
        try:
            # 从文件配置中提取各部分配置
            douyin_config = self._file_config.get('douyin', {})
            
            # 构建数据库配置
            db_config = self._build_database_config(douyin_config)
            
            # 构建Redis配置
            redis_config = self._build_redis_config()
            
            # 构建API配置
            api_config = self._build_api_config()
            
            # 构建抓取器配置
            fetcher_config = self._build_fetcher_config(douyin_config)
            
            # 构建总配置
            self._config = DouyinAPIConfig(
                app_name=self._get_env_or_default("DOUYIN_APP_NAME", "DouyinLiveAPI"),
                version=self._get_env_or_default("DOUYIN_VERSION", "1.0.0"),
                debug=self._get_bool_env_or_default("DOUYIN_DEBUG", False),
                database=db_config,
                redis=redis_config,
                api=api_config,
                fetcher=fetcher_config
            )
            
            # 验证配置
            if not self._config.validate():
                raise ValueError("Configuration validation failed")
                
            self.logger.info("Configuration built successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to build config: {e}")
            # 使用默认配置
            self._config = DouyinAPIConfig()
    
    def _build_database_config(self, douyin_config: Dict[str, Any]) -> DatabaseConfig:
        """构建数据库配置"""
        # 从现有config.json中查找数据库配置
        # 根据项目结构，可能在不同位置
        db_config_data = {}
        
        # 尝试从多个可能的位置获取数据库配置
        possible_paths = [
            self._file_config.get('database', {}),
            self._file_config.get('db', {}),
            douyin_config.get('database', {}),
            douyin_config.get('db', {})
        ]
        
        for config_data in possible_paths:
            if config_data:
                db_config_data = config_data
                break
        
        return DatabaseConfig(
            host=self._get_env_or_default("DB_HOST", db_config_data.get('host', 'localhost')),
            port=int(self._get_env_or_default("DB_PORT", db_config_data.get('port', 5432))),
            database=self._get_env_or_default("DB_NAME", db_config_data.get('database', 'douyin_live')),
            username=self._get_env_or_default("DB_USER", db_config_data.get('username', 'postgres')),
            password=self._get_env_or_default("DB_PASSWORD", db_config_data.get('password', '')),
            pool_size=int(self._get_env_or_default("DB_POOL_SIZE", db_config_data.get('pool_size', 10))),
            pool_timeout=int(self._get_env_or_default("DB_POOL_TIMEOUT", db_config_data.get('pool_timeout', 30)))
        )
    
    def _build_redis_config(self) -> RedisConfig:
        """构建Redis配置"""
        # 从缓存配置中获取Redis信息
        cache_config = self._file_config.get('cache', {})
        
        return RedisConfig(
            host=self._get_env_or_default("REDIS_HOST", cache_config.get('host', 'localhost')),
            port=int(self._get_env_or_default("REDIS_PORT", cache_config.get('port', 6379))),
            database=int(self._get_env_or_default("REDIS_DB", cache_config.get('database', 0))),
            password=self._get_env_or_default("REDIS_PASSWORD", cache_config.get('password', '')),
            max_connections=int(self._get_env_or_default("REDIS_MAX_CONN", cache_config.get('max_connections', 20))),
            socket_timeout=int(self._get_env_or_default("REDIS_TIMEOUT", cache_config.get('socket_timeout', 5)))
        )
    
    def _build_api_config(self) -> APIConfig:
        """构建API配置"""
        server_config = self._file_config.get('server', {})
        
        return APIConfig(
            host=self._get_env_or_default("API_HOST", server_config.get('host', '0.0.0.0')),
            port=int(self._get_env_or_default("API_PORT", server_config.get('port', 8000))),
            debug=self._get_bool_env_or_default("API_DEBUG", server_config.get('debug', False)),
            cors_origins=self._get_list_env_or_default("API_CORS_ORIGINS", server_config.get('cors_origins', [])),
            rate_limit=int(self._get_env_or_default("API_RATE_LIMIT", server_config.get('rate_limit', 100)))
        )
    
    def _build_fetcher_config(self, douyin_config: Dict[str, Any]) -> FetcherConfig:
        """构建抓取器配置"""
        return FetcherConfig(
            reconnect_interval=int(self._get_env_or_default(
                "FETCHER_RECONNECT_INTERVAL", 
                douyin_config.get('reconnect_interval', 5)
            )),
            max_reconnect_times=int(self._get_env_or_default(
                "FETCHER_MAX_RECONNECT", 
                douyin_config.get('max_reconnect_times', 3)
            )),
            message_buffer_size=int(self._get_env_or_default(
                "FETCHER_BUFFER_SIZE", 
                douyin_config.get('message_buffer_size', 1000)
            )),
            timeout=int(self._get_env_or_default(
                "FETCHER_TIMEOUT", 
                douyin_config.get('timeout', 30)
            )),
            enable_heartbeat=self._get_bool_env_or_default(
                "FETCHER_HEARTBEAT", 
                douyin_config.get('enable_heartbeat', True)
            ),
            heartbeat_interval=int(self._get_env_or_default(
                "FETCHER_HEARTBEAT_INTERVAL", 
                douyin_config.get('heartbeat_interval', 30)
            ))
        )
    
    def _get_env_or_default(self, env_key: str, default_value: Any) -> str:
        """获取环境变量或默认值"""
        return os.getenv(env_key, str(default_value))
    
    def _get_bool_env_or_default(self, env_key: str, default_value: bool) -> bool:
        """获取布尔型环境变量或默认值"""
        env_value = os.getenv(env_key)
        if env_value is None:
            return default_value
        return env_value.lower() in ('true', '1', 'yes', 'on')
    
    def _get_list_env_or_default(self, env_key: str, default_value: list) -> list:
        """获取列表型环境变量或默认值"""
        env_value = os.getenv(env_key)
        if env_value is None:
            return default_value
        return [item.strip() for item in env_value.split(',') if item.strip()]
    
    @property
    def config(self) -> DouyinAPIConfig:
        """获取配置对象"""
        if self._config is None:
            self._config = DouyinAPIConfig()
        return self._config
    
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return self.config.database
    
    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return self.config.redis
    
    def get_api_config(self) -> APIConfig:
        """获取API配置"""
        return self.config.api
    
    def get_fetcher_config(self) -> FetcherConfig:
        """获取抓取器配置"""
        return self.config.fetcher
    
    def update_config(self, **kwargs) -> bool:
        """
        运行时更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新配置对象
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            
            # 验证更新后的配置
            if not self._config.validate():
                self.logger.error("Updated configuration is invalid")
                return False
            
            self.logger.info(f"Configuration updated: {kwargs}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def save_config(self, file_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            file_path: 保存路径，默认为原配置文件
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if file_path is None:
                file_path = self.config_file
            
            config_dict = asdict(self._config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Configuration saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        重新加载配置
        
        Returns:
            bool: 重新加载是否成功
        """
        try:
            self._load_config()
            self.logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload config: {e}")
            return False
    
    def validate_config(self) -> tuple[bool, str]:
        """
        验证当前配置
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if self._config is None:
                return False, "Configuration not loaded"
            
            if not self._config.validate():
                return False, "Configuration validation failed"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要（隐藏敏感信息）"""
        if self._config is None:
            return {}
        
        config_dict = asdict(self._config)
        
        # 隐藏敏感信息
        if 'database' in config_dict and 'password' in config_dict['database']:
            config_dict['database']['password'] = '***'
        
        if 'redis' in config_dict and 'password' in config_dict['redis']:
            config_dict['redis']['password'] = '***'
        
        return config_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值或默认值
        """
        try:
            # 首先尝试从文件配置中获取
            if key in self._file_config:
                return self._file_config[key]
            
            # 然后尝试从环境变量获取
            env_value = os.getenv(key.upper())
            if env_value is not None:
                return env_value
            
            # 最后返回默认值
            return default
            
        except Exception as e:
            self.logger.error(f"Failed to get config key '{key}': {e}")
            return default


# ================================
# 全局配置管理器实例
# ================================

# 创建全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def get_config() -> DouyinAPIConfig:
    """获取配置对象"""
    return get_config_manager().config


def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return get_config_manager().get_database_config()


def get_redis_config() -> RedisConfig:
    """获取Redis配置"""
    return get_config_manager().get_redis_config()


def get_api_config() -> APIConfig:
    """获取API配置"""
    return get_config_manager().get_api_config()


def get_fetcher_config() -> FetcherConfig:
    """获取抓取器配置"""
    return get_config_manager().get_fetcher_config()


# ================================
# 配置验证工具
# ================================

def validate_database_connection(config: DatabaseConfig) -> tuple[bool, str]:
    """
    验证数据库连接配置
    
    Args:
        config: 数据库配置
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        # 基础验证
        if not config.validate():
            return False, "Database configuration validation failed"
        
        # 连接测试（这里只做基础检查，实际连接测试在数据库模块中进行）
        if not config.host:
            return False, "Database host is required"
        
        if not config.database:
            return False, "Database name is required"
        
        if not config.username:
            return False, "Database username is required"
        
        return True, "Database configuration is valid"
        
    except Exception as e:
        return False, f"Database configuration error: {str(e)}"


def validate_redis_connection(config: RedisConfig) -> tuple[bool, str]:
    """
    验证Redis连接配置
    
    Args:
        config: Redis配置
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        # 基础验证
        if not config.validate():
            return False, "Redis configuration validation failed"
        
        # 端口范围检查
        if not (0 <= config.port <= 65535):
            return False, "Redis port must be between 0 and 65535"
        
        # 数据库编号检查
        if not (0 <= config.database <= 15):
            return False, "Redis database must be between 0 and 15"
        
        return True, "Redis configuration is valid"
        
    except Exception as e:
        return False, f"Redis configuration error: {str(e)}"


# ================================
# 全局配置管理函数
# ================================

# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def load_config(config_file: Optional[str] = None) -> DouyinAPIConfig:
    """
    加载配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        DouyinAPIConfig: 配置对象
    """
    if config_file:
        manager = ConfigManager(config_file)
    else:
        manager = get_config_manager()
    return manager.get_config()


def validate_config(config: DouyinAPIConfig) -> tuple[bool, str]:
    """
    验证完整配置
    
    Args:
        config: 配置对象
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        # 验证数据库配置
        db_valid, db_msg = validate_database_connection(config.database)
        if not db_valid:
            return False, f"Database config error: {db_msg}"
        
        # 验证Redis配置
        redis_valid, redis_msg = validate_redis_connection(config.redis)
        if not redis_valid:
            return False, f"Redis config error: {redis_msg}"
        
        # 验证API配置
        if not config.api.validate():
            return False, "API configuration validation failed"
        
        # 验证抓取器配置
        if not config.fetcher.validate():
            return False, "Fetcher configuration validation failed"
        
        return True, "Configuration is valid"
        
    except Exception as e:
        return False, f"Configuration validation error: {str(e)}"