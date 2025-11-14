#!/usr/bin/env python3
"""
简单测试SenseVoice + VAD模型
"""
import asyncio
import os
import sys
from pathlib import Path

# 强制使用CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from server.modules.ast.sensevoice_service import SenseVoiceConfig, SenseVoiceService


async def test_sensevoice():
    """测试SenseVoice服务"""
    print("=" * 80)
    print("🚀 测试 SenseVoice + VAD 模型")
    print("=" * 80)
    
    # 初始化SenseVoice服务
    print("\n📦 初始化SenseVoice服务...")
    
    # 确保使用本地模型
    project_root = Path(__file__).parent
    local_sensevoice = project_root / "server" / "models" / "models" / "iic" / "SenseVoiceSmall"
    local_vad = project_root / "server" / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    
    print(f"📂 本地SenseVoice模型: {local_sensevoice}")
    print(f"   存在: {local_sensevoice.exists()}")
    print(f"📂 本地VAD模型: {local_vad}")
    print(f"   存在: {local_vad.exists()}")
    
    config = SenseVoiceConfig(
        model_id=str(local_sensevoice) if local_sensevoice.exists() else "iic/SenseVoiceSmall",
        vad_model_id=str(local_vad) if local_vad.exists() else "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    )
    
    service = SenseVoiceService(config)
    
    print("⏳ 正在加载模型（首次加载需要10-15秒）...")
    success = await service.initialize()
    
    if not success:
        print("❌ 模型初始化失败")
        return
    
    print("✅ 模型初始化成功")
    
    # 获取模型信息
    model_info = service.get_model_info()
    print(f"\n📋 模型信息:")
    print(f"   模型ID: {model_info.get('model_id', 'N/A')}")
    print(f"   VAD模型: {model_info.get('vad_model', 'N/A')}")
    
    # 查找测试音频文件
    sessions_dir = project_root / "records" / "sessions"
    print(f"\n🔍 查找音频文件: {sessions_dir}")
    
    # 查找第一个PCM文件
    pcm_file = None
    for session_dir in sessions_dir.iterdir():
        if session_dir.is_dir():
            for file_path in session_dir.iterdir():
                if file_path.suffix == '.pcm':
                    pcm_file = file_path
                    break
            if pcm_file:
                break
    
    if not pcm_file:
        print("❌ 未找到PCM音频文件")
        await service.cleanup()
        return
    
    print(f"📁 找到音频文件: {pcm_file.name}")
    print(f"📏 文件大小: {pcm_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 转换PCM为WAV
    import subprocess
    import tempfile
    
    print("\n🔄 转换PCM为WAV格式...")
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        wav_path = tmp_wav.name
    
    try:
        # 转换PCM为WAV（16kHz, 单声道, s16le）
        cmd = [
            'ffmpeg', '-y',
            '-f', 's16le',
            '-ar', '16000',
            '-ac', '1',
            '-i', str(pcm_file),
            '-t', '30',  # 只取前30秒
            wav_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg转换失败: {result.stderr[:500]}")
            return
        
        print(f"✅ 转换完成: {Path(wav_path).stat().st_size / 1024:.2f} KB")
        
        # 进行语音转写
        print("\n🎙️  开始语音转写...")
        print("⏱️  这可能需要一些时间...")
        
        result = await service.transcribe_file(wav_path)
        
        print("\n" + "=" * 80)
        print("📝 转写结果")
        print("=" * 80)
        
        if result and result.get('text'):
            text = result['text'].strip()
            print(f"\n✅ 转写成功!")
            print(f"\n识别文本:\n{text}\n")
            print(f"📊 统计:")
            print(f"   - 字数: {len(text)} 字")
            if 'language' in result:
                print(f"   - 语言: {result['language']}")
        else:
            print("⚠️  转写结果为空")
            print(f"完整结果: {result}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        
        # 清理服务
        print("\n🧹 清理资源...")
        await service.cleanup()
    
    print("\n🎉 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_sensevoice())

