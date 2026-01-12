#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频语音转写测试脚本
使用 SenseVoice 模块对视频文件进行语音转写

审查人: 叶维哲
"""

import asyncio
import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger


class VideoTranscriber:
    """视频语音转写器"""
    
    def __init__(self):
        """初始化转写器"""
        self.sensevoice_service = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """初始化 SenseVoice 服务"""
        try:
            from modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig
            
            config = SenseVoiceConfig(
                model_id="iic/SenseVoiceSmall",
                language="auto",
                use_itn=True,
            )
            
            self.sensevoice_service = SenseVoiceService(config)
            success = await self.sensevoice_service.initialize()
            
            if success:
                logger.info("✅ SenseVoice 服务初始化成功")
                self._initialized = True
            else:
                logger.warning("⚠️ SenseVoice 服务初始化失败，将使用模拟转写")
                self._initialized = True  # 允许使用模拟转写
                
            return True
            
        except ImportError as e:
            logger.error(f"❌ 导入 SenseVoice 服务失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False
    
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        从视频文件提取音频并转换为 PCM 格式 (16kHz, mono, 16bit)
        
        Args:
            video_path: 视频文件路径
            output_path: 输出 PCM 文件路径（可选）
            
        Returns:
            PCM 文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 生成输出路径
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = os.path.join(
                tempfile.gettempdir(), 
                f"transcribe_{video_name}_{int(time.time())}.pcm"
            )
        
        # 查找 ffmpeg
        ffmpeg_bin = self._find_ffmpeg()
        
        logger.info(f"📹 正在从视频提取音频: {video_path}")
        
        try:
            cmd = [
                ffmpeg_bin,
                "-i", video_path,    # 输入视频
                "-vn",               # 不要视频
                "-ac", "1",          # 单声道
                "-ar", "16000",      # 16kHz 采样率
                "-f", "s16le",       # 16bit PCM 格式
                "-y",                # 覆盖输出
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 音频提取成功: {output_path}")
                return output_path
            else:
                raise RuntimeError(f"ffmpeg 错误: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("音频提取超时（5分钟）")
        except Exception as e:
            raise RuntimeError(f"音频提取失败: {e}")
    
    def _find_ffmpeg(self) -> str:
        """查找 ffmpeg 可执行文件"""
        import shutil
        
        # 优先使用环境变量
        ffmpeg_bin = os.environ.get("FFMPEG_BIN")
        if ffmpeg_bin and os.path.exists(ffmpeg_bin):
            return ffmpeg_bin
        
        # 尝试 PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # 尝试项目本地工具
        project_root = Path(__file__).parent.parent
        if os.name == "nt":  # Windows
            local_ffmpeg = project_root / "tools" / "ffmpeg" / "win64" / "bin" / "ffmpeg.exe"
        elif sys.platform == "darwin":  # macOS
            local_ffmpeg = project_root / "tools" / "ffmpeg" / "mac" / "bin" / "ffmpeg"
        else:  # Linux
            local_ffmpeg = project_root / "tools" / "ffmpeg" / "linux" / "bin" / "ffmpeg"
        
        if local_ffmpeg.exists():
            return str(local_ffmpeg)
        
        raise FileNotFoundError("未找到 ffmpeg，请安装 ffmpeg 或设置 FFMPEG_BIN 环境变量")
    
    async def transcribe_pcm_file(
        self, 
        pcm_path: str, 
        chunk_duration: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        转写 PCM 文件
        
        Args:
            pcm_path: PCM 文件路径 (16kHz, mono, 16bit)
            chunk_duration: 每个分段的时长（秒）
            
        Returns:
            转写结果列表
        """
        if not self._initialized:
            raise RuntimeError("服务未初始化，请先调用 initialize()")
        
        # 读取 PCM 数据
        with open(pcm_path, 'rb') as f:
            pcm_data = f.read()
        
        logger.info(f"📊 PCM 文件大小: {len(pcm_data) / 1024:.1f} KB")
        
        # 计算音频时长
        sample_rate = 16000
        bytes_per_sample = 2  # 16bit = 2 bytes
        total_samples = len(pcm_data) // bytes_per_sample
        total_duration = total_samples / sample_rate
        
        logger.info(f"⏱️ 音频总时长: {total_duration:.1f} 秒")
        
        # 分段处理
        chunk_samples = int(chunk_duration * sample_rate)
        chunk_bytes = chunk_samples * bytes_per_sample
        
        results = []
        offset = 0
        segment_id = 0
        
        while offset < len(pcm_data):
            segment_id += 1
            chunk = pcm_data[offset:offset + chunk_bytes]
            
            start_time = offset / bytes_per_sample / sample_rate
            end_time = min((offset + len(chunk)) / bytes_per_sample / sample_rate, total_duration)
            
            logger.info(f"🎤 转写分段 {segment_id}: {start_time:.1f}s - {end_time:.1f}s")
            
            try:
                result = await self.sensevoice_service.transcribe_audio(chunk)
                
                text = result.get("text", "").strip()
                confidence = result.get("confidence", 0.0)
                result_type = result.get("type", "unknown")
                
                segment_result = {
                    "segment_id": segment_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "text": text,
                    "confidence": confidence,
                    "type": result_type,
                    "success": result.get("success", True)
                }
                
                results.append(segment_result)
                
                # 打印结果
                if text:
                    logger.success(f"   📝 [{result_type}] {text}")
                else:
                    logger.debug(f"   🔇 [{result_type}] (无语音)")
                    
            except Exception as e:
                logger.error(f"   ❌ 转写失败: {e}")
                results.append({
                    "segment_id": segment_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "text": "",
                    "confidence": 0.0,
                    "type": "error",
                    "success": False,
                    "error": str(e)
                })
            
            offset += chunk_bytes
        
        return results
    
    async def transcribe_video(
        self, 
        video_path: str,
        chunk_duration: float = 5.0
    ) -> Dict[str, Any]:
        """
        转写视频文件
        
        Args:
            video_path: 视频文件路径
            chunk_duration: 每个分段的时长（秒）
            
        Returns:
            完整转写结果
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📽️ 开始转写视频: {video_path}")
        logger.info(f"{'='*60}\n")
        
        pcm_path = None
        try:
            # 1. 提取音频
            pcm_path = self.extract_audio_from_video(video_path)
            
            # 2. 转写
            results = await self.transcribe_pcm_file(pcm_path, chunk_duration)
            
            # 3. 汇总结果
            full_text = " ".join([r["text"] for r in results if r["text"]])
            total_duration = sum(r["duration"] for r in results)
            speech_segments = [r for r in results if r["text"]]
            
            summary = {
                "video_path": video_path,
                "total_duration": total_duration,
                "total_segments": len(results),
                "speech_segments": len(speech_segments),
                "full_transcript": full_text,
                "segments": results,
            }
            
            return summary
            
        finally:
            # 清理临时文件
            if pcm_path and os.path.exists(pcm_path):
                os.remove(pcm_path)
                logger.debug(f"🗑️ 已清理临时文件: {pcm_path}")


def print_transcription_report(result: Dict[str, Any]):
    """打印转写报告"""
    print("\n" + "="*70)
    print("📊 视频语音转写报告")
    print("="*70)
    
    print(f"\n📹 视频文件: {result['video_path']}")
    print(f"⏱️ 总时长: {result['total_duration']:.1f} 秒")
    print(f"🔢 总分段数: {result['total_segments']}")
    print(f"🎤 有语音分段: {result['speech_segments']}")
    
    print("\n" + "-"*70)
    print("📝 完整转写文本:")
    print("-"*70)
    
    if result['full_transcript']:
        print(f"\n{result['full_transcript']}\n")
    else:
        print("\n(未检测到语音内容)\n")
    
    print("-"*70)
    print("📋 分段详情:")
    print("-"*70)
    
    for seg in result['segments']:
        time_str = f"{seg['start_time']:.1f}s - {seg['end_time']:.1f}s"
        if seg['text']:
            print(f"  [{time_str}] {seg['text']}")
        else:
            print(f"  [{time_str}] (静音/无语音)")
    
    print("\n" + "="*70)


async def main():
    """主函数"""
    # 要转写的视频文件列表
    video_files = [
        r"d:\gsxm\timao-douyin-live-manager\server\data\b0722709b58e54faf251f01cf7514d6b.mp4",
        r"d:\gsxm\timao-douyin-live-manager\server\data\5dea5079c6ef031ce4a94d8d95008b6c.mp4",
        r"d:\gsxm\timao-douyin-live-manager\server\data\a365d85f5443af16724c61e0cc3d7df5.mp4",
    ]
    
    # 检查是否有命令行参数指定视频文件
    if len(sys.argv) > 1:
        video_files = sys.argv[1:]
    
    print("="*70)
    print("🎬 视频语音转写测试程序")
    print("="*70)
    print(f"📁 待处理视频数量: {len(video_files)}")
    print()
    
    # 创建转写器
    transcriber = VideoTranscriber()
    
    # 初始化
    success = await transcriber.initialize()
    if not success:
        print("❌ 初始化失败，退出")
        return
    
    # 处理每个视频
    all_results = []
    for video_path in video_files:
        if not os.path.exists(video_path):
            print(f"⚠️ 视频文件不存在，跳过: {video_path}")
            continue
        
        try:
            result = await transcriber.transcribe_video(video_path, chunk_duration=5.0)
            all_results.append(result)
            print_transcription_report(result)
            
        except Exception as e:
            print(f"❌ 转写失败: {video_path}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "="*70)
    print("🏁 转写完成")
    print("="*70)
    print(f"✅ 成功处理: {len(all_results)}/{len(video_files)} 个视频")
    
    # 保存结果到文件
    if all_results:
        import json
        output_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"transcription_results_{int(time.time())}.json"
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"📄 结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

