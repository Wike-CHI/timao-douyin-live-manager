# -*- coding: utf-8 -*-
"""
提猫直播助手 FastAPI 主应用
"""

import logging
from pathlib import Path
import os
import ssl
import sys

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 确保项目根目录在 Python 路径中，以便正确导入 DouyinLiveWebFetcher 等模块
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _load_env_once() -> None:
    """Load .env from project root regardless of working directory."""
    try:
        root_env = Path(__file__).resolve().parents[2] / ".env"
        if root_env.exists():
            load_dotenv(dotenv_path=root_env, override=False)
        else:
            load_dotenv(override=False)
    except Exception:
        load_dotenv(override=False)

# 预先加载环境变量，确保在配置模块导入前生效
_load_env_once()

from server.app.database import init_database, close_database
from server.app.models import Base
from server.utils.ai_defaults import ensure_default_ai_env
from server.config import config_manager

def _disable_ssl_verify_if_requested() -> None:
    """Opt-in dev helper to skip SSL certificate verification."""
    if os.getenv("DISABLE_SSL_VERIFY", "1") != "1":
        return
    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass

ensure_default_ai_env()
_disable_ssl_verify_if_requested()

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Reduce noisy httpx logs (e.g., HEAD 405 from CDN probes)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 创建FastAPI应用
app = FastAPI(
    title="提猫直播助手 API",
    description="基于自研抓取器与本地语音识别能力的抖音直播弹幕抓取和语音转录服务",
    version="1.0.0",
)

# CORS配置 - 允许本地开发环境访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:30013",
        "http://localhost:30013",
        "http://127.0.0.1:10090",  # 允许后端静态文件访问 API
        "http://localhost:10090",   # 允许后端静态文件访问 API
        "http://127.0.0.1:8090",    # 兼容旧端口
        "http://localhost:8090",     # 兼容旧端口
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # 允许前端访问所有响应头
)

def _include_router_safe(desc: str, import_path: str):
    """Import and include a router; log error but don't crash on failure."""
    try:
        import importlib
        mod = importlib.import_module(import_path)
        app.include_router(getattr(mod, "router"))
        logging.info(f"✅ 路由已加载: {desc}")
    except Exception as e:
        logging.error(f"❌ 路由加载失败[{desc}]: {e}")


# 分段加载（避免单个模块失败影响全局）
_include_router_safe("直播音频转写", "server.app.api.live_audio")
_include_router_safe("直播复盘", "server.app.api.live_report")
_include_router_safe("AI 测试", "server.app.api.ai_test")
_include_router_safe("抖音 API", "server.app.api.douyin")
_include_router_safe("抖音 Web 测试", "server.app.api.douyin_web")
_include_router_safe("联合测试", "server.app.api.live_test")
_include_router_safe("NLP 管理", "server.app.api.nlp_hotwords")
_include_router_safe("AI 实时分析", "server.app.api.ai_live")
_include_router_safe("AI 话术生成", "server.app.api.ai_scripts")
_include_router_safe("资源自检", "server.app.api.bootstrap")
_include_router_safe("工具", "server.app.api.tools")
_include_router_safe("AI 使用监控", "server.app.api.ai_usage")
_include_router_safe("AI 网关管理", "server.app.api.ai_gateway_api")
_include_router_safe("用户认证", "server.app.api.auth")
_include_router_safe("订阅管理", "server.app.api.subscription")
_include_router_safe("管理员", "server.app.api.admin")

# WebSocket 广播与管理服务（容错）
try:
    from server.websocket_handler import (start_websocket_services,  # type: ignore
                                     stop_websocket_services)
    logging.info("✅ WebSocket 服务导入成功")
except Exception as e:
    logging.error(f"❌ WebSocket 服务导入失败: {e}")

    def start_websocket_services():
        logging.warning("⚠️ start_websocket_services 未加载，跳过启动")

    def stop_websocket_services():
        logging.warning("⚠️ stop_websocket_services 未加载，跳过停止")


# 静态文件服务 (前端)
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logging.info(f"✅ 静态文件服务已启用: {frontend_path}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🐱 提猫直播助手 · TalkingCat</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                margin: 0;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { font-size: 2.5em; margin-bottom: 20px; }
            .cat { font-size: 4em; margin-bottom: 20px; animation: bounce 2s infinite; }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            .status { margin: 20px 0; }
            .link {
                color: #ffd700;
                text-decoration: none;
                font-weight: bold;
                margin: 0 10px;
            }
            .link:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="cat">🐱</div>
            <h1>提猫直播助手 · TalkingCat</h1>
            <p>本地语音转写 + 抖音直播互动 · 隐私不出机</p>

            <div class="status">
                <h3>🚀 服务状态</h3>
                <p>API服务: ✅ 运行中</p>
                <p>转录服务: 🔄 待启动</p>
            </div>

            <div>
                <a href="/docs" class="link">📚 API文档</a>
                <a href="/api/live_audio/status" class="link">💚 转写状态</a>
                <a href="/static/index.html" class="link">🎯 Web 界面</a>
                <a href="/static/douyin_test.html" class="link">🧪 Douyin 测试面板</a>
                <a href="/static/live_test.html" class="link">🧪 联合测试面板</a>
            </div>

            <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
                <p>MVP版本 v1.0 | 提猫直播助手 · TalkingCat</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "提猫直播助手",
        "version": "1.0.0",
        "timestamp": "2025-01-20",
    }


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logging.info("🐱 提猫直播助手启动中...")
    
    # 初始化 Redis
    try:
        from server.utils.redis_manager import init_redis
        from server.config import RedisConfig
        
        # 确保传递 RedisConfig 对象
        redis_config = config_manager.config.redis
        if isinstance(redis_config, dict):
            redis_config = RedisConfig(**redis_config)
        
        redis_client = init_redis(redis_config)
        if redis_client.is_enabled():
            logging.info("✅ Redis 缓存已启用")
        else:
            logging.warning("⚠️ Redis 缓存未启用，将使用内存存储")
    except Exception as e:
        logging.warning(f"⚠️ Redis 初始化失败: {e}")
    
    # 初始化数据库
    try:
        db_config = config_manager.config.database
        init_database(db_config)
        logging.info("✅ 数据库已初始化")
    except Exception as e:
        logging.error(f"❌ 数据库初始化失败: {e}")
    
    try:
        start_websocket_services()
        logging.info("✅ WebSocket 服务已启动")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务启动失败: {e}")
    logging.info("✅ FastAPI服务已启动")

    # 后台引导：FFmpeg 与模型（首次启动自动准备）
    async def _bootstrap():
        try:
            from ..utils import bootstrap  # type: ignore
            bootstrap.start_bootstrap_async()
            logging.info("🔧 资源自检已开始（后台）")
        except Exception as e:  # pragma: no cover
            logging.warning(f"资源自检失败（可忽略）：{e}")

    try:
        asyncio.create_task(_bootstrap())
    except Exception:
        pass


# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    logging.info("🐱 提猫直播助手正在关闭...")
    
    # 关闭 Redis 连接
    try:
        from server.utils.redis_manager import close_redis
        close_redis()
        logging.info("✅ Redis 连接已关闭")
    except Exception as e:
        logging.error(f"❌ Redis 关闭失败: {e}")
    
    try:
        stop_websocket_services()
        logging.info("✅ WebSocket 服务已停止")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务停止失败: {e}")
    
    try:
        close_database()
        logging.info("✅ 数据库连接已关闭")
    except Exception as e:
        logging.error(f"❌ 数据库关闭失败: {e}")
    logging.info("✅ FastAPI服务已关闭")


if __name__ == "__main__":
    import uvicorn

    # 使用默认端口 10090，与 Electron 启动配置保持一致
    uvicorn.run("main:app", host="0.0.0.0", port=10090, reload=True, log_level="info")
