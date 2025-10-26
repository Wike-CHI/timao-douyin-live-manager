# 🎯 AI 使用监控系统 - 使用文档

> 实时追踪 AI API 的 Token 消耗和费用，帮助优化成本

---

## 📚 功能概述

### 核心功能
1. **实时监控**：自动追踪每次 AI 调用的 Token 使用和费用
2. **统计分析**：按小时、天、月汇总使用数据
3. **成本计算**：自动计算不同模型的调用费用
4. **用户分析**：统计各用户的使用情况
5. **报告导出**：生成 JSON 格式的使用报告

### 支持的模型
- ✅ Qwen 系列（Qwen-Max, Qwen-Plus, Qwen-Turbo）
- ✅ OpenAI 系列（GPT-4, GPT-3.5-Turbo）
- ✅ 自动识别其他兼容模型

---

## 🚀 快速开始

### 1. 在代码中添加监控

#### 方法 A：使用装饰器（推荐）

```python
from server.utils.ai_tracking_decorator import track_ai_usage

@track_ai_usage("实时分析", "qwen-plus")
def generate_analysis(context):
    """生成直播分析"""
    response = ai_client.chat.completions.create(
        model="qwen-plus",
        messages=[...],
        temperature=0.3
    )
    return response
```

#### 方法 B：手动记录

```python
from server.utils.ai_usage_monitor import record_ai_usage
import time

start_time = time.time()
response = ai_client.chat.completions.create(...)
duration_ms = (time.time() - start_time) * 1000

record_ai_usage(
    model="qwen-plus",
    function="实时分析",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    duration_ms=duration_ms,
    success=True,
    anchor_id="anchor_123",
    session_id="session_456"
)
```

### 2. 访问监控页面

启动服务后，访问：

```
http://localhost:10090/static/ai_usage_monitor.html
```

或通过 API：

```
http://localhost:10090/api/ai_usage/dashboard
```

---

## 📊 API 接口说明

### 1. 获取实时统计

**GET** `/api/ai_usage/stats/current`

返回当前小时和今日的统计数据。

**响应示例**：
```json
{
  "current_hour": {
    "calls": 36,
    "tokens": 97200,
    "cost": 2.94,
    "success_rate": 100
  },
  "today": {
    "calls": 360,
    "tokens": 972000,
    "cost": 29.52,
    "by_model": {...},
    "by_function": {...}
  }
}
```

---

### 2. 获取每日统计

**GET** `/api/ai_usage/stats/daily?days_ago=0`

参数：
- `days_ago`: 天数偏移（0=今天，1=昨天）

**响应示例**：
```json
{
  "period": "daily",
  "date": "2025-10-26",
  "total_calls": 360,
  "total_tokens": 972000,
  "total_cost": 29.52,
  "by_model": {
    "qwen-plus": {
      "calls": 300,
      "total_tokens": 810000,
      "cost": 6.48
    }
  }
}
```

---

### 3. 获取 Top 用户

**GET** `/api/ai_usage/top_users?limit=10&days=7`

参数：
- `limit`: 返回数量（1-100）
- `days`: 统计天数（1-90）

**响应示例**：
```json
{
  "period_days": 7,
  "top_users": [
    {
      "user_id": "user_001",
      "calls": 120,
      "tokens": 324000,
      "cost": 9.72
    }
  ]
}
```

---

### 4. 获取成本趋势

**GET** `/api/ai_usage/cost_trend?days=30`

返回每日成本数据，用于绘制趋势图。

**响应示例**：
```json
{
  "period_days": 30,
  "data": [
    {"date": "2025-10-01", "cost": 25.50},
    {"date": "2025-10-02", "cost": 28.30}
  ]
}
```

---

### 5. 导出报告

**POST** `/api/ai_usage/export_report?days=7`

生成并导出 JSON 格式的使用报告。

**响应示例**：
```json
{
  "success": true,
  "report_path": "records/ai_usage/usage_report_20251026_143022.json",
  "download_url": "/api/ai_usage/download_report?path=usage_report_20251026_143022.json"
}
```

---

## 💰 费用计算

### 定价配置

系统内置了主流模型的定价（2025年10月标准）：

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| Qwen-Plus（推荐） | ¥0.0004/1K | ¥0.002/1K |
| Qwen-Turbo | ¥0.0003/1K | ¥0.0006/1K |
| Qwen-Max | ¥0.02/1K | ¥0.06/1K |
| GPT-4 | ¥0.21/1K | ¥0.42/1K |
| GPT-3.5-Turbo | ¥0.0035/1K | ¥0.007/1K |

### 费用公式

```python
费用 = (输入Token / 1000) × 输入价格 + (输出Token / 1000) × 输出价格
```

### 自定义定价

修改 `server/utils/ai_usage_monitor.py` 中的 `ModelPricing` 类：

```python
class ModelPricing:
    CUSTOM_PRICING = {
        "my-model": {
            "input": 0.01,
            "output": 0.03,
            "display_name": "我的自定义模型"
        }
    }
```

---

## 📂 数据存储

### 文件结构

```
records/ai_usage/
├── usage_2025-10-26.jsonl    # 每日记录（JSONL 格式）
├── usage_2025-10-27.jsonl
└── usage_report_*.json       # 导出的报告
```

### 记录格式

每条记录包含以下字段：

```json
{
  "timestamp": 1730001234.56,
  "user_id": "user_001",
  "anchor_id": "anchor_123",
  "session_id": "session_456",
  "model": "qwen-plus",
  "function": "实时分析",
  "input_tokens": 2000,
  "output_tokens": 700,
  "total_tokens": 2700,
  "cost": 0.0164,
  "duration_ms": 1234.5,
  "success": true,
  "error_msg": null
}
```

---

## 🔧 高级用法

### 1. 会话级统计

```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()
stats = monitor.get_session_stats("session_123")

print(f"会话调用次数: {stats['calls']}")
print(f"会话Token消耗: {stats['tokens']}")
print(f"会话总费用: ¥{stats['cost']:.4f}")
```

### 2. 自定义时间范围

```python
# 获取指定小时的统计
summary = monitor.get_hourly_summary(hours_ago=2)  # 2小时前

# 获取指定日期的统计
summary = monitor.get_daily_summary(days_ago=7)  # 7天前

# 获取指定月份的统计
summary = monitor.get_monthly_summary(year=2025, month=9)
```

### 3. 程序化报告

```python
from pathlib import Path

# 导出报告到指定路径
output_path = Path("reports") / "monthly_usage.json"
monitor.export_report(output_path=output_path, days=30)
```

---

## 📈 监控最佳实践

### 1. 成本控制

#### 设置预算告警

```python
# 每日费用超过 ¥50 时发送告警
daily_summary = monitor.get_daily_summary()
if daily_summary.total_cost > 50:
    send_alert(f"今日AI费用已超 ¥50: ¥{daily_summary.total_cost}")
```

#### 限制用户额度

```python
# 检查用户是否超出额度
user_stats = monitor.get_top_users(limit=100, days=30)
for user in user_stats:
    if user['cost'] > 100:  # 月费用超 ¥100
        notify_user(user['user_id'], "您的AI额度即将用尽")
```

### 2. 性能优化

#### 缓存结果

```python
# 对相似的分析请求使用缓存
cache_key = f"{anchor_id}_{hour_timestamp}"
if cache_key in analysis_cache:
    return analysis_cache[cache_key]
```

#### 批量处理

```python
# 合并多个小请求为一个大请求
# 减少调用次数，降低成本
```

### 3. 定期审计

```python
# 每周生成报告并审查
import schedule

def weekly_audit():
    report = monitor.export_report(days=7)
    send_email_to_admin(report)

schedule.every().monday.at("09:00").do(weekly_audit)
```

---

## 🎯 实际案例

### 案例 1：6 小时直播成本分析

```python
# 假设：每分钟分析 1 次 + 每小时 30 次话术生成
# 模型：Qwen-Max

daily_summary = monitor.get_daily_summary()
print(f"总调用: {daily_summary.total_calls}")
print(f"总Token: {daily_summary.total_tokens:,}")
print(f"总费用: ¥{daily_summary.total_cost:.2f}")

# 输出示例：
# 总调用: 540
# 总Token: 1,206,000
# 总费用: ¥36.60
```

### 案例 2：月度成本预测

```python
# 基于前 7 天数据预测本月费用
cost_trend = monitor.get_cost_trend(days=7)
avg_daily = sum(d['cost'] for d in cost_trend) / 7
predicted_monthly = avg_daily * 30

print(f"日均费用: ¥{avg_daily:.2f}")
print(f"预测月费: ¥{predicted_monthly:.2f}")
```

### 案例 3：模型选择建议

```python
# 对比不同模型的性价比
today = monitor.get_daily_summary()

for model, stats in today.by_model.items():
    avg_cost_per_call = stats['cost'] / stats['calls']
    print(f"{model}: 平均 ¥{avg_cost_per_call:.4f}/次")

# 输出示例：
# qwen-plus: 平均 ¥0.0082/次
# qwen-turbo: 平均 ¥0.0041/次  ← 更经济
```

---

## 🛠️ 故障排查

### 问题 1：监控页面无法访问

**检查清单**：
1. 确认后端服务已启动（端口 10090）
2. 检查防火墙设置
3. 查看浏览器控制台错误

### 问题 2：数据不准确

**可能原因**：
- 装饰器未正确应用
- Token 提取逻辑错误
- 模型名称不匹配

**解决方法**：
```python
# 启用详细日志
import logging
logging.getLogger('server.utils.ai_usage_monitor').setLevel(logging.DEBUG)
```

### 问题 3：文件权限错误

**解决方法**：
```bash
# 确保 records/ 目录有写入权限
mkdir -p records/ai_usage
chmod 755 records/ai_usage
```

---

## 📝 TODO

### 近期计划
- [ ] 添加实时告警功能（费用超限时推送）
- [ ] 支持 Prometheus 指标导出
- [ ] 增加更多可视化图表（饼图、柱状图）
- [ ] 支持按主播分组统计

### 长期计划
- [ ] 机器学习预测未来成本
- [ ] 自动化成本优化建议
- [ ] 集成多个 AI 服务商

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest server/tests/test_ai_usage_monitor.py
```

---

**文档更新时间**：2025-10-26  
**版本**：v1.0.0  
**维护者**：提猫科技团队
