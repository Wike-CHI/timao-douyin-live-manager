# 🚀 云服务器部署方案

> 基于 **单一职责原则** 设计的模块化部署解决方案

## 📋 目录

- [方案概述](#方案概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [分步部署](#分步部署)
- [常见问题](#常见问题)
- [运维管理](#运维管理)

---

## 方案概述

### 设计原则

本部署方案严格遵循 **单一职责原则 (Single Responsibility Principle)**，将部署流程分解为6个独立的职责模块：

| 模块 | 职责 | 脚本 | 依赖 |
|-----|------|------|------|
| 环境准备器 | 检查和安装云服务器基础环境 | `1_prepare_environment.sh` | 无 |
| 代码传输器 | 将项目代码上传到云服务器 | `2_upload_code.sh` | 环境准备器 |
| 配置管理器 | 配置环境变量和数据库连接 | `3_configure_environment.sh` | 代码传输器 |
| 服务部署器 | 构建Docker镜像并启动服务 | `4_deploy_services.sh` | 配置管理器 |
| 部署验证器 | 验证部署是否成功 | `5_validate_deployment.sh` | 服务部署器 |
| 运维监控器 | 配置日志、监控和自动重启 | `6_setup_monitoring.sh` | 部署验证器 |

### 优势

- ✅ **职责清晰**：每个模块只做一件事
- ✅ **易于维护**：模块独立，互不干扰
- ✅ **灵活组合**：可以单独执行或组合执行
- ✅ **错误隔离**：问题定位快速准确
- ✅ **可复用**：模块可在不同项目中复用

---

## 架构设计

### 部署流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     一键部署脚本                              │
│                 deploy_all.sh                                │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 1: 环境准备器 (Environment Preparator)                  │
│  ├─ 检查操作系统                                              │
│  ├─ 检查 Docker / Docker Compose                             │
│  ├─ 检查端口占用                                              │
│  └─ 检查磁盘和内存                                            │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 2: 代码传输器 (Code Uploader)                           │
│  ├─ 检查服务器连接                                            │
│  ├─ 准备服务器目录                                            │
│  ├─ 上传项目代码 (rsync/scp)                                 │
│  └─ 验证上传结果                                              │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 3: 配置管理器 (Config Manager)                          │
│  ├─ 交互式配置收集                                            │
│  ├─ 生成配置文件                                              │
│  ├─ 上传到服务器                                              │
│  └─ 测试数据库连接                                            │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 4: 服务部署器 (Service Deployer)                        │
│  ├─ 构建 Docker 镜像                                          │
│  ├─ 停止旧服务                                                │
│  ├─ 启动新服务                                                │
│  └─ 检查服务状态                                              │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 5: 部署验证器 (Deployment Validator)                    │
│  ├─ 测试容器状态                                              │
│  ├─ 测试端口监听                                              │
│  ├─ 测试服务健康                                              │
│  └─ 生成验证报告                                              │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  步骤 6: 运维监控器 (Operations Monitor)                      │
│  ├─ 配置日志轮转                                              │
│  ├─ 配置自动重启                                              │
│  ├─ 创建监控脚本                                              │
│  └─ 配置定时任务                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 前提条件

- 一台云服务器（Ubuntu/Debian）
- SSH 访问权限
- 本地已安装 `rsync` 或 `scp`

### 一键部署

```bash
# 1. 配置服务器信息（首次部署）
cp deploy/upload_config.env.template deploy/upload_config.env
vim deploy/upload_config.env

# 2. 一键部署
chmod +x deploy/deploy_all.sh
./deploy/deploy_all.sh
```

就这么简单！脚本会自动执行所有步骤。

---

## 分步部署

如果需要更精细的控制，可以分步执行：

### 步骤 1: 准备环境

```bash
chmod +x deploy/1_prepare_environment.sh
./deploy/1_prepare_environment.sh
```

**功能**：
- 检查操作系统版本
- 检查 Docker 和 Docker Compose 安装状态
- 检查端口占用情况（80, 11111）
- 检查磁盘空间和内存
- 可选：自动安装 Docker

**输出**：
- `deploy/environment_check_report.txt` - 环境检查报告

### 步骤 2: 上传代码

```bash
chmod +x deploy/2_upload_code.sh
./deploy/2_upload_code.sh
```

**前提**：
- 已配置 `deploy/upload_config.env`

**功能**：
- 检查服务器 SSH 连接
- 创建项目目录
- 使用 rsync 或 scp 上传代码
- 自动排除不必要的文件（.git, node_modules 等）
- 验证上传结果

**输出**：
- `deploy/upload_report.txt` - 上传报告

### 步骤 3: 配置环境

```bash
chmod +x deploy/3_configure_environment.sh
./deploy/3_configure_environment.sh
```

**功能**：
- 交互式收集配置信息
  - 后端端口
  - 数据库配置
  - JWT 密钥
  - CORS 配置
- 生成生产环境 `.env` 文件
- 上传到服务器
- 测试数据库连接

**输出**：
- `deploy/configure_report.txt` - 配置报告
- 服务器上的 `server/.env` 文件

### 步骤 4: 部署服务

```bash
chmod +x deploy/4_deploy_services.sh
./deploy/4_deploy_services.sh
```

**功能**：
- 构建 Docker 镜像（后端、前端）
- 停止旧服务（如果存在）
- 启动新服务
- 检查服务状态

**输出**：
- `deploy/deploy_report.txt` - 部署报告

### 步骤 5: 验证部署

```bash
chmod +x deploy/5_validate_deployment.sh
./deploy/5_validate_deployment.sh
```

**功能**：
- 测试容器状态
- 测试端口监听
- 测试服务健康（本地和外部）
- 测试 API 文档访问
- 测试数据库连接
- 测试资源使用
- 生成验证报告

**输出**：
- `deploy/validation_report.txt` - 验证报告

### 步骤 6: 配置监控

```bash
chmod +x deploy/6_setup_monitoring.sh
./deploy/6_setup_monitoring.sh
```

**功能**：
- 配置日志轮转（7天，10MB）
- 配置 Docker 自动重启
- 创建健康检查脚本
- 创建日志查看脚本
- 配置定时任务（每小时健康检查）

**输出**：
- `deploy/monitoring_report.txt` - 监控配置报告
- 服务器上的监控脚本

---

## 配置说明

### upload_config.env 配置

```env
# 服务器配置
SERVER_HOST="your-server-ip"        # 云服务器IP或域名
SERVER_USER="root"                   # SSH 用户名
SERVER_PORT="22"                     # SSH 端口
SERVER_PATH="/opt/timao-douyin"      # 项目部署路径

# SSH 密钥配置（可选）
SSH_KEY_PATH="~/.ssh/id_rsa"        # SSH 私钥路径

# 传输方式
TRANSFER_METHOD="rsync"              # rsync 或 scp
```

### 生产环境配置

部署过程中会交互式收集以下配置：

```env
# 后端端口
BACKEND_PORT=11111

# 数据库配置
MYSQL_HOST=your-database-host
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=timao

# 安全配置
SECRET_KEY=auto-generated-or-manual
CORS_ORIGINS=*

# 日志配置
LOG_LEVEL=INFO
```

---

## 常见问题

### Q1: 如何使用 SSH 密钥登录？

在 `deploy/upload_config.env` 中配置：

```env
SSH_KEY_PATH="~/.ssh/id_rsa"
```

### Q2: 端口被占用怎么办？

1. 检查占用端口的进程：
   ```bash
   lsof -i :80
   lsof -i :11111
   ```

2. 停止占用的进程或修改配置使用其他端口

### Q3: 外部无法访问服务？

检查防火墙规则：

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 11111/tcp

# CentOS
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=11111/tcp
sudo firewall-cmd --reload
```

### Q4: 如何重新部署？

```bash
# 只重新部署服务（不重新上传代码）
./deploy/4_deploy_services.sh

# 完整重新部署
./deploy/deploy_all.sh
```

### Q5: 如何查看错误日志？

```bash
ssh user@server '/opt/timao-douyin/view_logs.sh backend'
ssh user@server '/opt/timao-douyin/view_logs.sh frontend'
ssh user@server '/opt/timao-douyin/view_logs.sh all'
```

### Q6: 数据库连接失败？

1. 检查数据库配置是否正确
2. 检查数据库是否允许远程连接
3. 检查防火墙是否允许数据库端口

---

## 运维管理

### 健康检查

```bash
# 在服务器上执行
/opt/timao-douyin/health_check.sh

# 或从本地执行
ssh user@server '/opt/timao-douyin/health_check.sh'
```

### 查看日志

```bash
# 后端日志
ssh user@server '/opt/timao-douyin/view_logs.sh backend'

# 前端日志
ssh user@server '/opt/timao-douyin/view_logs.sh frontend'

# 所有日志
ssh user@server '/opt/timao-douyin/view_logs.sh all'
```

### 重启服务

```bash
ssh user@server 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml restart'
```

### 停止服务

```bash
ssh user@server 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml down'
```

### 启动服务

```bash
ssh user@server 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml up -d'
```

### 查看资源使用

```bash
ssh user@server 'docker stats --no-stream'
```

---

## 文件结构

```
deploy/
├── README.md                           # 本文档
├── deploy_all.sh                       # 一键部署脚本
├── 1_prepare_environment.sh            # 环境准备器
├── 2_upload_code.sh                    # 代码传输器
├── 3_configure_environment.sh          # 配置管理器
├── 4_deploy_services.sh                # 服务部署器
├── 5_validate_deployment.sh            # 部署验证器
├── 6_setup_monitoring.sh               # 运维监控器
├── upload_config.env.template          # 配置模板
└── 生成的报告文件/
    ├── environment_check_report.txt
    ├── upload_report.txt
    ├── configure_report.txt
    ├── deploy_report.txt
    ├── validation_report.txt
    ├── monitoring_report.txt
    └── final_deployment_report.txt
```

---

## 设计原则说明

### 单一职责原则的应用

每个脚本模块只负责一个明确的职责：

1. **环境准备器** - 只负责检查和准备环境
2. **代码传输器** - 只负责代码传输
3. **配置管理器** - 只负责配置管理
4. **服务部署器** - 只负责服务部署
5. **部署验证器** - 只负责部署验证
6. **运维监控器** - 只负责运维配置

### 优势

- **易于理解**：每个模块功能单一，代码清晰
- **易于测试**：可以独立测试每个模块
- **易于维护**：修改一个模块不影响其他模块
- **易于扩展**：可以轻松添加新模块
- **易于调试**：问题定位快速准确

---

## 审查信息

**审查人**: 叶维哲  
**创建时间**: 2024-01-15  
**版本**: 1.0.0  

---

## 支持

如有问题，请检查：

1. 服务器 SSH 连接是否正常
2. Docker 和 Docker Compose 是否已安装
3. 数据库配置是否正确
4. 防火墙规则是否正确
5. 磁盘空间是否充足

**祝部署顺利！** 🎉
