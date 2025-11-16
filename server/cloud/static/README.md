# 云端服务控制台

**TalkingCat提猫直播助手 - 云端服务控制台**

---

## 📋 功能说明

这是一个静态HTML页面，用于展示云端服务的运行状态和可用功能。

### 显示内容

- ✅ **服务状态**: 实时显示云端服务运行状态
- ✅ **TalkingCat Logo**: 品牌标识展示
- ✅ **核心功能**: 用户系统、身份认证、订阅管理、支付处理、积分系统
- ✅ **API端点**: 列出所有可用的API接口
- ✅ **健康检查**: 可点击测试服务连接
- ✅ **版本信息**: 显示Python版本和内存限制
- ✅ **自动刷新**: 每30秒自动检查服务状态

---

## 🌐 访问方式

### 1. 本地直接访问
```
http://localhost:15000/
```

### 2. 通过Nginx访问
```
http://localhost/
```

### 3. 公网访问
```
http://服务器IP/
```

### 4. 域名访问（待备案）
```
https://api.timao.com/
```

---

## 📁 文件结构

```
server/cloud/static/
├── index.html              # 主页面（控制台）
├── assets/
│   └── logo_cat_headset.jpg  # TalkingCat Logo
└── README.md              # 本文档
```

---

## 🎨 设计特点

### 视觉设计
- 🎨 **渐变背景**: 紫色渐变背景，现代感十足
- 🖼️ **Logo动画**: TalkingCat Logo带脉搏动画效果
- 💫 **交互反馈**: 按钮和卡片带悬停效果
- 📱 **响应式设计**: 支持桌面和移动端访问

### 功能设计
- 🔄 **实时状态**: 状态徽章实时显示服务运行状态
- 🧪 **健康测试**: 点击按钮即可测试服务连接
- 📊 **信息展示**: 清晰展示服务类型、端口、内存限制等信息
- 🔌 **API列表**: 列出所有核心API端点

### 技术特点
- ⚡ **纯静态**: 无需额外依赖，FastAPI直接服务
- 🎯 **轻量级**: 单个HTML文件，加载快速
- 🔄 **自动刷新**: JavaScript定时检查服务状态
- 📡 **API调用**: 通过Fetch API获取实时数据

---

## 🔧 自定义修改

### 修改Logo
替换 `assets/logo_cat_headset.jpg` 为你自己的Logo图片。

### 修改样式
编辑 `index.html` 中的 `<style>` 标签内容。

### 修改API端点列表
编辑 `index.html` 中的 `.endpoint-list` 部分：
```html
<li class="endpoint-item">
    <span class="endpoint-method">GET</span>
    <span class="endpoint-path">/your/api/path</span>
</li>
```

### 修改功能卡片
编辑 `index.html` 中的 `.features-grid` 部分：
```html
<div class="feature-card">
    <div class="feature-icon">🆕</div>
    <div class="feature-title">新功能</div>
</div>
```

---

## 🧪 测试

### 快速测试
```bash
# 测试控制台页面
./scripts/test_cloud_dashboard.sh
```

### 手动测试
```bash
# 1. 测试健康检查
curl http://localhost:15000/health

# 2. 测试主页
curl http://localhost:15000/

# 3. 测试Logo
curl -I http://localhost:15000/static/assets/logo_cat_headset.jpg
```

### 浏览器测试
1. 打开浏览器访问: `http://localhost:15000/`
2. 点击"测试连接"按钮
3. 查看状态徽章是否显示"运行中"
4. 检查Logo是否正常加载

---

## 📊 状态说明

| 状态徽章 | 颜色 | 说明 |
|---------|------|------|
| 运行中 | 🟢 绿色 | 服务正常运行 |
| 异常 | 🔴 红色 | 服务运行异常 |
| 离线 | ⚪ 灰色 | 无法连接服务 |

---

## 🔐 安全建议

### 生产环境配置

1. **限制访问**: 配置Nginx限制只允许特定IP访问控制台
```nginx
location / {
    allow 192.168.1.0/24;  # 允许内网访问
    deny all;              # 拒绝其他访问
    try_files $uri @backend;
}
```

2. **添加认证**: 使用Nginx基础认证
```nginx
location / {
    auth_basic "Cloud Service Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    try_files $uri @backend;
}
```

3. **HTTPS加密**: 配置SSL证书
```bash
sudo certbot --nginx -d api.timao.com
```

---

## 🐛 故障排查

### 问题1: 页面显示空白

**可能原因**: 静态文件未正确挂载

**解决方案**:
```bash
# 检查静态文件是否存在
ls -la server/cloud/static/

# 重启服务
pm2 restart timao-cloud
```

### 问题2: Logo无法加载

**可能原因**: Logo文件路径错误

**解决方案**:
```bash
# 确认Logo文件存在
ls -la server/cloud/static/assets/logo_cat_headset.jpg

# 检查文件权限
chmod 644 server/cloud/static/assets/logo_cat_headset.jpg
```

### 问题3: 状态显示"离线"

**可能原因**: 服务未启动或健康检查失败

**解决方案**:
```bash
# 检查服务状态
pm2 status timao-cloud

# 查看日志
pm2 logs timao-cloud

# 测试健康检查
curl http://localhost:15000/health
```

---

## 📞 技术支持

- **代码审查人**: 叶维哲
- **相关文档**: 
  - `docs/部署文档/Electron桌面应用云端连接说明.md`
  - `docs/部署文档/云端服务部署指南.md`
- **测试脚本**: `scripts/test_cloud_dashboard.sh`

---

## 🎯 更新日志

### v1.0.0 (2025-11-16)
- ✅ 初始版本
- ✅ 添加TalkingCat Logo
- ✅ 显示服务状态和API端点
- ✅ 实现健康检查测试按钮
- ✅ 添加自动状态刷新
- ✅ 响应式设计

---

**快速访问**: 打开浏览器访问 `http://localhost:15000/` 查看控制台 🚀

