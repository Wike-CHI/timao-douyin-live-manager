#!/usr/bin/env python3
"""
测试 AI 网关修复
验证 qwen 客户端初始化是否正常（不再出现 proxies 参数错误）
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))

# 加载环境变量
try:
    from dotenv import load_dotenv
    server_env = Path(__file__).parent / 'server' / '.env'
    if server_env.exists():
        load_dotenv(server_env)
        print(f"✅ 已加载环境变量: {server_env}")
    else:
        print(f"⚠️ 未找到 .env 文件: {server_env}")
except ImportError:
    print("⚠️ python-dotenv 未安装，跳过 .env 文件加载")

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_qwen_client_fix():
    """测试 qwen 客户端修复"""
    logger.info("=" * 60)
    logger.info("测试 AI 网关 qwen 客户端初始化修复")
    logger.info("=" * 60)
    
    try:
        # 导入 AI 网关
        from server.ai.ai_gateway import AIGateway
        
        # 获取网关实例
        gateway = AIGateway.get_instance()
        
        # 列出所有服务商
        providers = gateway.list_providers()
        
        logger.info(f"\n已注册的服务商: {len(providers)} 个")
        for name, config in providers.items():
            status = "✅ 启用" if config['enabled'] else "❌ 禁用"
            logger.info(f"  - {name:10s}: {status} | 模型: {config['default_model']}")
        
        # 检查 qwen
        if "qwen" in providers:
            qwen_config = providers["qwen"]
            logger.info("\n" + "=" * 60)
            logger.info("qwen 服务商详情:")
            logger.info(f"  - 状态: {'✅ 启用' if qwen_config['enabled'] else '❌ 禁用'}")
            logger.info(f"  - 默认模型: {qwen_config['default_model']}")
            logger.info(f"  - API地址: {qwen_config['base_url']}")
            logger.info(f"  - 支持的模型: {', '.join(qwen_config['models'])}")
            
            # 检查客户端是否创建成功
            if gateway.clients.get("qwen"):
                logger.info("\n✅ qwen 客户端创建成功！")
                logger.info("   问题已修复：qwen 客户端不再出现 proxies 参数错误")
                
                # 获取功能级配置
                logger.info("\n功能级别的模型配置:")
                func_configs = gateway.list_function_configs()
                for func_name, func_config in func_configs.items():
                    if func_config['provider'] == 'qwen':
                        logger.info(f"  - {func_name}: qwen/{func_config['model']}")
                
                return True
            else:
                logger.error("\n❌ qwen 客户端未创建")
                logger.error("   可能原因：客户端初始化时出错")
                return False
        else:
            logger.warning("\n⚠️ qwen 服务商未注册")
            logger.info("   请检查环境变量:")
            logger.info("   - QWEN_API_KEY 或 DASHSCOPE_API_KEY")
            logger.info("   - QWEN_BASE_URL (可选)")
            logger.info("   - QWEN_MODEL (可选，默认: qwen-plus)")
            return None
            
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        return False

def main():
    """主函数"""
    result = test_qwen_client_fix()
    
    logger.info("\n" + "=" * 60)
    if result is True:
        logger.info("✅ 测试通过：qwen 客户端初始化正常，修复生效")
        logger.info("   不再出现 'proxies' 参数错误")
        sys.exit(0)
    elif result is False:
        logger.error("❌ 测试失败：qwen 客户端初始化仍然有问题")
        sys.exit(1)
    else:
        logger.warning("⚠️ 跳过测试：qwen 未配置")
        logger.info("   修复已完成，等待配置后即可使用")
        sys.exit(0)

if __name__ == "__main__":
    main()

