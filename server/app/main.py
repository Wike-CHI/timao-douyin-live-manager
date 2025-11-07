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
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 确保项目根目录在 Python 路径中（模块已迁移到 server/modules/）
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
from server.utils.service_logger import log_service_start, log_service_stop

if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

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

# 配置日志 - 支持UTF-8编码以正确显示中文
import os
import sys
if os.name == 'nt':  # Windows系统
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置控制台编码为UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 配置日志处理器，确保中文正确显示
import logging
from logging import StreamHandler

class UTF8StreamHandler(StreamHandler):
    """UTF-8编码的流处理器"""
    def __init__(self, stream=None):
        super().__init__(stream)
        self.setStream(stream)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # 确保消息以UTF-8编码输出
            if hasattr(stream, 'buffer'):
                stream.buffer.write(msg.encode('utf-8') + b'\n')
                stream.buffer.flush()
            else:
                stream.write(msg + '\n')
                if hasattr(stream, 'flush'):
                    stream.flush()
        except Exception:
            self.handleError(record)

# 清除现有的处理器
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 配置新的日志系统
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[UTF8StreamHandler(sys.stdout)]
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
# 注意：不能同时使用 allow_origins=["*"] 和 allow_credentials=True
# 浏览器安全策略不允许这种组合，所以必须明确列出所有允许的来源
# 将CORS中间件放在最前面，确保在所有路由之前处理
allowed_origins = [
    "http://127.0.0.1:10030",
    "http://localhost:10030",
    "http://127.0.0.1:10109",  # 前端新默认端口（避免 Windows 端口排除范围 10009-10108）
    "http://localhost:10109",  # 前端新默认端口（避免 Windows 端口排除范围 10009-10108）
    "http://127.0.0.1:9019",  # 允许后端静态文件访问 API
    "http://localhost:9019",   # 允许后端静态文件访问 API
    "http://127.0.0.1:10050",  # 管理后台开发端口
    "http://localhost:10050",  # 管理后台开发端口
    "http://127.0.0.1:8090",    # 兼容旧端口
    "http://localhost:8090",     # 兼容旧端口
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8000",    # 兼容测试端口
    "http://localhost:8000",     # 兼容测试端口
    "http://127.0.0.1:5173",     # Vite默认端口
    "http://localhost:5173",     # Vite默认端口
]

# Allow extra origins configured at runtime so credentials remain supported.
try:
    extra_origins = config_manager.config.security.cors_origins or []
    for origin in extra_origins:
        if origin and origin != "*" and origin not in allowed_origins:
            allowed_origins.append(origin)
except Exception:
    logging.warning(
        "Failed to extend CORS allow list from config; falling back to defaults",
        exc_info=True,
    )

_ALLOWED_ORIGIN_SET = set(allowed_origins)
_LOCALHOST_PREFIXES = (
    "http://localhost",
    "http://127.0.0.1",
    "https://localhost",
    "https://127.0.0.1",
)
_CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]
_CORS_ALLOW_HEADERS = [
    "Content-Type",
    "Authorization",
    "Accept",
    "Origin",
    "X-Requested-With",
    "Access-Control-Request-Method",
    "Access-Control-Request-Headers",
]
_CORS_EXPOSE_HEADERS = ["*"]
_CORS_MAX_AGE = 3600


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    if origin in _ALLOWED_ORIGIN_SET:
        return True
    for prefix in _LOCALHOST_PREFIXES:
        if origin.startswith(prefix):
            return True
    try:
        parsed = urlparse(origin)
    except Exception:
        return False
    return (parsed.hostname or "") in {"localhost", "127.0.0.1"}


def _ensure_vary_header(response: Response, value: str) -> None:
    current = response.headers.get("Vary")
    if not current:
        response.headers["Vary"] = value
        return
    items = [v.strip() for v in current.split(",") if v.strip()]
    if value not in items:
        items.append(value)
        response.headers["Vary"] = ", ".join(items)


@app.middleware("http")
async def cors_preflight_guard(request: Request, call_next):
    origin = request.headers.get("origin", "")
    origin_allowed = _origin_allowed(origin)

    if request.method == "OPTIONS":
        logging.info(
            "CORS preflight - origin=%s path=%s",
            origin or "n/a",
            request.url.path,
        )
        response = Response(status_code=200)
        if origin_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = ", ".join(_CORS_ALLOW_METHODS)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(_CORS_ALLOW_HEADERS)
        response.headers["Access-Control-Max-Age"] = str(_CORS_MAX_AGE)
        response.headers["Access-Control-Expose-Headers"] = ", ".join(_CORS_EXPOSE_HEADERS)
        if origin_allowed:
            _ensure_vary_header(response, "Origin")
        return response

    response = await call_next(request)

    if origin_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers.setdefault(
            "Access-Control-Expose-Headers", ", ".join(_CORS_EXPOSE_HEADERS)
        )
        _ensure_vary_header(response, "Origin")
    return response

# 直接使用CORSMiddleware处理CORS，包括OPTIONS预检请求
# CORSMiddleware会自动处理OPTIONS请求，不需要自定义中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=_CORS_ALLOW_METHODS,
    allow_headers=_CORS_ALLOW_HEADERS,
    expose_headers=_CORS_EXPOSE_HEADERS,  # 允许前端访问所有响应头
    max_age=_CORS_MAX_AGE,  # 预检请求缓存时间
)

# 日志输出CORS配置（启动时）
logging.info("=" * 60)
logging.info("🌐 CORS配置已加载")
logging.info(f"   允许的来源: {len(allowed_origins)} 个")
for origin in allowed_origins:
    logging.info(f"   - {origin}")
logging.info("=" * 60)

# OPTIONS路由处理器（作为备用，正常情况下CORSMiddleware会处理）
@app.options("/{full_path:path}")
async def options_handler_fallback(request: Request, full_path: str):
    """OPTIONS请求备用处理器"""
    origin = request.headers.get("origin", "")
    logging.info(f"🌐 [OPTIONS路由] 预检请求 - Origin: {origin}, Path: /{full_path}")
    
    # 确定允许的origin
    if origin and origin in allowed_origins:
        allow_origin = origin
    elif origin and ("localhost" in origin or "127.0.0.1" in origin):
        allow_origin = origin
    else:
        allow_origin = origin if origin else "*"
    
    logging.info(f"✅ [OPTIONS路由] 返回200 - Allow-Origin: {allow_origin}")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": ", ".join(_CORS_ALLOW_METHODS),
            "Access-Control-Allow-Headers": ", ".join(_CORS_ALLOW_HEADERS),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": str(_CORS_MAX_AGE),
            "Access-Control-Expose-Headers": ", ".join(_CORS_EXPOSE_HEADERS),
        }
    )

# 添加CORS测试端点（用于验证CORS配置）
@app.get("/api/cors-test")
async def cors_test(request: Request):
    """CORS测试端点"""
    origin = request.headers.get("origin")
    return {
        "message": "CORS配置正常",
        "origin": origin,
        "allowed_origins": allowed_origins,
        "origin_allowed": origin in allowed_origins if origin else False,
    }

def _include_router_safe(desc: str, import_path: str):
    """Import and include a router; log error but don't crash on failure."""
    try:
        import importlib
        mod = importlib.import_module(import_path)
        router = getattr(mod, "router", None)
        if router is None:
            logging.error(f"❌ 路由加载失败[{desc}]: 模块 {import_path} 中没有找到 'router' 对象")
            return
        app.include_router(router)
        logging.info(f"✅ 路由已加载: {desc} (路径: {import_path})")
    except ImportError as e:
        logging.error(f"❌ 路由导入失败[{desc}]: {e}", exc_info=True)
    except AttributeError as e:
        logging.error(f"❌ 路由属性错误[{desc}]: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"❌ 路由加载失败[{desc}]: {e}", exc_info=True)


# 分段加载（避免单个模块失败影响全局）
_include_router_safe("直播音频转写", "server.app.api.live_audio")
_include_router_safe("直播复盘", "server.app.api.live_report")
_include_router_safe("直播复盘分析", "server.app.api.live_review")  # 新增：Gemini 复盘
_include_router_safe("统一会话管理", "server.app.api.live_session")  # 🆕 统一会话管理
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
# payment.py 已移除，统一使用 subscription.py
_include_router_safe("管理员", "server.app.api.admin")
_include_router_safe("直播评论管理", "server.app.api.live_comments")

# WebSocket 服务已迁移到 FastAPI 原生 WebSocket 实现
# 原 Flask WebSocket 处理器已归档到 docs/legacy_flask_code/
def start_websocket_services():
    logging.info("✅ WebSocket 服务已集成到 FastAPI 路由中")

def stop_websocket_services():
    logging.info("✅ WebSocket 服务停止（由 FastAPI 管理）")


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
@app.head("/health")
async def health_check():
    """健康检查 - 支持GET和HEAD方法"""
    return {
        "status": "healthy",
        "service": "提猫直播助手",
        "version": "1.0.0",
        "timestamp": "2025-10-28",
    }


@app.get("/api/streamcap/health")
async def streamcap_health_check():
    """StreamCap 模块健康检查（已集成到主服务）"""
    try:
        # 检查 StreamCap 模块是否可用
        from server.modules.streamcap.platforms import get_platform_handler
        return {
            "status": "ok",
            "service": "StreamCap",
            "integrated": True,
            "message": "StreamCap 已集成到主服务中",
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "StreamCap",
            "integrated": True,
            "message": f"StreamCap 模块加载失败: {str(e)}",
        }


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logging.info("🐱 提猫直播助手启动中...")
    log_service_start("FastAPI主服务")
    
    # 初始化 Redis
    try:
        from server.utils.redis_manager import init_redis
        from server.config import RedisConfig
        
        # 确保传递 RedisConfig 对象
        redis_config = config_manager.config.redis
        if isinstance(redis_config, dict):
            redis_config = RedisConfig(**redis_config)
        # 如果禁用，则跳过连接，直接进入内存模式
        if not redis_config.enabled:
            redis_client = init_redis(redis_config)
            logging.info("⏭️ 已跳过 Redis 启动，使用内存缓存")
        else:
            redis_client = init_redis(redis_config)
            if redis_client.is_enabled():
                log_service_start("Redis缓存服务")
                logging.info("✅ Redis 缓存已启用")
            else:
                logging.warning("⚠️ Redis 连接失败，已回退到内存缓存")
    except Exception as e:
        logging.warning(f"⚠️ Redis 初始化失败: {e}")
    
    # 初始化数据库
    try:
        db_config = config_manager.config.database
        # 确保使用MySQL（如果配置为mysql）
        if db_config.db_type == "mysql":
            logging.info(f"📊 数据库配置: MySQL - {db_config.mysql_user}@{db_config.mysql_host}:{db_config.mysql_port}/{db_config.mysql_database}")
        else:
            logging.warning(f"⚠️ 数据库配置: {db_config.db_type} (建议使用MySQL)")
        init_database(db_config)
        log_service_start("数据库服务")
        logging.info("✅ 数据库已初始化")
    except Exception as e:
        logging.error(f"❌ 数据库初始化失败: {e}")
        import traceback
        logging.error(traceback.format_exc())
    
    try:
        start_websocket_services()
        log_service_start("WebSocket服务")
        logging.info("✅ WebSocket 服务已启动")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务启动失败: {e}")
    
    log_service_start("FastAPI主服务", status="启动完成")
    logging.info("✅ FastAPI服务已启动")

    # 后台引导：FFmpeg 与模型（首次启动自动准备）
    async def _bootstrap():
        try:
            from server.utils import bootstrap  # type: ignore
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
    log_service_stop("FastAPI主服务")
    
    # 关闭 Redis 连接
    try:
        from server.utils.redis_manager import close_redis
        close_redis()
        log_service_stop("Redis缓存服务")
        logging.info("✅ Redis 连接已关闭")
    except Exception as e:
        logging.error(f"❌ Redis 关闭失败: {e}")
    
    try:
        stop_websocket_services()
        log_service_stop("WebSocket服务")
        logging.info("✅ WebSocket 服务已停止")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务停止失败: {e}")
    
    try:
        close_database()
        log_service_stop("数据库服务")
        logging.info("✅ 数据库连接已关闭")
    except Exception as e:
        logging.error(f"❌ 数据库关闭失败: {e}")
    logging.info("✅ FastAPI服务已关闭")


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    # 排除脚本目录、日志目录等，避免自动重载导致的频繁重启
    reload_exclude = [
        "**/scripts/**",
        "**/logs/**",
        "**/*.pyc",
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/.venv/**",
        "**/.git/**",
    ]

    # 从环境变量读取后端端口，默认 9030
    # 统一端口配置管理: 请在 .env 文件中设置 BACKEND_PORT
    import os
    backend_port = int(os.getenv("BACKEND_PORT", "9030"))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # Windows兼容: 使用127.0.0.1而非0.0.0.0避免权限问题
        port=backend_port,
        reload=True,
        log_level="info"
    )
