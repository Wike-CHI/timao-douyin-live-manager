# 项目结构说明

本文档说明提猫直播助手项目的目录结构和文件组织方式。

## 📁 目录结构

```
timao-douyin-live-manager/
├── server/                    # 后端服务代码（所有后端相关代码统一在此）
│   ├── app/                   # FastAPI 应用
│   │   ├── main.py           # FastAPI 入口
│   │   ├── api/              # REST/WebSocket 路由
│   │   ├── services/        # 业务逻辑服务
│   │   ├── models/           # 数据模型
│   │   └── database/         # 数据库管理
│   ├── ai/                    # AI 相关模块
│   │   ├── ai_gateway.py     # AI 网关（统一管理多 AI 服务商）
│   │   ├── langgraph_live_workflow.py  # AI 工作流
│   │   └── ...
│   ├── modules/               # 核心功能模块
│   │   ├── ast/              # 音频转写模块（从 AST_module 迁移）
│   │   ├── douyin/           # 抖音抓取模块（从 DouyinLiveWebFetcher 迁移）
│   │   └── streamcap/        # 流媒体处理模块（从 StreamCap 迁移）
│   ├── utils/                 # 工具函数
│   ├── tests/                 # 测试文件
│   └── requirements.txt       # Python 依赖
│
├── electron/                  # 桌面端应用
│   ├── main.js               # Electron 主进程
│   └── renderer/             # React + Vite 前端
│
├── scripts/                   # 工具脚本
│   ├── check_db_config.py    # 数据库配置检查
│   ├── init_mysql.py         # MySQL 初始化
│   ├── create_admin_user.py  # 创建管理员用户
│   └── ...
│
├── docs/                      # 文档目录（所有文档统一在此）
│   ├── AI处理工作流/          # AI 工作流相关文档
│   ├── legacy_code/           # 历史代码（已弃用）
│   └── *.md                   # 各种文档文件
│
├── migrations/                # 数据库迁移文件
├── tests/                     # 全局测试文件
├── tools/                     # 开发工具
├── config/                    # 配置文件
├── records/                   # 记录文件（日志、数据等）
├── logs/                      # 日志文件
│
└── README.md                  # 项目主文档

```

## 🔑 关键目录说明

### `server/` - 后端代码
**所有后端相关代码统一放在 `server/` 目录下**，包括：
- FastAPI 应用代码
- AI 服务模块
- 数据库模型和服务
- 业务逻辑处理
- 工具函数

### `scripts/` - 工具脚本
**所有工具脚本统一放在 `scripts/` 目录下**，包括：
- 数据库初始化脚本
- 用户管理脚本
- 调试诊断脚本
- 服务启动脚本

### `docs/` - 文档
**所有文档文件统一放在 `docs/` 目录下**，包括：
- 开发文档
- 使用指南
- 配置说明
- 历史代码（`docs/legacy_code/`）

### `server/tests/` - 测试文件
**所有测试文件统一放在 `server/tests/` 目录下**，包括：
- 单元测试
- 集成测试
- API 测试

## 📝 文件组织原则

1. **后端代码统一在 `server/`**：所有 Python 后端代码都在 `server/` 目录下，便于维护和部署
2. **脚本统一在 `scripts/`**：所有工具脚本都在 `scripts/` 目录下，便于查找和使用
3. **文档统一在 `docs/`**：所有文档都在 `docs/` 目录下，便于查找和阅读
4. **测试统一在 `server/tests/`**：所有测试文件都在 `server/tests/` 目录下，便于测试管理

## 🔄 迁移历史

以下模块已从根目录迁移到 `server/modules/`：
- `AST_module` → `server/modules/ast/`
- `DouyinLiveWebFetcher` → `server/modules/douyin/`
- `StreamCap` 后端 → `server/modules/streamcap/`

历史代码已移动到 `docs/legacy_code/` 目录，仅用于参考。

## 📚 相关文档

- [README.md](../README.md) - 项目主文档
- [AI模型配置指南.md](AI模型配置指南.md) - AI 模型配置说明
- [DEPRECATION_NOTICE.md](DEPRECATION_NOTICE.md) - 模块迁移说明

