# 直播数据实时更新 Bug 修复

## 🐛 问题描述

**现象**: 在录制直播时，前端显示的直播数据（新增关注、进场人数、最高在线、新增点赞）一直显示为 0，没有实时更新。

**根本原因**: 
- 后端 `LiveReportService.status()` 方法直接返回 `self._session`
- 而 `self._session.metrics` 只在调用 `stop()` 方法时才会从 `self._agg` 同步
- 导致前端每 2 秒轮询获取的 status 数据中，metrics 始终为初始值（全是 0）

## ✅ 修复方案

**修改文件**: `server/app/services/live_report_service.py`

**修改位置**: `status()` 方法（约第 433 行）

**修改内容**:
```python
# 修改前
def status(self) -> Optional[LiveReportStatus]:
    return self._session

# 修改后
def status(self) -> Optional[LiveReportStatus]:
    # 实时同步 metrics 到 session，确保前端能获取最新数据
    if self._session and hasattr(self, '_agg'):
        try:
            self._session.metrics = dict(self._agg)
        except Exception:
            pass
    return self._session
```

**工作原理**:
1. 后台的 `_consume_danmu()` 协程持续接收弹幕事件
2. 每个事件都会实时更新 `self._agg` 字典（关注、进场、点赞、礼物等）
3. 修改后的 `status()` 方法在每次被调用时，都会将最新的 `self._agg` 同步到 `self._session.metrics`
4. 前端每 2 秒轮询 `/api/report/live/status` 时，就能获取到最新的数据

## 🧪 测试步骤

### 1. 重启后端服务（必须！）

```powershell
# 停止现有服务 (Ctrl+C)
# 重新启动
npm run dev
```

### 2. 测试实时数据更新

```bash
# 操作步骤：
1. 打开前端页面，进入"整场复盘"
2. 输入一个正在直播的抖音直播地址
   例如：https://live.douyin.com/xxxxx
3. 点击"开始录制"
4. 等待 5-10 秒
5. 观察"直播数据"区域

# 预期结果：
✅ 新增关注、进场人数、最高在线、新增点赞 应该开始实时增长
✅ 数据每 2 秒刷新一次
✅ 如果直播间有礼物，礼物统计也会实时更新
```

### 3. 验证数据准确性

```bash
# 打开浏览器控制台 (F12)，查看 Network 标签

1. 找到 "/api/report/live/status" 请求
2. 查看响应内容：
   {
     "active": true,
     "status": {
       "session_id": "live_抖音_主播名_1762011511",
       "metrics": {
         "follows": 5,      // 应该是实时变化的数字
         "entries": 12,     // 应该是实时变化的数字
         "peak_viewers": 8, // 应该是实时变化的数字
         "like_total": 45,  // 应该是实时变化的数字
         "gifts": {
           "玫瑰花": 3,
           "棒棒糖": 5
         }
       },
       ...
     }
   }

# 如果 metrics 中的数字开始变化，说明修复成功！
```

### 4. 完整流程测试

```bash
# 完整的录制流程：
1. 开始录制 → 观察数据是否开始累积
2. 录制 2-3 分钟 → 数据持续增长
3. 停止录制 → 数据停止更新但保留最终值
4. 生成报告 → 报告中应包含累积的数据
5. 查看复盘 → 复盘页面应显示正确的数据指标
```

## 🔍 调试信息

### 检查后端日志

后端启动时应该能看到：
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
```

录制开始时：
```
[日志] 开始录制: live_抖音_主播名_1762011511
[日志] FFmpeg 进程已启动, PID: xxxxx
```

### 检查前端轮询

浏览器控制台应该每 2 秒看到一次请求：
```
GET http://127.0.0.1:9019/api/report/live/status
Status: 200 OK
```

### 常见问题排查

**Q1: 数据仍然显示为 0**
- 检查：后端服务是否重启了？
- 检查：直播间是否真的在直播？
- 检查：浏览器控制台是否有错误？
- 检查：Network 标签中 status 请求的响应是否包含 metrics？

**Q2: 数据更新很慢**
- 正常：前端每 2 秒轮询一次
- 正常：如果直播间人气低，数据增长会慢
- 建议：选择一个人气较高的直播间测试

**Q3: 只有部分数据更新**
- 可能原因：不同事件类型的触发频率不同
- 例如：关注事件相对较少，点赞事件很频繁
- 正常现象：这取决于直播间的实际互动情况

## 📊 数据来源说明

- **新增关注**: 弹幕事件类型 `follow`
- **进场人数**: 弹幕事件类型 `member` (action=enter)
- **最高在线**: 弹幕事件类型 `room_user_stats` (current/total_user)
- **新增点赞**: 弹幕事件类型 `like` (count)
- **礼物统计**: 弹幕事件类型 `gift` (gift_name + count)

这些数据都是从抖音 WebSocket 弹幕流实时解析得到的。

## ✅ 验证成功标准

1. ✅ 开始录制后，数据在 5-10 秒内开始变化
2. ✅ 数据持续累积，不会重置为 0
3. ✅ 停止录制后，数据保持最终值
4. ✅ 生成的报告中包含正确的累积数据
5. ✅ 复盘页面的"数据指标"标签显示正确

## 🚀 提交代码

如果测试通过，可以提交代码：

```bash
git add server/app/services/live_report_service.py
git commit -m "fix: 修复直播数据实时更新问题

- 在 status() 方法中实时同步 _agg 到 session.metrics
- 确保前端轮询时能获取最新的直播数据
- 修复新增关注、进场人数、最高在线、新增点赞一直显示为 0 的问题"
git push
```

---

**重要提醒**: 必须重启后端服务才能生效！Python 代码不会热重载。
