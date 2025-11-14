#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试百度ASR初始化"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv
env_path = project_root / "server" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ 已加载环境变量: {env_path}")
else:
    print(f"⚠️ .env文件不存在: {env_path}")

async def test_baidu_asr():
    print("=" * 80)
    print("测试百度ASR初始化")
    print("=" * 80)
    
    # 1. 检查环境变量
    print("\n1. 检查环境变量:")
    use_baidu = os.getenv("USE_BAIDU_ASR", "0")
    app_id = os.getenv("BAIDU_ASR_APP_ID", "")
    api_key = os.getenv("BAIDU_ASR_API_KEY", "")
    secret_key = os.getenv("BAIDU_ASR_SECRET_KEY", "")
    
    print(f"   USE_BAIDU_ASR: {use_baidu}")
    print(f"   BAIDU_ASR_APP_ID: {app_id[:10]}..." if app_id else "   BAIDU_ASR_APP_ID: (空)")
    print(f"   BAIDU_ASR_API_KEY: {api_key[:10]}..." if api_key else "   BAIDU_ASR_API_KEY: (空)")
    print(f"   BAIDU_ASR_SECRET_KEY: {secret_key[:10]}..." if secret_key else "   BAIDU_ASR_SECRET_KEY: (空)")
    
    # 2. 尝试导入
    print("\n2. 尝试导入百度ASR模块:")
    try:
        from server.modules.ast.baidu_asr_adapter import BaiduASRService, BaiduASRConfig
        print("   ✅ 导入成功")
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return
    
    # 3. 检查服务中的可用性
    print("\n3. 检查服务中的BAIDU_AVAILABLE标志:")
    try:
        from server.app.services.live_audio_stream_service import BAIDU_AVAILABLE
        print(f"   BAIDU_AVAILABLE: {BAIDU_AVAILABLE}")
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    # 4. 测试初始化
    print("\n4. 测试百度ASR初始化:")
    try:
        service = BaiduASRService()
        print("   ✅ 创建服务实例成功")
        
        print("   开始初始化...")
        success = await service.initialize()
        
        if success:
            print("   ✅ 初始化成功!")
            model_info = service.get_model_info()
            print(f"   模型信息: {model_info}")
        else:
            print("   ❌ 初始化失败")
            
    except Exception as e:
        print(f"   ❌ 初始化异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_baidu_asr())

