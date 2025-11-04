# -*- coding: utf-8 -*-
"""
测试 Gemini API 连接

用于验证 AiHubMix API Key 是否配置正确，以及 Gemini 服务是否可用。

使用方法：
1. 在 .env 文件中配置 AIHUBMIX_API_KEY
2. 运行: python tools/test_gemini.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

from server.ai.gemini_adapter import get_gemini_adapter


def test_connection():
    """测试 Gemini API 连接"""
    print("=" * 60)
    print("测试 Gemini API 连接")
    print("=" * 60)
    print()
    
    # 检查环境变量
    api_key = os.getenv("AIHUBMIX_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 未配置 AIHUBMIX_API_KEY")
        print()
        print("请在 .env 文件中添加:")
        print("AIHUBMIX_API_KEY=sk-your-aihubmix-api-key")
        print()
        print("获取 API Key: https://aihubmix.com")
        return False
    
    print(f"✅ API Key 已配置: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # 获取适配器
    adapter = get_gemini_adapter()
    
    if not adapter.is_available():
        print("❌ Gemini 适配器不可用")
        return False
    
    print(f"✅ Gemini 适配器初始化成功")
    print(f"   模型: {adapter.model}")
    print(f"   Base URL: {adapter.base_url}")
    print()
    
    # 测试简单调用
    print("🧪 测试简单调用...")
    prompt = """请用 JSON 格式返回一个简单的直播复盘示例，包含以下字段：
{
  "overall_score": 85,
  "key_highlights": ["亮点1", "亮点2"],
  "key_issues": ["问题1"]
}

只返回 JSON，不要其他解释。"""
    
    result = adapter.generate_review(
        prompt=prompt,
        temperature=0.3,
        max_tokens=500,
        response_format="json"
    )
    
    if not result:
        print("❌ API 调用失败")
        return False
    
    print()
    print("✅ API 调用成功！")
    print()
    print(f"📊 使用情况:")
    print(f"   输入 Tokens: {result['usage']['prompt_tokens']}")
    print(f"   输出 Tokens: {result['usage']['completion_tokens']}")
    print(f"   总计 Tokens: {result['usage']['total_tokens']}")
    print(f"   成本: ${result['cost']:.6f} 美元")
    print(f"   耗时: {result['duration']:.2f} 秒")
    print()
    
    print(f"📝 返回内容（前 500 字符）:")
    print("-" * 60)
    print(result['text'][:500])
    print("-" * 60)
    print()
    
    # 测试 JSON 解析
    print("🧪 测试 JSON 解析...")
    parsed = adapter.parse_json_response(result['text'])
    
    if parsed:
        print("✅ JSON 解析成功")
        print()
        print("解析结果:")
        import json
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        print("❌ JSON 解析失败")
        return False
    
    print()
    print("=" * 60)
    print("✅ 所有测试通过！Gemini API 配置正确。")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    success = test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
