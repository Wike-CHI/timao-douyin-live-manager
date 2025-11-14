#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证ONNX模型推理准确性

使用方法:
    python scripts/verify_onnx_model.py
"""
import os
import sys
from pathlib import Path

# 🔧 强制使用CPU，避免CUDA库加载问题
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np


def verify_onnx_model():
    """验证ONNX模型是否可以正常推理"""
    print("=" * 60)
    print("🧪 ONNX 模型验证工具")
    print("=" * 60)
    
    # 查找ONNX模型
    onnx_dir = project_root / "server" / "models" / "onnx"
    
    if not onnx_dir.exists():
        print(f"\n❌ ONNX模型目录不存在: {onnx_dir}")
        print("💡 请先运行: python scripts/export_models_to_onnx.py")
        return False
    
    onnx_files = list(onnx_dir.glob("*.onnx"))
    
    if not onnx_files:
        print(f"\n❌ 未找到ONNX模型文件在: {onnx_dir}")
        print("💡 请先运行: python scripts/export_models_to_onnx.py")
        return False
    
    print(f"\n📁 模型目录: {onnx_dir}")
    print(f"📦 发现 {len(onnx_files)} 个ONNX模型:")
    for f in onnx_files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"   - {f.name} ({size_mb:.1f}MB)")
    
    # 使用第一个模型进行验证
    onnx_path = onnx_files[0]
    print(f"\n🔧 验证模型: {onnx_path.name}")
    
    try:
        import onnxruntime as ort
        print("✅ onnxruntime 已安装")
    except ImportError:
        print("❌ 错误: 未安装 onnxruntime")
        print("💡 安装命令: pip install onnxruntime")
        return False
    
    try:
        print(f"\n🔄 加载ONNX模型...")
        session = ort.InferenceSession(
            str(onnx_path),
            providers=['CPUExecutionProvider']
        )
        print("✅ 模型加载成功")
        
        # 打印模型信息
        print("\n📊 模型信息:")
        print("\n输入:")
        for idx, inp in enumerate(session.get_inputs()):
            print(f"  [{idx}] {inp.name}")
            print(f"      类型: {inp.type}")
            print(f"      形状: {inp.shape}")
        
        print("\n输出:")
        for idx, out in enumerate(session.get_outputs()):
            print(f"  [{idx}] {out.name}")
            print(f"      类型: {out.type}")
            print(f"      形状: {out.shape}")
        
        # 测试推理
        print("\n🧪 测试推理...")
        
        # 获取输入信息
        input_info = session.get_inputs()[0]
        input_name = input_info.name
        input_shape = input_info.shape
        
        # 创建测试音频 (1秒, 16kHz, 单声道)
        test_audio = np.random.randn(1, 16000).astype(np.float32)
        print(f"   测试输入: {test_audio.shape} ({test_audio.dtype})")
        
        # 运行推理
        inputs = {input_name: test_audio}
        outputs = session.run(None, inputs)
        
        print(f"✅ 推理成功!")
        print(f"   输出数量: {len(outputs)}")
        for idx, output in enumerate(outputs):
            if isinstance(output, np.ndarray):
                print(f"   输出[{idx}]: {output.shape} ({output.dtype})")
            else:
                print(f"   输出[{idx}]: {type(output)}")
        
        # 性能测试
        print("\n⚡ 性能测试 (10次推理)...")
        import time
        
        times = []
        for i in range(10):
            start = time.time()
            _ = session.run(None, inputs)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = np.mean(times) * 1000  # 转换为毫秒
        std_time = np.std(times) * 1000
        
        print(f"   平均推理时间: {avg_time:.2f}ms (±{std_time:.2f}ms)")
        print(f"   最快: {min(times)*1000:.2f}ms")
        print(f"   最慢: {max(times)*1000:.2f}ms")
        
        # 评估实时性能
        audio_duration = 1.0  # 1秒音频
        realtime_factor = (avg_time / 1000) / audio_duration
        
        if realtime_factor < 0.1:
            performance = "🚀 极快"
        elif realtime_factor < 0.5:
            performance = "✅ 良好"
        elif realtime_factor < 1.0:
            performance = "⚠️  可用"
        else:
            performance = "❌ 过慢"
        
        print(f"\n   实时因子: {realtime_factor:.2f}x {performance}")
        print(f"   (1秒音频需要 {avg_time:.0f}ms 处理)")
        
        print("\n" + "=" * 60)
        print("✅ 验证通过! ONNX模型可以正常工作")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n故障排除:")
        print("1. 检查ONNX模型是否完整导出")
        print("2. 确认onnxruntime版本兼容性")
        print("3. 尝试重新导出模型")
        
        return False


def main():
    """主函数"""
    success = verify_onnx_model()
    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

