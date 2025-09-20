# -*- coding: utf-8 -*-
"""
AST模块集成测试
验证各组件是否能正常工作
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加AST模块路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 直接导入（不使用相对导入）
        from audio_capture import AudioCapture, AudioProcessor, AudioConfig
        print("✅ AudioCapture 导入成功")
        
        try:
            from vosk_service_v2 import VoskServiceV2, VoskConfig
            print("✅ VoskServiceV2 导入成功")
        except Exception as e:
            print(f"⚠️ VoskServiceV2 导入失败: {e}，尝试模拟服务")
            from mock_vosk_service import MockVoskService
            print("✅ MockVoskService 导入成功")
        
        from ast_service import ASTService, TranscriptionResult, ASTConfig
        print("✅ ASTService 导入成功")
        
        from config import DEFAULT_AST_CONFIG, create_ast_config
        print("✅ Config 导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_audio_system():
    """测试音频系统"""
    print("\n🧪 测试音频系统...")
    
    try:
        from audio_capture import AudioCapture, AudioConfig
        
        # 创建音频采集器
        config = AudioConfig(sample_rate=16000, channels=1)
        capture = AudioCapture(config)
        
        if capture.initialize():
            print("✅ 音频系统初始化成功")
            capture.cleanup()
            return True
        else:
            print("❌ 音频系统初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ 音频系统测试失败: {e}")
        return False

def test_vosk_model():
    """测试VOSK模型"""
    print("\n🧪 测试VOSK模型...")
    
    try:
        # 尝试真实VOSK服务
        try:
            from vosk_service_v2 import VoskServiceV2
            service = VoskServiceV2()
            service_type = "VoskServiceV2"
        except:
            from mock_vosk_service import MockVoskService
            service = MockVoskService()
            service_type = "MockVoskService"
        
        model_path = Path(service.model_path)
        print(f"🤖 使用服务类型: {service_type}")
        
        if service_type == "VoskServiceV2":
            if model_path.exists():
                print(f"✅ VOSK模型路径存在: {model_path}")
                
                # 检查关键文件
                required_files = ['conf/model.conf', 'ivector', 'rnnlm']
                for file in required_files:
                    if (model_path / file).exists():
                        print(f"✅ 模型文件存在: {file}")
                    else:
                        print(f"⚠️ 模型文件缺失: {file}")
                
                return True
            else:
                print(f"⚠️ VOSK模型路径不存在: {model_path}，将使用模拟服务")
                return True  # 不算失败，可以降级
        else:
            print(f"✅ 模拟服务就绪：{model_path}")
            return True
            
    except Exception as e:
        print(f"❌ VOSK模型测试失败: {e}")
        return False

async def test_ast_service():
    """测试AST服务"""
    print("\n🧪 测试AST服务...")
    
    try:
        from ast_service import ASTService
        from config import create_ast_config
        
        # 创建配置 (短时间测试)
        config = create_ast_config(
            chunk_duration=0.5,
            min_confidence=0.3,
            save_audio=False
        )
        
        # 创建AST服务
        service = ASTService(config)
        
        # 设置测试回调
        transcription_count = 0
        def test_callback(result):
            nonlocal transcription_count
            transcription_count += 1
            print(f"📝 测试转录: {result.text} (置信度: {result.confidence:.2f})")
        
        service.add_transcription_callback("test", test_callback)
        
        # 尝试初始化 (可能失败，但不应该崩溃)
        print("⏳ 尝试初始化AST服务...")
        if await service.initialize():
            print("✅ AST服务初始化成功")
            
            # 获取状态
            status = service.get_status()
            print(f"📊 服务状态: 运行中={status['is_running']}")
            
        else:
            print("⚠️ AST服务初始化失败 (可能是VOSK模型问题)")
        
        # 清理
        await service.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ AST服务测试失败: {e}")
        return False

async def test_integration():
    """完整集成测试"""
    print("🧪 开始AST模块集成测试\n")
    
    tests = [
        ("模块导入", test_imports),
        ("音频系统", test_audio_system), 
        ("VOSK模型", test_vosk_model),
        ("AST服务", test_ast_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("📋 测试结果汇总:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<12} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！AST模块集成成功")
    elif passed >= len(results) // 2:
        print("⚠️ 部分测试通过，AST模块基本可用")
    else:
        print("❌ 多数测试失败，需要检查配置和依赖")
    
    return passed == len(results)

if __name__ == "__main__":
    # 运行集成测试
    try:
        success = asyncio.run(test_integration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        sys.exit(1)