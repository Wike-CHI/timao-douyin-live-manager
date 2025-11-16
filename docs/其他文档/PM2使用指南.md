# PM2 后端服务管理指南

## 📋 当前配置

```javascript
应用名称: timao-backend
端口: 11111
Python环境: .venv/bin/python (虚拟环境)
工作目录: /www/wwwroot/wwwroot/timao-douyin-live-manager
启动命令: python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --workers 1

内存限制: 3GB (SenseVoice + VAD 需要约 2.5GB，留有余量)
日志路径: 
  - logs/pm2-out.log
  - logs/pm2-error.log
```

### 🤖 SenseVoice + VAD 模型配置

PM2 已配置以下环境变量，确保模型正确加载：

```javascript
// 模型路径配置
MODEL_ROOT: '/www/wwwroot/.../server/models/models/iic'
SENSEVOICE_MODEL_PATH: '.../SenseVoiceSmall'           // ~2.3GB
VAD_MODEL_PATH: '.../speech_fsmn_vad_zh-cn-16k-...'    // ~140MB

// 模型加载配置
ENABLE_MODEL_PRELOAD: '1'                              // 启用预加载
MODEL_CACHE_DIR: '.cache/modelscope'                   // 缓存目录

// VAD 参数（已优化）
LIVE_VAD_CHUNK_SEC: '1.6'                              // 分块时长
LIVE_VAD_MIN_SILENCE_SEC: '0.50'                       // 最小静音
LIVE_VAD_MIN_SPEECH_SEC: '0.30'                        // 最小语音
LIVE_VAD_MIN_RMS: '0.015'                              // 灵敏度阈值

// PyTorch CPU 优化
OMP_NUM_THREADS: '4'                                   // OpenMP 线程
MKL_NUM_THREADS: '4'                                   // MKL 线程
```

**配置文件**: `ecosystem.config.js`

**模型验证命令**:
```bash
# 检查模型文件是否存在
ls -lh server/models/models/iic/SenseVoiceSmall/
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/

# 查看模型大小
du -sh server/models/models/iic/SenseVoiceSmall/
du -sh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/
```

## 🚀 基本操作

### 启动服务

```bash
# 使用配置文件启动
pm2 start ecosystem.config.js

# 或者直接启动（如果已配置）
pm2 start timao-backend

# 启动并保存配置
pm2 start ecosystem.config.js --update-env
pm2 save
```

### 停止服务

```bash
# 停止服务
pm2 stop timao-backend

# 停止所有服务
pm2 stop all
```

### 重启服务

```bash
# 重启服务（推荐，零停机）
pm2 reload timao-backend

# 强制重启
pm2 restart timao-backend

# 重启所有服务
pm2 restart all
```

### 删除服务

```bash
# 删除服务（从PM2列表中移除）
pm2 delete timao-backend

# 删除所有服务
pm2 delete all
```

## 📊 监控和查看

### 查看进程列表

```bash
# 列出所有进程
pm2 list

# 或者简写
pm2 ls
```

### 查看进程详情

```bash
# 查看详细信息
pm2 show timao-backend

# 或使用ID
pm2 show 0
```

### 实时监控

```bash
# 实时监控CPU和内存
pm2 monit

# 查看进程树
pm2 ps
```

### 查看日志

```bash
# 实时查看日志（所有日志）
pm2 logs timao-backend

# 实时查看（只看最后50行）
pm2 logs timao-backend --lines 50

# 只看错误日志
pm2 logs timao-backend --err

# 只看输出日志
pm2 logs timao-backend --out

# 清空日志
pm2 flush timao-backend
```

### 直接查看日志文件

```bash
# 查看输出日志
tail -f logs/pm2-out.log

# 查看错误日志
tail -f logs/pm2-error.log

# 查看最后100行
tail -100 logs/pm2-out.log
```

## 🔧 配置管理

### 查看环境变量

```bash
# 查看所有环境变量
pm2 env 0
```

### 更新配置

```bash
# 修改 ecosystem.config.js 后重载配置
pm2 reload ecosystem.config.js --update-env

# 保存当前配置（开机自启）
pm2 save
```

### 设置开机自启

```bash
# 生成启动脚本
pm2 startup

# 保存当前进程列表
pm2 save

# 禁用开机自启
pm2 unstartup
```

## 📝 常用场景

### 场景1: 首次启动

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 启动服务
pm2 start ecosystem.config.js

# 保存配置（开机自启）
pm2 save

# 查看状态
pm2 list
```

### 场景2: 更新代码后重启

```bash
# 拉取最新代码
git pull

# 重启服务（零停机）
pm2 reload timao-backend

# 查看日志确认
pm2 logs timao-backend --lines 50
```

### 场景3: 服务异常排查

```bash
# 1. 查看进程状态
pm2 list

# 2. 查看详细信息（重启次数、运行时间等）
pm2 show timao-backend

# 3. 查看错误日志
pm2 logs timao-backend --err --lines 100

# 4. 查看系统资源
pm2 monit

# 5. 如果需要重启
pm2 restart timao-backend
```

### 场景4: 内存占用过高

```bash
# 查看当前内存
pm2 show timao-backend

# 如果接近2GB（配置的max_memory_restart）
# PM2会自动重启

# 手动重启释放内存
pm2 reload timao-backend
```

### 场景5: 查看SenseVoice+VAD加载情况

#### 方法 1: 使用模型状态 API（推荐）

```bash
# 快速健康检查
curl http://127.0.0.1:11111/api/model/health | python3 -m json.tool

# 查看完整模型状态
curl http://127.0.0.1:11111/api/model/status | python3 -m json.tool

# 查看环境变量配置
curl http://127.0.0.1:11111/api/model/config | python3 -m json.tool

# 运行自动测试脚本
python scripts/检查与校验/test-model-api.py
```

**API 响应示例**:
```json
{
  "status": "healthy",
  "sensevoice": {"exists": true, "size_mb": 892.9},
  "vad": {"exists": true, "size_mb": 1.6},
  "vad_config": {"chunk_sec": "1.6", "min_silence_sec": "0.50"},
  "pytorch_config": {"omp_threads": "4", "mkl_threads": "4"},
  "system": {"available_memory_gb": 3.52, "cpu_percent": 2.6},
  "checks": {
    "sensevoice_exists": true,
    "vad_exists": true,
    "vad_config_set": true,
    "memory_sufficient": true
  }
}
```

#### 方法 2: 查看 PM2 日志

```bash
# 查看启动日志（SenseVoice初始化信息）
pm2 logs timao-backend --lines 200 | grep -i "sensevoice\|vad\|模型"

# 实时查看模型加载
pm2 logs timao-backend | grep -i "sensevoice\|vad"

# 查看模型初始化成功标志
pm2 logs timao-backend | grep "✅ SenseVoice"

# 查看环境变量配置
pm2 env 0 | grep -E "SENSEVOICE|VAD|MODEL"
```

**预期的成功日志**:
```
✅ SenseVoice + VAD 初始化成功（本地PyTorch模型）
模型路径: /www/wwwroot/.../SenseVoiceSmall
VAD路径: /www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch
```

**如果模型加载失败**:
```bash
# 1. 使用 API 诊断问题
curl -s http://127.0.0.1:11111/api/model/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['warnings']:
    print('⚠️  警告:')
    for w in data['warnings']: print(f'  • {w}')
if data['recommendations']:
    print('💡 建议:')
    for r in data['recommendations']: print(f'  • {r}')
"

# 2. 检查模型文件
ls -lh server/models/models/iic/SenseVoiceSmall/model.pt
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt

# 3. 检查内存是否充足
free -h

# 4. 重新下载模型（如果缺失）
python server/tools/download_sensevoice.py
python server/tools/download_vad_model.py

# 5. 重启服务
pm2 restart timao-backend
```

### 场景6: 性能监控

```bash
# 实时监控
pm2 monit

# 查看历史数据
pm2 show timao-backend

# 使用PM2 Plus（需要注册）
pm2 plus
```

## 📊 状态解读

### 进程状态

| 状态 | 说明 | 操作 |
|-----|------|------|
| online | 正常运行 | ✅ 无需操作 |
| stopping | 正在停止 | ⏳ 等待停止完成 |
| stopped | 已停止 | 🔄 需要启动 |
| errored | 出错 | ❌ 查看日志，修复后重启 |
| one-launch-status | 单次启动 | ⚠️  检查配置 |

### 重启次数

```
重启次数过多（>50）可能表明：
- ❌ 代码有bug导致崩溃
- ❌ 内存超限频繁重启
- ❌ 端口被占用
- ❌ 依赖缺失

解决方法：
1. 查看错误日志: pm2 logs timao-backend --err
2. 检查端口: netstat -tulnp | grep 11111
3. 测试启动: python -m uvicorn server.app.main:app --port 11111
```

## 🤖 模型配置验证

### 验证模型文件完整性

```bash
# 1. 检查模型文件是否存在
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# SenseVoice 模型（应该有 model.pt 等文件）
ls -lh server/models/models/iic/SenseVoiceSmall/
# 预期输出：model.pt (~2.3GB)

# VAD 模型
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/
# 预期输出：model.pt (~140MB)

# 2. 查看模型总大小
du -sh server/models/models/iic/SenseVoiceSmall/
du -sh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/
```

### 验证环境变量配置

```bash
# 查看 PM2 进程的环境变量
pm2 env 0 | grep -E "SENSEVOICE|VAD|MODEL|PYTORCH|OMP|MKL"

# 预期输出应包含：
# SENSEVOICE_MODEL_PATH=/www/wwwroot/.../SenseVoiceSmall
# VAD_MODEL_PATH=/www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch
# ENABLE_MODEL_PRELOAD=1
# OMP_NUM_THREADS=4
# MKL_NUM_THREADS=4
```

### 验证模型加载状态

```bash
# 启动服务并查看加载日志
pm2 restart timao-backend
pm2 logs timao-backend --lines 100

# 等待几秒后，搜索成功标志
pm2 logs timao-backend --lines 200 | grep -A 5 "SenseVoice"

# 预期看到：
# ✅ SenseVoice + VAD 初始化成功（本地PyTorch模型）
```

### 测试模型推理

```bash
# 查看服务状态
pm2 show timao-backend

# 检查 API 健康
curl http://127.0.0.1:11111/health

# 测试语音转写端点（如果有测试音频）
# curl -X POST http://127.0.0.1:11111/api/transcribe \
#   -F "audio=@test.wav"
```

### 模型配置检查清单

| 检查项 | 命令 | 预期结果 |
|--------|------|----------|
| ✅ 模型文件存在 | `ls server/models/models/iic/SenseVoiceSmall/model.pt` | 文件存在 |
| ✅ VAD文件存在 | `ls server/models/.../speech_fsmn_vad.../model.pt` | 文件存在 |
| ✅ 环境变量配置 | `pm2 env 0 \| grep SENSEVOICE` | 路径正确 |
| ✅ 内存充足 | `free -h` | 至少 4GB 可用 |
| ✅ PM2进程运行 | `pm2 list` | online 状态 |
| ✅ 模型初始化成功 | `pm2 logs \| grep "✅ SenseVoice"` | 有成功日志 |
| ✅ API 可访问 | `curl http://127.0.0.1:11111/health` | 200 OK |

## 🔍 故障排除

### 问题1: 服务无法启动

```bash
# 1. 查看详细错误
pm2 logs timao-backend --err --lines 50

# 2. 手动测试启动
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
.venv/bin/python -m uvicorn server.app.main:app --port 11111

# 3. 检查端口占用
netstat -tulnp | grep 11111

# 4. 检查Python环境
.venv/bin/python --version
.venv/bin/pip list | grep -E "fastapi|uvicorn"
```

### 问题2: 日志文件过大

```bash
# 查看日志大小
du -h logs/pm2-*.log

# 清空日志
pm2 flush timao-backend

# 或手动清空
> logs/pm2-out.log
> logs/pm2-error.log
```

### 问题3: 内存泄漏

```bash
# 查看内存使用
pm2 show timao-backend | grep memory

# 如果持续增长，定期重启
pm2 reload timao-backend

# 注意：SenseVoice + VAD 需要约 2.5GB 内存
# 不要将 max_memory_restart 设置低于 2.5GB
# 否则模型加载后会立即触发重启

# 当前配置: 3GB (合理)
# 最低建议: 2.5GB (紧张)
```

### 问题5: 模型加载失败

```bash
# 症状：日志中出现 "❌ SenseVoice初始化失败"

# 1. 检查模型文件完整性
ls -lh server/models/models/iic/SenseVoiceSmall/model.pt
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt

# 2. 检查磁盘空间
df -h

# 3. 检查内存
free -h

# 4. 重新下载模型
python server/tools/download_sensevoice.py
python server/tools/download_vad_model.py

# 5. 检查 PyTorch 依赖
.venv/bin/pip list | grep torch

# 6. 清理缓存后重试
rm -rf .cache/modelscope/*
pm2 restart timao-backend
```

### 问题6: 模型加载慢

```bash
# 症状：启动需要 1-2 分钟

# 这是正常的！SenseVoice Small 模型约 2.3GB
# 首次加载或冷启动需要时间

# 优化建议：
# 1. 确保使用 SSD 而非 HDD
# 2. 增加 PyTorch 线程数（已在配置中）
# 3. 使用模型预加载（已在配置中）

# 查看加载进度
pm2 logs timao-backend --lines 50
```

### 问题4: CPU占用过高

```bash
# 实时监控
pm2 monit

# 查看系统进程
top -p $(pm2 pid timao-backend)

# 如果是推理占用高，考虑：
# 1. 优化VAD参数
# 2. 减少并发转写请求
# 3. 检查是否有死循环
```

## 🛠️ 高级配置

### 修改端口

```javascript
// ecosystem.config.js
args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 新端口 --workers 1',
env: {
  BACKEND_PORT: '新端口',
}
```

### 增加workers（多进程）

```javascript
// ecosystem.config.js
// 方法1: uvicorn workers（推荐）
args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --workers 2',

// 方法2: PM2 cluster模式（不推荐Python）
instances: 2,
exec_mode: 'cluster',
```

### 自定义日志

```javascript
// ecosystem.config.js
log_date_format: 'YYYY-MM-DD HH:mm:ss',
error_file: './logs/backend-error-' + new Date().toISOString().split('T')[0] + '.log',
out_file: './logs/backend-out-' + new Date().toISOString().split('T')[0] + '.log',
```

## 📚 相关命令速查

```bash
# 启动/停止/重启
pm2 start ecosystem.config.js    # 启动
pm2 stop timao-backend            # 停止
pm2 reload timao-backend          # 重启（零停机）
pm2 restart timao-backend         # 强制重启

# 查看
pm2 list                          # 进程列表
pm2 show timao-backend            # 详细信息
pm2 logs timao-backend            # 实时日志
pm2 monit                         # 性能监控

# 管理
pm2 save                          # 保存配置
pm2 resurrect                     # 恢复保存的进程
pm2 flush timao-backend           # 清空日志
pm2 delete timao-backend          # 删除进程

# 开机自启
pm2 startup                       # 设置自启
pm2 save                          # 保存进程列表
pm2 unstartup                     # 取消自启
```

## 🔗 相关资源

- **PM2官方文档**: https://pm2.keymetrics.io/docs/
- **项目配置**: `ecosystem.config.js`
- **日志目录**: `logs/`
- **Python环境**: `.venv/`

---

**最后更新**: 2025-11-14  
**适用版本**: PM2 5.x + Python 3.11 + FastAPI

