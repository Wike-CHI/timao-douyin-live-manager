#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频格式转换工具
将各种音频格式转换为讯飞API需要的PCM格式
"""

import subprocess
from pathlib import Path
from loguru import logger


class AudioConverter:
    """音频格式转换器"""
    
    @staticmethod
    def convert_to_pcm(input_file: str, output_file: str = None) -> str:
        """
        将音频文件转换为PCM格式（16k采样率，16bit，单声道）
        
        Args:
            input_file: 输入音频文件路径（支持mp3, wav, m4a等）
            output_file: 输出PCM文件路径（可选，默认在同目录生成.pcm文件）
            
        Returns:
            转换后的PCM文件路径
        """
        input_path = Path(input_file)
        
        if output_file is None:
            output_file = input_path.with_suffix(".pcm")
        
        try:
            # 使用ffmpeg转换
            cmd = [
                "ffmpeg",
                "-i", str(input_file),  # 输入文件
                "-ar", "16000",         # 采样率16k
                "-ac", "1",             # 单声道
                "-f", "s16le",          # 16bit PCM
                "-y",                   # 覆盖输出文件
                str(output_file)        # 输出文件
            ]
            
            logger.info(f"开始转换: {input_file} -> {output_file}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"转换成功: {output_file}")
                return str(output_file)
            else:
                logger.error(f"转换失败: {result.stderr}")
                raise RuntimeError(f"ffmpeg转换失败: {result.stderr}")
                
        except FileNotFoundError:
            logger.error("ffmpeg未安装，请先安装: apt-get install ffmpeg")
            raise
        except subprocess.TimeoutExpired:
            logger.error("转换超时（5分钟）")
            raise
        except Exception as e:
            logger.error(f"转换异常: {e}")
            raise
    
    @staticmethod
    def get_audio_info(audio_file: str) -> dict:
        """
        获取音频文件信息
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            音频信息字典
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # 提取关键信息
                audio_stream = next(
                    (s for s in info.get("streams", []) if s["codec_type"] == "audio"),
                    {}
                )
                
                return {
                    "duration": float(info.get("format", {}).get("duration", 0)),
                    "sample_rate": int(audio_stream.get("sample_rate", 0)),
                    "channels": int(audio_stream.get("channels", 0)),
                    "codec": audio_stream.get("codec_name", "unknown"),
                    "size": int(info.get("format", {}).get("size", 0)),
                }
            else:
                logger.error(f"获取音频信息失败: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"获取音频信息异常: {e}")
            return {}


# 使用示例
if __name__ == "__main__":
    converter = AudioConverter()
    
    # 示例：转换MP3到PCM
    # pcm_file = converter.convert_to_pcm("input.mp3")
    # print(f"转换完成: {pcm_file}")
    
    # 示例：获取音频信息
    # info = converter.get_audio_info("input.mp3")
    # print(f"音频信息: {info}")

