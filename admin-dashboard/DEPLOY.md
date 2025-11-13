# 管理后台部署文档

## 部署到公网IP: 129.211.218.135

### 部署路径
- 公网访问地址: `http://129.211.218.135/admin/`
- 或: `http://129.211.218.135:10065/` (如果使用独立端口)

---

## 部署方案

### 方案一：使用 Nginx 反向代理（推荐）

#### 1. 构建生产版本

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard

# 设置生产环境变量
export VITE_FASTAPI_URL=http://129.211.218.135:10090
export VITE_ADMIN_PORT=10065

# 构建
npm run build
```

构建产物位于 `dist/` 目录。

#### 2. 配置 Nginx

创建或编辑 Nginx 配置文件：

```nginx
server {
    listen 80;
    server_name 129.211.218.135;

    # 管理后台路径
    location /admin/ {
        alias /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard/dist/;
        try_files $uri $uri/ /admin/index.html;
        index index.html;
        
        # 添加安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # API 代理（如果需要）
    location /api/ {
        proxy_pass http://127.0.0.1:10090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS 配置（如果需要）
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        alias /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 3. 配置 Vite 构建

修改 `vite.config.ts` 以支持子路径部署：

```typescript
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const port = Number(env.VITE_ADMIN_PORT || env.PORT || '10065');
  const apiTarget = env.VITE_FASTAPI_URL || 'http://127.0.0.1:10090';

  return {
    plugins: [react()],
    base: '/admin/',  // 添加 base 路径
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  };
});
```

#### 4. 重新构建并重启 Nginx

```bash
# 重新构建
npm run build

# 测试 Nginx 配置
nginx -t

# 重启 Nginx
systemctl restart nginx
# 或
service nginx restart
```

---

### 方案二：使用 Vite Preview（开发/测试）

#### 1. 配置环境变量

创建 `.env.production` 文件：

```env
VITE_ADMIN_PORT=10065
VITE_FASTAPI_URL=http://129.211.218.135:10090
```

#### 2. 构建并预览

```bash
# 构建
npm run build

# 预览（监听所有网络接口）
npm run preview -- --host 0.0.0.0 --port 10065
```

访问: `http://129.211.218.135:10065`

---

### 方案三：使用 PM2 管理（生产环境）

#### 1. 安装 PM2

```bash
npm install -g pm2
```

#### 2. 创建启动脚本

创建 `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'admin-dashboard',
    script: 'npm',
    args: 'run preview',
    cwd: '/www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard',
    env: {
      NODE_ENV: 'production',
      VITE_ADMIN_PORT: 10065,
      VITE_FASTAPI_URL: 'http://129.211.218.135:10090'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
```

#### 3. 启动服务

```bash
# 构建
npm run build

# 启动 PM2
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs admin-dashboard

# 设置开机自启
pm2 startup
pm2 save
```

---

## 环境变量配置

### 生产环境变量文件 `.env.production`

```env
# 后端 API 地址（公网IP）
VITE_FASTAPI_URL=http://129.211.218.135:10090

# 管理后台端口
VITE_ADMIN_PORT=10065
```

### 开发环境变量文件 `.env.development`

```env
# 后端 API 地址（本地开发）
VITE_FASTAPI_URL=http://127.0.0.1:10090

# 管理后台端口
VITE_ADMIN_PORT=10065
```

---

## 安全检查清单

- [ ] 修改默认管理员密码
- [ ] 配置 HTTPS（使用 Let's Encrypt）
- [ ] 配置防火墙规则（只开放必要端口）
- [ ] 配置 CORS 策略（限制允许的域名）
- [ ] 启用 Nginx 访问日志和错误日志
- [ ] 配置速率限制（防止暴力破解）
- [ ] 定期更新依赖包

---

## 防火墙配置

```bash
# 开放必要端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-port=10065/tcp  # 如果使用独立端口
firewall-cmd --permanent --add-port=10090/tcp  # 后端API端口
firewall-cmd --reload
```

---

## HTTPS 配置（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
yum install certbot python3-certbot-nginx -y

# 获取证书
certbot --nginx -d 129.211.218.135

# 自动续期
certbot renew --dry-run
```

---

## 故障排查

### 1. 无法访问

- 检查防火墙是否开放端口
- 检查 Nginx 是否运行: `systemctl status nginx`
- 检查端口是否被占用: `netstat -tlnp | grep 10065`
- 查看 Nginx 错误日志: `tail -f /var/log/nginx/error.log`

### 2. API 请求失败

- 检查后端服务是否运行
- 检查 CORS 配置
- 检查 `VITE_FASTAPI_URL` 环境变量是否正确
- 查看浏览器控制台网络请求

### 3. 静态资源 404

- 检查 `base` 路径配置是否正确
- 检查 Nginx `alias` 路径是否正确
- 检查文件权限: `chmod -R 755 dist/`

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 安装依赖（如果有更新）
npm install

# 3. 重新构建
npm run build

# 4. 重启服务
# Nginx 方案：无需重启，自动使用新文件
# PM2 方案：pm2 restart admin-dashboard
```

---

## 联系信息

- 审查人: 叶维哲
- 部署日期: 2025-01-XX

