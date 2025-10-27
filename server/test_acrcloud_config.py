# -*- coding: utf-8 -*-
"""
ACRCloud 配置测试脚本
测试 ACRCloud 音乐识别服务的配置是否正确
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "server"))

# Windows 编码设置
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def load_env_file():
    """加载 .env 文件"""
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"错误: .env 文件不存在: {env_file}")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    
    return True

def test_acrcloud_config():
    """测试 ACRCloud 配置"""
    print("=" * 60)
    print("ACRCloud 配置测试")
    print("=" * 60)
    
    # 加载环境变量
    if not load_env_file():
        return False
    
    # 检查必需的环境变量
    required_vars = [
        'ACR_HOST',
        'ACR_ACCESS_KEY', 
        'ACR_SECRET_KEY'
    ]
    
    optional_vars = [
        'ACR_ENABLE',
        'ACR_MIN_SCORE',
        'ACR_TIMEOUT',
        'LIVE_ACR_SEGMENT_SEC',
        'LIVE_ACR_COOLDOWN_SEC',
        'LIVE_ACR_MATCH_HOLD_SEC'
    ]
    
    print("\n1. 环境变量检查:")
    print("-" * 40)
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != 'your_access_key_here' and value != 'your_secret_key_here':
            print(f"  [OK] {var}: {value[:10]}..." if len(value) > 10 else f"  [OK] {var}: {value}")
        else:
            print(f"  [缺失] {var}: 未配置或使用默认值")
            missing_vars.append(var)
    
    print("\n2. 可选配置检查:")
    print("-" * 40)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  [OK] {var}: {value}")
        else:
            print(f"  [默认] {var}: 使用默认值")
    
    if missing_vars:
        print(f"\n错误: 缺少必需的配置项: {', '.join(missing_vars)}")
        print("\n请按照以下步骤配置:")
        print("1. 注册 ACRCloud 账号: https://www.acrcloud.com/")
        print("2. 创建项目并获取 Access Key 和 Secret Key")
        print("3. 在 .env 文件中配置相应的环境变量")
        return False
    
    # 测试 ACRCloud 客户端加载
    print("\n3. ACRCloud 客户端测试:")
    print("-" * 40)
    
    try:
        from AST_module.acrcloud_client import load_acr_client_from_env
        
        client, error = load_acr_client_from_env()
        
        if client:
            print("  [OK] ACRCloud 客户端创建成功")
            print(f"  [OK] 服务器: {os.getenv('ACR_HOST')}")
            print(f"  [OK] 最小分数: {os.getenv('ACR_MIN_SCORE', '0.65')}")
            print(f"  [OK] 超时时间: {os.getenv('ACR_TIMEOUT', '10')}秒")
            
            # 测试配置参数
            acr_enable = os.getenv('ACR_ENABLE', '0')
            if acr_enable == '1':
                print("  [OK] ACRCloud 服务已启用")
            else:
                print("  [警告] ACRCloud 服务未启用 (ACR_ENABLE=0)")
            
            return True
        else:
            print(f"  [错误] ACRCloud 客户端创建失败: {error}")
            return False
            
    except ImportError as e:
        print(f"  [错误] 无法导入 ACRCloud 模块: {e}")
        print("  请确保已安装 acrcloud_sdk_python:")
        print("  pip install acrcloud_sdk_python")
        return False
    except Exception as e:
        print(f"  [错误] 测试过程中出现异常: {e}")
        return False

def test_acrcloud_sdk():
    """测试 ACRCloud SDK 安装"""
    print("\n4. ACRCloud SDK 安装检查:")
    print("-" * 40)
    
    try:
        import acrcloud
        print("  [OK] acrcloud_sdk_python 已安装")
        
        # 检查版本
        try:
            version = acrcloud.__version__
            print(f"  [OK] SDK 版本: {version}")
        except:
            print("  [OK] SDK 已安装 (无法获取版本信息)")
        
        return True
    except ImportError:
        print("  [错误] acrcloud_sdk_python 未安装")
        print("  请运行: pip install acrcloud_sdk_python")
        return False

def main():
    """主函数"""
    print("ACRCloud 音乐识别服务配置测试")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 测试 SDK 安装
    sdk_ok = test_acrcloud_sdk()
    
    # 测试配置
    config_ok = test_acrcloud_config()
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    if sdk_ok and config_ok:
        print("状态: 配置完成")
        print("ACRCloud 音乐识别服务已正确配置，可以正常使用")
        
        print("\n下一步操作:")
        print("1. 启动服务: python -m uvicorn app.main:app --host 0.0.0.0 --port 10090")
        print("2. 查看状态: curl http://localhost:10090/api/live_audio/status")
        print("3. 查看文档: docs/ACRCloud_Setup_Guide.md")
        
    elif not sdk_ok:
        print("状态: SDK 未安装")
        print("请先安装 ACRCloud SDK: pip install acrcloud_sdk_python")
        
    elif not config_ok:
        print("状态: 配置不完整")
        print("请完善 .env 文件中的 ACRCloud 配置")
        
    else:
        print("状态: 配置失败")
        print("请检查上述错误信息并修复")

if __name__ == "__main__":
    main()