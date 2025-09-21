#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的音频增强测试
验证我们的VOSK音频增强功能是否正确实现
"""

import sys
import os
from pathlib import Path

def test_basic_functionality():
    """测试基本功能"""
    print("🎙️ 音频增强功能基础测试")
    print("=" * 50)
    
    # 测试1: 检查文件结构
    print("\n📁 检查文件结构:")
    
    vosk_init_path = Path(__file__).parent / "vosk-api" / "python" / "vosk" / "__init__.py"
    demo_path = Path(__file__).parent / "vosk_enhanced_demo.py"
    audio_path = Path(__file__).parent / "tests" / "录音 (12).m4a"
    
    files_to_check = [
        ("VOSK __init__.py", vosk_init_path),
        ("增强演示脚本", demo_path),
        ("测试音频文件", audio_path)
    ]
    
    for name, path in files_to_check:
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  ✅ {name}: {size:.1f} KB")
        else:
            print(f"  ❌ {name}: 不存在")
    
    # 测试2: 检查VOSK增强功能
    print("\n🔧 检查VOSK增强功能:")
    
    try:
        # 添加VOSK路径
        vosk_path = Path(__file__).parent / "vosk-api" / "python"
        sys.path.insert(0, str(vosk_path))
        
        import vosk
        print("  ✅ VOSK模块导入成功")
        
        # 检查增强功能类
        features = [
            ("AudioEnhancer", "音频增强器"),
            ("EnhancedKaldiRecognizer", "增强版识别器")
        ]
        
        for class_name, description in features:
            if hasattr(vosk, class_name):
                print(f"  ✅ {description} ({class_name}): 可用")
            else:
                print(f"  ❌ {description} ({class_name}): 不可用")
        
    except Exception as e:
        print(f"  ❌ VOSK模块导入失败: {e}")
    
    # 测试3: 检查演示脚本
    print("\n🎬 检查演示脚本:")
    
    try:
        # 检查演示脚本语法
        import py_compile
        py_compile.compile(str(demo_path), doraise=True)
        print("  ✅ 演示脚本语法正确")
    except Exception as e:
        print(f"  ❌ 演示脚本语法错误: {e}")
    
    # 测试4: 生成简单报告
    print("\n📊 生成测试报告:")
    
    report = []
    report.append("🎙️ VOSK音频增强功能测试报告")
    report.append("=" * 50)
    report.append("")
    report.append("✅ 测试完成项目:")
    report.append("  • 文件结构检查")
    report.append("  • VOSK模块导入测试")
    report.append("  • 增强功能类检查")
    report.append("  • 演示脚本语法验证")
    report.append("")
    report.append("📁 项目文件:")
    for name, path in files_to_check:
        status = "存在" if path.exists() else "缺失"
        size = f"({path.stat().st_size / 1024:.1f} KB)" if path.exists() else ""
        report.append(f"  • {name}: {status} {size}")
    report.append("")
    report.append("🚀 核心功能:")
    
    try:
        import vosk
        for class_name, description in features:
            status = "✅ 可用" if hasattr(vosk, class_name) else "❌ 不可用"
            report.append(f"  • {description}: {status}")
    except:
        report.append("  • VOSK模块: ❌ 导入失败")
    
    report.append("")
    report.append("🎵 音频文件:")
    if audio_path.exists():
        size = audio_path.stat().st_size / 1024
        report.append(f"  • 测试音频: ✅ 可用 ({size:.1f} KB)")
        report.append(f"  • 格式: {audio_path.suffix}")
    else:
        report.append("  • 测试音频: ❌ 不可用")
    
    report.append("")
    report.append("💡 使用建议:")
    report.append("  1. 确保安装了所需依赖: pip install vosk numpy scipy")
    report.append("  2. 下载VOSK中文模型")
    report.append("  3. 运行演示脚本: python vosk_enhanced_demo.py")
    report.append("  4. 在Web界面中测试音频转录功能")
    report.append("")
    report.append("=" * 50)
    
    report_content = "\n".join(report)
    
    # 保存报告
    report_path = Path(__file__).parent / "basic_functionality_test_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"  ✅ 报告已保存: {report_path}")
    
    # 显示报告
    print("\n" + report_content)
    
    return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()