"""
本地服务 - FastAPI 入口
重度服务：弹幕拉取、语音转写、AI处理
运行在用户本地（Electron 内嵌）
基于文档: docs/部分服务从服务器转移本地.md
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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
    print("🚀 本地服务启动中...")
    # TODO: 预加载模型（如果本地存在）
    # from .services.asr_service import ASRService
    # asr_service = ASRService()
    # await asr_service.initialize()
    # app.state.asr_service = asr_service
    print("✅ 本地服务启动完成")

# TODO: 注册路由（从现有 server/app/api 迁移重度服务）
# app.include_router(live.router, prefix="/api/live", tags=["直播"])
# app.include_router(transcribe.router, prefix="/api/transcribe", tags=["转写"])
# app.include_router(ai.router, prefix="/api/ai", tags=["AI"])

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
