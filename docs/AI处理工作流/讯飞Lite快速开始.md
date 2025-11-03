# 科大讯飞 Lite 模型快速开始

## 5 分钟快速接入

### 1️⃣ 配置 API Key

在项目根目录的 `.env` 文件中添加：

```bash
XUNFEI_API_KEY=你的APPID:你的APISecret
XUNFEI_MODEL=lite
```

> 💡 从示例文件复制：`cp .env.xunfei.example .env`

### 2️⃣ 测试连接

运行测试脚本：

```bash
python test_xunfei_integration.py
```

### 3️⃣ 调用 API

```python
from server.ai.xunfei_lite_client import get_xunfei_client

# 初始化客户端
client = get_xunfei_client()

# 氛围分析
result = client.analyze_live_atmosphere(
    transcript="欢迎来到直播间...",
    comments=[{"user": "观众1", "content": "主播好！"}]
)

# 查看结果和 Token 消耗
print(f"氛围: {result['atmosphere']['level']}")
print(f"Token: {result['_usage']['total_tokens']}")
```

## 核心功能

### 🌡️ 氛围与情绪分析

评估直播间氛围（冷淡/一般/活跃/火爆）和观众情绪

```bash
POST /api/ai/xunfei/analyze/atmosphere
```

### 📢 话术生成

智能生成 6 种类型的直播话术

```bash
POST /api/ai/xunfei/generate/script
```

### 📊 实时分析

窗口级实时分析，输出亮点、风险、建议

```bash
POST /api/ai/xunfei/analyze/realtime
```

## Token 消耗监控

自动记录所有调用的 Token 消耗：

```bash
# 查看今日统计
curl http://localhost:9019/api/ai_usage/stats/current

# 查看讯飞模型统计
curl http://localhost:9019/api/ai/xunfei/usage/stats?days=7
```

## 成本说明

**Lite 模型（默认）：完全免费 🎉**

- 每次氛围分析：约 200-300 tokens（¥0.00）
- 每次话术生成：约 100-200 tokens（¥0.00）
- 每次实时分析：约 300-500 tokens（¥0.00）

日均 1000 次调用：**¥0.00**

## API 文档

启动服务后访问：http://localhost:9019/docs

查找 "**科大讯飞AI**" 标签，查看所有接口

## 获取 API Key

1. 访问 [讯飞开放平台](https://www.xfyun.cn/)
2. 注册并登录
3. 创建应用
4. 获取 APPID 和 APISecret
5. 格式：`APPID:APISecret`

## 下一步

- 📖 [完整文档](./讯飞星火Lite模型集成说明.md)
- 🔧 [集成到现有服务](#集成到现有服务)
- 💰 [Token 优化建议](#token-优化建议)

---

**有问题？** 查看[故障排查](./讯飞星火Lite模型集成说明.md#故障排查)

