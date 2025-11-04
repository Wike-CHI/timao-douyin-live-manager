"""
快速测试修复后的导入
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🔍 测试导入修复...")
print("=" * 60)

# 测试 1: streamcap utils
try:
    from server.modules.streamcap.utils import trace_error_decorator
    print("✅ server.modules.streamcap.utils.trace_error_decorator")
except Exception as e:
    print(f"❌ server.modules.streamcap.utils: {e}")

# 测试 2: streamcap logger  
try:
    from server.modules.streamcap.logger import logger
    print("✅ server.modules.streamcap.logger")
except Exception as e:
    print(f"❌ server.modules.streamcap.logger: {e}")

# 测试 3: handlers 导入
try:
    from server.modules.streamcap.platforms.platform_handlers.handlers import CustomHandler
    print("✅ server.modules.streamcap.platforms.platform_handlers.handlers")
except Exception as e:
    print(f"❌ handlers: {e}")

# 测试 4: direct_downloader 导入
try:
    from server.modules.streamcap.media.direct_downloader import DirectStreamDownloader
    print("✅ server.modules.streamcap.media.direct_downloader")
except Exception as e:
    print(f"❌ direct_downloader: {e}")

print("=" * 60)
print("🎉 所有导入测试完成！")
