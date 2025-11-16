#!/usr/bin/env python3
"""
测试SenseVoice + VAD模型
使用sessions目录中的音频文件进行测试
"""
import asyncio
import os
import sys
from pathlib import Path
import subprocess
import tempfile

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from server.modules.ast.sensevoice_service import SenseVoiceConfig, SenseVoiceService


def pcm_to_wav(pcm_path: str, wav_path: str, sample_rate: int = 16000, channels: int = 1):
    """将PCM文件转换为WAV格式"""
    cmd = [
        'ffmpeg', '-y',
        '-f', 's16le',
        '-ar', str(sample_rate),
        '-ac', str(channels),
        '-i', pcm_path,
        wav_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def mp4_to_wav(mp4_path: str, wav_path: str):
    """从MP4提取音频为WAV格式"""
    cmd = [
        'ffmpeg', '-y',
        '-i', mp4_path,
        '-ar', '16000',
        '-ac', '1',
        '-f', 'wav',
        wav_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)


async def test_audio_file(service: SenseVoiceService, audio_path: Path, file_type: str):
    """测试单个音频文件"""
    print(f"\n{'='*80}")
    print(f"📁 测试文件: {audio_path.name}")
    print(f"📊 文件类型: {file_type}")
    print(f"📏 文件大小: {audio_path.stat().st_size / 1024:.2f} KB")
    print(f"{'='*80}")
    
    # 转换为WAV格式（临时文件）
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        wav_path = tmp_wav.name
    
    try:
        print("🔄 转换音频格式...")
        if file_type == 'pcm':
            pcm_to_wav(str(audio_path), wav_path)
        elif file_type == 'mp4':
            mp4_to_wav(str(audio_path), wav_path)
        else:
            print(f"❌ 不支持的文件类型: {file_type}")
            return
        
        print(f"✅ 转换完成: {Path(wav_path).stat().st_size / 1024:.2f} KB")
        
        # 进行语音转写
        print("🎙️  开始语音转写...")
        result = await service.transcribe_file(wav_path)
        
        if result and result.get('text'):
            text = result['text'].strip()
            print(f"\n✅ 转写成功!")
            print(f"📝 识别文本: {text}")
            print(f"🎯 文本长度: {len(text)} 字")
            
            # 显示详细信息
            if 'language' in result:
                print(f"🌍 语言: {result['language']}")
            if 'duration' in result:
                print(f"⏱️  音频时长: {result['duration']:.2f}秒")
        else:
            print("⚠️  转写结果为空")
            print(f"📋 完整结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件
        try:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except:
            pass


async def main():
    print("🚀 开始测试 SenseVoice + VAD 模型")
    print("="*80)
    
    # 初始化SenseVoice服务
    print("\n📦 初始化SenseVoice服务...")
    config = SenseVoiceConfig(
        model_id="iic/SenseVoiceSmall",
        vad_model_id="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
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
    print(f"   - 模型ID: {model_info.get('model_id', 'N/A')}")
    print(f"   - VAD模型: {model_info.get('vad_model', 'N/A')}")
    print(f"   - 后端: {model_info.get('backend', 'PyTorch')}")
    
    # 查找测试音频文件
    sessions_dir = Path(__file__).parent / "records" / "sessions"
    print(f"\n🔍 扫描音频文件目录: {sessions_dir}")
    
    audio_files = []
    
    # 查找PCM和MP4文件
    for session_dir in sessions_dir.iterdir():
        if session_dir.is_dir():
            for file_path in session_dir.iterdir():
                if file_path.suffix == '.pcm':
                    audio_files.append((file_path, 'pcm'))
                elif file_path.suffix == '.mp4':
                    audio_files.append((file_path, 'mp4'))
    
    print(f"📊 找到 {len(audio_files)} 个音频文件")
    
    if not audio_files:
        print("⚠️  未找到音频文件")
        return
    
    # 测试前5个文件
    test_count = min(5, len(audio_files))
    print(f"\n🎯 将测试前 {test_count} 个文件")
    
    success_count = 0
    for i, (audio_path, file_type) in enumerate(audio_files[:test_count], 1):
        print(f"\n\n{'#'*80}")
        print(f"# 测试 {i}/{test_count}")
        print(f"{'#'*80}")
        
        try:
            await test_audio_file(service, audio_path, file_type)
            success_count += 1
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 清理
    print("\n\n🧹 清理资源...")
    await service.cleanup()
    
    # 最终统计
    print("\n" + "="*80)
    print("📊 测试统计")
    print("="*80)
    print(f"✅ 成功: {success_count}/{test_count}")
    print(f"❌ 失败: {test_count - success_count}/{test_count}")
    print(f"📈 成功率: {success_count/test_count*100:.1f}%")
    print("\n🎉 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())

