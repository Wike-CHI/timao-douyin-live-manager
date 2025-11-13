# 快速部署指南

## 一键部署到 129.211.218.135

### 快速步骤（3步）

```bash
# 1. 进入项目目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard

# 2. 创建生产环境变量文件
cat > .env.production << EOF
VITE_FASTAPI_URL=http://129.211.218.135:10090
VITE_ADMIN_PORT=10065
EOF

# 3. 运行部署脚本
./deploy.sh
```

### 配置 Nginx（如果使用）

```bash
# 复制配置示例
sudo cp nginx.conf.example /etc/nginx/conf.d/admin-dashboard.conf

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 访问地址

- **管理后台**: http://129.211.218.135/admin/
- **默认账号**: tc1102Admin / xjystimao1115

---

## 详细说明

查看完整文档：
- **完整部署文档**: [DEPLOY.md](./DEPLOY.md)
- **部署检查清单**: [DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)

