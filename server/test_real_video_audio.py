#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实视频文件音频测试脚本
用于测试音频门控算法在真实抖音直播视频上的表现
"""

import os
import sys
import numpy as np
import librosa
from pathlib import Path
from datetime import datetime

# 尝试导入moviepy
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    print("警告: moviepy未正确安装，尝试使用ffmpeg直接提取音频")
    VideoFileClip = None

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.audio_gate import is_speech_like

class RealVideoAudioTester:
    def __init__(self, video_path):
        """
        初始化真实视频音频测试器
        
        Args:
            video_path: 视频文件路径
        """
        self.video_path = video_path
        self.results = []
        
    def extract_audio_from_video(self, output_path=None):
        """
        从视频文件中提取音频
        
        Args:
            output_path: 输出音频文件路径，如果为None则自动生成
            
        Returns:
            str: 提取的音频文件路径
        """
        print(f"正在从视频文件提取音频: {self.video_path}")
        
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        
        # 生成输出路径
        if output_path is None:
            video_name = Path(self.video_path).stem
            output_path = f"extracted_audio_{video_name}.wav"
        
        try:
            # 使用moviepy提取音频
            if VideoFileClip is None:
                raise ImportError("MoviePy not available")
                
            video = VideoFileClip(self.video_path)
            audio = video.audio
            
            if audio is None:
                raise ValueError("视频文件中没有音频轨道")
            
            # 导出音频为WAV格式
            audio.write_audiofile(output_path, verbose=False, logger=None)
            
            # 清理资源
            audio.close()
            video.close()
            
            print(f"音频提取完成: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"MoviePy音频提取失败: {str(e)}")
            # 尝试使用ffmpeg直接提取
            return self._extract_audio_with_ffmpeg(output_path)
    
    def _extract_audio_with_ffmpeg(self, output_path):
        """
        使用ffmpeg直接提取音频
        """
        import subprocess
        
        try:
            print("尝试使用ffmpeg直接提取音频...")
            cmd = [
                'ffmpeg', '-i', self.video_path, 
                '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '44100', '-ac', '2', 
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"ffmpeg音频提取完成: {output_path}")
                return output_path
            else:
                raise Exception(f"ffmpeg错误: {result.stderr}")
                
        except FileNotFoundError:
            print("错误: 未找到ffmpeg，请安装ffmpeg或moviepy")
            raise
        except Exception as e:
            print(f"ffmpeg音频提取失败: {str(e)}")
            raise
    
    def analyze_audio_segments(self, audio_path, segment_duration=2.0):
        """
        分析音频片段
        
        Args:
            audio_path: 音频文件路径
            segment_duration: 每个片段的时长（秒）
            
        Returns:
            list: 分析结果列表
        """
        print(f"正在分析音频文件: {audio_path}")
        
        # 加载音频
        y, sr = librosa.load(audio_path, sr=None)
        total_duration = len(y) / sr
        
        print(f"音频总时长: {total_duration:.2f}秒")
        print(f"采样率: {sr}Hz")
        
        # 分段分析
        segment_samples = int(segment_duration * sr)
        num_segments = int(np.ceil(len(y) / segment_samples))
        
        results = []
        
        for i in range(num_segments):
            start_idx = i * segment_samples
            end_idx = min((i + 1) * segment_samples, len(y))
            segment = y[start_idx:end_idx]
            
            # 跳过太短的片段
            if len(segment) < sr * 0.5:  # 至少0.5秒
                continue
            
            start_time = start_idx / sr
            end_time = end_idx / sr
            
            print(f"分析片段 {i+1}/{num_segments}: {start_time:.1f}s - {end_time:.1f}s")
            
            # 使用音频门控算法分析
            try:
                # 转换为PCM16格式
                pcm16_data = (segment * 32767).astype(np.int16).tobytes()
                is_speech, details = is_speech_like(pcm16_data, sr)
                
                # 计算额外的音频特征
                rms = np.sqrt(np.mean(segment**2))
                spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)[0].mean()
                zero_crossing_rate = librosa.feature.zero_crossing_rate(segment)[0].mean()
                
                result = {
                    'segment_id': i + 1,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'is_speech': is_speech,
                    'details': details,
                    'rms': rms,
                    'spectral_centroid': spectral_centroid,
                    'zero_crossing_rate': zero_crossing_rate,
                    'audio_data': segment  # 保存音频数据用于进一步分析
                }
                
                results.append(result)
                
                # 打印实时结果
                status = "✅ 语音" if is_speech else "❌ 非语音/音乐"
                print(f"  结果: {status} | RMS: {rms:.4f} | 频谱质心: {spectral_centroid:.1f}Hz")
                
            except Exception as e:
                print(f"  分析失败: {str(e)}")
                continue
        
        self.results = results
        return results
    
    def generate_detailed_report(self):
        """
        生成详细的分析报告
        """
        if not self.results:
            print("没有分析结果可用于生成报告")
            return
        
        print("\n" + "="*80)
        print("真实视频音频分析详细报告")
        print("="*80)
        
        # 基本统计
        total_segments = len(self.results)
        speech_segments = sum(1 for r in self.results if r['is_speech'])
        non_speech_segments = total_segments - speech_segments
        
        total_duration = sum(r['duration'] for r in self.results)
        speech_duration = sum(r['duration'] for r in self.results if r['is_speech'])
        non_speech_duration = total_duration - speech_duration
        
        print(f"\n📊 基本统计:")
        print(f"  总片段数: {total_segments}")
        print(f"  语音片段: {speech_segments} ({speech_segments/total_segments*100:.1f}%)")
        print(f"  非语音片段: {non_speech_segments} ({non_speech_segments/total_segments*100:.1f}%)")
        print(f"  总时长: {total_duration:.1f}秒")
        print(f"  语音时长: {speech_duration:.1f}秒 ({speech_duration/total_duration*100:.1f}%)")
        print(f"  非语音时长: {non_speech_duration:.1f}秒 ({non_speech_duration/total_duration*100:.1f}%)")
        
        # 音频特征统计
        speech_results = [r for r in self.results if r['is_speech']]
        non_speech_results = [r for r in self.results if not r['is_speech']]
        
        print(f"\n🎵 音频特征对比:")
        if speech_results:
            speech_rms_avg = np.mean([r['rms'] for r in speech_results])
            speech_centroid_avg = np.mean([r['spectral_centroid'] for r in speech_results])
            speech_zcr_avg = np.mean([r['zero_crossing_rate'] for r in speech_results])
            
            print(f"  语音片段平均特征:")
            print(f"    RMS: {speech_rms_avg:.4f}")
            print(f"    频谱质心: {speech_centroid_avg:.1f}Hz")
            print(f"    过零率: {speech_zcr_avg:.4f}")
        
        if non_speech_results:
            non_speech_rms_avg = np.mean([r['rms'] for r in non_speech_results])
            non_speech_centroid_avg = np.mean([r['spectral_centroid'] for r in non_speech_results])
            non_speech_zcr_avg = np.mean([r['zero_crossing_rate'] for r in non_speech_results])
            
            print(f"  非语音片段平均特征:")
            print(f"    RMS: {non_speech_rms_avg:.4f}")
            print(f"    频谱质心: {non_speech_centroid_avg:.1f}Hz")
            print(f"    过零率: {non_speech_zcr_avg:.4f}")
        
        # 时间线分析
        print(f"\n⏰ 时间线分析:")
        print("  时间段 | 状态 | RMS | 频谱质心 | 过零率")
        print("  " + "-"*60)
        
        for result in self.results[:20]:  # 显示前20个片段
            status = "语音" if result['is_speech'] else "非语音"
            print(f"  {result['start_time']:5.1f}s-{result['end_time']:5.1f}s | {status:4s} | "
                  f"{result['rms']:6.4f} | {result['spectral_centroid']:8.1f}Hz | {result['zero_crossing_rate']:6.4f}")
        
        if len(self.results) > 20:
            print(f"  ... (还有 {len(self.results)-20} 个片段)")
        
        # 连续性分析
        print(f"\n🔄 连续性分析:")
        speech_blocks = []
        non_speech_blocks = []
        
        current_block = None
        for result in self.results:
            if current_block is None:
                current_block = {
                    'type': 'speech' if result['is_speech'] else 'non_speech',
                    'start_time': result['start_time'],
                    'end_time': result['end_time'],
                    'count': 1
                }
            elif (result['is_speech'] and current_block['type'] == 'speech') or \
                 (not result['is_speech'] and current_block['type'] == 'non_speech'):
                # 继续当前块
                current_block['end_time'] = result['end_time']
                current_block['count'] += 1
            else:
                # 开始新块
                if current_block['type'] == 'speech':
                    speech_blocks.append(current_block)
                else:
                    non_speech_blocks.append(current_block)
                
                current_block = {
                    'type': 'speech' if result['is_speech'] else 'non_speech',
                    'start_time': result['start_time'],
                    'end_time': result['end_time'],
                    'count': 1
                }
        
        # 添加最后一个块
        if current_block:
            if current_block['type'] == 'speech':
                speech_blocks.append(current_block)
            else:
                non_speech_blocks.append(current_block)
        
        print(f"  连续语音块数: {len(speech_blocks)}")
        if speech_blocks:
            avg_speech_duration = np.mean([b['end_time'] - b['start_time'] for b in speech_blocks])
            max_speech_duration = max([b['end_time'] - b['start_time'] for b in speech_blocks])
            print(f"    平均持续时间: {avg_speech_duration:.1f}秒")
            print(f"    最长持续时间: {max_speech_duration:.1f}秒")
        
        print(f"  连续非语音块数: {len(non_speech_blocks)}")
        if non_speech_blocks:
            avg_non_speech_duration = np.mean([b['end_time'] - b['start_time'] for b in non_speech_blocks])
            max_non_speech_duration = max([b['end_time'] - b['start_time'] for b in non_speech_blocks])
            print(f"    平均持续时间: {avg_non_speech_duration:.1f}秒")
            print(f"    最长持续时间: {max_non_speech_duration:.1f}秒")
        
        # 算法性能评估
        print(f"\n⚡ 算法性能评估:")
        print("  基于真实抖音直播视频的测试结果:")
        
        if speech_duration > 0 and non_speech_duration > 0:
            print(f"  ✅ 能够区分语音和非语音内容")
            print(f"  📈 语音检测覆盖率: {speech_duration/total_duration*100:.1f}%")
            
            # 判断是否过度过滤
            if speech_duration / total_duration < 0.1:
                print(f"  ⚠️  警告: 语音检测率较低，可能存在过度过滤")
            elif speech_duration / total_duration > 0.8:
                print(f"  ⚠️  警告: 语音检测率较高，可能存在欠过滤")
            else:
                print(f"  ✅ 语音检测率适中，算法表现良好")
        
        print(f"\n🎯 总体评估:")
        if 0.2 <= speech_duration / total_duration <= 0.7:
            print("  ✅ 优秀 - 算法在真实视频上表现良好")
        elif 0.1 <= speech_duration / total_duration < 0.2 or 0.7 < speech_duration / total_duration <= 0.9:
            print("  ⚠️  良好 - 算法基本可用，但可能需要微调")
        else:
            print("  ❌ 需要改进 - 算法在真实视频上表现不佳")
    
    def save_results_to_file(self, output_file=None):
        """
        保存分析结果到文件
        
        Args:
            output_file: 输出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"real_video_audio_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("真实视频音频分析结果\n")
            f.write("="*50 + "\n")
            f.write(f"视频文件: {self.video_path}\n")
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in self.results:
                status = "语音" if result['is_speech'] else "非语音"
                f.write(f"片段 {result['segment_id']}: {result['start_time']:.1f}s-{result['end_time']:.1f}s | "
                       f"{status} | RMS: {result['rms']:.4f} | "
                       f"频谱质心: {result['spectral_centroid']:.1f}Hz\n")
        
        print(f"分析结果已保存到: {output_file}")

def main():
    """主函数"""
    # 视频文件路径
    video_path = r"d:\gsxm\timao-douyin-live-manager\StreamCap\downloads\抖音\@金\@金_2025-10-27_18-15-18_000.mp4"
    
    print("="*80)
    print("真实视频音频测试程序")
    print("="*80)
    
    try:
        # 创建测试器
        tester = RealVideoAudioTester(video_path)
        
        # 提取音频
        audio_path = tester.extract_audio_from_video()
        
        # 分析音频
        results = tester.analyze_audio_segments(audio_path, segment_duration=2.0)
        
        # 生成报告
        tester.generate_detailed_report()
        
        # 保存结果
        tester.save_results_to_file()
        
        # 清理临时音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"已清理临时音频文件: {audio_path}")
        
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()