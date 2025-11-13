# 部署检查清单

## 部署前准备

### 1. 环境检查
- [ ] Node.js >= 16 已安装
- [ ] npm >= 8 已安装
- [ ] 后端服务运行在 `http://129.211.218.135:10090`
- [ ] 防火墙已开放端口 80/443（Nginx）或 10065（独立端口）

### 2. 配置文件
- [ ] 创建 `.env.production` 文件（参考下方内容）
- [ ] 确认 `VITE_FASTAPI_URL=http://129.211.218.135:10090`
- [ ] 确认 `VITE_ADMIN_PORT=10065`

### 3. 构建
- [ ] 运行 `./deploy.sh` 或 `npm run build`
- [ ] 检查 `dist/` 目录是否存在
- [ ] 检查 `dist/index.html` 是否存在

---

## 部署步骤

### 方案一：Nginx 部署（推荐）

1. **构建项目**
   ```bash
   cd /www/wwwroot/wwwroot/timao-douyin-live-manager/admin-dashboard
   ./deploy.sh
   ```

2. **配置 Nginx**
   ```bash
   # 复制配置示例
   sudo cp nginx.conf.example /etc/nginx/conf.d/admin-dashboard.conf
   
   # 或编辑主配置文件
   sudo vim /etc/nginx/nginx.conf
   ```

3. **测试配置**
   ```bash
   sudo nginx -t
   ```

4. **重启 Nginx**
   ```bash
   sudo systemctl restart nginx
   # 或
   sudo service nginx restart
   ```

5. **验证部署**
   - 访问: http://129.211.218.135/admin/
   - 检查静态资源加载
   - 检查 API 请求是否正常

---

### 方案二：PM2 部署

1. **安装 PM2**
   ```bash
   npm install -g pm2
   ```

2. **创建 ecosystem.config.js**（参考 DEPLOY.md）

3. **构建并启动**
   ```bash
   npm run build
   pm2 start ecosystem.config.js
   pm2 save
   ```

4. **验证**
   - 访问: http://129.211.218.135:10065
   - 检查: `pm2 status`
   - 查看日志: `pm2 logs admin-dashboard`

---

## 环境变量文件内容

创建 `.env.production`:

```env
VITE_FASTAPI_URL=http://129.211.218.135:10090
VITE_ADMIN_PORT=10065
```

创建 `.env.development`:

```env
VITE_FASTAPI_URL=http://127.0.0.1:10090
VITE_ADMIN_PORT=10065
```

---

## 部署后验证

### 功能测试
- [ ] 访问登录页面: http://129.211.218.135/admin/
- [ ] 使用默认账号登录（tc1102Admin / xjystimao1115）
- [ ] 检查仪表板数据加载
- [ ] 检查用户管理功能
- [ ] 检查支付管理功能
- [ ] 检查订阅套餐管理
- [ ] 检查 AI 成本监控
- [ ] 检查数据分析图表
- [ ] 检查系统监控
- [ ] 检查审计日志

### 性能测试
- [ ] 页面加载速度 < 3秒
- [ ] API 请求响应正常
- [ ] 静态资源缓存生效
- [ ] 无控制台错误

### 安全检查
- [ ] 修改默认管理员密码
- [ ] 配置 HTTPS（推荐）
- [ ] 检查 CORS 配置
- [ ] 检查防火墙规则
- [ ] 检查访问日志

---

## 常见问题

### 1. 404 错误
- 检查 Nginx `alias` 路径是否正确
- 检查 `base` 路径配置（应为 `/admin/`）
- 检查 `try_files` 配置

### 2. API 请求失败
- 检查后端服务是否运行
- 检查 `VITE_FASTAPI_URL` 环境变量
- 检查 CORS 配置
- 查看浏览器控制台网络请求

### 3. 静态资源 404
- 检查文件权限: `chmod -R 755 dist/`
- 检查 Nginx 配置中的静态资源路径
- 检查 `base` 路径配置

### 4. 页面空白
- 检查浏览器控制台错误
- 检查 `dist/index.html` 中的资源路径
- 检查网络请求是否被阻止

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 安装依赖（如有更新）
npm install

# 3. 重新构建
npm run build

# 4. 重启服务
# Nginx: 无需重启，自动使用新文件
# PM2: pm2 restart admin-dashboard
```

---

## 回滚步骤

```bash
# 1. 切换到上一个版本
git checkout <previous-commit-hash>

# 2. 重新构建
npm run build

# 3. 重启服务（如需要）
```

---

## 联系信息

- 审查人: 叶维哲
- 部署日期: 2025-01-XX

