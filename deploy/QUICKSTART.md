# ⚡ 快速开始指南

> 5分钟完成云服务器部署

## 🎯 快速部署（3步）

### 第1步：配置服务器信息

```bash
# 复制配置模板
cp deploy/upload_config.env.template deploy/upload_config.env

# 编辑配置（填写服务器信息）
vim deploy/upload_config.env
```

**必填配置**：
```env
SERVER_HOST="12.34.56.78"           # 你的服务器IP
SERVER_USER="root"                   # SSH用户名
SERVER_PATH="/opt/timao-douyin"      # 部署路径
```

### 第2步：一键部署

```bash
# 赋予执行权限
chmod +x deploy/deploy_all.sh

# 开始部署
./deploy/deploy_all.sh
```

### 第3步：访问服务

```bash
# 前端
http://你的服务器IP

# 后端
http://你的服务器IP:11111

# API文档
http://你的服务器IP:11111/docs
```

---

## 🔧 部署过程

部署脚本会自动执行以下步骤：

1. ✅ **检查环境** - 检查Docker、端口、磁盘空间
2. ✅ **上传代码** - 通过rsync快速上传
3. ✅ **配置环境** - 交互式配置数据库等信息
4. ✅ **部署服务** - 构建镜像并启动服务
5. ✅ **验证部署** - 自动测试服务是否正常
6. ✅ **配置监控** - 设置日志和健康检查

**预计耗时**：10-15分钟（首次部署）

---

## ⚙️ 配置说明

### 交互式配置

部署过程中会提示输入以下配置：

```
后端端口: [11111]
数据库地址: [localhost]
数据库端口: [3306]
数据库用户名: [timao]
数据库密码: ********
数据库名称: [timao]
JWT密钥: [自动生成]
CORS源: [*]
日志级别: [INFO]
```

**提示**：
- 方括号 `[]` 中的是默认值
- 留空回车即使用默认值
- JWT密钥留空会自动生成安全密钥

---

## 🚨 常见问题

### Q1: Docker未安装？

脚本会提示安装，选择 `y` 自动安装：

```bash
是否安装 Docker? (y/n)
y
```

### Q2: 端口被占用？

查看占用进程：
```bash
lsof -i :80
lsof -i :11111
```

释放端口或修改配置使用其他端口。

### Q3: 外部无法访问？

开放防火墙端口：

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 11111/tcp

# CentOS
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=11111/tcp
sudo firewall-cmd --reload
```

### Q4: 数据库连接失败？

检查：
1. 数据库地址是否正确
2. 数据库用户名和密码是否正确
3. 数据库是否允许远程连接
4. 防火墙是否开放数据库端口

---

## 📊 部署后管理

### 查看服务状态

```bash
ssh user@server 'cd /opt/timao-douyin && docker-compose -f docker-compose.full.yml ps'
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

### 健康检查

```bash
ssh user@server '/opt/timao-douyin/health_check.sh'
```

---

## 🎯 高级选项

### 跳过环境检查

如果已经部署过，可以跳过环境检查：

```bash
./deploy/deploy_all.sh --skip-prepare
```

### 仅检查环境

只检查环境，不执行部署：

```bash
./deploy/deploy_all.sh --check-only
```

### 分步部署

如果需要更精细的控制：

```bash
# 1. 环境准备
./deploy/1_prepare_environment.sh

# 2. 上传代码
./deploy/2_upload_code.sh

# 3. 配置环境
./deploy/3_configure_environment.sh

# 4. 部署服务
./deploy/4_deploy_services.sh

# 5. 验证部署
./deploy/5_validate_deployment.sh

# 6. 配置监控
./deploy/6_setup_monitoring.sh
```

---

## 📝 部署报告

部署完成后会生成以下报告：

```
deploy/
├── environment_check_report.txt    # 环境检查报告
├── upload_report.txt               # 上传报告
├── configure_report.txt            # 配置报告
├── deploy_report.txt               # 部署报告
├── validation_report.txt           # 验证报告
├── monitoring_report.txt           # 监控配置报告
└── final_deployment_report.txt     # 完整部署报告
```

---

## 🆘 获取帮助

如需详细文档，查看：

```bash
cat deploy/README.md
```

如有问题，检查部署报告：

```bash
cat deploy/final_deployment_report.txt
```

---

**祝部署顺利！** 🎉

