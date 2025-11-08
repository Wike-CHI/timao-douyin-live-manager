"""
AI配置诊断脚本
用于检查AI服务配置状态，帮助诊断密钥丢失问题

审查人: 叶维哲
遵循原则: KISS、单一职责、墨菲定律
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_env_file():
    """检查 .env 文件状态"""
    print("=" * 60)
    print("📁 检查 .env 文件")
    print("=" * 60)
    
    env_path = project_root / "server" / ".env"
    
    if env_path.exists():
        print(f"✅ .env 文件存在: {env_path}")
        print(f"   文件大小: {env_path.stat().st_size} 字节")
        print(f"   最后修改: {env_path.stat().st_mtime}")
        
        # 尝试读取文件
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                # 统计配置行数（非空且非注释）
                config_lines = [
                    line for line in lines 
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                print(f"   配置行数: {len(config_lines)}")
                print(f"   总行数: {len(lines)}")
                
                # 检查是否包含AI相关配置
                ai_keys = [
                    'GEMINI_API_KEY', 'QWEN_API_KEY', 'XUNFEI_API_KEY',
                    'DEEPSEEK_API_KEY', 'DOUBAO_API_KEY', 'GLM_API_KEY',
                    'OPENAI_API_KEY', 'AI_API_KEY'
                ]
                
                found_keys = []
                for key in ai_keys:
                    if key in content:
                        # 检查是否有实际值
                        for line in config_lines:
                            if line.startswith(key):
                                value = line.split('=', 1)[1].strip() if '=' in line else ''
                                if value and value != '':
                                    found_keys.append((key, True, len(value)))
                                else:
                                    found_keys.append((key, False, 0))
                                break
                
                print("\n🔑 AI密钥配置状态:")
                if found_keys:
                    for key, has_value, length in found_keys:
                        status = "✅ 已配置" if has_value else "❌ 未配置"
                        value_info = f"({length}字符)" if has_value else ""
                        print(f"   {key}: {status} {value_info}")
                else:
                    print("   ⚠️ 未找到任何AI密钥配置")
                
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    else:
        print(f"❌ .env 文件不存在: {env_path}")
        print("   建议: 从 ENV_TEMPLATE.md 创建 .env 文件")
    
    print()

def check_json_config():
    """检查 JSON 配置文件"""
    print("=" * 60)
    print("📄 检查 JSON 配置文件")
    print("=" * 60)
    
    config_files = [
        project_root / "server" / "config" / "app.json",
        project_root / "server" / "app" / "config" / "app.json",
        project_root / "config" / "app.json",
    ]
    
    for config_path in config_files:
        if config_path.exists():
            print(f"\n📝 {config_path.relative_to(project_root)}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'ai' in config:
                    ai_config = config['ai']
                    print("   AI配置:")
                    
                    ai_keys = [
                        'openai_api_key', 'qwen_api_key', 'baidu_api_key',
                        'baidu_secret_key'
                    ]
                    
                    for key in ai_keys:
                        if key in ai_config:
                            value = ai_config[key]
                            if value and value != '':
                                print(f"   ✅ {key}: 已配置 ({len(value)}字符)")
                            else:
                                print(f"   ❌ {key}: 未配置")
                else:
                    print("   ⚠️ 未找到AI配置")
                    
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")
        else:
            print(f"⚠️ 文件不存在: {config_path.relative_to(project_root)}")
    
    print()

def check_env_variables():
    """检查环境变量"""
    print("=" * 60)
    print("🌐 检查环境变量")
    print("=" * 60)
    
    # 加载 .env 文件
    env_path = project_root / "server" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 已加载: {env_path}")
    
    ai_env_keys = [
        'AI_SERVICE', 'AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL',
        'GEMINI_API_KEY', 'AIHUBMIX_API_KEY', 'GEMINI_MODEL',
        'QWEN_API_KEY', 'DASHSCOPE_API_KEY', 'QWEN_MODEL',
        'XUNFEI_API_KEY', 'XUNFEI_MODEL',
        'DEEPSEEK_API_KEY', 'DOUBAO_API_KEY', 'GLM_API_KEY',
        'OPENAI_API_KEY', 'OPENAI_MODEL',
        'DEFAULT_AI_PROVIDER'
    ]
    
    print("\n🔑 环境变量状态:")
    found_any = False
    for key in ai_env_keys:
        value = os.getenv(key)
        if value:
            found_any = True
            # 隐藏实际密钥内容，只显示长度
            if 'KEY' in key.upper():
                masked = f"{value[:8]}..." if len(value) > 8 else "***"
                print(f"   ✅ {key}: {masked} ({len(value)}字符)")
            else:
                print(f"   ✅ {key}: {value}")
        else:
            print(f"   ❌ {key}: 未设置")
    
    if not found_any:
        print("   ⚠️ 未找到任何AI相关环境变量")
    
    print()

def check_ai_gateway():
    """检查AI网关状态"""
    print("=" * 60)
    print("🤖 检查AI网关状态")
    print("=" * 60)
    
    try:
        from server.ai.ai_gateway import get_gateway
        
        gateway = get_gateway()
        providers = gateway.list_providers()
        
        print(f"✅ AI网关已初始化")
        print(f"\n📊 已注册的服务商:")
        
        if providers:
            for name, config in providers.items():
                enabled = "✅ 启用" if config.get('enabled') else "❌ 禁用"
                model = config.get('default_model', 'N/A')
                print(f"   {name}: {enabled} (默认模型: {model})")
        else:
            print("   ⚠️ 未注册任何服务商")
            print("   原因: 可能没有配置任何AI密钥")
        
        # 显示当前服务商
        current = gateway.current_provider
        if current:
            print(f"\n🎯 当前服务商: {current}")
        else:
            print(f"\n⚠️ 未设置当前服务商")
        
    except Exception as e:
        print(f"❌ AI网关检查失败: {e}")
        print(f"   详细错误: {type(e).__name__}")
    
    print()

def provide_recommendations():
    """提供建议"""
    print("=" * 60)
    print("💡 建议")
    print("=" * 60)
    
    print("""
如果您的密钥丢失了，可能的原因：

1. 📁 .env 文件被清空或覆盖
   解决: 从备份恢复，或重新配置

2. 🔄 代码更新覆盖了配置
   解决: 检查 git 历史，恢复配置

3. 🗂️ 配置在 JSON 文件中，但文件被重置
   解决: 从备份恢复，或重新配置

4. 🌐 配置在系统环境变量中，重启后丢失
   解决: 将配置写入 .env 文件

推荐的配置方式:
1. 在 server/.env 文件中配置（推荐）
2. 至少配置一个主要服务商（如 Gemini 或 通义千问）
3. 定期备份 .env 文件

配置示例:
```
DEFAULT_AI_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
```
""")

def main():
    """主函数"""
    print("\n")
    print("🔍 AI配置诊断工具")
    print("=" * 60)
    print()
    
    # 执行所有检查
    check_env_file()
    check_json_config()
    check_env_variables()
    check_ai_gateway()
    provide_recommendations()
    
    print("=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

