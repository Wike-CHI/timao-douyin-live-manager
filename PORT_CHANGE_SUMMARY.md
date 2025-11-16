# 🔄 端口变更总结

> **变更时间**：2025-01-15  
> **分支**：local-view  
> **审查人**：叶维哲

---

## 📊 端口变更

### 旧端口配置
| 服务 | 旧端口 | 问题 |
|------|-------|------|
| 后端 | 15000 | 不常用，可能有权限问题 |
| 前端 | 10050 | Windows权限拒绝错误 |

### 新端口配置 ✅
| 服务 | 新端口 | 说明 |
|------|-------|------|
| 后端 | **8080** | 常用开发端口，无权限问题 |
| 前端 | **3000** | React默认端口，无权限问题 |

---

## 🔧 修改的文件

### 1. server/.env
```env
BACKEND_PORT=8080  # 从 15000 改为 8080
```

### 2. electron/renderer/vite.config.ts
```typescript
server: {
  port: 3000,  // 从 10050 改为 3000
}
```

### 3. package.json
更新所有涉及端口的脚本：
- `server` 和 `server:prod`: 8080
- `health:*` 系列: 8080 和 3000
- `kill:*` 系列: 8080 和 3000
- `dev:electron`: 3000
- `dev:step3`: 3000
- `quick:start`: 3000

---

## 🚀 新的访问地址

| 服务 | 地址 |
|------|------|
| 后端API | http://127.0.0.1:8080 |
| 前端开发 | http://127.0.0.1:3000 |
| 健康检查 | http://127.0.0.1:8080/health |
| API文档 | http://127.0.0.1:8080/docs |

---

## ✅ 优势

1. **无权限问题** - 8080和3000是常用开发端口
2. **符合习惯** - 开发者熟悉这些端口
3. **更好兼容** - 不需要管理员权限
4. **易于记忆** - 标准的开发端口

---

## 🚀 快速启动

```bash
# 直接启动（不需要管理员权限）
npm run dev
```

启动后访问：
- 前端：http://127.0.0.1:3000
- 后端：http://127.0.0.1:8080

---

## 📝 测试验证

```bash
# 验证端口配置
type server\.env | findstr "BACKEND_PORT"
# 应该显示：BACKEND_PORT=8080

# 检查端口占用
netstat -ano | findstr ":8080"
netstat -ano | findstr ":3000"
```

---

## 🔄 如果需要改回去

```bash
# 1. 修改 server/.env
BACKEND_PORT=15000

# 2. 修改 electron/renderer/vite.config.ts
port: 10050

# 3. 修改 package.json 中的所有端口引用

# 4. 提交更改
git add -A
git commit -m "Revert port changes"
```

