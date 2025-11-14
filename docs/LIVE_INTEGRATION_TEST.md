# 直播间完整功能和性能测试指南

**审查人**: 叶维哲

## 📋 测试目标

完整验证抖音直播间的功能和性能，包括：

1. **功能完整性** - 验证所有核心功能正常工作
2. **MySQL性能** - 监控数据库查询性能
3. **Redis性能** - 监控缓存操作性能
4. **SenseVoice + VAD** - 监控语音转写性能
5. **AI分析性能** - 监控AI分析响应时间
6. **实时弹幕性能** - 监控弹幕处理性能

## 🚀 快速开始

### 方法1：使用运行脚本（推荐）

```bash
# 使用默认配置（10分钟测试）
./run_live_test.sh

# 自定义测试时长（单位：分钟）
./run_live_test.sh "https://live.douyin.com/932546434419?room_id=7572532254115826451" 15
```

### 方法2：直接运行Python脚本

```bash
# 激活虚拟环境
source .venv/bin/activate

# 设置Python路径
export PYTHONPATH=$PWD:$PYTHONPATH

# 运行测试
python tests/test_live_integration.py
```

## 📝 测试配置

### 测试参数

在 `tests/test_live_integration.py` 中修改配置：

```python
# 主函数中的配置
async def main():
    # 直播间URL
    room_url = "https://live.douyin.com/932546434419?room_id=7572532254115826451"
    
    # 测试时长（分钟）
    test_duration_minutes = 10
    
    # 创建测试实例
    test = LiveIntegrationTest(room_url, test_duration_minutes)
    
    # 运行测试
    await test.run()
```

### 环境变量

确保 `.env` 文件中配置正确：

```bash
# Redis配置
REDIS_ENABLED=True
REDIS_HOST=localhost
REDIS_PORT=6379

# MySQL配置
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=timao20251102Xjys
MYSQL_DATABASE=timao

# Redis批量写入配置
REDIS_BATCH_ENABLED=1
REDIS_BATCH_SIZE=100
REDIS_BATCH_INTERVAL=10.0

# 弹幕批量配置
DANMU_BATCH_SIZE=500
DANMU_BATCH_INTERVAL=5.0

# AI缓存配置
AI_CACHE_ENABLED=1
AI_CACHE_TTL=3600

# 性能监控配置
MONITOR_ENABLED=1
MONITOR_INTERVAL=30.0
```

## 📊 测试指标

### MySQL性能指标

- **查询次数** - 总查询数量
- **平均查询时间** - 平均每次查询耗时
- **慢查询数** - 超过100ms的查询数
- **错误数** - 查询失败次数

### Redis性能指标

- **操作次数** - 总操作数量（set/get/delete等）
- **平均操作时间** - 平均每次操作耗时
- **缓存命中率** - 命中次数 / 总请求次数
- **错误数** - 操作失败次数

### 语音转写指标

- **处理片段数** - 已处理的音频片段数
- **平均处理时间** - 平均每个片段处理耗时
- **VAD检测数** - 语音活动检测次数
- **错误数** - 转写失败次数

### AI分析指标

- **分析次数** - AI分析调用次数
- **平均分析时间** - 平均每次分析耗时
- **缓存命中率** - 缓存命中次数 / 总请求次数
- **错误数** - 分析失败次数

### 弹幕性能指标

- **接收消息数** - 从直播间接收的消息总数
- **处理消息数** - 成功处理的消息数
- **平均处理时间** - 平均每条消息处理耗时
- **错误数** - 处理失败次数

### 系统资源指标

- **平均内存使用** - 测试期间平均内存占用
- **峰值内存使用** - 测试期间最大内存占用
- **平均CPU使用** - 测试期间平均CPU占用
- **峰值CPU使用** - 测试期间最大CPU占用

## 📈 测试报告

### 报告位置

测试完成后，报告保存在：

```
test_reports/live_integration_test_YYYYMMDD_HHMMSS.json
```

### 报告格式

```json
{
  "start_time": "2024-01-15T10:00:00",
  "end_time": "2024-01-15T10:10:00",
  "duration_seconds": 600,
  "test_passed": true,
  "errors": [],
  "metrics": {
    "mysql": {
      "queries": 150,
      "avg_query_time": 25.5,
      "slow_queries": 2,
      "errors": 0
    },
    "redis": {
      "operations": 500,
      "avg_operation_time": 1.2,
      "cache_hits": 120,
      "cache_misses": 30,
      "errors": 0
    },
    "transcription": {
      "segments_processed": 45,
      "avg_processing_time": 150.3,
      "vad_detections": 42,
      "errors": 0
    },
    "ai_analysis": {
      "analyses_performed": 20,
      "avg_analysis_time": 800.5,
      "cache_hits": 5,
      "errors": 0
    },
    "danmu": {
      "messages_received": 350,
      "messages_processed": 348,
      "avg_processing_time": 5.2,
      "errors": 2
    },
    "system": {
      "memory_usage_mb": [450.2, 465.8, 472.1],
      "cpu_usage_percent": [15.2, 18.5, 22.1],
      "active_connections": [12, 14, 13]
    }
  }
}
```

## 🔍 性能基准

### 正常性能基准

- **MySQL平均查询时间**: < 50ms
- **Redis平均操作时间**: < 5ms
- **语音转写平均时间**: < 200ms/片段
- **AI分析平均时间**: < 1000ms/次
- **弹幕平均处理时间**: < 10ms/条
- **平均内存使用**: < 1GB
- **平均CPU使用**: < 30%

### 慢查询告警阈值

- **MySQL慢查询**: > 100ms
- **Redis慢操作**: > 10ms
- **语音转写超时**: > 500ms
- **AI分析超时**: > 2000ms
- **弹幕处理超时**: > 50ms

## 🐛 故障排查

### Redis连接失败

```bash
# 检查Redis状态
redis-cli ping

# 启动Redis
sudo systemctl start redis

# 查看Redis日志
sudo tail -f /var/log/redis/redis-server.log
```

### MySQL连接失败

```bash
# 测试MySQL连接
mysql -h rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com \
      -P 3306 \
      -u timao \
      -p timao20251102Xjys \
      -e "SELECT 1"
```

### SenseVoice模型缺失

```bash
# 检查模型文件
ls -la models/SenseVoiceSmall/

# 如果缺失，需要下载模型
# 参考项目文档下载SenseVoice模型
```

### 内存不足

```bash
# 检查可用内存
free -h

# 检查进程内存使用
ps aux | grep python | grep live

# 如果内存不足，可以：
# 1. 减少测试时长
# 2. 减少批量处理大小
# 3. 增加服务器内存
```

## 📚 相关文档

- [Redis配置指南](REDIS_CONFIG.md)
- [压力测试指南](STRESS_TEST.md)
- [实施总结](IMPLEMENTATION_SUMMARY.md)
- [部署检查清单](../DEPLOYMENT_CHECKLIST.md)

## ⚠️ 注意事项

1. **测试时长** - 首次测试建议从5分钟开始，验证功能正常后再增加时长
2. **资源监控** - 测试期间密切监控服务器资源使用情况
3. **错误处理** - 测试会捕获错误但不会中断，最后统一报告
4. **数据清理** - 测试完成后会自动清理会话数据
5. **网络稳定** - 确保网络连接稳定，避免直播间断连

## 🎯 测试目标值

测试通过标准：

- ✅ **功能完整性**: 所有核心服务正常启动
- ✅ **MySQL性能**: 平均查询时间 < 50ms
- ✅ **Redis性能**: 平均操作时间 < 5ms
- ✅ **转写性能**: 平均处理时间 < 200ms
- ✅ **AI性能**: 平均分析时间 < 1000ms
- ✅ **弹幕性能**: 平均处理时间 < 10ms
- ✅ **系统资源**: 内存使用 < 1GB，CPU使用 < 30%
- ✅ **错误率**: 各服务错误率 < 1%

---

**如有问题，请联系审查人：叶维哲**

