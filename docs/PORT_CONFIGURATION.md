# 端口配置管理文档

**审查人**: 叶维哲  
**更新时间**: 2025-11-07  
**原则**: 奥卡姆剃刀原则、单一职责原则、KISS原则

---

## 📋 概述

本项目采用**前后端分离**的端口配置管理策略，每个模块在自己的目录中维护独立的`.env`文件。

### 核心原则

1. ✅ **单一职责**: 前后端各自管理自己的配置
2. ✅ **简单明了**: 配置文件就近放置，易于查找和修改
3. ✅ **避免硬编码**: 所有端口从环境变量读取
4. ✅ **默认值合理**: 提供合理的默认端口，开箱即用

---

## 🚀 端口分配表

| 服务 | 端口 | 环境变量 | 配置文件位置 | 说明 |
|------|------|---------|-------------|------|
| **前端开发服务器** | 10013 | `VITE_PORT` | `electron/renderer/.env` | Vite开发服务器 |
| **Electron主窗口** | - | - | - | 使用file://协议 |
| **后端主服务** | 9030 | `BACKEND_PORT` | `server/.env` | FastAPI主服务 |
| **StreamCap** | 9030 | - | - | 已集成到主服务 |
| **Douyin** | 9030 | - | - | 已集成到主服务 |

### 🔄 端口统一说明

- ✅ **所有后端服务已统一到9030端口**（遵循KISS原则）
- ✅ **前端开发端口独立为10013**（前后端分离）
- ✅ **避免Windows保留端口**（8930-9029为Windows保留范围）

---

## 📁 配置文件结构

```
timao-douyin-live-manager/
├── electron/
│   └── renderer/
│       ├── .env                    # 前端环境变量
│       ├── .env.example           # 前端配置示例
│       └── package.json           # dev命令使用VITE_PORT
│
└── server/
    ├── .env                       # 后端环境变量
    ├── .env.example              # 后端配置示例
    └── config.py                 # 读取BACKEND_PORT
```

---

## 🎨 前端配置

### 配置文件: `electron/renderer/.env`

```env
# ============================================
# 前端开发环境变量
# ============================================

# ------------------------------------------
# 🌐 开发服务器配置
# ------------------------------------------
# Vite开发服务器端口
VITE_PORT=10013

# 开发服务器主机
VITE_HOST=127.0.0.1

# ------------------------------------------
# 🔗 后端服务地址
# ------------------------------------------
# FastAPI主服务地址
VITE_FASTAPI_URL=http://127.0.0.1:9030

# StreamCap服务地址（已集成到主服务）
VITE_STREAMCAP_URL=http://127.0.0.1:9030

# Douyin服务地址（已集成到主服务）
VITE_DOUYIN_URL=http://127.0.0.1:9030

# ------------------------------------------
# 🔐 认证配置
# ------------------------------------------
# 认证基础URL（可选，默认使用VITE_FASTAPI_URL）
# VITE_AUTH_BASE_URL=http://127.0.0.1:9030

# ------------------------------------------
# 🛠️ 开发配置
# ------------------------------------------
# 启用HMR热更新
VITE_HMR=true

# 启用源码映射
VITE_SOURCEMAP=true
```

### 使用方式

**package.json**:
```json
{
  "scripts": {
    "dev": "vite --host $VITE_HOST --port $VITE_PORT"
  }
}
```

**TypeScript代码**:
```typescript
// 读取后端服务地址
const apiBaseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9030';
```

---

## 🖥️ 后端配置

### 配置文件: `server/.env`

```env
# ============================================
# 后端服务环境变量
# ============================================

# ------------------------------------------
# 🚀 服务端口配置
# ------------------------------------------
# FastAPI主服务端口
BACKEND_PORT=9030

# ------------------------------------------
# 🗄️ 数据库配置
# ------------------------------------------
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=timao_live

# ------------------------------------------
# 🔐 安全配置
# ------------------------------------------
# JWT密钥（生产环境必须修改！）
SECRET_KEY=your-secret-key-change-in-production

# 数据加密密钥
ENCRYPTION_KEY=your-encryption-key-32chars

# ------------------------------------------
# 🤖 AI服务配置
# ------------------------------------------
# OpenAI
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 阿里通义千问
QWEN_API_KEY=

# 百度文心一言
BAIDU_API_KEY=
BAIDU_SECRET_KEY=

# Google Gemini
GEMINI_API_KEY=

# 默认AI服务商 (openai/qwen/baidu/gemini)
DEFAULT_AI_PROVIDER=gemini

# ------------------------------------------
# 📊 Redis配置（可选）
# ------------------------------------------
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ------------------------------------------
# 🎯 抖音直播配置
# ------------------------------------------
# 抖音Cookie（用于获取直播间信息）
DOUYIN_COOKIE=

# ------------------------------------------
# 🔊 音频转写配置
# ------------------------------------------
# SenseVoice模型路径
SENSEVOICE_MODEL_PATH=

# ------------------------------------------
# 📝 日志配置
# ------------------------------------------
LOG_LEVEL=INFO
LOG_DIR=logs

# ------------------------------------------
# 🌐 CORS配置
# ------------------------------------------
CORS_ORIGINS=*

# ------------------------------------------
# 💾 存储配置
# ------------------------------------------
DATA_DIR=data
UPLOAD_DIR=uploads
REPORT_DIR=reports

# ------------------------------------------
# ⚙️ 应用配置
# ------------------------------------------
# 开发模式
DEBUG=false

# 时区
TIMEZONE=Asia/Shanghai

# ------------------------------------------
# 📦 功能开关
# ------------------------------------------
# WebSocket支持
WEBSOCKET_ENABLED=true

# 评论过滤
COMMENT_FILTER_ENABLED=true

# AI情感分析
SENTIMENT_ANALYSIS_ENABLED=true
```

### 使用方式

**config.py**:
```python
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

@dataclass
class ServerConfig:
    # 从环境变量读取端口
    port: int = int(os.getenv("BACKEND_PORT", "9030"))
```

**main.py**:
```python
import os

if __name__ == "__main__":
    backend_port = int(os.getenv("BACKEND_PORT", "9030"))
    uvicorn.run("main:app", host="0.0.0.0", port=backend_port)
```

---

## 🔄 迁移指南

### 从根目录.env迁移到前后端分离

#### 步骤1: 识别配置项

根目录`.env`中的配置项按功能分类：

**前端相关** → 迁移到 `electron/renderer/.env`:
- `VITE_PORT`
- `VITE_FASTAPI_URL`
- `VITE_STREAMCAP_URL`
- `VITE_DOUYIN_URL`
- `VITE_*` 所有前端环境变量

**后端相关** → 迁移到 `server/.env`:
- `BACKEND_PORT`
- `DB_TYPE`, `MYSQL_*` 数据库配置
- `SECRET_KEY`, `ENCRYPTION_KEY` 安全配置
- `OPENAI_*`, `QWEN_*`, `BAIDU_*`, `GEMINI_*` AI配置
- `REDIS_*` Redis配置
- `DOUYIN_COOKIE`
- `SENSEVOICE_MODEL_PATH`
- `LOG_*` 日志配置
- 其他后端服务配置

#### 步骤2: 创建前端.env

```bash
# 创建前端环境变量文件
cd electron/renderer
cat > .env << 'EOF'
VITE_PORT=10013
VITE_HOST=127.0.0.1
VITE_FASTAPI_URL=http://127.0.0.1:9030
VITE_STREAMCAP_URL=http://127.0.0.1:9030
VITE_DOUYIN_URL=http://127.0.0.1:9030
EOF
```

#### 步骤3: 创建后端.env

```bash
# 创建后端环境变量文件
cd server
cat > .env << 'EOF'
BACKEND_PORT=9030
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=timao_live
# ... 复制其他后端配置
EOF
```

#### 步骤4: 验证配置

```bash
# 1. 验证前端配置
cd electron/renderer
npm run dev
# 应该启动在 http://127.0.0.1:10013

# 2. 验证后端配置
cd server
python -m uvicorn app.main:app --reload
# 应该启动在 http://0.0.0.0:9030
```

---

## 🧪 测试配置

### 测试环境变量: `server/tests/.env.test`

```env
# 测试环境配置
BACKEND_PORT=10090  # 测试专用端口，避免冲突
DB_TYPE=sqlite
DATABASE_PATH=:memory:  # 内存数据库
REDIS_ENABLED=false
```

### 集成测试配置

测试脚本中读取配置:

```python
# server/tests/integration/test_douyin_live_integration.py
import os

BASE_URL = f"http://localhost:{os.getenv('BACKEND_PORT', '9030')}"
```

---

## 🛠️ 开发工具

### 1. 端口检查脚本

```python
# scripts/check_ports.py
import os
import socket

def check_port(port: int, service: str):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"❌ {service} 端口 {port} 已被占用")
        return False
    else:
        print(f"✅ {service} 端口 {port} 可用")
        return True

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # 加载后端配置
    load_dotenv('server/.env')
    backend_port = int(os.getenv('BACKEND_PORT', '9030'))
    
    # 加载前端配置
    load_dotenv('electron/renderer/.env')
    frontend_port = int(os.getenv('VITE_PORT', '10013'))
    
    print("🔍 检查端口占用情况...")
    check_port(backend_port, "后端服务")
    check_port(frontend_port, "前端开发服务器")
```

### 2. 配置验证脚本

```python
# scripts/validate_config.py
import os
from pathlib import Path

def validate_env_file(env_path: str, required_vars: list):
    """验证.env文件是否包含必需变量"""
    if not Path(env_path).exists():
        print(f"❌ 配置文件不存在: {env_path}")
        return False
    
    from dotenv import dotenv_values
    config = dotenv_values(env_path)
    
    missing = [var for var in required_vars if var not in config]
    
    if missing:
        print(f"❌ {env_path} 缺少配置: {', '.join(missing)}")
        return False
    else:
        print(f"✅ {env_path} 配置完整")
        return True

if __name__ == "__main__":
    # 验证前端配置
    frontend_required = ['VITE_PORT', 'VITE_FASTAPI_URL']
    validate_env_file('electron/renderer/.env', frontend_required)
    
    # 验证后端配置
    backend_required = ['BACKEND_PORT', 'DB_TYPE', 'SECRET_KEY']
    validate_env_file('server/.env', backend_required)
```

---

## 🚨 常见问题

### Q1: 为什么不用根目录统一管理？

**A**: 遵循**单一职责原则**和**就近原则**:
- ✅ 前端开发者只需关注`electron/renderer/.env`
- ✅ 后端开发者只需关注`server/.env`
- ✅ 配置修改影响范围明确
- ✅ 减少配置冲突和误修改

### Q2: 端口冲突怎么办？

**A**: 修改对应的`.env`文件:
```bash
# 如果9030被占用，修改server/.env
BACKEND_PORT=9031

# 如果10013被占用，修改electron/renderer/.env
VITE_PORT=10014
```

### Q3: 集成测试如何配置端口？

**A**: 测试脚本从环境变量读取:
```python
# 默认使用开发环境端口
BASE_URL = f"http://localhost:{os.getenv('BACKEND_PORT', '9030')}"

# 或在测试启动前设置环境变量
export BACKEND_PORT=10090
python scripts/test_douyin_live.py
```

### Q4: Docker部署如何配置？

**A**: 使用Docker环境变量覆盖:
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - BACKEND_PORT=9030
    ports:
      - "9030:9030"
```

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `electron/renderer/.env` | 前端环境变量 |
| `electron/renderer/.env.example` | 前端配置示例 |
| `electron/renderer/package.json` | 前端启动脚本 |
| `electron/renderer/src/services/apiConfig.ts` | 前端API配置 |
| `server/.env` | 后端环境变量 |
| `server/.env.example` | 后端配置示例 |
| `server/config.py` | 后端配置管理 |
| `server/app/main.py` | 后端启动入口 |
| `scripts/check_ports.py` | 端口检查工具 |
| `scripts/validate_config.py` | 配置验证工具 |

---

## ✅ 最佳实践

1. **不要提交.env到Git**
   ```bash
   # .gitignore 已包含
   .env
   server/.env
   electron/renderer/.env
   ```

2. **维护.env.example**
   ```bash
   # 更新配置后同步更新example
   cp server/.env server/.env.example
   # 移除敏感信息
   ```

3. **使用环境变量覆盖**
   ```bash
   # 临时修改端口启动
   BACKEND_PORT=9031 python server/app/main.py
   ```

4. **生产环境使用环境变量**
   ```bash
   # 不依赖.env文件
   export BACKEND_PORT=9030
   export SECRET_KEY=production-secret
   ```

---

## 📝 总结

✅ **前端端口**: 10013 (`electron/renderer/.env` → `VITE_PORT`)  
✅ **后端端口**: 9030 (`server/.env` → `BACKEND_PORT`)  
✅ **配置分离**: 前后端各自管理，职责清晰  
✅ **避免硬编码**: 所有端口从环境变量读取  
✅ **默认值合理**: 开箱即用，降低配置门槛

**遵循原则**: 奥卡姆剃刀（简单优先）、KISS（保持简单）、单一职责（各管各的）

