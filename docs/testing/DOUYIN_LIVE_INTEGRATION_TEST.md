# 抖音直播间集成测试指南

## 📋 概述

这是一个完整的抖音直播间集成测试脚本，用于测试直播监控、音频转写、AI分析和报告生成等核心功能。

**测试直播间**: [https://live.douyin.com/191495446158](https://live.douyin.com/191495446158)  
**房间ID**: 7569996511182932786  
**主播ID**: 58994334334  
**测试时长**: 5分钟（300秒）

---

## 🎯 测试目标

### 测试内容

1. ✅ **直播监控** - 启动抖音直播间监控
2. 🎤 **音频转写** - 实时音频转文字功能
3. 🤖 **AI分析** - AI实时分析直播内容
4. 📊 **数据收集** - 持续收集5分钟数据
5. 📝 **报告生成** - 生成直播复盘报告

### 验证指标

- 监控启动成功率
- 音频转写准确性
- AI分析响应时间
- 报告生成完整性
- 服务稳定性

---

## 🚀 快速开始

### 方法1: 使用快捷脚本（推荐）

```bash
# 1. 确保后端服务正在运行
cd d:\gsxm\timao-douyin-live-manager
python server/main.py

# 2. 在新终端运行测试
python scripts/test_douyin_live.py
```

### 方法2: 使用pytest

```bash
# 运行完整测试套件
pytest server/tests/integration/test_douyin_live_integration.py -v -s

# 只运行集成测试
pytest server/tests/integration/test_douyin_live_integration.py::test_douyin_live_integration -v -s
```

### 方法3: 直接运行测试文件

```bash
cd d:\gsxm\timao-douyin-live-manager
python server/tests/integration/test_douyin_live_integration.py
```

---

## ⚙️ 配置选项

### 自定义测试参数

```bash
# 指定不同的直播间
python scripts/test_douyin_live.py --url https://live.douyin.com/YOUR_ROOM_ID

# 修改测试时长（单位：秒）
python scripts/test_douyin_live.py --duration 600  # 10分钟

# 指定后端服务地址
python scripts/test_douyin_live.py --backend http://192.168.1.100:8000
```

### 修改代码配置

编辑 `server/tests/integration/test_douyin_live_integration.py`:

```python
# 修改这些常量
TEST_DURATION_SECONDS = 300  # 测试时长（秒）
BASE_URL = "http://localhost:8000"  # 后端地址
LIVE_ROOM_URL = "https://live.douyin.com/191495446158"  # 直播间URL
ROOM_ID = "7569996511182932786"  # 房间ID
```

---

## 📊 测试流程详解

### 阶段1: 启动监控（0-10秒）

```
[00:00] 启动抖音直播监控
  └─ POST /api/douyin/start
  └─ 验证监控状态
  └─ 等待连接稳定
```

### 阶段2: 启动音频转写（10-20秒）

```
[00:10] 启动音频转写
  └─ POST /api/live/audio/start
  └─ 配置语言: zh (中文)
  └─ 启用保存到数据库
  └─ 检查转写状态
```

### 阶段3: 启动AI分析（20-30秒）

```
[00:20] 启动AI实时分析
  └─ POST /api/ai/live/start
  └─ 分析间隔: 30秒
  └─ 启用情感分析
  └─ 启用主题识别
```

### 阶段4: 监控数据（30秒-5分钟）

```
[00:30 - 05:00] 持续监控
  └─ 每30秒检查服务状态
  └─ 记录监控指标:
      ├─ 抖音监控状态
      ├─ 音频片段数量
      └─ AI分析次数
```

### 阶段5: 生成报告并停止（5分钟后）

```
[05:00] 清理和报告
  ├─ 停止AI分析
  ├─ 停止音频转写
  ├─ 生成直播报告
  └─ 停止抖音监控
```

---

## 📈 预期结果

### 成功的测试输出

```
==============================================================
抖音直播间集成测试
==============================================================
测试直播间: https://live.douyin.com/191495446158
房间ID: 7569996511182932786
测试时长: 300秒 (5分钟)
开始时间: 2025-11-07 23:15:00

==============================================================
测试 1/5: 启动抖音直播监控
==============================================================
响应状态: 200
✅ 直播监控启动成功

==============================================================
测试 2/5: 启动音频转写
==============================================================
响应状态: 200
✅ 音频转写启动成功

==============================================================
测试 3/5: 启动AI实时分析
==============================================================
响应状态: 200
✅ AI分析启动成功

==============================================================
测试 4/5: 监控并收集数据
==============================================================
[进度 1/9] 已运行: 30秒, 剩余: 270秒
  📊 抖音监控: running
  🎤 音频转写: 运行中, 片段数: 15
  🤖 AI分析: 运行中, 分析次数: 1
...

==============================================================
测试 5/5: 生成报告并停止监控
==============================================================
  ✅ AI分析已停止
  ✅ 音频转写已停止
  📝 生成直播报告...
  ✅ 直播报告生成成功
  ✅ 直播监控已停止

==============================================================
测试总结
==============================================================

📊 测试结果: 5/5 通过

  ✅ 通过 - 监控启动
  ✅ 通过 - 音频转写
  ✅ 通过 - AI分析
  ✅ 通过 - 直播报告
  ✅ 通过 - 监控停止

⏱️  总测试时长: 305秒 (5分5秒)
==============================================================
```

---

## 🐛 故障排查

### 问题1: 无法连接后端服务

**错误**: `❌ 无法连接到后端服务: Connection refused`

**解决方案**:
```bash
# 1. 检查后端是否运行
# 在新终端运行:
python server/main.py

# 2. 检查端口是否正确
netstat -an | grep 8000

# 3. 检查防火墙设置
```

### 问题2: 监控启动失败

**错误**: `❌ 监控启动失败: invalid room_id`

**解决方案**:
```python
# 1. 检查直播间是否在线
# 访问: https://live.douyin.com/191495446158

# 2. 更新房间ID
# 从URL获取最新的room_id参数

# 3. 检查直播间权限
# 确保直播间不是私密直播
```

### 问题3: 音频转写失败

**错误**: `❌ HTTP错误: 409 - 转写服务已在运行`

**解决方案**:
```bash
# 停止现有转写服务
curl -X POST http://localhost:8000/api/live/audio/stop

# 或重启后端服务
```

### 问题4: AI分析异常

**错误**: `❌ AI分析异常: API key not configured`

**解决方案**:
```bash
# 1. 检查环境变量
echo $GEMINI_API_KEY

# 2. 配置AI服务
# 编辑 config.json 或 .env 文件

# 3. 重启后端服务
```

---

## 📝 测试报告

测试完成后，您可以在以下位置找到生成的报告:

```
server/records/
├── live_抖音_[主播名]_[时间戳]/
│   ├── report.html          # 📄 可视化报告
│   ├── review_data.json     # 📊 复盘数据
│   ├── audio_segments.json  # 🎤 音频片段
│   └── ai_analysis.json     # 🤖 AI分析结果
```

查看报告:
```bash
# 方法1: 通过API查看
curl http://localhost:8000/api/live/report/history

# 方法2: 直接打开HTML
# 找到最新的report.html文件并在浏览器中打开
```

---

## 🔧 高级用法

### 自定义测试场景

创建自己的测试脚本:

```python
from server.tests.integration.test_douyin_live_integration import DouyinLiveIntegrationTest

async def custom_test():
    async with DouyinLiveIntegrationTest() as test:
        # 自定义测试流程
        await test.test_1_start_douyin_monitoring()
        
        # 添加自定义检查
        await asyncio.sleep(60)  # 等待1分钟
        
        # 检查特定指标
        response = await test.client.get("/api/douyin/metrics")
        # ... 验证指标
        
        await test.test_5_generate_report_and_stop()
```

### 批量测试多个直播间

```python
# scripts/batch_test_live_rooms.py
import asyncio

ROOMS = [
    "https://live.douyin.com/191495446158",
    "https://live.douyin.com/ROOM_2",
    "https://live.douyin.com/ROOM_3",
]

async def test_all_rooms():
    for room_url in ROOMS:
        print(f"\n测试直播间: {room_url}")
        # 更新配置并运行测试
        # ...

asyncio.run(test_all_rooms())
```

---

## 📞 支持

如果遇到问题:

1. 查看日志: `server/logs/app.log`
2. 检查后端状态: `http://localhost:8000/api/health`
3. 查看测试输出中的错误信息
4. 参考故障排查章节

---

## 🎓 最佳实践

1. **测试前准备**
   - ✅ 确保后端服务正在运行
   - ✅ 检查直播间是否在线
   - ✅ 验证API密钥配置

2. **测试期间**
   - 📊 监控系统资源使用
   - 📝 记录异常日志
   - ⏱️ 注意响应时间

3. **测试后分析**
   - 📈 查看生成的报告
   - 🔍 分析音频转写准确率
   - 🤖 评估AI分析质量

---

**测试愉快！** 🎉

如有问题，请查看 [常见问题](../FAQ.md) 或联系技术支持。

