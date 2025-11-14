#!/usr/bin/env python3
"""
简单测试SenseVoice + VAD模型
直接测试音频URL或本地文件
"""
import asyncio
import sys
import subprocess
import tempfile
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 强制使用CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from server.modules.ast.sensevoice_service import SenseVoiceConfig, SenseVoiceService


def download_audio(url: str, output_path: str):
    """下载视频并提取音频为WAV"""
    print(f"📥 下载音频: {url[:80]}...")
    cmd = [
        'ffmpeg', '-y',
        '-i', url,
        '-ar', '16000',
        '-ac', '1',
        '-t', '30',  # 只下载前30秒
        '-f', 'wav',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ FFmpeg错误: {result.stderr[:500]}")
        raise Exception("下载失败")
    print(f"✅ 下载完成: {Path(output_path).stat().st_size / 1024:.2f} KB")


async def test_url(url: str):
    """测试URL音频转写"""
    print("="*80)
    print("🚀 开始测试 SenseVoice + VAD")
    print("="*80)
    
    # 初始化服务
    print("\n📦 初始化SenseVoice服务...")
    config = SenseVoiceConfig(
        model_id="iic/SenseVoiceSmall",
        vad_model_id="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    )
    service = SenseVoiceService(config)
    
    print("⏳ 加载模型（首次需要10-15秒）...")
    success = await service.initialize()
    
    if not success:
        print("❌ 模型初始化失败")
        return
    
    print("✅ 模型初始化成功")
    
    # 显示模型信息
    model_info = service.get_model_info()
    print(f"\n📋 模型信息:")
    print(f"   模型ID: {model_info.get('model_id', 'N/A')}")
    print(f"   VAD: {model_info.get('vad_model', 'N/A')}")
    
    # 下载音频
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        wav_path = tmp.name
    
    try:
        download_audio(url, wav_path)
        
        # 转写
        print("\n🎙️  开始语音转写...")
        result = await service.transcribe_file(wav_path)
        
        print("\n" + "="*80)
        print("📝 转写结果")
        print("="*80)
        
        if result and result.get('text'):
            text = result['text'].strip()
            print(f"✅ 识别成功!")
            print(f"\n文本内容:\n{text}\n")
            print(f"📊 统计:")
            print(f"   - 字数: {len(text)}")
            if 'language' in result:
                print(f"   - 语言: {result['language']}")
            if 'duration' in result:
                print(f"   - 时长: {result['duration']:.2f}秒")
        else:
            print("⚠️  转写结果为空")
            print(f"原始结果: {result}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        await service.cleanup()
    
    print("\n✅ 测试完成!")


async def test_local_files():
    """测试本地音频文件"""
    print("="*80)
    print("🚀 测试本地音频文件")
    print("="*80)
    
    # 初始化服务
    print("\n📦 初始化SenseVoice服务...")
    config = SenseVoiceConfig(
        model_id="iic/SenseVoiceSmall",
        vad_model_id="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    )
    service = SenseVoiceService(config)
    
    print("⏳ 加载模型...")
    success = await service.initialize()
    
    if not success:
        print("❌ 模型初始化失败")
        return
    
    print("✅ 模型初始化成功")
    
    # 查找音频文件
    sessions_dir = Path(__file__).parent / "records" / "sessions"
    audio_files = []
    
    for session_dir in sessions_dir.iterdir():
        if session_dir.is_dir():
            for file_path in session_dir.iterdir():
                if file_path.suffix in ['.mp4', '.pcm']:
                    audio_files.append(file_path)
                    if len(audio_files) >= 3:  # 只测试3个
                        break
            if len(audio_files) >= 3:
                break
    
    print(f"\n📊 找到 {len(audio_files)} 个测试文件")
    
    for i, audio_path in enumerate(audio_files, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(audio_files)}: {audio_path.name}")
        print(f"{'='*80}")
        
        # 转换为WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        
        try:
            if audio_path.suffix == '.mp4':
                cmd = ['ffmpeg', '-y', '-i', str(audio_path), '-ar', '16000', '-ac', '1', '-t', '30', '-f', 'wav', wav_path]
            else:  # pcm
                cmd = ['ffmpeg', '-y', '-f', 's16le', '-ar', '16000', '-ac', '1', '-i', str(audio_path), '-t', '30', '-f', 'wav', wav_path]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 转写
            result = await service.transcribe_file(wav_path)
            
            if result and result.get('text'):
                text = result['text'].strip()
                print(f"✅ 转写成功: {text[:100]}...")
            else:
                print("⚠️  转写为空")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
    
    await service.cleanup()
    print("\n✅ 所有测试完成!")


async def main():
    import sys
    
    # 测试B站视频
    bilibili_url = "https://upos-sz-estgcos.bilivideo.com/upgcxcode/19/86/61698619/61698619-1-30280.m4s?e=ig8euxZM2rNcNbdlhoNvNC8BqJIzNbfqXBvEqxTEto8BTrNvN0GvT90W5JZMkX_YN0MvXg8gNEV4NC8xNEV4N03eN0B5tZlqNxTEto8BTrNvNeZVuJ10Kj_g2UB02J0mN0B5tZlqNCNEto8BTrNvNC7MTX502C8f2jmMQJ6mqF2fka1mqx6gqj0eN0B599M=&uipk=5&platform=pc&os=estgcos&og=cos&oi=2062504548&mid=252020052&trid=7be7d89771a143d1823278c7068565fu&gen=playurlv3&nbs=1&deadline=1763111744&upsig=679288a49a393e3014869eebafbed6ee&uparams=e,uipk,platform,os,og,oi,mid,trid,gen,nbs,deadline&bvc=vod&nettype=0&bw=127197&dl=0&f=u_0_0&agrr=1&buvid=987BD7F9-9916-AC3E-0F01-2249CE575B7E11491infoc&build=0&orderid=0,3"
    
    print("📺 测试B站视频音频转写\n")
    await test_url(bilibili_url)
    
    print("\n\n" + "="*80)
    print("\n📁 测试本地音频文件\n")
    await test_local_files()


if __name__ == "__main__":
    asyncio.run(main())

