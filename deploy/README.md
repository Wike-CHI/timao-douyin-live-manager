# 部署相关文件说明

本目录包含所有与部署相关的文件和文档。

## 📁 目录结构

```
deploy/
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml            # Docker Compose 配置（主服务）
├── docker-compose.mysql.yml      # Docker Compose 配置（MySQL）
├── cloudbaserc.json              # 云开发部署配置
├── config/                       # 部署配置文件
│   ├── deployment.json          # 部署配置
│   └── local-deployment.json    # 本地部署配置
├── scripts/                      # 部署脚本
│   ├── package-docker.bat       # Docker 打包脚本
│   ├── package-portable.bat     # 便携版打包脚本
│   └── package-local.bat        # 本地打包脚本
├── setup-dev-mysql.bat          # Windows MySQL 初始化脚本
├── setup-dev-mysql.sh           # Linux/Mac MySQL 初始化脚本
├── DEPLOYMENT.md                 # 部署主文档
├── DOCKER_README.md             # Docker 使用说明
└── README_DEPLOYMENT.md         # 部署快速指南
```

## 🚀 快速开始

### Docker 部署

```bash
# 从项目根目录运行
cd deploy
docker-compose up -d
```

### 本地部署

参考 `DEPLOYMENT.md` 获取详细的部署指南。

### MySQL 初始化

**Windows:**
```bash
deploy\setup-dev-mysql.bat
```

**Linux/Mac:**
```bash
bash deploy/setup-dev-mysql.sh
```

## 📚 文档说明

- **DEPLOYMENT.md** - 完整的部署文档，包含所有部署方式
- **DOCKER_README.md** - Docker 容器化部署详细说明
- **README_DEPLOYMENT.md** - 快速部署指南

## 🔧 配置文件

- **deployment.json** - 生产环境部署配置
- **local-deployment.json** - 本地开发环境配置
- **cloudbaserc.json** - 云开发平台配置

## 📝 注意事项

1. Docker Compose 文件中的 `context` 指向项目根目录（`..`），`dockerfile` 使用相对路径
2. 部署脚本需要从项目根目录运行
3. 配置文件中的路径可能需要根据实际部署环境调整

