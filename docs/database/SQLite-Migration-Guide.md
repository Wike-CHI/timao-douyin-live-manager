# SQLite迁移指南

## 概述

本指南帮助你从MySQL迁移到SQLite数据库。SQLite是提猫直播助手的新默认数据库，简化了Electron桌面应用的部署。

## 为什么迁移到SQLite？

1. **简化部署**: 无需安装和配置MySQL服务
2. **降低资源占用**: 适合Electron桌面应用
3. **便于备份**: 单文件数据库，易于复制和备份
4. **性能优化**: WAL模式提供良好的并发性能
5. **零配置**: 开箱即用，无需数据库管理员

## 快速开始

### 1. 修改配置

编辑 `.env` 文件：

```bash
DB_TYPE=sqlite
SQLITE_DATA_DIR=data
```

### 2. 初始化数据库

```bash
python -m server.database.init_db
```

### 3. 验证

检查 `data/` 目录下是否创建了数据库文件：

```bash
# Linux/macOS
ls -la data/

# Windows
dir data\
```

应该看到：
```
data/
├── timao.db
├── ai/
│   ├── memory_vectors.db
│   ├── style_profiles.db
│   └── ai_usage_logs.db
└── sessions/
```

## MySQL到SQLite迁移

### 步骤1: 导出MySQL数据

```bash
# 导出结构和数据
mysqldump -u timao -p timao_live > mysql_backup.sql

# 或只导出数据
mysqldump -u timao -p --no-create-info timao_live > data_only.sql
```

### 步骤2: 转换SQL语法

MySQL和SQLite有一些语法差异，需要转换：

| MySQL | SQLite |
|-------|--------|
| `AUTO_INCREMENT` | `AUTOINCREMENT` |
| `` `backticks` `` | `"double quotes"` 或 `[brackets]` |
| `DATETIME` | `TEXT` (ISO8601格式) |
| `TEXT CHARACTER SET utf8mb4` | `TEXT` |
| `BIGINT UNSIGNED` | `INTEGER` |
| `ENGINE=InnoDB` | (删除此行) |

可以使用在线工具或脚本进行转换。

### 步骤3: 切换到SQLite

```bash
# 1. 停止应用
# 2. 修改配置
echo "DB_TYPE=sqlite" >> .env

# 3. 初始化数据库
python -m server.database.init_db

# 4. 导入数据（如果需要）
sqlite3 data/timao.db < converted_data.sql
```

## 数据目录结构

```
data/
├── timao.db                 # 主数据库（用户、配置）
│
├── ai/                      # AI专用数据库
│   ├── memory_vectors.db    # 向量记忆存储
│   ├── style_profiles.db    # 主播风格画像
│   └── ai_usage_logs.db     # AI调用日志（成本监控）
│
└── sessions/                # 直播会话数据库（按月分库）
    ├── live_2025-01.db      # 2025年1月数据
    ├── live_2025-02.db      # 2025年2月数据
    └── ...
```

### 分库策略

| 数据库 | 用途 | 分库策略 |
|--------|------|----------|
| `timao.db` | 用户、配置、订阅 | 单库 |
| `ai/memory_vectors.db` | AI向量记忆 | 单库 |
| `ai/style_profiles.db` | 主播风格画像 | 单库 |
| `ai/ai_usage_logs.db` | AI调用日志 | 单库 |
| `sessions/live_YYYY-MM.db` | 直播会话数据 | 按月分库 |

## 性能优化

### WAL模式

SQLite默认使用WAL（Write-Ahead Logging）模式，提供更好的并发性能：

- **多读单写**: 支持多个并发读取，单个写入
- **不阻塞读**: 写入不会阻塞读取操作
- **适合桌面应用**: 对于直播助手的负载完全足够

### PRAGMA配置

系统自动应用以下优化：

```sql
PRAGMA journal_mode=WAL;        -- 写前日志
PRAGMA synchronous=NORMAL;      -- 平衡性能和安全
PRAGMA cache_size=-64000;       -- 64MB缓存
PRAGMA temp_store=MEMORY;       -- 临时表在内存
PRAGMA mmap_size=268435456;     -- 256MB内存映射
PRAGMA foreign_keys=ON;         -- 启用外键约束
```

## 备份与恢复

### 备份

```bash
# Linux/macOS: 简单复制（确保没有写入操作）
cp -r data/ data_backup_$(date +%Y%m%d)/

# Windows
xcopy /E /I data data_backup_%date:~0,10%

# 或使用SQLite在线备份
sqlite3 data/timao.db ".backup 'data/timao_backup.db'"
```

### 恢复

```bash
# Linux/macOS
cp -r data_backup_20250217/* data/

# Windows
xcopy /E /Y data_backup_20250217 data
```

### 自动备份建议

可以设置定时任务自动备份：

```bash
# Linux/macOS crontab
0 2 * * * cp -r /path/to/timao/data /backup/timao_$(date +\%Y\%m\%d)

# Windows Task Scheduler
# 创建计划任务执行备份脚本
```

## 常见问题

### Q: SQLite支持多少并发连接？

A: SQLite使用WAL模式，支持多读单写。对于桌面应用场景（单用户、中等负载）完全足够。理论支持无限并发读取，写入时需要排队。

### Q: 数据库文件最大多大？

A: 理论上支持140TB。实际使用中，几十GB的数据库文件没有问题。按月分库后，单个会话数据库通常不会超过几百MB。

### Q: 如何查看数据库内容？

A: 使用SQLite命令行工具或GUI工具：

```bash
# 命令行
sqlite3 data/timao.db
sqlite> .tables
sqlite> SELECT * FROM users;
sqlite> .schema users
sqlite> .quit
```

推荐GUI工具：
- **DB Browser for SQLite**（免费，跨平台）: https://sqlitebrowser.org/
- **SQLiteStudio**（免费）: https://sqlitestudio.pl/
- **DataGrip**（付费，JetBrains）: https://www.jetbrains.com/datagrip/

### Q: 按月分库是什么意思？

A: 直播会话数据按月份存储在不同的数据库文件中。例如：
- `live_2025-01.db` 存储2025年1月的数据
- `live_2025-02.db` 存储2025年2月的数据

这样做的好处：
- 避免单个文件过大
- 便于归档旧数据
- 提高查询性能
- 可以直接删除旧月份数据释放空间

### Q: 切换回MySQL怎么办？

A: 修改 `.env` 文件：

```bash
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=timao_live
```

然后重启应用即可。数据需要重新导入MySQL。

### Q: 数据库文件损坏怎么办？

A:
1. 首先尝试恢复备份
2. 如果没有备份，SQLite有内置恢复机制：
```bash
sqlite3 data/timao.db ".recover" | sqlite3 data/timao_recovered.db
```

### Q: 如何迁移到新电脑？

A: 只需复制整个 `data/` 目录到新电脑，确保 `.env` 配置相同即可。

## 技术细节

### 连接字符串

```python
# SQLite
sqlite:///data/timao.db

# SQLite with absolute path (Windows)
sqlite:///D:/gsxm/timao-douyin-live-manager/data/timao.db

# MySQL
mysql+pymysql://user:password@host:port/database
```

### SQLAlchemy集成

系统使用SQLAlchemy ORM，切换数据库不需要修改应用代码：

```python
from server.app.database import get_db_session

with get_db_session() as session:
    # 无论SQLite还是MySQL，代码相同
    users = session.query(User).all()
```

### 事务处理

SQLite默认每个INSERT/UPDATE都是事务，批量操作时建议显式使用事务：

```python
with get_db_session() as session:
    for item in items:
        session.add(item)
    session.commit()  # 一次性提交
```

## 数据完整性

### 外键约束

SQLite默认启用外键约束，确保数据完整性：

```sql
PRAGMA foreign_keys=ON;
```

### 数据类型

SQLite使用动态类型，但以下类型会被正确处理：

| 声明类型 | 实际存储 |
|----------|----------|
| INTEGER | 64位整数 |
| REAL | 64位浮点数 |
| TEXT | UTF-8字符串 |
| BLOB | 二进制数据 |

日期时间推荐使用ISO8601格式的TEXT存储。

## 监控与诊断

### 查看数据库状态

```bash
sqlite3 data/timao.db

-- 查看页大小和页数
sqlite> PRAGMA page_size;
sqlite> PRAGMA page_count;

-- 计算数据库大小（字节）
sqlite> SELECT page_size * page_count FROM pragma_page_count();

-- 查看表信息
sqlite> .tables
sqlite> .schema tablename

-- 查看索引
sqlite> .indices
```

### 性能分析

```bash
-- 启用性能分析
sqlite> EXPLAIN QUERY PLAN SELECT * FROM users WHERE id = 1;
```

## 相关资源

- [SQLite官方文档](https://www.sqlite.org/docs.html)
- [SQLite WAL模式](https://www.sqlite.org/wal.html)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [项目设计文档](../plans/2025-02-17-ai-architecture-redesign.md)

## 更新日志

- 2025-02-19: 创建SQLite迁移指南
- 数据库系统从MySQL迁移到SQLite作为默认选项
- 新增按月分库策略
- 新增AI专用数据库分库
