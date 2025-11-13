#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科大讯飞星火大模型快速测试脚本

快速测试接口是否可用，不包含详细输出

使用方法：
    python server/test_xunfei_quick.py

审查人: 叶维哲
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_file = project_root / "server" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

def test_xunfei():
    """快速测试科大讯飞接口"""
    # 检查环境变量
    api_key = os.getenv("XUNFEI_API_KEY")
    if not api_key:
        print("❌ XUNFEI_API_KEY 未设置")
        print("请在 server/.env 文件中添加: XUNFEI_API_KEY=APPID:APISecret")
        return False
    
    if ":" not in api_key:
        print("❌ XUNFEI_API_KEY 格式错误，应为: APPID:APISecret")
        return False
    
    # 测试OpenAI客户端
    try:
        from openai import OpenAI
        
        base_url = os.getenv("XUNFEI_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
        model = os.getenv("XUNFEI_MODEL", "lite")
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "说'测试成功'"}],
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print("✅ 接口测试成功！")
        print(f"响应: {content}")
        return True
        
    except ImportError:
        print("❌ openai 库未安装")
        print("请运行: pip install openai")
        return False
    except Exception as e:
        print(f"❌ 接口测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_xunfei()
    sys.exit(0 if success else 1)

