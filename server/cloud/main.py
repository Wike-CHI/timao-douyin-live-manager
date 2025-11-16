"""
云端服务 - FastAPI 入口
轻量级服务：用户系统、鉴权、支付
内存目标: < 512MB
基于文档: docs/部分服务从服务器转移本地.md
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

# 导入云端路由
from .routers import auth_router, profile_router, subscription_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="提猫直播助手 - 云端服务",
    description="轻量级用户、鉴权、支付服务",
    version="1.0.0"
)

# CORS 配置（允许本地应用访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件配置
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"✅ 静态文件目录已挂载: {STATIC_DIR}")
else:
    logger.warning(f"⚠️  静态文件目录不存在: {STATIC_DIR}")

# 注册云端路由
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(subscription_router)

logger.info("✅ 云端路由已注册: 认证、用户资料、订阅/支付")

@app.on_event("startup")
async def startup_event():
    """云端服务启动事件"""
    logger.info("=" * 60)
    logger.info("🚀 云端服务启动中...")
    logger.info(f"   服务类型: 云端(用户/鉴权/支付)")
    logger.info(f"   内存目标: < 512MB")
    logger.info("=" * 60)
    logger.info("✅ 云端服务启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """云端服务关闭事件"""
    logger.info("🛑 云端服务关闭中...")

@app.get("/health")
async def health_check():
    """健康检查端点(无需认证)"""
    import sys
    return {
        "status": "healthy", 
        "service": "cloud",
        "memory_limit": "512MB",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

@app.get("/")
async def root():
    """返回云端服务控制台页面"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        # 如果静态文件不存在，返回JSON
        return {
            "service": "提猫直播助手 - 云端服务",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                "/api/auth/*   - 用户认证",
                "/profile/*    - 用户资料",
                "/api/subscription/* - 订阅管理",
                "/api/payment/* - 支付处理",
                "/docs         - API文档",
                "/health       - 健康检查"
            ]
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CLOUD_PORT", "15000"))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
