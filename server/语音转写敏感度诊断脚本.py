#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转写敏感度诊断脚本

用于分析和调试语音转写有时灵敏有时识别不到的问题。
该脚本会检查各个组件的配置参数，并提供优化建议。

使用方法:
    python 语音转写敏感度诊断脚本.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入相关模块
try:
    from app.services.live_audio_stream_service import LiveAudioStreamService
    from AST_module.sensevoice_service import SenseVoiceConfig
    from AST_module.audio_capture import AudioConfig
    from server.audio_gate import is_speech_like
    import numpy as np
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)

class VoiceTranscriptionDiagnostic:
    """语音转写敏感度诊断器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results = {}
        self.recommendations = []
        
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """运行完整诊断"""
        print("=" * 60)
        print("语音转写敏感度诊断工具")
        print("=" * 60)
        
        # 1. 检查LiveAudioStreamService配置
        self._check_live_audio_service()
        
        # 2. 检查音频门控算法
        self._check_audio_gate()
        
        # 3. 检查SenseVoice配置
        self._check_sensevoice_config()
        
        # 4. 检查环境变量
        self._check_environment_variables()
        
        # 5. 生成诊断报告
        self._generate_report()
        
        return self.results
    
    def _check_live_audio_service(self):
        """检查LiveAudioStreamService配置"""
        print("\n1. 检查LiveAudioStreamService配置...")
        
        try:
            service = LiveAudioStreamService()
            
            # VAD参数
            vad_params = {
                "vad_min_rms": service.vad_min_rms,
                "vad_min_speech_sec": service.vad_min_speech_sec,
                "vad_min_silence_sec": service.vad_min_silence_sec,
                "vad_hangover_sec": service.vad_hangover_sec,
                "chunk_seconds": service.chunk_seconds,
                "profile": service.profile
            }
            
            # AGC参数
            agc_params = {
                "agc_enabled": service.agc_enabled,
                "agc_target_rms": service.agc_target_rms,
                "agc_max_gain": service.agc_max_gain,
                "agc_min_gain": service.agc_min_gain,
                "agc_smooth": service.agc_smooth
            }
            
            # 音乐检测参数
            music_params = {
                "music_detection_enabled": service.music_detection_enabled,
                "music_detect_threshold": service.music_detect_threshold,
                "music_rms_boost": service.music_rms_boost,
                "music_min_speech_boost": service.music_min_speech_boost
            }
            
            self.results["live_audio_service"] = {
                "vad_params": vad_params,
                "agc_params": agc_params,
                "music_params": music_params,
                "status": "success"
            }
            
            print(f"  ✓ 当前配置档位: {service.profile}")
            print(f"  ✓ VAD RMS阈值: {service.vad_min_rms}")
            print(f"  ✓ 最小语音时长: {service.vad_min_speech_sec}s")
            print(f"  ✓ 最小静音时长: {service.vad_min_silence_sec}s")
            print(f"  ✓ AGC启用状态: {service.agc_enabled}")
            print(f"  ✓ AGC目标RMS: {service.agc_target_rms}")
            
            # 分析潜在问题
            self._analyze_vad_params(vad_params)
            self._analyze_agc_params(agc_params)
            
        except Exception as e:
            self.results["live_audio_service"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ✗ 检查失败: {e}")
    
    def _check_audio_gate(self):
        """检查音频门控算法"""
        print("\n2. 检查音频门控算法...")
        
        try:
            # 创建测试音频数据
            sample_rate = 16000
            duration = 2.0
            test_audio = np.random.normal(0, 0.1, int(sample_rate * duration)).astype(np.float32)
            
            # 测试不同音量级别的音频
            volume_levels = [0.01, 0.02, 0.05, 0.1, 0.2]
            gate_results = {}
            
            for volume in volume_levels:
                scaled_audio = test_audio * volume
                is_speech = is_speech_like(scaled_audio, sample_rate)
                gate_results[f"volume_{volume}"] = is_speech
                print(f"  音量 {volume}: {'✓ 检测为语音' if is_speech else '✗ 未检测为语音'}")
            
            self.results["audio_gate"] = {
                "test_results": gate_results,
                "status": "success"
            }
            
            # 分析音频门控敏感度
            self._analyze_audio_gate_sensitivity(gate_results)
            
        except Exception as e:
            self.results["audio_gate"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ✗ 检查失败: {e}")
    
    def _check_sensevoice_config(self):
        """检查SenseVoice配置"""
        print("\n3. 检查SenseVoice配置...")
        
        try:
            # 检查默认配置
            config = SenseVoiceConfig()
            
            config_params = {
                "model_id": config.model_id,
                "language": config.language,
                "enable_streaming": config.enable_streaming,
                "vad_model_id": config.vad_model_id
            }
            
            self.results["sensevoice_config"] = {
                "params": config_params,
                "status": "success"
            }
            
            print(f"  ✓ 模型ID: {config.model_id}")
            print(f"  ✓ 语言设置: {config.language}")
            print(f"  ✓ 流式处理: {config.enable_streaming}")
            print(f"  ✓ VAD模型: {config.vad_model_id}")
            
        except Exception as e:
            self.results["sensevoice_config"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ✗ 检查失败: {e}")
    
    def _check_environment_variables(self):
        """检查环境变量配置"""
        print("\n4. 检查环境变量配置...")
        
        # 关键环境变量
        key_env_vars = [
            "LIVE_AUDIO_PROFILE",
            "LIVE_VAD_MIN_RMS",
            "LIVE_VAD_MIN_SPEECH_SEC",
            "LIVE_VAD_MIN_SILENCE_SEC",
            "LIVE_AUDIO_AGC",
            "LIVE_AUDIO_AGC_TARGET",
            "LIVE_VAD_MUSIC_DETECT"
        ]
        
        env_config = {}
        for var in key_env_vars:
            value = os.getenv(var)
            env_config[var] = value
            status = "✓ 已设置" if value else "- 未设置(使用默认值)"
            print(f"  {var}: {value or '默认'} {status}")
        
        self.results["environment_variables"] = env_config
    
    def _analyze_vad_params(self, params: Dict[str, Any]):
        """分析VAD参数并提供建议"""
        # RMS阈值分析
        if params["vad_min_rms"] > 0.02:
            self.recommendations.append({
                "type": "vad_rms_high",
                "message": f"VAD RMS阈值({params['vad_min_rms']})较高，可能导致轻声说话无法检测",
                "suggestion": "建议降低到0.012-0.015之间"
            })
        elif params["vad_min_rms"] < 0.01:
            self.recommendations.append({
                "type": "vad_rms_low",
                "message": f"VAD RMS阈值({params['vad_min_rms']})较低，可能导致噪音误触发",
                "suggestion": "建议提高到0.012-0.015之间"
            })
        
        # 语音时长分析
        if params["vad_min_speech_sec"] > 0.5:
            self.recommendations.append({
                "type": "speech_duration_long",
                "message": f"最小语音时长({params['vad_min_speech_sec']}s)较长，可能错过短语音",
                "suggestion": "建议降低到0.3-0.4秒"
            })
        
        # 静音时长分析
        if params["vad_min_silence_sec"] > 0.8:
            self.recommendations.append({
                "type": "silence_duration_long",
                "message": f"最小静音时长({params['vad_min_silence_sec']}s)较长，响应可能较慢",
                "suggestion": "建议降低到0.5-0.6秒"
            })
    
    def _analyze_agc_params(self, params: Dict[str, Any]):
        """分析AGC参数并提供建议"""
        if not params["agc_enabled"]:
            self.recommendations.append({
                "type": "agc_disabled",
                "message": "自动增益控制(AGC)未启用，可能影响音量一致性",
                "suggestion": "建议启用AGC以提高音频质量"
            })
        
        if params["agc_target_rms"] < 0.05:
            self.recommendations.append({
                "type": "agc_target_low",
                "message": f"AGC目标RMS({params['agc_target_rms']})较低，可能导致音量不足",
                "suggestion": "建议提高到0.08-0.1之间"
            })
    
    def _analyze_audio_gate_sensitivity(self, results: Dict[str, bool]):
        """分析音频门控敏感度"""
        # 统计检测成功率
        detected_count = sum(1 for detected in results.values() if detected)
        total_count = len(results)
        detection_rate = detected_count / total_count if total_count > 0 else 0
        
        if detection_rate < 0.4:
            self.recommendations.append({
                "type": "audio_gate_insensitive",
                "message": f"音频门控检测率较低({detection_rate:.1%})，可能过于严格",
                "suggestion": "建议降低音频门控的RMS阈值或调整其他参数"
            })
        elif detection_rate > 0.8:
            self.recommendations.append({
                "type": "audio_gate_oversensitive",
                "message": f"音频门控检测率较高({detection_rate:.1%})，可能过于敏感",
                "suggestion": "建议提高音频门控的阈值以减少误检"
            })
    
    def _generate_report(self):
        """生成诊断报告"""
        print("\n" + "=" * 60)
        print("诊断报告")
        print("=" * 60)
        
        # 总体状态
        total_checks = len(self.results)
        successful_checks = sum(1 for r in self.results.values() 
                              if isinstance(r, dict) and r.get("status") == "success")
        
        print(f"\n总体状态: {successful_checks}/{total_checks} 项检查通过")
        
        # 问题和建议
        if self.recommendations:
            print(f"\n发现 {len(self.recommendations)} 个潜在问题:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"\n{i}. {rec['message']}")
                print(f"   建议: {rec['suggestion']}")
        else:
            print("\n✓ 未发现明显问题，配置看起来正常")
        
        # 优化建议
        print("\n" + "-" * 40)
        print("通用优化建议:")
        print("-" * 40)
        print("1. 如果语音识别过于敏感:")
        print("   - 提高 LIVE_VAD_MIN_RMS (如 0.018)")
        print("   - 增加 LIVE_VAD_MIN_SPEECH_SEC (如 0.5)")
        print("   - 启用音乐检测 LIVE_VAD_MUSIC_DETECT=1")
        
        print("\n2. 如果语音识别不够敏感:")
        print("   - 降低 LIVE_VAD_MIN_RMS (如 0.012)")
        print("   - 减少 LIVE_VAD_MIN_SPEECH_SEC (如 0.3)")
        print("   - 启用AGC LIVE_AUDIO_AGC=1")
        print("   - 提高AGC目标 LIVE_AUDIO_AGC_TARGET=0.08")
        
        print("\n3. 如果响应速度慢:")
        print("   - 使用快速档位 LIVE_AUDIO_PROFILE=fast")
        print("   - 减少 LIVE_VAD_MIN_SILENCE_SEC (如 0.45)")
        print("   - 减少 chunk_seconds (如 0.4)")
        
        # 保存报告
        self._save_report()
    
    def _save_report(self):
        """保存诊断报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"语音转写敏感度诊断报告_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "diagnostic_results": self.results,
            "recommendations": self.recommendations,
            "summary": {
                "total_checks": len(self.results),
                "successful_checks": sum(1 for r in self.results.values() 
                                       if isinstance(r, dict) and r.get("status") == "success"),
                "issues_found": len(self.recommendations)
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n诊断报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n保存报告失败: {e}")

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行诊断
    diagnostic = VoiceTranscriptionDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    print(f"\n诊断完成! 共检查了 {len(results)} 个组件")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n诊断被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)