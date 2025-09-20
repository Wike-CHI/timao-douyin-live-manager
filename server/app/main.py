# -*- coding: utf-8 -*-
"""
提猫直播助手 FastAPI 主应用
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建FastAPI应用
app = FastAPI(
    title="提猫直播助手 API",
    description="基于F2 + VOSK的抖音直播弹幕抓取和语音转录服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入API路由
try:
    # 使用相对导入
    from .api.transcription import router as transcription_router
    app.include_router(transcription_router)
    logging.info("✅ 转录API路由已加载")

    from .api.douyin import router as douyin_router
    app.include_router(douyin_router)
    logging.info("✅ 抖音API路由已加载")

    # WebSocket 广播与管理服务（相对导入）
    from ..websocket_handler import start_websocket_services, stop_websocket_services  # type: ignore
    logging.info("✅ WebSocket 服务导入成功（相对导入）")
except ImportError:
    try:
        # 如果相对导入失败，使用包路径导入，确保子模块内的相对导入可解析
        import importlib, sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent  # 项目根目录（包含 server 包）
        if str(project_root) not in sys.path:
            sys.path.append(str(project_root))

        # 以完整包名导入，维持 __package__=server.app.api.*，使相对导入生效
        transcription_mod = importlib.import_module('server.app.api.transcription')
        app.include_router(getattr(transcription_mod, 'router'))
        logging.info("✅ 转录API路由已加载")

        douyin_mod = importlib.import_module('server.app.api.douyin')
        app.include_router(getattr(douyin_mod, 'router'))
        logging.info("✅ 抖音API路由已加载")

        ws_mod = importlib.import_module('server.websocket_handler')
        start_websocket_services = getattr(ws_mod, 'start_websocket_services')
        stop_websocket_services = getattr(ws_mod, 'stop_websocket_services')
        logging.info("✅ WebSocket 服务导入成功（包路径导入）")
    except ImportError as e:
        logging.error(f"❌ API路由/WS服务加载失败: {e}")
        # 提供空占位，避免后续引用报错
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
        <title>🐱 提猫直播助手</title>
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
            <h1>提猫直播助手</h1>
            <p>基于F2 + VOSK的抖音直播弹幕抓取和语音转录服务</p>
            
            <div class="status">
                <h3>🚀 服务状态</h3>
                <p>API服务: ✅ 运行中</p>
                <p>转录服务: 🔄 待启动</p>
            </div>
            
            <div>
                <a href="/docs" class="link">📚 API文档</a>
                <a href="/api/transcription/health" class="link">💚 健康检查</a>
                <a href="/static/index.html" class="link">🎯 前端界面</a>
            </div>
            
            <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
                <p>MVP版本 v1.0 | 提猫科技出品</p>
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
        "timestamp": "2025-01-20"
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logging.info("🐱 提猫直播助手启动中...")
    try:
        start_websocket_services()
        logging.info("✅ WebSocket 服务已启动")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务启动失败: {e}")
    logging.info("✅ FastAPI服务已启动")

# 应用关闭事件  
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    logging.info("🐱 提猫直播助手正在关闭...")
    try:
        stop_websocket_services()
        logging.info("✅ WebSocket 服务已停止")
    except Exception as e:
        logging.error(f"❌ WebSocket 服务停止失败: {e}")
    logging.info("✅ FastAPI服务已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )