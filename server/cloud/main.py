"""
云端服务 - FastAPI 入口
轻量级服务：用户系统、鉴权、支付
内存目标: < 512MB
基于文档: docs/部分服务从服务器转移本地.md
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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

# TODO: 注册路由（从现有 server/app/api 迁移）
# app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
# app.include_router(user.router, prefix="/api/user", tags=["用户"])
# app.include_router(payment.router, prefix="/api/payment", tags=["支付"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "cloud",
        "memory_limit": "512MB"
    }

@app.get("/")
async def root():
    return {
        "service": "提猫直播助手 - 云端服务",
        "endpoints": [
            "/api/auth/*",
            "/api/user/*",
            "/api/payment/*",
            "/api/admin/*"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CLOUD_PORT", "15000"))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
