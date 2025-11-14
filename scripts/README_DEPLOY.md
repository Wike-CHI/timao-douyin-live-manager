# 📦 前端构建和部署说明

## 🚀 快速开始

### 一键构建和部署

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
./scripts/build-and-deploy-web.sh
```

这个脚本会自动：
1. ✅ 检查项目目录和环境
2. ✅ 检查 Node.js 和 npm
3. ✅ 安装前端依赖（如需要）
4. ✅ 清理旧的构建产物
5. ✅ 使用生产配置构建前端
6. ✅ 备份当前版本
7. ✅ 部署到公网目录
8. ✅ 设置正确的文件权限

## 📂 目录结构

```
/www/wwwroot/
├── wwwroot/timao-douyin-live-manager/   # 项目源码
│   ├── electron/renderer/               # 前端源码
│   │   ├── .env.production             # 生产环境配置
│   │   └── dist/                       # 构建产物（临时）
│   └── scripts/
│       ├── build-and-deploy-web.sh     # 构建部署脚本
│       └── nginx-app-config.conf       # Nginx 配置参考
├── timao-app/                           # 公网访问目录（部署目标）
└── timao-app-backups/                   # 备份目录（自动管理）
```

## 🌐 访问地址

部署完成后，可以通过以下地址访问：

- **公网访问**: http://129.211.218.135/
- **本地访问**: http://127.0.0.1/

## ⚙️ 配置说明

### 前端生产环境配置

文件位置: `electron/renderer/.env.production`

```env
# 生产环境配置
VITE_FASTAPI_URL=http://129.211.218.135
VITE_STREAMCAP_URL=http://129.211.218.135
VITE_DOUYIN_URL=http://129.211.218.135
VITE_APP_ENV=production
```

### Nginx 配置

Nginx 配置已在 `nginx-final-config.conf` 中设置：

```nginx
location / {
    root /www/wwwroot/timao-app;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

## 🔧 手动操作

### 仅构建（不部署）

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer
npm run build
```

构建产物在 `electron/renderer/dist/` 目录。

### 手动部署

```bash
# 备份旧版本
cp -r /www/wwwroot/timao-app /www/wwwroot/timao-app-backups/backup-$(date +%Y%m%d_%H%M%S)

# 清空部署目录
rm -rf /www/wwwroot/timao-app/*

# 复制构建产物
cp -r /www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer/dist/* /www/wwwroot/timao-app/

# 设置权限
chmod -R 755 /www/wwwroot/timao-app
```

### 重新加载 Nginx

```bash
# 测试配置
nginx -t

# 重新加载
nginx -s reload

# 或者通过宝塔面板重载
```

## 🔄 回滚到旧版本

如果新版本有问题，可以快速回滚：

```bash
# 1. 查看可用备份
ls -lt /www/wwwroot/timao-app-backups/

# 2. 选择要恢复的备份（替换 BACKUP_NAME）
BACKUP_NAME="timao-app-backup-20251113_120000"

# 3. 恢复
rm -rf /www/wwwroot/timao-app/*
cp -r /www/wwwroot/timao-app-backups/$BACKUP_NAME/* /www/wwwroot/timao-app/
```

## 📊 备份管理

- **自动备份**: 每次部署前自动备份当前版本
- **备份保留**: 自动保留最近 5 个备份
- **备份位置**: `/www/wwwroot/timao-app-backups/`

## 🐛 故障排查

### 问题 1: 构建失败

```bash
# 清理依赖重新安装
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer
rm -rf node_modules package-lock.json
npm install
```

### 问题 2: 页面空白或 404

**原因**: Nginx 配置不正确或文件权限问题

**解决**:
```bash
# 检查文件是否存在
ls -la /www/wwwroot/timao-app/

# 检查权限
chmod -R 755 /www/wwwroot/timao-app

# 检查 Nginx 配置
nginx -t

# 查看 Nginx 错误日志
tail -f /www/wwwlogs/timao-error.log
```

### 问题 3: API 请求失败

**原因**: 后端服务未启动或环境变量配置错误

**解决**:
```bash
# 检查后端服务状态
pm2 list

# 重启后端
pm2 restart timao-backend

# 检查后端日志
pm2 logs timao-backend
```

### 问题 4: 环境变量未生效

**原因**: 环境变量在构建时注入，需要重新构建

**解决**:
```bash
# 修改 .env.production 后，必须重新构建
./scripts/build-and-deploy-web.sh
```

## 📝 开发流程

### 开发环境

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/electron/renderer
npm run dev
```

访问: http://127.0.0.1:10050

### 生产部署

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
./scripts/build-and-deploy-web.sh
```

访问: http://129.211.218.135/

## 🔐 安全提示

1. **环境变量**: 不要在 `.env.production` 中存放敏感信息（API密钥等）
2. **文件权限**: 部署目录权限应为 `755`
3. **备份**: 定期清理旧备份，避免占用过多磁盘空间
4. **HTTPS**: 生产环境建议配置 HTTPS（SSL证书）

## 📞 技术支持

- **项目文档**: `/www/wwwroot/wwwroot/timao-douyin-live-manager/CONFIG_GUIDE.md`
- **配置总结**: `/www/wwwroot/wwwroot/timao-douyin-live-manager/CONFIG_SUMMARY.md`
- **构建日志**: `/www/wwwroot/wwwroot/timao-douyin-live-manager/build-deploy.log`

