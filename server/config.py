"""
提猫直播助手 - 配置管理模块
负责应用配置的加载、验证和管理
"""

import os
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path

from server.utils.helpers import read_json_file, write_json_file, safe_get


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    secret_key: str = "your-secret-key-here"
    cors_origins: list = field(default_factory=lambda: ["*"])
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    
    # WebSocket配置
    websocket_enabled: bool = True
    websocket_cors_allowed_origins: list = field(default_factory=lambda: ["*"])
    websocket_ping_timeout: int = 60
    websocket_ping_interval: int = 25


@dataclass
class AIConfig:
    """AI配置"""
    # OpenAI配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    
    # 通义千问配置
    qwen_api_key: str = ""
    qwen_model: str = "qwen-turbo"
    
    # 百度文心配置
    baidu_api_key: str = ""
    baidu_secret_key: str = ""
    baidu_model: str = "ERNIE-Bot-turbo"
    
    # 默认AI服务商
    default_provider: str = "openai"  # openai, qwen, baidu
    
    # 话术生成配置
    script_max_length: int = 200
    script_temperature: float = 0.8
    script_batch_size: int = 5
    script_retry_times: int = 3
    
    # 情感分析配置
    sentiment_enabled: bool = True
    sentiment_threshold: float = 0.6


@dataclass
class CommentConfig:
    """评论处理配置"""
    # 评论队列配置
    max_queue_size: int = 1000
    process_interval: float = 0.1
    batch_size: int = 10
    
    # 热词统计配置
    hotword_min_length: int = 2
    hotword_max_length: int = 10
    hotword_min_count: int = 2
    hotword_time_window: int = 300  # 5分钟
    hotword_max_count: int = 50
    
    # 过滤配置
    filter_enabled: bool = True
    filter_keywords: list = field(default_factory=lambda: ["广告", "刷屏", "垃圾"])
    filter_min_length: int = 1
    filter_max_length: int = 500
    
    # 模拟配置（用于测试）
    simulation_enabled: bool = False
    simulation_interval: float = 2.0
    simulation_comments: list = field(default_factory=lambda: [
        "主播好棒！", "这个产品不错", "价格怎么样？", "有优惠吗？",
        "质量好吗？", "包邮吗？", "什么时候发货？", "支持退换吗？"
    ])


@dataclass
class UIConfig:
    """UI配置"""
    # 主题配置
    theme: str = "light"  # light, dark, auto
    primary_color: str = "#1890ff"
    success_color: str = "#52c41a"
    warning_color: str = "#faad14"
    error_color: str = "#f5222d"
    
    # 布局配置
    sidebar_width: int = 250
    header_height: int = 60
    footer_height: int = 40
    
    # 数据展示配置
    comments_per_page: int = 50
    hotwords_display_count: int = 20
    scripts_per_page: int = 20
    
    # 刷新间隔（毫秒）
    comment_refresh_interval: int = 1000
    hotword_refresh_interval: int = 5000
    script_refresh_interval: int = 10000
    
    # 动画配置
    animation_enabled: bool = True
    animation_duration: int = 300


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/app.log"
    file_max_size: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5
    console_enabled: bool = True


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # 数据库类型
    db_type: str = "mysql"  # mysql 或 sqlite
    
    # MySQL配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "timao"
    mysql_password: str = ""
    mysql_database: str = "timao_live"
    mysql_charset: str = "utf8mb4"
    
    # SQLite配置（备用）
    sqlite_path: str = "data/app.db"
    sqlite_timeout: int = 30
    
    # 连接池配置
    pool_size: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True  # 连接前测试
    max_overflow: int = 10  # 最大溢出连接数
    
    # 备份配置
    backup_enabled: bool = True
    backup_interval: int = 3600  # 1小时
    backup_keep_days: int = 7

    # 自动建库配置
    mysql_auto_create_db: bool = True


@dataclass
class SecurityConfig:
    """安全配置"""
    # API安全
    api_rate_limit: int = 100  # 每分钟请求数
    api_key_required: bool = False
    api_key: str = ""
    
    # CORS配置
    cors_enabled: bool = True
    cors_origins: list = field(default_factory=lambda: ["*"])
    cors_methods: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_headers: list = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    # 加密配置
    encryption_enabled: bool = False
    encryption_key: str = ""


@dataclass
class RedisConfig:
    """
Redis缓存配置"""
    # 基本配置
    enabled: bool = True
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    
    # 连接池配置
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    
    # 缓存配置
    default_ttl: int = 3600  # 默认过期时间（秒）
    key_prefix: str = "timao:"  # 键前缀
    
    # 重连配置
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class AppConfig:
    """应用总配置"""
    server: ServerConfig = field(default_factory=ServerConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    comment: CommentConfig = field(default_factory=CommentConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    log: LogConfig = field(default_factory=LogConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # 应用信息
    app_name: str = "提猫直播助手"
    app_version: str = "1.0.0"
    app_description: str = "智能直播评论分析和话术生成助手"
    
    # 环境配置
    environment: str = "development"  # development, production, testing
    debug: bool = True


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "app.json"
        self.env_file = Path(".env")
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 从环境变量覆盖配置
        self._load_env_variables()
    
    def _load_config(self) -> AppConfig:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                config_data = read_json_file(str(self.config_file))
                return self._dict_to_config(config_data)
            else:
                # 创建默认配置
                default_config = AppConfig()
                self.save_config(default_config)
                return default_config
                
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")
            return AppConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """字典转配置对象"""
        try:
            # 递归处理嵌套配置
            config_dict = {}
            
            for key, value in data.items():
                if key == "server" and isinstance(value, dict):
                    config_dict[key] = ServerConfig(**value)
                elif key == "ai" and isinstance(value, dict):
                    config_dict[key] = AIConfig(**value)
                elif key == "comment" and isinstance(value, dict):
                    config_dict[key] = CommentConfig(**value)
                elif key == "ui" and isinstance(value, dict):
                    config_dict[key] = UIConfig(**value)
                elif key == "log" and isinstance(value, dict):
                    config_dict[key] = LogConfig(**value)
                elif key == "database" and isinstance(value, dict):
                    config_dict[key] = DatabaseConfig(**value)
                elif key == "security" and isinstance(value, dict):
                    config_dict[key] = SecurityConfig(**value)
                else:
                    config_dict[key] = value
            
            return AppConfig(**config_dict)
            
        except Exception as e:
            print(f"配置转换失败: {e}")
            return AppConfig()
    
    def _load_env_variables(self):
        """从环境变量加载配置"""
        try:
            # 加载.env文件
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            
            # 覆盖配置
            env_mappings = {
                # 服务器配置
                'SERVER_HOST': ('server', 'host'),
                'SERVER_PORT': ('server', 'port', int),
                'SERVER_DEBUG': ('server', 'debug', bool),
                'SECRET_KEY': ('server', 'secret_key'),
                
                # AI配置
                'OPENAI_API_KEY': ('ai', 'openai_api_key'),
                'OPENAI_BASE_URL': ('ai', 'openai_base_url'),
                'OPENAI_MODEL': ('ai', 'openai_model'),
                'QWEN_API_KEY': ('ai', 'qwen_api_key'),
                'BAIDU_API_KEY': ('ai', 'baidu_api_key'),
                'BAIDU_SECRET_KEY': ('ai', 'baidu_secret_key'),
                'AI_PROVIDER': ('ai', 'default_provider'),
                
                # 数据库配置
                'DB_TYPE': ('database', 'db_type'),
                'MYSQL_HOST': ('database', 'mysql_host'),
                'MYSQL_PORT': ('database', 'mysql_port', int),
                'MYSQL_USER': ('database', 'mysql_user'),
                'MYSQL_PASSWORD': ('database', 'mysql_password'),
                'MYSQL_DATABASE': ('database', 'mysql_database'),
                'DATABASE_PATH': ('database', 'sqlite_path'),
                
                # Redis配置
                'REDIS_ENABLED': ('redis', 'enabled', bool),
                'REDIS_HOST': ('redis', 'host'),
                'REDIS_PORT': ('redis', 'port', int),
                'REDIS_DB': ('redis', 'db', int),
                'REDIS_PASSWORD': ('redis', 'password'),
                'REDIS_MAX_CONNECTIONS': ('redis', 'max_connections', int),
                'REDIS_CACHE_TTL': ('redis', 'default_ttl', int),
                
                # 安全配置
                'API_KEY': ('security', 'api_key'),
                'API_RATE_LIMIT': ('security', 'api_rate_limit', int),
                
                # 应用配置
                'ENVIRONMENT': ('environment',),
                'DEBUG': ('debug', bool),
            }
            
            for env_key, config_path in env_mappings.items():
                env_value = os.getenv(env_key)
                if env_value is not None:
                    self._set_config_value(config_path, env_value)
                    
        except Exception as e:
            print(f"加载环境变量失败: {e}")
    
    def _set_config_value(self, path: tuple, value: str):
        """设置配置值"""
        try:
            # 获取类型转换函数
            convert_func = str
            if len(path) > 2:
                convert_func = path[2]
                path = path[:2]
            
            # 转换值
            if convert_func == bool:
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif convert_func == int:
                value = int(value)
            elif convert_func == float:
                value = float(value)
            
            # 设置配置值
            if len(path) == 1:
                setattr(self.config, path[0], value)
            elif len(path) == 2:
                section = getattr(self.config, path[0])
                setattr(section, path[1], value)
                
        except Exception as e:
            print(f"设置配置值失败 {path}: {e}")
    
    def save_config(self, config: AppConfig = None):
        """保存配置"""
        try:
            if config is None:
                config = self.config
            
            config_dict = asdict(config)
            write_json_file(str(self.config_file), config_dict)
            print(f"配置已保存到: {self.config_file}")
            
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        try:
            # 深度更新配置
            self._deep_update_config(self.config, updates)
            self.save_config()
            
        except Exception as e:
            print(f"更新配置失败: {e}")
    
    def _deep_update_config(self, config_obj: Any, updates: Dict[str, Any]):
        """深度更新配置对象"""
        for key, value in updates.items():
            if hasattr(config_obj, key):
                current_value = getattr(config_obj, key)
                
                if isinstance(value, dict) and hasattr(current_value, '__dict__'):
                    # 递归更新嵌套对象
                    self._deep_update_config(current_value, value)
                else:
                    # 直接设置值
                    setattr(config_obj, key, value)
    
    def get_section(self, section_name: str) -> Any:
        """获取配置节"""
        return getattr(self.config, section_name, None)
    
    def validate_config(self) -> Dict[str, list]:
        """验证配置"""
        errors = {}
        
        # 验证服务器配置
        server_errors = []
        if not (1 <= self.config.server.port <= 65535):
            server_errors.append("端口号必须在1-65535之间")
        if not self.config.server.secret_key or self.config.server.secret_key == "your-secret-key-here":
            server_errors.append("请设置安全的密钥")
        if server_errors:
            errors["server"] = server_errors
        
        # 验证AI配置
        ai_errors = []
        if self.config.ai.default_provider == "openai" and not self.config.ai.openai_api_key:
            ai_errors.append("使用OpenAI时必须设置API密钥")
        if self.config.ai.default_provider == "qwen" and not self.config.ai.qwen_api_key:
            ai_errors.append("使用通义千问时必须设置API密钥")
        if self.config.ai.default_provider == "baidu" and (not self.config.ai.baidu_api_key or not self.config.ai.baidu_secret_key):
            ai_errors.append("使用百度文心时必须设置API密钥和Secret密钥")
        if ai_errors:
            errors["ai"] = ai_errors
        
        # 验证数据库配置
        db_errors = []
        db_path = Path(self.config.database.sqlite_path)
        if not db_path.parent.exists():
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                db_errors.append(f"无法创建数据库目录: {e}")
        if db_errors:
            errors["database"] = db_errors
        
        return errors
    
    def create_sample_env(self):
        """创建示例.env文件"""
        sample_content = """# 提猫直播助手配置文件
# 复制此文件为.env并修改相应配置

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=5000
SERVER_DEBUG=false
SECRET_KEY=your-very-secure-secret-key-here

# AI配置 - 选择一个或多个服务商
# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 通义千问配置
QWEN_API_KEY=your-qwen-api-key

# 百度文心配置
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret-key

# 默认AI服务商 (openai/qwen/baidu)
AI_PROVIDER=openai

# 数据库配置
DATABASE_PATH=data/app.db

# 安全配置
API_KEY=your-api-key
API_RATE_LIMIT=100

# 应用配置
ENVIRONMENT=production
DEBUG=false
"""
        
        sample_file = Path(".env.example")
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            print(f"示例配置文件已创建: {sample_file}")
        except Exception as e:
            print(f"创建示例配置文件失败: {e}")
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = AppConfig()
        self.save_config()
        print("配置已重置为默认值")
    
    def export_config(self, file_path: str):
        """导出配置"""
        try:
            config_dict = asdict(self.config)
            write_json_file(file_path, config_dict)
            print(f"配置已导出到: {file_path}")
        except Exception as e:
            print(f"导出配置失败: {e}")
    
    def import_config(self, file_path: str):
        """导入配置"""
        try:
            config_data = read_json_file(file_path)
            self.config = self._dict_to_config(config_data)
            self.save_config()
            print(f"配置已从 {file_path} 导入")
        except Exception as e:
            print(f"导入配置失败: {e}")


# 全局配置管理器实例
config_manager = ConfigManager()
config = config_manager.get_config()


def get_config() -> AppConfig:
    """获取应用配置"""
    return config


def update_config(updates: Dict[str, Any]):
    """更新配置"""
    config_manager.update_config(updates)


def validate_config() -> Dict[str, list]:
    """验证配置"""
    return config_manager.validate_config()


def save_config():
    """保存配置"""
    config_manager.save_config()


def reset_config():
    """重置配置"""
    config_manager.reset_to_defaults()
