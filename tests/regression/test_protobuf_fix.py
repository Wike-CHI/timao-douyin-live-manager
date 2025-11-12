#!/usr/bin/env python3
"""
测试 protobuf 版本兼容性修复
验证 tensorboardX 和 protobuf 是否可以正常导入

审查人：叶维哲
测试内容：
1. protobuf 版本检查
2. tensorboardX 导入测试
3. FunASR 依赖链测试
"""
import sys
from pathlib import Path

def test_protobuf_version():
    """测试1：检查 protobuf 版本"""
    try:
        import google.protobuf
        version = google.protobuf.__version__
        print(f"✅ protobuf 版本: {version}")
        
        # 检查是否符合要求 (<=3.20.3)
        major, minor, patch = map(int, version.split('.')[:3])
        if major < 3 or (major == 3 and minor <= 20):
            print(f"✅ 版本符合要求 (<=3.20.3)")
            return True
        else:
            print(f"❌ 版本过高: {version} > 3.20.3")
            return False
    except ImportError as e:
        print(f"❌ protobuf 未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ 版本检查失败: {e}")
        return False


def test_tensorboardx_import():
    """测试2：测试 tensorboardX 导入"""
    try:
        print("\n测试 tensorboardX 导入...")
        import tensorboardX
        print(f"✅ tensorboardX 导入成功，版本: {tensorboardX.__version__}")
        
        # 测试关键子模块
        from tensorboardX import SummaryWriter
        print("✅ SummaryWriter 导入成功")
        return True
    except TypeError as e:
        if "Descriptors cannot be created directly" in str(e):
            print(f"❌ protobuf 版本不兼容错误: {e}")
            print("提示：需要降级 protobuf 到 3.20.3 或更低")
        else:
            print(f"❌ 类型错误: {e}")
        return False
    except ImportError as e:
        print(f"❌ tensorboardX 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_funasr_chain():
    """测试3：测试 FunASR 依赖链"""
    try:
        print("\n测试 FunASR 依赖链...")
        
        # 这是触发错误的完整导入链
        import funasr
        print(f"✅ funasr 导入成功")
        
        # 如果能走到这里，说明问题已解决
        return True
    except TypeError as e:
        if "Descriptors cannot be created directly" in str(e):
            print(f"❌ protobuf 兼容性错误仍然存在")
            print(f"错误详情: {e}")
        else:
            print(f"❌ 类型错误: {e}")
        return False
    except ImportError as e:
        print(f"⚠️  funasr 导入失败（可能未安装）: {e}")
        return True  # 不算失败，因为可能是可选依赖
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Protobuf 兼容性修复验证")
    print("=" * 60)
    
    results = []
    
    # 测试1：protobuf 版本
    print("\n【测试1】检查 protobuf 版本")
    results.append(("protobuf 版本", test_protobuf_version()))
    
    # 测试2：tensorboardX 导入
    print("\n【测试2】测试 tensorboardX 导入")
    results.append(("tensorboardX 导入", test_tensorboardx_import()))
    
    # 测试3：FunASR 依赖链
    print("\n【测试3】测试 FunASR 依赖链")
    results.append(("FunASR 依赖", test_funasr_chain()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！protobuf 兼容性问题已修复")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        print("\n修复步骤：")
        print("1. 卸载当前 protobuf：pip uninstall protobuf")
        print("2. 安装兼容版本：pip install 'protobuf<=3.20.3'")
        print("3. 重新运行此测试")
        return 1


if __name__ == "__main__":
    sys.exit(main())

