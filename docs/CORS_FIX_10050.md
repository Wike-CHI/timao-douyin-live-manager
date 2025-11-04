# CORS修复 - 端口10050

## 问题
管理后台已改为端口10050，但仍遇到CORS错误：
- `Access to fetch at 'http://127.0.0.1:9019/api/auth/login' from origin 'http://localhost:10050' has been blocked by CORS policy`
- OPTIONS请求返回400错误

## 修复内容

### 1. 端口配置更新
- ✅ `admin-dashboard/vite.config.ts` - 端口改为10050
- ✅ `server/app/main.py` - CORS允许列表添加10050端口
- ✅ `server/app/core/middleware.py` - 默认CORS源更新
- ✅ 启动脚本和文档已更新

### 2. OPTIONS请求处理
创建了专门的中间件 `OPTIONSHandlerMiddleware`，在CORS中间件之前拦截所有OPTIONS请求：
- 中间件优先处理OPTIONS预检请求
- 返回正确的CORS响应头
- 详细的日志记录便于调试

### 3. 错误日志增强
- 后端：OPTIONS中间件会记录所有预检请求的详细信息
- 前端：authProvider增加了详细的请求/响应日志

## 使用说明

### 1. 重启后端服务（必须）
```powershell
# 停止当前服务（Ctrl+C）
# 重新启动
uvicorn server.app.main:app --reload --port 9019
```

### 2. 启动管理后台
```powershell
cd admin-dashboard
npm run dev
```

### 3. 访问地址
- 管理后台：http://localhost:10050
- 后端API：http://127.0.0.1:9019

### 4. 验证CORS
后端启动后，你应该看到：
```
🌐 CORS配置已加载
   - http://localhost:10050  # 应该在这里
```

当有OPTIONS请求时，应该看到：
```
🌐 [OPTIONS中间件] 预检请求 - Origin: http://localhost:10050, Path: /api/auth/login
✅ [OPTIONS中间件] Origin在允许列表中: http://localhost:10050
📤 [OPTIONS中间件] 返回200响应 - Allow-Origin: http://localhost:10050
```

## 调试步骤

如果仍有CORS错误：

1. **检查后端日志**
   - 查看是否有 `[OPTIONS中间件]` 日志
   - 如果没有，说明中间件没有执行，需要检查中间件配置
   - 如果有但返回400，检查中间件代码

2. **检查前端日志**
   - 打开浏览器控制台（F12）
   - 查看网络标签页，检查OPTIONS请求的状态码
   - 查看响应头是否包含 `Access-Control-Allow-Origin`

3. **测试CORS端点**
   ```
   http://localhost:10050 -> http://127.0.0.1:9019/api/cors-test
   ```
   应该返回：
   ```json
   {
     "message": "CORS配置正常",
     "origin": "http://localhost:10050",
     "origin_allowed": true
   }
   ```

4. **验证OPTIONS请求**
   - 在浏览器控制台执行：
   ```javascript
   fetch('http://127.0.0.1:9019/api/auth/login', {
     method: 'OPTIONS',
     headers: {
       'Origin': 'http://localhost:10050',
       'Access-Control-Request-Method': 'POST'
     }
   }).then(r => {
     console.log('Status:', r.status);
     console.log('Headers:', [...r.headers.entries()]);
   });
   ```

## 管理员账号

- 用户名：`tc1102Admin`
- 密码：`xjystimao1115`

