# -*- coding: utf-8 -*-
"""
本地AI配置管理服务

管理AI服务商配置、功能模型映射等，替代数据库配置存储。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .local_storage import local_storage

logger = logging.getLogger(__name__)


class LocalAIConfig:
    """本地AI配置管理"""
    
    CONFIG_FILE = "ai_config.json"
    USAGE_FILE = "ai_usage.json"
    
    # 支持的AI服务商模板
    PROVIDER_TEMPLATES = {
        "qwen": {
            "name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen3-max"],
            "default_model": "qwen-plus"
        },
        "xunfei": {
            "name": "讯飞星火",
            "base_url": "https://spark-api-open.xf-yun.com/v1",
            "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"],
            "default_model": "lite"
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-coder"],
            "default_model": "deepseek-chat"
        },
        "doubao": {
            "name": "字节豆包",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "models": ["doubao-pro", "doubao-lite"],
            "default_model": "doubao-pro"
        },
        "glm": {
            "name": "智谱ChatGLM",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-3-turbo"],
            "default_model": "glm-4"
        },
        "gemini": {
            "name": "Google Gemini",
            "base_url": "https://aihubmix.com/v1",
            "models": ["gemini-2.5-flash-preview-09-2025"],
            "default_model": "gemini-2.5-flash-preview-09-2025"
        },
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default_model": "gpt-4o-mini"
        }
    }
    
    # 功能默认配置
    DEFAULT_FUNCTION_MODELS = {
        "live_analysis": {"provider": "xunfei", "model": "lite"},
        "style_profile": {"provider": "qwen", "model": "qwen3-max"},
        "script_generation": {"provider": "qwen", "model": "qwen3-max"},
        "live_review": {"provider": "gemini", "model": "gemini-2.5-flash-preview-09-2025"},
        "chat_focus": {"provider": "qwen", "model": "qwen3-max"},
        "topic_generation": {"provider": "qwen", "model": "qwen3-max"}
    }
    
    # 功能名称映射
    FUNCTION_NAMES = {
        "live_analysis": "实时分析",
        "style_profile": "风格画像与氛围分析",
        "script_generation": "话术生成",
        "live_review": "复盘总结",
        "chat_focus": "聊天焦点摘要",
        "topic_generation": "智能话题生成"
    }
    
    @classmethod
    def _get_default_config(cls) -> Dict:
        """获取默认配置"""
        return {
            "providers": {},
            "function_models": cls.DEFAULT_FUNCTION_MODELS.copy(),
            "active_provider": None,
            "initialized": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查是否已初始化（至少配置了一个服务商）"""
        config = local_storage.read(cls.CONFIG_FILE, {})
        if not config.get("initialized", False):
            return False
        # 检查是否有任何已启用的服务商
        providers = config.get("providers", {})
        return any(p.get("enabled") and p.get("api_key") for p in providers.values())
    
    @classmethod
    def get_config(cls) -> Dict:
        """获取完整配置"""
        config = local_storage.read(cls.CONFIG_FILE)
        if not config:
            config = cls._get_default_config()
            local_storage.write(cls.CONFIG_FILE, config)
        return config
    
    @classmethod
    def save_config(cls, config: Dict) -> bool:
        """保存完整配置"""
        config["updated_at"] = datetime.now().isoformat()
        return local_storage.write(cls.CONFIG_FILE, config)
    
    @classmethod
    def get_provider_templates(cls) -> Dict:
        """获取所有服务商模板"""
        return cls.PROVIDER_TEMPLATES.copy()
    
    @classmethod
    def get_configured_providers(cls) -> Dict:
        """获取已配置的服务商"""
        config = cls.get_config()
        return config.get("providers", {})
    
    @classmethod
    def save_provider(cls, provider_id: str, api_key: str, 
                      base_url: Optional[str] = None,
                      default_model: Optional[str] = None,
                      enabled: bool = True) -> bool:
        """
        保存服务商配置
        
        Args:
            provider_id: 服务商ID（如 qwen, xunfei）
            api_key: API密钥
            base_url: API地址（可选，使用默认值）
            default_model: 默认模型（可选，使用默认值）
            enabled: 是否启用
            
        Returns:
            是否保存成功
        """
        config = cls.get_config()
        
        template = cls.PROVIDER_TEMPLATES.get(provider_id, {})
        
        config["providers"][provider_id] = {
            "api_key": api_key,
            "base_url": base_url or template.get("base_url", ""),
            "default_model": default_model or template.get("default_model", ""),
            "enabled": enabled,
            "name": template.get("name", provider_id),
            "updated_at": datetime.now().isoformat()
        }
        
        # 如果是第一个配置的服务商，设为默认
        if not config.get("active_provider"):
            config["active_provider"] = provider_id
        
        logger.info(f"✅ 保存服务商配置: {provider_id}")
        return cls.save_config(config)
    
    @classmethod
    def remove_provider(cls, provider_id: str) -> bool:
        """移除服务商配置"""
        config = cls.get_config()
        if provider_id in config.get("providers", {}):
            del config["providers"][provider_id]
            
            # 如果移除的是当前活跃服务商，切换到其他
            if config.get("active_provider") == provider_id:
                remaining = list(config.get("providers", {}).keys())
                config["active_provider"] = remaining[0] if remaining else None
            
            return cls.save_config(config)
        return True
    
    @classmethod
    def set_active_provider(cls, provider_id: str) -> bool:
        """设置当前活跃的服务商"""
        config = cls.get_config()
        if provider_id in config.get("providers", {}):
            config["active_provider"] = provider_id
            return cls.save_config(config)
        return False
    
    @classmethod
    def get_active_provider(cls) -> Optional[Dict]:
        """获取当前活跃的服务商配置"""
        config = cls.get_config()
        active_id = config.get("active_provider")
        if not active_id:
            return None
        
        provider = config.get("providers", {}).get(active_id)
        if provider and provider.get("enabled"):
            return {
                "id": active_id,
                **provider
            }
        return None
    
    @classmethod
    def set_function_model(cls, function_id: str, provider: str, model: str) -> bool:
        """
        设置功能使用的模型
        
        Args:
            function_id: 功能ID（如 live_analysis）
            provider: 服务商ID
            model: 模型名称
            
        Returns:
            是否保存成功
        """
        config = cls.get_config()
        
        if "function_models" not in config:
            config["function_models"] = {}
        
        config["function_models"][function_id] = {
            "provider": provider,
            "model": model
        }
        
        logger.info(f"✅ 设置功能模型: {function_id} -> {provider}/{model}")
        return cls.save_config(config)
    
    @classmethod
    def get_function_models(cls) -> Dict:
        """获取所有功能的模型配置"""
        config = cls.get_config()
        return config.get("function_models", cls.DEFAULT_FUNCTION_MODELS.copy())
    
    @classmethod
    def get_provider_for_function(cls, function_id: str) -> Optional[Dict]:
        """
        获取指定功能使用的服务商和模型配置
        
        Args:
            function_id: 功能ID
            
        Returns:
            包含provider, model, api_key, base_url的配置字典，或None
        """
        config = cls.get_config()
        func_config = config.get("function_models", {}).get(function_id)
        
        if not func_config:
            # 使用默认配置
            func_config = cls.DEFAULT_FUNCTION_MODELS.get(function_id)
            if not func_config:
                return None
        
        provider_id = func_config.get("provider")
        provider_config = config.get("providers", {}).get(provider_id)
        
        if not provider_config:
            logger.warning(f"功能 {function_id} 配置的服务商 {provider_id} 未找到")
            return None
        
        if not provider_config.get("enabled"):
            logger.warning(f"功能 {function_id} 配置的服务商 {provider_id} 已禁用")
            return None
        
        if not provider_config.get("api_key"):
            logger.warning(f"功能 {function_id} 配置的服务商 {provider_id} 未配置API Key")
            return None
        
        return {
            "provider": provider_id,
            "model": func_config.get("model"),
            "api_key": provider_config.get("api_key"),
            "base_url": provider_config.get("base_url")
        }
    
    @classmethod
    def mark_initialized(cls) -> bool:
        """标记为已初始化"""
        config = cls.get_config()
        config["initialized"] = True
        logger.info("✅ AI配置已标记为初始化完成")
        return cls.save_config(config)
    
    @classmethod
    def test_provider(cls, provider_id: str) -> Dict:
        """
        测试服务商连接
        
        Args:
            provider_id: 服务商ID
            
        Returns:
            测试结果 {"success": bool, "message": str, "latency_ms": int}
        """
        import time
        config = cls.get_config()
        provider = config.get("providers", {}).get(provider_id)
        
        if not provider:
            return {"success": False, "message": "服务商未配置"}
        
        if not provider.get("api_key"):
            return {"success": False, "message": "API Key未配置"}
        
        try:
            import httpx
            start = time.time()
            
            # 发送简单的测试请求
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    f"{provider['base_url']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {provider['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": provider.get("default_model", ""),
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5
                    }
                )
                
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return {"success": True, "message": "连接成功", "latency_ms": latency}
            elif response.status_code == 401:
                return {"success": False, "message": "API Key无效", "latency_ms": latency}
            elif response.status_code == 403:
                return {"success": False, "message": "权限不足", "latency_ms": latency}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}", "latency_ms": latency}
                
        except Exception as e:
            return {"success": False, "message": str(e)[:100]}
    
    # ========== AI使用统计 ==========
    
    @classmethod
    def record_usage(cls, provider: str, model: str, 
                     input_tokens: int, output_tokens: int,
                     cost: float = 0.0, function: str = "") -> bool:
        """记录AI使用"""
        usage = local_storage.read(cls.USAGE_FILE, {"records": [], "summary": {}})
        
        record = {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "function": function,
            "timestamp": datetime.now().isoformat()
        }
        
        usage["records"].append(record)
        
        # 更新汇总
        key = f"{provider}_{model}"
        if key not in usage["summary"]:
            usage["summary"][key] = {
                "provider": provider,
                "model": model,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0
            }
        
        usage["summary"][key]["total_calls"] += 1
        usage["summary"][key]["total_input_tokens"] += input_tokens
        usage["summary"][key]["total_output_tokens"] += output_tokens
        usage["summary"][key]["total_cost"] += cost
        
        return local_storage.write(cls.USAGE_FILE, usage)
    
    @classmethod
    def get_usage_stats(cls) -> Dict:
        """获取使用统计"""
        usage = local_storage.read(cls.USAGE_FILE, {"records": [], "summary": {}})
        return usage.get("summary", {})
    
    @classmethod
    def get_recent_usage(cls, limit: int = 100) -> List[Dict]:
        """获取最近的使用记录"""
        usage = local_storage.read(cls.USAGE_FILE, {"records": [], "summary": {}})
        records = usage.get("records", [])
        return records[-limit:] if len(records) > limit else records

