#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出 SenseVoice Small 模型为 ONNX 格式

使用方法:
    python scripts/export_models_to_onnx.py
"""
import os
import sys
from pathlib import Path

# 🔧 强制使用CPU，避免CUDA库加载问题
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import torch
import numpy as np


def export_sensevoice_to_onnx():
    """导出SenseVoice模型为ONNX格式"""
    print("=" * 60)
    print("🔧 SenseVoice ONNX 模型导出工具")
    print("=" * 60)
    
    # 使用本地模型路径
    model_path = project_root / "server" / "models" / ".cache" / "modelscope" / "iic" / "SenseVoiceSmall"
    
    if not model_path.exists():
        print(f"❌ 错误: 本地模型不存在: {model_path}")
        print("💡 提示: 请先运行服务使SenseVoice模型下载到本地")
        return False
    
    print(f"\n📁 模型路径: {model_path}")
    print(f"📦 模型大小: {sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file()) / 1024 / 1024:.1f}MB")
    
    # 准备输出目录
    output_dir = project_root / "server" / "models" / "onnx"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 输出目录: {output_dir}")
    
    try:
        print("\n🔧 加载 FunASR 和 SenseVoice 模型...")
        from funasr import AutoModel
        
        # 设置环境变量避免UMAP/numba问题
        os.environ.setdefault("UMAP_DONT_USE_NUMBA", "1")
        os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
        
        model = AutoModel(
            model=str(model_path),
            device="cpu",
            disable_update=True
        )
        print("✅ 模型加载成功")
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🔄 导出 ONNX 模型...")
    print("⚠️  注意: 这可能需要几分钟时间...")
    
    try:
        # 方法1: 尝试使用FunASR的export功能
        print("\n方法1: 使用 FunASR.export() 功能")
        
        if hasattr(model, 'export'):
            try:
                model.export(
                    type="onnx",
                    quantize=False,  # 不量化，保持准确率
                    fallback_num=0,
                    output_dir=str(output_dir)
                )
                print(f"✅ 模型导出成功 (FunASR export)")
                
                # 检查导出的文件
                onnx_files = list(output_dir.glob("*.onnx"))
                if onnx_files:
                    for f in onnx_files:
                        size_mb = f.stat().st_size / 1024 / 1024
                        print(f"📦 {f.name}: {size_mb:.1f}MB")
                    return True
                else:
                    print("⚠️  未找到导出的ONNX文件，尝试方法2")
                    
            except Exception as e:
                print(f"⚠️  FunASR.export()失败: {e}")
                print("尝试方法2...")
        else:
            print("⚠️  当前FunASR版本不支持export方法")
            print("尝试方法2...")
        
        # 方法2: 手动使用torch.onnx.export
        print("\n方法2: 使用 torch.onnx.export()")
        
        # 获取内部模型
        if hasattr(model, 'model'):
            inner_model = model.model
        else:
            inner_model = model
        
        # 创建示例输入（1秒音频，16kHz）
        dummy_audio = torch.randn(1, 16000)
        
        output_file = output_dir / "sensevoice_small.onnx"
        
        print(f"🔄 导出到: {output_file}")
        
        torch.onnx.export(
            inner_model,
            dummy_audio,
            str(output_file),
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=['audio'],
            output_names=['logits'],
            dynamic_axes={
                'audio': {0: 'batch_size', 1: 'length'},
                'logits': {0: 'batch_size'}
            },
            verbose=False
        )
        
        if output_file.exists():
            size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"✅ 模型导出成功: {output_file.name} ({size_mb:.1f}MB)")
            return True
        else:
            print("❌ 导出失败: 文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ 导出过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_vad_to_onnx():
    """处理VAD模型（推荐使用轻量级RMS VAD）"""
    print("\n" + "=" * 60)
    print("🔧 VAD模型处理")
    print("=" * 60)
    print("\n💡 建议: 使用轻量级RMS能量VAD，无需额外模型")
    print("   RMS VAD特点:")
    print("   ✅ 几乎零内存开销")
    print("   ✅ 实时性能极佳")
    print("   ✅ 适合直播场景")
    print("\n   如需导出FSMN VAD模型，可参考FunASR官方文档")
    print("   https://github.com/alibaba-damo-academy/FunASR")
    return True


def main():
    """主函数"""
    print("\n🚀 开始导出模型...\n")
    
    # 导出SenseVoice
    success_sv = export_sensevoice_to_onnx()
    
    # 处理VAD
    success_vad = export_vad_to_onnx()
    
    print("\n" + "=" * 60)
    if success_sv:
        print("✅ 导出完成!")
        print("\n下一步:")
        print("1. 运行验证脚本: python scripts/verify_onnx_model.py")
        print("2. 启用ONNX后端: export SENSEVOICE_USE_ONNX=true")
        print("3. 启动服务测试")
    else:
        print("❌ 导出失败")
        print("\n故障排除:")
        print("1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("2. 确保SenseVoice模型已下载到本地")
        print("3. 检查torch和onnx版本兼容性")
    print("=" * 60)
    
    return success_sv


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

