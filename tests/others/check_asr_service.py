#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查当前使用的ASR服务"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
env_path = project_root / "server" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ 已加载环境变量: {env_path}")
else:
    print(f"⚠️ .env文件不存在: {env_path}")

print("\n" + "="*80)
print("检查ASR服务配置")
print("="*80 + "\n")

# 检查环境变量
print("1. 环境变量配置:")
print(f"   USE_BAIDU_ASR: {os.getenv('USE_BAIDU_ASR', '未设置')}")
print(f"   USE_ALIYUN_ASR: {os.getenv('USE_ALIYUN_ASR', '未设置')}")
print(f"   USE_IFLYTEK_ASR: {os.getenv('USE_IFLYTEK_ASR', '未设置')}")

# 导入并测试服务
print("\n2. 导入ASR服务:")
try:
    from server.app.services.live_audio_stream_service import get_live_audio_service
    print("   ✅ 导入成功")
    
    # 获取服务实例
    service = get_live_audio_service()
    print("   ✅ 服务实例创建成功")
    
    # 检查服务内部的ASR实例
    import asyncio
    async def check_service():
        # 确保ASR已加载
        await service._ensure_sv()
        
        if service._sv:
            model_info = service._sv.get_model_info()
            print(f"\n3. 当前使用的ASR服务:")
            print(f"   Backend: {model_info.get('backend', 'Unknown')}")
            print(f"   Model: {model_info.get('model_name', 'Unknown')}")
            print(f"   Provider: {model_info.get('provider', 'Unknown')}")
            return model_info.get('backend')
        else:
            print("\n3. ❌ ASR服务未初始化")
            return None
    
    backend = asyncio.run(check_service())
    
    print("\n" + "="*80)
    if backend == "baidu":
        print("✅ 正在使用: 百度ASR")
    elif backend == "aliyun":
        print("✅ 正在使用: 阿里云ASR")
    elif backend == "sensevoice":
        print("✅ 正在使用: SenseVoice（本地）")
    else:
        print(f"⚠️ 正在使用: {backend}")
    print("="*80)
    
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

