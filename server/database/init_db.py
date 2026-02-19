"""数据库初始化脚本

一键初始化所有SQLite数据库和表结构

用法:
    python -m server.database.init_db
    或
    python server/database/init_db.py
"""
import argparse
import logging
import sys
from pathlib import Path

from server.database import get_sqlite_manager, init_ai_tables, close_sqlite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_database(data_dir: str = "data", verbose: bool = True) -> bool:
    """初始化数据库

    Args:
        data_dir: 数据目录路径
        verbose: 是否输出详细日志

    Returns:
        是否成功
    """
    try:
        if verbose:
            logger.info("=" * 50)
            logger.info("SQLite 数据库初始化")
            logger.info("=" * 50)

        # 设置数据目录
        from server.database.sqlite_manager import SQLiteConfig, SQLiteDatabaseManager
        config = SQLiteConfig(data_dir=data_dir)
        manager = SQLiteDatabaseManager(config)
        manager.initialize()

        if verbose:
            logger.info("数据库管理器已初始化")

        # 初始化AI表
        init_ai_tables(manager)

        if verbose:
            logger.info("AI数据表已创建")

        # 显示目录结构
        if verbose:
            data_path = Path(data_dir)
            logger.info("")
            logger.info("数据库目录结构:")
            logger.info("   %s/", data_dir)
            logger.info("   ├── timao.db           (主数据库)")
            logger.info("   ├── ai/")
            logger.info("   │   ├── memory_vectors.db  (向量记忆)")
            logger.info("   │   ├── style_profiles.db  (风格画像)")
            logger.info("   │   └── ai_usage_logs.db   (使用日志)")
            logger.info("   └── sessions/")
            logger.info("       └── live_YYYY-MM.db    (按月分库)")
            logger.info("")
            logger.info("数据库初始化完成！")

        manager.close()
        return True

    except Exception as e:
        logger.error("数据库初始化失败: %s", e)
        import traceback
        traceback.print_exc()
        return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="初始化SQLite数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python -m server.database.init_db
    python -m server.database.init_db --data-dir ./mydata
        """
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="数据目录路径 (默认: data)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式，减少输出"
    )

    args = parser.parse_args()

    success = init_database(
        data_dir=args.data_dir,
        verbose=not args.quiet
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
