# -*- coding: utf-8 -*-
"""
真实VOSK语音识别测试
录制真实的麦克风音频并进行识别
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加AST模块路径
sys.path.append(str(Path(__file__).parent))

async def test_real_vosk_recognition():
    """测试真实的VOSK语音识别"""
    
    print("🎤 真实VOSK语音识别测试")
    print("=" * 50)
    
    try:
        # 导入模块
        from ast_service import ASTService, TranscriptionResult
        from config import create_ast_config
        
        # 创建配置（使用真实设置）
        config = create_ast_config(
            chunk_duration=2.0,      # 2秒音频块
            min_confidence=0.3,      # 降低置信度阈值以看到更多结果
            save_audio=True          # 保存音频文件用于调试
        )
        
        # 创建AST服务
        service = ASTService(config)
        
        # 转录结果计数器
        transcription_count = 0
        
        def transcription_callback(result: TranscriptionResult):
            """转录结果回调"""
            nonlocal transcription_count
            transcription_count += 1
            
            # 显示转录结果
            confidence_emoji = "🟢" if result.confidence > 0.7 else "🟡" if result.confidence > 0.4 else "🔴"
            type_emoji = "✅" if result.is_final else "⏳"
            
            print(f"\n{type_emoji} 转录 #{transcription_count}")
            print(f"文本: {result.text}")
            print(f"置信度: {confidence_emoji} {result.confidence:.2f}")
            print(f"类型: {'最终结果' if result.is_final else '临时结果'}")
            print(f"时间: {result.timestamp}")
            
            if result.words:
                words_info = []
                for word in result.words:
                    if isinstance(word, dict):
                        words_info.append(f"{word.get('word', '')}")
                print(f"词汇: {' | '.join(words_info)}")
            
            print("-" * 40)
        
        # 添加回调
        service.add_transcription_callback("real_test", transcription_callback)
        
        # 初始化服务
        print("⏳ 正在初始化AST服务...")
        if await service.initialize():
            print("✅ AST服务初始化成功")
            
            # 获取服务状态
            status = service.get_status()
            vosk_info = status.get("vosk_info", {})
            print(f"📊 VOSK状态: {vosk_info.get('status', '未知')}")
            print(f"📁 模型路径: {vosk_info.get('model_path', '未知')}")
            print(f"🎯 部署模式: {vosk_info.get('deployment_mode', '未知')}")
            
            # 开始录音和转录
            print("\n🎤 开始录音转录测试...")
            print("请对着麦克风说话，测试将持续15秒")
            print("建议说一些简单的中文短句，比如：")
            print("- 你好世界")
            print("- 今天天气很好")
            print("- 测试语音识别")
            print("- 一二三四五")
            
            if await service.start_transcription("real_test_room"):
                print("✅ 转录已开始")
                
                # 运行15秒
                for i in range(15):
                    await asyncio.sleep(1)
                    print(f"⏱️ 录音中... {i+1}/15秒", end="\r")
                
                print("\n\n⏹️ 停止录音...")
                await service.stop_transcription()
                
                # 显示最终统计
                final_status = service.get_status()
                stats = final_status.get("stats", {})
                
                print("\n" + "=" * 50)
                print("📊 测试结果统计:")
                print(f"总转录次数: {stats.get('successful_transcriptions', 0)}")
                print(f"失败次数: {stats.get('failed_transcriptions', 0)}")
                print(f"平均置信度: {stats.get('average_confidence', 0):.2f}")
                print(f"音频块总数: {stats.get('total_audio_chunks', 0)}")
                
                if transcription_count > 0:
                    print("🎉 真实语音识别测试完成！")
                    
                    # 检查是否使用了真实VOSK
                    if vosk_info.get('deployment_mode') == 'direct_integration':
                        print("✅ 使用了真实VOSK模型进行识别")
                    else:
                        print("⚠️ 使用了模拟服务")
                else:
                    print("⚠️ 没有识别到任何语音内容")
                    print("可能原因:")
                    print("- 麦克风没有正确配置")
                    print("- 环境噪音太大")
                    print("- 说话声音太小")
                    print("- VOSK模型加载失败")
            else:
                print("❌ 转录启动失败")
        else:
            print("❌ AST服务初始化失败")
            print("可能原因:")
            print("- VOSK模型文件不存在或损坏")
            print("- 麦克风设备不可用")
            print("- 权限问题")
        
        # 清理
        await service.cleanup()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 启动真实VOSK语音识别测试")
    asyncio.run(test_real_vosk_recognition())