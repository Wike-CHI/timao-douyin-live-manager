#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST语音转录测试服务器启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    try:
        # 检查AST模块
        try:
            from AST_module import ASTService, create_ast_config
            logging.info("✅ AST模块导入成功")
        except ImportError as e:
            logging.error(f"❌ AST模块导入失败: {e}")
            return False

        # 检查VOSK模型
        from AST_module.config import DEFAULT_MODEL_PATH
        if not Path(DEFAULT_MODEL_PATH).exists():
            logging.warning(f"⚠️ VOSK模型不存在: {DEFAULT_MODEL_PATH}")
            logging.info("将使用模拟服务进行测试")
        else:
            logging.info(f"✅ VOSK模型存在: {DEFAULT_MODEL_PATH}")

        # 启动FastAPI服务器
        logging.info("🚀 启动AST测试服务器...")
        
        import uvicorn
        from server.app.main import app
        
        # 配置服务器
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=8001,
            log_level="info",
            reload=False  # 避免重载问题
        )
        
        server = uvicorn.Server(config)
        
        logging.info("=" * 60)
        logging.info("🎤 AST语音转录测试服务器已启动")
        logging.info("📍 服务地址: http://127.0.0.1:8001")
        logging.info("🌐 测试页面: http://127.0.0.1:8001/../AST_test_page.html")
        logging.info("📚 API文档: http://127.0.0.1:8001/docs")
        logging.info("💚 健康检查: http://127.0.0.1:8001/api/transcription/health")
        logging.info("=" * 60)
        
        # 运行服务器
        server.run()
        
    except KeyboardInterrupt:
        logging.info("👋 用户中断，服务器关闭")
    except Exception as e:
        logging.error(f"❌ 服务器启动失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)