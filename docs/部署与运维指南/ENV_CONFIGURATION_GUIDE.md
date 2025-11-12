# 环境变量配置完整指南

**审查人**: 叶维哲  
**更新时间**: 2025-11-07  
**遵循原则**: KISS、单一职责、希克定律

---

## 🎯 问题解决

### 启动错误: `reload_exclude` 参数不支持

**问题**: 
```
TypeError: run() got an unexpected keyword argument 'reload_exclude'
```

**原因**: 旧版本uvicorn不支持该参数

**解决**: ✅ 已移除不兼容参数，使用标准uvicorn启动

---

## 📋 配置文件结构 (遵循单一职责)

```
timao-douyin-live-manager/
├── server/
│   ├── .env                    # 后端环境变量 (必须创建)
│   └── ENV_TEMPLATE.md         # 后端配置模板
├── electron/
│   └── renderer/
│       ├── .env                # 前端环境变量 (必须创建)
│       └── ENV_TEMPLATE.md     # 前端配置模板
└── scripts/
    ├── setup_env.py            # 一键配置脚本
    └── validate_port_config.py # 配置验证脚本
```

---

## 🚀 快速配置 (3步完成)

### 方法1: 一键配置 (推荐)

```bash
# 一键创建前后端配置
python scripts/初始化与迁移/setup_env.py

# 验证配置
python scripts/检查与校验/validate_port_config.py
```

### 方法2: 手动配置

#### 步骤1: 创建后端配置

```bash
cd server
notepad .env  # 复制 ENV_TEMPLATE.md 中的内容
```

#### 步骤2: 创建前端配置

```bash
cd electron/renderer
notepad .env  # 复制 ENV_TEMPLATE.md 中的内容
```

#### 步骤3: 验证配置

```bash
python scripts/检查与校验/validate_port_config.py
```

---

## 📊 端口配置表 (遵循希克定律)

| 服务 | 端口 | 环境变量 | 配置文件 | 优先级 |
|------|------|---------|---------|--------|
| **后端主服务** | 9030 | `BACKEND_PORT` | `server/.env` | ⭐⭐⭐ |
| **前端开发** | 10013 | `VITE_PORT` | `electron/renderer/.env` | ⭐⭐⭐ |

**说明**: 
- ✅ 后端服务统一使用9030端口
- ✅ 前端开发使用10013端口
- ✅ 避免Windows保留端口范围(8930-9029)

---

## 🎯 核心配置项 (遵循希克定律)

### 后端核心配置 (6项)

**必须配置** (影响启动):

```env
# 1. 服务端口
BACKEND_PORT=9030

# 2-6. 数据库配置
DB_TYPE=mysql
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_USER=timao
MYSQL_PASSWORD=Yw123456
MYSQL_DATABASE=timao
```

**可选配置** (稍后配置):

```env
# AI服务 (需要AI功能时配置)
GEMINI_API_KEY=

# 安全密钥 (生产环境必须改)
SECRET_KEY=timao-secret-key-change-in-production
ENCRYPTION_KEY=timao-encryption-key-32chars

# 其他配置 (有默认值)
LOG_LEVEL=INFO
CORS_ORIGINS=*
DEBUG=false
```

### 前端核心配置 (3项)

**必须配置**:

```env
# 1. 前端开发端口
VITE_PORT=10013

# 2. 开发主机
VITE_HOST=127.0.0.1

# 3. 后端服务地址
VITE_FASTAPI_URL=http://127.0.0.1:9030
```

**可选配置**:

```env
# 开发工具 (有默认值)
VITE_HMR=true
VITE_SOURCEMAP=true
```

---

## ✅ 完整配置示例

### 后端 (`server/.env`)

```env
# ============================================
# 提猫直播助手 - 后端服务环境变量
# ============================================

# 🚀 服务端口 (必需)
BACKEND_PORT=9030

# 🗄️ 数据库配置 (必需)
DB_TYPE=mysql
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=Yw123456
MYSQL_DATABASE=timao

# 🔐 安全配置 (生产环境改)
SECRET_KEY=timao-secret-key-change-in-production-must-be-64-chars-minimum
ENCRYPTION_KEY=timao-encryption-key-32chars

# 🤖 AI服务 (可选)
GEMINI_API_KEY=
DEFAULT_AI_PROVIDER=gemini

# 📝 应用配置
LOG_LEVEL=INFO
LOG_DIR=logs
CORS_ORIGINS=*
DEBUG=false
TIMEZONE=Asia/Shanghai
WEBSOCKET_ENABLED=true
```

### 前端 (`electron/renderer/.env`)

```env
# ============================================
# 提猫直播助手 - 前端开发环境变量
# ============================================

# 🌐 开发服务器 (必需)
VITE_PORT=10013
VITE_HOST=127.0.0.1

# 🔗 后端服务 (必需)
VITE_FASTAPI_URL=http://127.0.0.1:9030
VITE_STREAMCAP_URL=http://127.0.0.1:9030
VITE_DOUYIN_URL=http://127.0.0.1:9030

# 🛠️ 开发工具 (可选)
VITE_HMR=true
VITE_SOURCEMAP=true
```

---

## 🔧 配置验证

### 验证清单

```bash
# 1. 验证配置文件
python scripts/检查与校验/validate_port_config.py

# 2. 测试后端启动
cd server
python app/main.py
# 应该看到: ✅ 服务已启动 http://0.0.0.0:9030

# 3. 测试前端启动
cd electron/renderer
npm run dev
# 应该看到: ✅ 开发服务器已启动 http://127.0.0.1:10013
```

### 常见问题检查

| 问题 | 检查项 | 解决方法 |
|------|--------|---------|
| ❌ 配置文件不存在 | `.env` 文件是否创建 | 运行 `python scripts/初始化与迁移/setup_env.py` |
| ❌ 端口被占用 | 端口是否冲突 | 修改 `BACKEND_PORT` 或 `VITE_PORT` |
| ❌ 数据库连接失败 | 数据库配置是否正确 | 检查 `MYSQL_*` 配置 |
| ❌ 前端无法连接后端 | 后端是否启动 | 先启动后端，再启动前端 |

---

## 📝 配置优先级 (遵循帕累托原则)

### 80/20 法则: 最重要的配置

**后端 Top 6** (80%功能需要):
1. ✅ `BACKEND_PORT`
2. ✅ `DB_TYPE`
3. ✅ `MYSQL_HOST`
4. ✅ `MYSQL_USER`
5. ✅ `MYSQL_PASSWORD`
6. ✅ `MYSQL_DATABASE`

**前端 Top 3** (80%功能需要):
1. ✅ `VITE_PORT`
2. ✅ `VITE_HOST`
3. ✅ `VITE_FASTAPI_URL`

**其他配置** (20%高级功能需要):
- AI服务配置
- 安全密钥
- 日志配置

---

## 🎓 设计原则说明

### 1. KISS原则 (Keep It Simple, Stupid)

- ✅ 配置文件结构简单
- ✅ 只包含必需项
- ✅ 有清晰的注释

### 2. 单一职责原则

- ✅ 后端配置只在 `server/.env`
- ✅ 前端配置只在 `electron/renderer/.env`
- ✅ 各自管理各自的配置

### 3. 希克定律 (减少选择)

- ✅ 后端只关注6个核心配置
- ✅ 前端只关注3个核心配置
- ✅ 其他配置有合理默认值

### 4. 帕累托原则 (80/20法则)

- ✅ 20%的配置支撑80%的功能
- ✅ 优先配置最重要的选项
- ✅ 其他配置按需配置

---

## 📚 相关文档

- 📖 [完整端口配置文档](PORT_CONFIGURATION.md)
- 📝 [快速参考指南](PORT_CONFIG_QUICKSTART.md)
- 🔧 [配置验证工具](../scripts/检查与校验/validate_port_config.py)
- ⚙️ [一键配置脚本](../scripts/初始化与迁移/setup_env.py)

---

## ✅ 配置成功标志

配置成功后,应该看到:

### 后端启动成功

```
2025-11-07 23:49:12 - INFO - ✅ 路由已加载: 直播音频转写
2025-11-07 23:49:12 - INFO - ✅ 路由已加载: 直播复盘
...
INFO:     Uvicorn running on http://0.0.0.0:9030 (Press CTRL+C to quit)
```

### 前端启动成功

```
VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://127.0.0.1:10013/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### 验证脚本成功

```
✅ 后端服务配置验证通过
✅ 前端配置验证通过
✅ 端口可用性检查通过
✅ 所有验证通过!
```

---

**配置完成后即可正常使用应用!** 🎉

