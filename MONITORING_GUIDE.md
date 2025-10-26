# 🔍 AI 使用监控程序 - 使用指南

> **快速开始**：3 分钟学会监控 AI 成本，节省 60% 费用！

---

## 📚 目录

1. [快速上手](#快速上手)
2. [在代码中添加监控](#在代码中添加监控)
3. [查看监控数据](#查看监控数据)
4. [导出和分析报告](#导出和分析报告)
5. [成本优化建议](#成本优化建议)
6. [常见问题](#常见问题)

---

## 🚀 快速上手

### 第一步：启动服务

```bash
# 进入项目目录
cd d:\gsxm\timao-douyin-live-manager

# 启动完整服务（包含监控）
npm run dev
```

**服务启动后，监控系统会自动运行** ✅

---

### 第二步：访问监控页面

打开浏览器，访问：

```
http://localhost:10090/static/ai_usage_monitor.html
```

你会看到一个漂亮的监控仪表盘，显示：
- ✅ 今日调用次数
- ✅ Token 消耗量
- ✅ 实时费用
- ✅ 成本趋势图

---

## 💻 在代码中添加监控

### 方法 1：使用装饰器（推荐）⭐

最简单的方式，只需要在函数上加一行装饰器：

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

**就这么简单！** 装饰器会自动：
- ✅ 记录 Token 使用量
- ✅ 计算费用
- ✅ 追踪调用耗时
- ✅ 统计成功率

---

### 方法 2：手动记录

如果需要更精细的控制：

```python
from server.utils.ai_usage_monitor import record_ai_usage
import time

# 记录开始时间
start_time = time.time()

# 调用 AI
response = ai_client.chat.completions.create(...)

# 计算耗时
duration_ms = (time.time() - start_time) * 1000

# 手动记录
record_ai_usage(
    model="qwen-plus",
    function="实时分析",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    duration_ms=duration_ms,
    success=True,
    anchor_id="anchor_123",  # 可选：主播 ID
    session_id="session_456"  # 可选：会话 ID
)
```

---

### 实际案例：修改现有代码

**修改前**（没有监控）：
```python
def generate_analysis(context):
    response = ai_client.chat.completions.create(...)
    return response
```

**修改后**（添加监控）：
```python
from server.utils.ai_tracking_decorator import track_ai_usage

@track_ai_usage("实时分析", "qwen-plus")
def generate_analysis(context):
    response = ai_client.chat.completions.create(...)
    return response
```

**就加一行！** 🎉

---

## 📊 查看监控数据

### 1. Web 界面（推荐）

访问：`http://localhost:10090/static/ai_usage_monitor.html`

**功能**：
- 📈 实时仪表盘
- 📉 成本趋势图（7天）
- 👥 Top 用户排行
- 🤖 模型使用分布
- ⚙️ 功能调用统计
- 🔄 自动刷新（30秒）

---

### 2. API 接口

#### 获取今日统计

```bash
curl http://localhost:10090/api/ai_usage/stats/current
```

**响应示例**：
```json
{
  "today": {
    "calls": 360,
    "tokens": 972000,
    "cost": 29.52,
    "success_rate": 100
  }
}
```

#### 获取仪表盘数据

```bash
curl http://localhost:10090/api/ai_usage/dashboard
```

#### 查看 Top 用户

```bash
curl "http://localhost:10090/api/ai_usage/top_users?limit=10&days=7"
```

---

### 3. Python 代码查询

```python
from server.utils.ai_usage_monitor import get_usage_monitor

# 获取监控器实例
monitor = get_usage_monitor()

# 获取今日统计
today = monitor.get_daily_summary(days_ago=0)
print(f"今日调用: {today.total_calls}")
print(f"今日费用: ¥{today.total_cost:.2f}")

# 获取会话统计
session_stats = monitor.get_session_stats("session_123")
print(f"会话费用: ¥{session_stats['cost']:.4f}")

# 获取 Top 用户
top_users = monitor.get_top_users(limit=5, days=7)
for user in top_users:
    print(f"{user['user_id']}: ¥{user['cost']:.2f}")
```

---

## 📄 导出和分析报告

### 方法 1：通过 Web 界面

1. 访问监控页面
2. 点击 **"📊 导出报告"** 按钮
3. 报告自动生成（JSON 格式）
4. 保存在 `records/ai_usage/` 目录

---

### 方法 2：通过 API

```bash
# 导出最近 7 天的报告
curl -X POST "http://localhost:10090/api/ai_usage/export_report?days=7"
```

**响应**：
```json
{
  "success": true,
  "report_path": "records/ai_usage/usage_report_20251026_143022.json",
  "download_url": "/api/ai_usage/download_report?path=usage_report_20251026_143022.json"
}
```

---

### 方法 3：通过 Python 代码

```python
from server.utils.ai_usage_monitor import get_usage_monitor
from pathlib import Path

monitor = get_usage_monitor()

# 导出最近 30 天的报告
output_path = Path("reports") / "monthly_usage.json"
monitor.export_report(output_path=output_path, days=30)

print(f"报告已导出到: {output_path}")
```

---

### 报告内容示例

```json
{
  "generated_at": "2025-10-26T14:30:22",
  "period_days": 7,
  "today_summary": {
    "total_calls": 540,
    "total_cost": 36.60,
    "by_model": {...},
    "by_function": {...}
  },
  "top_users": [...],
  "cost_trend": [...]
}
```

---

## 💡 成本优化建议

### 策略 1：切换到便宜的模型

**当前**：使用 Qwen-Max（¥0.02/1K 输入，¥0.06/1K 输出）  
**优化**：改用 Qwen-Plus（¥0.004/1K 输入，¥0.012/1K 输出）

**节省**：**80% 成本** 💰

```python
# 修改前
@track_ai_usage("实时分析", "qwen-max")

# 修改后
@track_ai_usage("实时分析", "qwen-plus")
```

---

### 策略 2：降低调用频率

**当前**：每 1 分钟分析 1 次  
**优化**：每 2 分钟分析 1 次

**节省**：**50% 成本**

```python
# 修改分析间隔
analysis_interval = 120  # 从 60 秒改为 120 秒
```

---

### 策略 3：智能触发

根据直播间活跃度动态调整：

- 冷场时：5 分钟分析 1 次
- 正常时：2 分钟分析 1 次  
- 活跃时：30 秒分析 1 次

**节省**：**30-50% 成本**

---

### 策略 4：混合模型

- **高频分析**：用 Qwen-Plus（便宜）
- **关键话术**：用 Qwen-Max（高质量）

**节省**：**60% 成本**

```python
# 实时分析用便宜的
@track_ai_usage("实时分析", "qwen-plus")
def generate_analysis(...):
    pass

# 话术生成用最好的
@track_ai_usage("话术生成", "qwen-max")
def generate_scripts(...):
    pass
```

---

## 📈 监控最佳实践

### 1. 设置成本告警

```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()
daily = monitor.get_daily_summary()

# 每日费用超过 ¥50 时告警
if daily.total_cost > 50:
    send_alert(f"⚠️ 今日AI费用已超 ¥50: ¥{daily.total_cost:.2f}")
```

---

### 2. 定期审查报告

```python
import schedule

def weekly_review():
    """每周一生成报告并发送"""
    monitor = get_usage_monitor()
    report = monitor.export_report(days=7)
    send_email_to_admin(report)

# 每周一早上 9 点执行
schedule.every().monday.at("09:00").do(weekly_review)
```

---

### 3. 追踪会话成本

```python
# 直播开始时
session_id = "live_20251026_123456"

# 使用装饰器时传入 session_id
@track_ai_usage("实时分析", "qwen-plus")
def analyze(context, session_id=None):
    # session_id 会自动记录
    pass

# 直播结束后查看成本
stats = monitor.get_session_stats(session_id)
print(f"本场直播AI成本: ¥{stats['cost']:.2f}")
```

---

## ❓ 常见问题

### Q1: 监控数据保存在哪里？

**A**: 保存在 `records/ai_usage/` 目录，按日期存储：

```
records/ai_usage/
├── usage_2025-10-26.jsonl    # 今日记录
├── usage_2025-10-25.jsonl    # 昨日记录
└── usage_report_*.json       # 导出的报告
```

---

### Q2: 如何删除历史数据？

**A**: 直接删除对应的 JSONL 文件即可：

```bash
# Windows
del records\ai_usage\usage_2025-10-01.jsonl

# 或删除整个目录重新开始
rmdir /s records\ai_usage
```

---

### Q3: 监控会影响性能吗？

**A**: 几乎没有影响（< 1ms）。监控是异步写入，不会阻塞主逻辑。

---

### Q4: 能否监控多个主播？

**A**: 可以！通过 `anchor_id` 区分：

```python
record_ai_usage(
    model="qwen-plus",
    function="实时分析",
    anchor_id="anchor_001",  # 主播 A
    ...
)

record_ai_usage(
    model="qwen-plus",
    function="实时分析",
    anchor_id="anchor_002",  # 主播 B
    ...
)
```

查询时按主播统计：

```python
daily = monitor.get_daily_summary()
for anchor_id, stats in daily.by_anchor.items():
    print(f"主播 {anchor_id}: ¥{stats['cost']:.2f}")
```

---

### Q5: 如何自定义模型定价？

**A**: 修改 `server/utils/ai_usage_monitor.py`：

```python
class ModelPricing:
    CUSTOM_PRICING = {
        "my-model": {
            "input": 0.01,   # 输入价格
            "output": 0.03,  # 输出价格
            "display_name": "我的模型"
        }
    }
    
    # 添加到总定价中
    ALL_PRICING = {**QWEN_PRICING, **OPENAI_PRICING, **CUSTOM_PRICING}
```

---

## 🎯 实战案例

### 案例 1：分析单个主播的成本

```python
from server.utils.ai_usage_monitor import get_usage_monitor

monitor = get_usage_monitor()

# 获取今日数据
daily = monitor.get_daily_summary()

# 查看某个主播的费用
anchor_stats = daily.by_anchor.get("anchor_123", {})
print(f"主播 123 今日费用: ¥{anchor_stats.get('cost', 0):.2f}")
print(f"调用次数: {anchor_stats.get('calls', 0)}")
```

---

### 案例 2：对比不同模型的成本

```python
daily = monitor.get_daily_summary()

for model, stats in daily.by_model.items():
    avg_cost = stats['cost'] / stats['calls'] if stats['calls'] > 0 else 0
    print(f"{model}:")
    print(f"  总调用: {stats['calls']}")
    print(f"  总费用: ¥{stats['cost']:.2f}")
    print(f"  平均每次: ¥{avg_cost:.4f}")
```

**输出示例**：
```
qwen-max:
  总调用: 360
  总费用: ¥29.52
  平均每次: ¥0.0820

qwen-plus:
  总调用: 180
  总费用: ¥1.46
  平均每次: ¥0.0081
```

**结论**：Qwen-Plus 便宜 10 倍！

---

### 案例 3：预测月度费用

```python
# 获取最近 7 天的成本趋势
trend = monitor.get_cost_trend(days=7)

# 计算日均费用
total_cost = sum(d['cost'] for d in trend)
avg_daily = total_cost / len(trend)

# 预测本月费用
import datetime
days_in_month = 30
predicted_monthly = avg_daily * days_in_month

print(f"最近 7 天日均: ¥{avg_daily:.2f}")
print(f"预测本月费用: ¥{predicted_monthly:.2f}")
```

---

## 📞 获取帮助

### 文档资源

- 📘 **详细文档**: [AI_USAGE_MONITOR_README.md](./AI_USAGE_MONITOR_README.md)
- 📗 **API 契约**: [API_CONTRACT.md](./API_CONTRACT.md)
- 📕 **成本分析**: [AI_COST_ANALYSIS.md](./AI_COST_ANALYSIS.md)

### 在线文档

访问 `http://localhost:10090/docs` 查看交互式 API 文档（Swagger UI）。

### 技术支持

- 📧 邮箱：support@talkingcat.ai
- 💬 微信：TalkingCat-Support

---

## ✅ 快速检查清单

使用监控前，确保：

- [x] 服务已启动（`npm run dev`）
- [x] 能访问监控页面（http://localhost:10090/static/ai_usage_monitor.html）
- [x] AI 函数已添加 `@track_ai_usage` 装饰器
- [x] 数据目录可写（`records/ai_usage/`）

---

**文档更新**: 2025-10-26  
**版本**: v1.0.0  
**维护**: 提猫科技团队
