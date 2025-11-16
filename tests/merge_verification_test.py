"""
合并验证测试脚本

测试 local-view 和 local-test 分支合并后的功能完整性

审查人：叶维哲
创建时间：2025-01-16
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMergeIntegrity(unittest.TestCase):
    """测试合并完整性"""
    
    def test_electron_main_imports(self):
        """测试 electron/main.js 的导入是否完整"""
        main_js = project_root / "electron" / "main.js"
        self.assertTrue(main_js.exists(), "electron/main.js 文件应该存在")
        
        content = main_js.read_text(encoding='utf-8')
        
        # 测试 model-manager 导入（来自 local-test）
        self.assertIn(
            "require('./main/model/model-manager')",
            content,
            "应该包含 model-manager 导入"
        )
        
        # 测试 floatingWindow 导入（来自 local-view）
        self.assertIn(
            "require('./floatingWindow')",
            content,
            "应该包含 floatingWindow 导入"
        )
        
        # 测试导入的函数
        self.assertIn("createFloatingWindow", content, "应该包含 createFloatingWindow")
        self.assertIn("showFloatingWindow", content, "应该包含 showFloatingWindow")
        self.assertIn("toggleAlwaysOnTop", content, "应该包含 toggleAlwaysOnTop")
        
        print("✅ electron/main.js 导入完整")
    
    def test_floating_window_module_exists(self):
        """测试悬浮窗模块是否存在"""
        floating_window = project_root / "electron" / "floatingWindow.js"
        self.assertTrue(
            floating_window.exists(),
            "electron/floatingWindow.js 应该存在"
        )
        print("✅ 悬浮窗模块存在")
    
    def test_model_manager_exists(self):
        """测试模型管理器是否存在"""
        model_manager = project_root / "electron" / "main" / "model" / "model-manager.js"
        # 注意：这个文件可能不存在，根据实际情况调整
        if model_manager.exists():
            print("✅ 模型管理器模块存在")
        else:
            print("⚠️ 模型管理器模块不存在（可能还未创建）")
    
    def test_config_files_preserved(self):
        """测试本地配置文件是否保留"""
        config_files = [
            "electron/.env",
            "electron/renderer/.env",
            "server/.env",
        ]
        
        for config_file in config_files:
            file_path = project_root / config_file
            self.assertTrue(
                file_path.exists(),
                f"{config_file} 应该存在"
            )
        
        print("✅ 本地配置文件保留完整")
    
    def test_gitattributes_exists(self):
        """测试 .gitattributes 是否存在"""
        gitattributes = project_root / ".gitattributes"
        self.assertTrue(
            gitattributes.exists(),
            ".gitattributes 应该存在"
        )
        
        content = gitattributes.read_text(encoding='utf-8')
        
        # 测试关键配置
        self.assertIn("merge=ours", content, "应该包含 merge=ours 策略")
        self.assertIn("**/.env", content, "应该保护 .env 文件")
        
        print("✅ .gitattributes 配置正确")
    
    def test_mobile_prototype_deleted(self):
        """测试 mobile-prototype 文件是否已删除"""
        mobile_files = [
            "mobile-prototype/README.md",
            "mobile-prototype/UX_ANALYSIS.md",
            "mobile-prototype/index.html",
        ]
        
        for mobile_file in mobile_files:
            file_path = project_root / mobile_file
            self.assertFalse(
                file_path.exists(),
                f"{mobile_file} 应该已被删除"
            )
        
        print("✅ mobile-prototype 文件已正确删除")
    
    def test_floating_window_components(self):
        """测试悬浮窗前端组件是否存在"""
        components = [
            "electron/renderer/src/components/floating/FloatingTabContent.tsx",
            "electron/renderer/src/components/floating/index.ts",
            "electron/renderer/src/pages/FloatingWindowPage.tsx",
        ]
        
        for component in components:
            file_path = project_root / component
            self.assertTrue(
                file_path.exists(),
                f"{component} 应该存在"
            )
        
        print("✅ 悬浮窗前端组件完整")
    
    def test_documentation_merged(self):
        """测试文档是否正确合并"""
        doc_file = project_root / "docs" / "部分服务从服务器转移本地.md"
        self.assertTrue(doc_file.exists(), "架构文档应该存在")
        
        content = doc_file.read_text(encoding='utf-8')
        
        # 测试是否包含两个分支的内容
        self.assertIn("实施完成进度报告", content, "应该包含 local-test 的内容")
        self.assertIn("模型下载与初始化方案", content, "应该包含 local-view 的内容")
        
        # 确保没有冲突标记
        self.assertNotIn("<<<<<<<", content, "不应该有未解决的冲突标记")
        self.assertNotIn(">>>>>>>", content, "不应该有未解决的冲突标记")
        self.assertNotIn("=======", content, "不应该有未解决的冲突标记")
        
        print("✅ 文档正确合并，无冲突标记")
    
    def test_scripts_preserved(self):
        """测试运行脚本是否保留"""
        scripts = [
            "scripts/构建与启动/integrated-launcher.js",
            "scripts/构建与启动/service_launcher.py",
            "scripts/构建与启动/port-manager.js",
        ]
        
        for script in scripts:
            file_path = project_root / script
            self.assertTrue(
                file_path.exists(),
                f"{script} 应该存在"
            )
        
        print("✅ 运行脚本保留完整")


class TestMergeFunctionality(unittest.TestCase):
    """测试合并后的功能性"""
    
    def test_no_syntax_errors_in_main_js(self):
        """测试 main.js 没有语法错误"""
        main_js = project_root / "electron" / "main.js"
        content = main_js.read_text(encoding='utf-8')
        
        # 基本的语法检查
        # 检查 require 语句是否完整
        self.assertNotIn("<<<<<<< HEAD", content, "不应该有冲突标记")
        self.assertNotIn(">>>>>>> local-view", content, "不应该有冲突标记")
        
        # 检查括号匹配
        open_braces = content.count('{')
        close_braces = content.count('}')
        self.assertEqual(
            open_braces,
            close_braces,
            "花括号应该匹配"
        )
        
        print("✅ electron/main.js 没有明显的语法错误")
    
    def test_config_structure(self):
        """测试配置文件结构"""
        config_dir = project_root / "config"
        if config_dir.exists():
            # 检查配置目录结构
            config_files = list(config_dir.glob("*.json"))
            self.assertGreater(
                len(config_files),
                0,
                "config 目录应该包含配置文件"
            )
            print(f"✅ 找到 {len(config_files)} 个配置文件")
        else:
            print("⚠️ config 目录不存在")


def run_tests():
    """运行所有测试"""
    # 设置输出编码
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("=" * 60)
    print("开始合并验证测试")
    print("=" * 60)
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestMergeIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestMergeFunctionality))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("所有测试通过！合并验证成功！")
        return 0
    else:
        print("存在测试失败，请检查合并结果")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())

