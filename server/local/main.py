"""
本地服务 - FastAPI 入口
重度服务:弹幕拉取、语音转写、AI处理
运行在用户本地(Electron 内嵌)
基于文档: docs/部分服务从服务器转移本地.md
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 导入本地路由
from .routers import (
    live_audio_router,
    ai_live_router,
    live_session_router,
    ai_gateway_router,
    douyin_web_router
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="提猫直播助手 - 本地服务",
    description="本地重度服务：弹幕、语音转写、AI",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时加载模型（懒加载）
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 本地服务启动中...")
    logger.info("📦 准备加载 SenseVoice 模型...")
    # TODO: 从 app.getPath('userData')/models 加载模型
    # from .services.asr_service import ASRService
    # asr_service = ASRService()
    # await asr_service.initialize()
    # app.state.asr_service = asr_service
    logger.info("✅ 本地服务启动完成")

# 注册本地路由
app.include_router(live_audio_router)
app.include_router(ai_live_router)
app.include_router(live_session_router)
app.include_router(ai_gateway_router)
app.include_router(douyin_web_router)

logger.info("✅ 本地路由已注册: 直播转写、AI、抖音弹幕")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "local",
        "note": "runs on user's machine"
    }

@app.get("/")
async def root():
    return {
        "service": "提猫直播助手 - 本地服务",
        "endpoints": [
            "/api/live/*",
            "/api/transcribe/*",
            "/api/ai/*",
            "/api/config/*"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LOCAL_PORT", "16000"))
    uvicorn.run(app, host="127.0.0.1", port=port, workers=1)
