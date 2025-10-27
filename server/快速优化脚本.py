#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转写敏感度快速优化脚本

此脚本用于快速应用推荐的参数优化，解决语音转写"有时灵敏有时识别不到"的问题。
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any

class VoiceTranscriptionOptimizer:
    """语音转写优化器"""
    
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.project_root = self.current_dir.parent
        
        # 推荐的优化参数
        self.optimized_params = {
            # VAD参数优化
            "LIVE_VAD_MIN_RMS": "0.012",           # 降低RMS阈值，提高敏感度
            "LIVE_VAD_MIN_SPEECH_SEC": "0.25",     # 减少最小语音时间
            "LIVE_VAD_MIN_SILENCE_SEC": "0.45",    # 减少最小静音时间
            "LIVE_VAD_HANGOVER_SEC": "0.5",        # 增加挂起时间
            
            # 音频处理优化
            "LIVE_AUDIO_PROFILE": "fast",          # 使用快速档位
            "LIVE_AUDIO_AGC_TARGET": "0.1",        # 提高AGC目标音量
            "LIVE_AUDIO_AGC_SMOOTH": "0.12",       # 调整AGC平滑系数
            
            # 置信度优化
            "AST_MIN_CONFIDENCE": "0.35",          # 降低最小置信度要求
            
            # 音频门控优化
            "AUDIO_GATE_RMS_THRESHOLD": "0.008",   # 降低音频门控RMS阈值
            "AUDIO_GATE_VOICE_RATIO": "0.25",      # 放宽人声频带要求
            
            # 背景音乐检测（如果干扰严重可以关闭）
            "LIVE_VAD_MUSIC_DETECT": "1",          # 保持开启，但可以调整
            "LIVE_VAD_MUSIC_THRESHOLD": "0.7",     # 提高音乐检测阈值
        }
        
        # 不同场景的预设配置
        self.presets = {
            "high_sensitivity": {
                "description": "高敏感度配置 - 适用于安静环境",
                "params": {
                    "LIVE_VAD_MIN_RMS": "0.008",
                    "LIVE_VAD_MIN_SPEECH_SEC": "0.2",
                    "LIVE_VAD_MIN_SILENCE_SEC": "0.4",
                    "AST_MIN_CONFIDENCE": "0.25",
                    "LIVE_VAD_MUSIC_DETECT": "0",  # 关闭音乐检测
                }
            },
            "balanced": {
                "description": "平衡配置 - 适用于一般环境",
                "params": {
                    "LIVE_VAD_MIN_RMS": "0.012",
                    "LIVE_VAD_MIN_SPEECH_SEC": "0.25",
                    "LIVE_VAD_MIN_SILENCE_SEC": "0.45",
                    "AST_MIN_CONFIDENCE": "0.35",
                    "LIVE_VAD_MUSIC_DETECT": "1",
                }
            },
            "noise_resistant": {
                "description": "抗噪配置 - 适用于嘈杂环境",
                "params": {
                    "LIVE_VAD_MIN_RMS": "0.018",
                    "LIVE_VAD_MIN_SPEECH_SEC": "0.35",
                    "LIVE_VAD_MIN_SILENCE_SEC": "0.6",
                    "AST_MIN_CONFIDENCE": "0.45",
                    "LIVE_VAD_MUSIC_DETECT": "1",
                    "LIVE_VAD_MUSIC_THRESHOLD": "0.6",
                }
            }
        }
    
    def backup_current_config(self) -> str:
        """备份当前环境变量配置"""
        backup_file = self.current_dir / "voice_config_backup.json"
        
        current_config = {}
        for key in self.optimized_params.keys():
            current_config[key] = os.environ.get(key, "未设置")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": str(Path(__file__).stat().st_mtime),
                "config": current_config
            }, f, indent=2, ensure_ascii=False)
        
        return str(backup_file)
    
    def apply_optimization(self, preset: str = "balanced") -> Dict[str, Any]:
        """应用优化配置"""
        print(f"🔧 应用语音转写优化配置...")
        
        # 备份当前配置
        backup_file = self.backup_current_config()
        print(f"📦 当前配置已备份到: {backup_file}")
        
        # 选择配置
        if preset in self.presets:
            params = self.presets[preset]["params"]
            print(f"📋 使用预设配置: {preset} - {self.presets[preset]['description']}")
        else:
            params = self.optimized_params
            print(f"📋 使用默认优化配置")
        
        # 应用环境变量
        applied_params = {}
        for key, value in params.items():
            os.environ[key] = value
            applied_params[key] = value
            print(f"   ✅ {key} = {value}")
        
        # 创建.env文件
        env_file = self.project_root / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# 语音转写优化配置\n")
            f.write("# 由快速优化脚本自动生成\n\n")
            for key, value in applied_params.items():
                f.write(f"{key}={value}\n")
        
        print(f"📄 配置已保存到: {env_file}")
        
        return {
            "status": "success",
            "preset": preset,
            "applied_params": applied_params,
            "backup_file": backup_file,
            "env_file": str(env_file)
        }
    
    def restore_backup(self, backup_file: str = None) -> Dict[str, Any]:
        """恢复备份的配置"""
        if backup_file is None:
            backup_file = self.current_dir / "voice_config_backup.json"
        else:
            backup_file = Path(backup_file)
        
        if not backup_file.exists():
            return {"status": "error", "message": "备份文件不存在"}
        
        print(f"🔄 恢复配置从: {backup_file}")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        restored_params = {}
        for key, value in backup_data["config"].items():
            if value != "未设置":
                os.environ[key] = value
                restored_params[key] = value
            elif key in os.environ:
                del os.environ[key]
                restored_params[key] = "已删除"
        
        print("✅ 配置已恢复")
        return {
            "status": "success",
            "restored_params": restored_params
        }
    
    def show_current_config(self):
        """显示当前配置"""
        print("\n📊 当前语音转写配置:")
        print("=" * 50)
        
        for key in self.optimized_params.keys():
            value = os.environ.get(key, "未设置")
            print(f"{key:30} = {value}")
        
        print("=" * 50)
    
    def test_configuration(self) -> Dict[str, Any]:
        """测试当前配置"""
        print("\n🧪 测试当前配置...")
        
        test_results = {
            "vad_sensitivity": "未知",
            "confidence_threshold": "未知",
            "agc_status": "未知",
            "music_detection": "未知"
        }
        
        # 检查VAD敏感度
        vad_rms = float(os.environ.get("LIVE_VAD_MIN_RMS", "0.015"))
        if vad_rms <= 0.010:
            test_results["vad_sensitivity"] = "高敏感度"
        elif vad_rms <= 0.015:
            test_results["vad_sensitivity"] = "中等敏感度"
        else:
            test_results["vad_sensitivity"] = "低敏感度"
        
        # 检查置信度阈值
        confidence = float(os.environ.get("AST_MIN_CONFIDENCE", "0.5"))
        if confidence <= 0.3:
            test_results["confidence_threshold"] = "宽松"
        elif confidence <= 0.4:
            test_results["confidence_threshold"] = "适中"
        else:
            test_results["confidence_threshold"] = "严格"
        
        # 检查AGC状态
        agc_target = float(os.environ.get("LIVE_AUDIO_AGC_TARGET", "0.08"))
        if agc_target >= 0.1:
            test_results["agc_status"] = "高增益"
        else:
            test_results["agc_status"] = "标准增益"
        
        # 检查音乐检测
        music_detect = os.environ.get("LIVE_VAD_MUSIC_DETECT", "1")
        test_results["music_detection"] = "开启" if music_detect == "1" else "关闭"
        
        print("测试结果:")
        for key, value in test_results.items():
            print(f"  {key:20} : {value}")
        
        return test_results

def main():
    """主函数"""
    optimizer = VoiceTranscriptionOptimizer()
    
    if len(sys.argv) < 2:
        print("🎙️  语音转写敏感度快速优化脚本")
        print("=" * 50)
        print("用法:")
        print("  python 快速优化脚本.py apply [preset]     # 应用优化配置")
        print("  python 快速优化脚本.py restore [backup]   # 恢复备份配置")
        print("  python 快速优化脚本.py show               # 显示当前配置")
        print("  python 快速优化脚本.py test               # 测试当前配置")
        print()
        print("可用预设:")
        for preset, info in optimizer.presets.items():
            print(f"  {preset:15} - {info['description']}")
        print()
        print("示例:")
        print("  python 快速优化脚本.py apply balanced")
        print("  python 快速优化脚本.py apply high_sensitivity")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "apply":
            preset = sys.argv[2] if len(sys.argv) > 2 else "balanced"
            result = optimizer.apply_optimization(preset)
            print(f"\n✅ 优化完成! 状态: {result['status']}")
            print("\n⚠️  请重启语音转写服务以使配置生效")
            
        elif command == "restore":
            backup_file = sys.argv[2] if len(sys.argv) > 2 else None
            result = optimizer.restore_backup(backup_file)
            print(f"✅ 恢复完成! 状态: {result['status']}")
            
        elif command == "show":
            optimizer.show_current_config()
            
        elif command == "test":
            optimizer.test_configuration()
            
        else:
            print(f"❌ 未知命令: {command}")
            
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()