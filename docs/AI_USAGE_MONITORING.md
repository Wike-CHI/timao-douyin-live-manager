# AI 使用监控系统 - 完整指南

## 📊 功能概述

AI 使用监控系统自动追踪所有 AI 模型调用，提供：

- ✅ **Token 统计** - 精确记录输入/输出 token 数量
- ✅ **费用计算** - 自动计算每次调用的成本
- ✅ **模型分析** - 按模型统计使用情况
- ✅ **功能分析** - 按功能模块统计
- ✅ **趋势分析** - 成本和使用量趋势
- ✅ **报告导出** - 生成使用报告

---

## 🎯 工作原理

### 1. 自动记录

所有通过 AI 网关的调用都会自动记录：

```
AI 调用 → AI 网关 → 执行调用 → 记录使用情况
                                  ↓
                           AI 使用监控系统
                                  ↓
                        ┌─────────┴─────────┐
                        │                   │
                   内存缓存            持久化存储
                  (最近1000条)        (按日期文件)
```

### 2. 数据记录

每次 AI 调用记录包含：

```json
{
  "timestamp": 1698765432.123,
  "user_id": "user_123",
  "session_id": "session_abc",
  "model": "qwen-plus",
  "function": "live_analysis",
  "input_tokens": 1500,
  "output_tokens": 800,
  "total_tokens": 2300,
  "cost": 0.0156,
  "duration_ms": 1245.6,
  "success": true
}
```

### 3. Token 计算

系统自动计算 token 数量：

- **输入 Token**：发送给 AI 的内容（提示词 + 上下文）
- **输出 Token**：AI 生成的内容
- **总 Token**：输入 + 输出

### 4. 费用计算

基于实际 token 数量和模型定价自动计算：

```python
# 以 qwen-plus 为例
input_cost = (input_tokens / 1000) * 0.004   # ¥0.004/1K tokens
output_cost = (output_tokens / 1000) * 0.012  # ¥0.012/1K tokens
total_cost = input_cost + output_cost
```

---

## 💰 支持的模型定价

### 通义千问系列

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|---------|
| qwen-max | ¥0.02/1K | ¥0.06/1K | 高质量任务 |
| qwen-plus | ¥0.004/1K | ¥0.012/1K | 日常使用 ⭐ |
| qwen-turbo | ¥0.002/1K | ¥0.006/1K | 快速响应 |

### OpenAI 系列

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|---------|
| gpt-4 | ¥0.21/1K | ¥0.42/1K | 复杂推理 |
| gpt-4-turbo | ¥0.07/1K | ¥0.21/1K | 平衡性能 |
| gpt-4o | ¥0.035/1K | ¥0.105/1K | 多模态 |
| gpt-4o-mini | ¥0.001/1K | ¥0.004/1K | 简单任务 |
| gpt-3.5-turbo | ¥0.0035/1K | ¥0.007/1K | 经济实惠 |

### DeepSeek 系列

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|---------|
| deepseek-chat | ¥0.001/1K | ¥0.002/1K | 极致省钱 ⭐ |
| deepseek-coder | ¥0.001/1K | ¥0.002/1K | 代码生成 |

### 字节豆包系列

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|---------|
| doubao-pro-32k | ¥0.008/1K | ¥0.008/1K | 长文本 |
| doubao-lite-32k | ¥0.003/1K | ¥0.003/1K | 经济型 |

### ChatGLM 系列

| 模型 | 输入价格 | 输出价格 | 推荐场景 |
|------|---------|---------|---------|
| glm-4 | ¥0.10/1K | ¥0.10/1K | 高质量 |
| glm-4-flash | ¥0.0/1K | ¥0.0/1K | 免费试用 ⭐ |
| glm-3-turbo | ¥0.005/1K | ¥0.005/1K | 快速响应 |

---

## 📱 使用方式

### 1. Web 监控面板

访问：http://localhost:10090/static/ai_usage_monitor.html

**功能**：
- 📊 实时仪表盘
- 📈 成本趋势图
- 🔝 Top 用户统计
- 📋 模型分布
- 📂 功能分布
- 📤 导出报告

### 2. API 接口

#### 获取今日统计

```bash
curl http://localhost:10090/api/ai_usage/stats/daily?days_ago=0
```

**响应**：
```json
{
  "period": "daily",
  "date": "2025-10-26",
  "total_calls": 145,
  "total_tokens": 98750,
  "total_cost": 0.42,
  "by_model": {
    "qwen-plus": {
      "calls": 120,
      "input_tokens": 72000,
      "output_tokens": 24000,
      "cost": 0.36
    }
  }
}
```

#### 获取成本趋势

```bash
curl http://localhost:10090/api/ai_usage/cost_trend?days=7
```

#### 获取 Top 用户

```bash
curl http://localhost:10090/api/ai_usage/top_users?limit=10&days=7
```

#### 获取模型定价

```bash
curl http://localhost:10090/api/ai_usage/models/pricing
```

#### 导出报告

```bash
curl -X POST http://localhost:10090/api/ai_usage/export_report?days=7
```

### 3. Python 代码

```python
from server.utils.ai_usage_monitor import get_usage_monitor

# 获取监控实例
monitor = get_usage_monitor()

# 手动记录（通常由 AI 网关自动调用）
monitor.record_usage(
    model="qwen-plus",
    function="live_analysis",
    input_tokens=1000,
    output_tokens=500,
    duration_ms=1234.5,
    success=True,
    user_id="user_123",
    session_id="session_abc"
)

# 获取今日统计
today = monitor.get_daily_summary(days_ago=0)
print(f"今日调用: {today.total_calls}")
print(f"今日费用: ¥{today.total_cost:.2f}")

# 获取本月统计
month = monitor.get_monthly_summary()
print(f"本月费用: ¥{month.total_cost:.2f}")

# 获取 Top 用户
top_users = monitor.get_top_users(limit=5, days=7)
for user in top_users:
    print(f"{user['user_id']}: {user['tokens']} tokens, ¥{user['cost']:.4f}")
```

---

## 📈 数据分析示例

### 成本优化分析

```python
# 比较不同模型的成本
monitor = get_usage_monitor()
summary = monitor.get_daily_summary()

for model, stats in summary.by_model.items():
    avg_cost_per_call = stats['cost'] / stats['calls']
    print(f"{model}: 平均每次调用 ¥{avg_cost_per_call:.4f}")
```

**输出示例**：
```
qwen-plus: 平均每次调用 ¥0.0035
qwen-max: 平均每次调用 ¥0.0124
deepseek-chat: 平均每次调用 ¥0.0008
```

### 功能模块分析

```python
# 分析各功能模块的使用情况
for function, stats in summary.by_function.items():
    print(f"{function}:")
    print(f"  调用次数: {stats['calls']}")
    print(f"  总费用: ¥{stats['cost']:.4f}")
    print(f"  总 Token: {stats['total_tokens']}")
```

**输出示例**：
```
live_analysis:
  调用次数: 45
  总费用: ¥0.1234
  总 Token: 23450

live_question:
  调用次数: 30
  总费用: ¥0.0856
  总 Token: 15600
```

---

## 🔍 监控数据存储

### 存储位置

```
records/ai_usage/
├── 2025-10-26.jsonl    # 2025年10月26日的记录
├── 2025-10-25.jsonl    # 2025年10月25日的记录
└── usage_report_20251026_143022.json  # 导出的报告
```

### 数据格式

每行一条 JSON 记录：

```jsonl
{"timestamp": 1698765432.123, "model": "qwen-plus", "input_tokens": 1000, ...}
{"timestamp": 1698765555.456, "model": "qwen-max", "input_tokens": 1500, ...}
```

### 数据保留

- 内存缓存：最近 1000 条记录
- 文件存储：永久保留（可手动清理）

---

## 💡 最佳实践

### 1. 成本控制

**设置预算警报**：

```python
# 检查今日费用
today = monitor.get_daily_summary()
if today.total_cost > 10.0:  # 超过 ¥10
    print("⚠️ 今日费用超标！")
    # 发送通知或切换到更便宜的模型
```

**自动切换模型**：

```python
from server.ai.ai_gateway import get_gateway

gateway = get_gateway()
today = monitor.get_daily_summary()

if today.total_cost > 5.0:
    # 成本高时切换到便宜模型
    gateway.switch_provider("deepseek", "deepseek-chat")
else:
    # 成本可控时使用质量模型
    gateway.switch_provider("qwen", "qwen-plus")
```

### 2. 性能优化

**分析慢调用**：

```python
# 找出耗时最长的调用
records = monitor._records
slow_calls = [r for r in records if r.duration_ms > 5000]  # 超过5秒
print(f"慢调用数量: {len(slow_calls)}")
```

### 3. 定期报告

**每日成本报告**：

```bash
# 每天导出一次报告
curl -X POST http://localhost:10090/api/ai_usage/export_report?days=1
```

**每周趋势分析**：

```python
# 生成每周报告
trend = monitor.get_cost_trend(days=7)
total_week = sum(day['cost'] for day in trend)
avg_daily = total_week / 7

print(f"本周总费用: ¥{total_week:.2f}")
print(f"日均费用: ¥{avg_daily:.2f}")
```

---

## 🛠️ 高级用法

### 自定义统计维度

```python
# 按时段统计
from datetime import datetime

monitor = get_usage_monitor()
records = monitor._get_recent_records(days=1)

# 按小时分组
hourly_stats = {}
for record in records:
    hour = datetime.fromtimestamp(record.timestamp).hour
    if hour not in hourly_stats:
        hourly_stats[hour] = {'calls': 0, 'cost': 0.0}
    hourly_stats[hour]['calls'] += 1
    hourly_stats[hour]['cost'] += record.cost

# 找出高峰时段
peak_hour = max(hourly_stats.items(), key=lambda x: x[1]['calls'])
print(f"高峰时段: {peak_hour[0]}:00, 调用 {peak_hour[1]['calls']} 次")
```

### 异常检测

```python
# 检测异常高成本调用
records = monitor._get_recent_records(days=1)
costs = [r.cost for r in records]
avg_cost = sum(costs) / len(costs)
std_cost = (sum((c - avg_cost) ** 2 for c in costs) / len(costs)) ** 0.5

threshold = avg_cost + 2 * std_cost  # 2倍标准差
anomalies = [r for r in records if r.cost > threshold]

print(f"发现 {len(anomalies)} 个异常高成本调用")
for a in anomalies:
    print(f"  {a.function}({a.model}): ¥{a.cost:.4f}")
```

---

## 📊 仪表盘指标说明

### 今日统计

- **调用次数**：今天的 AI 调用总数
- **Token 总量**：输入 + 输出 token 总和
- **总费用**：今天的总成本
- **成功率**：成功调用 / 总调用

### 本月统计

- **月度调用**：本月累计调用次数
- **月度费用**：本月累计成本
- **日均费用**：月度费用 / 当前日期

### 成本趋势

- **7天趋势图**：最近7天的每日费用曲线
- **环比变化**：今天 vs 昨天的费用变化百分比

### Top 用户

- **Token 消耗排名**：按 token 使用量排序
- **费用排名**：按费用排序

---

## ❓ 常见问题

### Q1: 为什么统计数据不准确？

**A**: 检查以下几点：

1. AI 网关是否正确集成
2. 是否所有调用都通过网关
3. Token 计数是否从 API 响应中正确提取

### Q2: 如何重置统计数据？

**A**: 删除对应日期的文件：

```bash
# 删除特定日期
rm records/ai_usage/2025-10-26.jsonl

# 清空所有数据
rm records/ai_usage/*.jsonl
```

### Q3: 费用计算不准确？

**A**: 检查模型定价配置：

```python
from server.utils.ai_usage_monitor import ModelPricing

# 查看模型定价
pricing = ModelPricing.get_pricing("qwen-plus")
print(pricing)

# 手动计算
cost = ModelPricing.calculate_cost("qwen-plus", 1000, 500)
print(f"费用: ¥{cost:.4f}")
```

### Q4: 如何添加新模型的定价？

**A**: 编辑 `server/utils/ai_usage_monitor.py`：

```python
# 添加到对应的定价字典
QWEN_PRICING = {
    # ... 现有模型 ...
    "qwen-new-model": {
        "input": 0.005,
        "output": 0.015,
        "display_name": "新模型"
    }
}
```

### Q5: 监控数据会自动清理吗？

**A**: 不会。需要手动清理旧数据：

```bash
# 删除30天前的数据
find records/ai_usage/ -name "*.jsonl" -mtime +30 -delete
```

---

## 🎯 总结

AI 使用监控系统提供：

✅ **自动化** - 无需手动记录，所有调用自动追踪  
✅ **精确化** - Token 级别的精确计费  
✅ **可视化** - 直观的Web界面和图表  
✅ **可分析** - 多维度数据分析和趋势预测  
✅ **可导出** - 生成报告用于财务和分析  

通过监控系统，您可以：
- 📊 实时了解 AI 使用情况
- 💰 控制和优化成本
- 🔍 发现使用模式和优化机会
- 📈 预测未来支出

---

**文档版本**: v1.0.0  
**更新日期**: 2025-10-26  
**适用系统**: 提猫直播助手 v1.0+
