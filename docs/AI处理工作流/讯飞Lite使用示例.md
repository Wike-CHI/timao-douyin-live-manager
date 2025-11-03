# 科大讯飞 Lite 模型使用示例

## Python 代码示例

### 示例 1：基础连接测试

```python
from server.ai.xunfei_lite_client import get_xunfei_client

# 初始化客户端
client = get_xunfei_client()

# 测试连接
content, usage = client.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=50
)

print(f"响应: {content}")
print(f"Token消耗: 输入{usage.prompt_tokens} + 输出{usage.completion_tokens} = {usage.total_tokens}")
print(f"耗时: {usage.request_time_ms:.2f}ms")
```

### 示例 2：直播间氛围分析

```python
from server.ai.xunfei_lite_client import get_xunfei_client

client = get_xunfei_client()

# 准备数据
transcript = """
大家好！欢迎来到我的直播间！
今天给大家带来了超值优惠，这款产品性价比超高！
看到很多新朋友进来，欢迎大家！
有什么想了解的可以打在公屏上。
"""

comments = [
    {"user": "小明", "content": "主播好！"},
    {"user": "小红", "content": "这个多少钱？"},
    {"user": "小刚", "content": "666"},
    {"user": "小美", "content": "什么时候发货"},
    {"user": "小李", "content": "支持主播"}
]

# 执行分析
result = client.analyze_live_atmosphere(
    transcript=transcript,
    comments=comments,
    context={
        "duration_minutes": 30,
        "viewer_count": 150,
        "product": "数码产品"
    }
)

# 输出结果
print("=== 氛围分析结果 ===")
print(f"氛围等级: {result['atmosphere']['level']}")
print(f"氛围评分: {result['atmosphere']['score']}/100")
print(f"氛围描述: {result['atmosphere']['description']}")

print(f"\n主要情绪: {result['emotion']['primary']}")
print(f"情绪强度: {result['emotion']['intensity']}/100")

print(f"\n互动参与度: {result['engagement']['interaction_rate']}%")
print(f"正向反馈率: {result['engagement']['positive_rate']}%")

print(f"\n改善建议:")
for i, suggestion in enumerate(result['suggestions'], 1):
    print(f"{i}. {suggestion}")

# Token 消耗
usage = result['_usage']
print(f"\nToken消耗: {usage['total_tokens']} (输入{usage['prompt_tokens']} + 输出{usage['completion_tokens']})")
```

**预期输出：**
```
=== 氛围分析结果 ===
氛围等级: 活跃
氛围评分: 75/100
氛围描述: 直播间氛围良好，观众参与度较高

主要情绪: 兴奋
情绪强度: 70/100

互动参与度: 65%
正向反馈率: 80%

改善建议:
1. 及时回应观众关于价格和发货的问题
2. 保持当前的热情，继续引导互动
3. 可以设置一些互动环节，如抽奖或问答

Token消耗: 230 (输入150 + 输出80)
```

### 示例 3：智能话术生成

```python
from server.ai.xunfei_lite_client import get_xunfei_client

client = get_xunfei_client()

# 生成不同类型的话术
script_types = {
    "interaction": "互动引导",
    "engagement": "关注点赞召唤",
    "clarification": "澄清回应",
    "humor": "幽默活跃",
    "transition": "转场过渡",
    "call_to_action": "行动召唤"
}

context = {
    "current_topic": "新品发布",
    "atmosphere": "活跃",
    "viewer_count": 200,
    "recent_comments": ["价格多少", "什么时候发货", "有优惠吗"]
}

for script_type, type_name in script_types.items():
    result = client.generate_script(
        script_type=script_type,
        context=context
    )
    
    print(f"\n【{type_name}】")
    print(f"话术: {result['line']}")
    print(f"语气: {result['tone']}")
    print(f"标签: {', '.join(result.get('tags', []))}")
    print(f"Token: {result['_usage']['total_tokens']}")
```

**预期输出：**
```
【互动引导】
话术: 宝宝们有没有想了解的问题呀？打在公屏上让我看到！
语气: 热情
标签: 互动, 引导, 提问
Token: 120

【关注点赞召唤】
话术: 喜欢的宝宝点个关注加个小红心，不迷路哦！
语气: 亲切
标签: 关注, 点赞, 召唤
Token: 115

【澄清回应】
话术: 看到有宝宝问价格，现在下单只要199元，限时优惠哦！
语气: 清晰
标签: 回应, 价格, 促销
Token: 130
```

### 示例 4：实时窗口分析

```python
from server.ai.xunfei_lite_client import get_xunfei_client

client = get_xunfei_client()

# 第一个窗口（0-5分钟）
window1_transcript = """
欢迎来到我的直播间！今天给大家带来了新品。
这款产品有三大优势：性能强、价格优、服务好。
"""

window1_comments = [
    {"user": "观众1", "content": "主播好"},
    {"user": "观众2", "content": "新品是什么？"}
]

result1 = client.analyze_realtime(
    transcript=window1_transcript,
    comments=window1_comments,
    previous_summary=None,  # 首个窗口
    anchor_id="anchor_001"
)

print("=== 窗口 1 分析 ===")
print(f"摘要: {result1['summary']}")
print(f"亮点: {result1['highlight_points']}")
print(f"氛围: {result1['atmosphere']['level']} ({result1['atmosphere']['score']}/100)")

# 第二个窗口（5-10分钟）
window2_transcript = """
刚才给大家介绍了产品特点，现在说说价格。
限时优惠价只要199元，前100名还送配件。
"""

window2_comments = [
    {"user": "观众1", "content": "多少钱？"},
    {"user": "观众2", "content": "有优惠吗？"},
    {"user": "观众3", "content": "什么时候发货？"}
]

result2 = client.analyze_realtime(
    transcript=window2_transcript,
    comments=window2_comments,
    previous_summary=result1['summary'],  # 传入上一窗口摘要
    anchor_id="anchor_001"
)

print("\n=== 窗口 2 分析 ===")
print(f"摘要: {result2['summary']}")
print(f"风险: {result2['risks']}")
print(f"建议: {result2['suggestions']}")
print(f"\n推荐话术:")
for i, script in enumerate(result2['scripts'][:2], 1):
    print(f"{i}. [{script['type']}] {script['text']}")
```

### 示例 5：批量处理与 Token 统计

```python
from server.ai.xunfei_lite_client import get_xunfei_client
from server.utils.ai_usage_monitor import get_usage_monitor

client = get_xunfei_client()
monitor = get_usage_monitor()

# 模拟一场直播的多个窗口
windows = [
    {"transcript": "开场介绍...", "comments": [...]},
    {"transcript": "产品讲解...", "comments": [...]},
    {"transcript": "互动答疑...", "comments": [...]},
]

total_tokens = 0
session_id = "live_session_001"

for i, window in enumerate(windows, 1):
    print(f"\n处理窗口 {i}...")
    
    result = client.analyze_realtime(
        transcript=window["transcript"],
        comments=window["comments"],
        anchor_id="anchor_001"
    )
    
    # 记录使用量
    usage = result['_usage']
    total_tokens += usage['total_tokens']
    
    monitor.record_usage(
        model=client.model,
        function="实时分析",
        input_tokens=usage['prompt_tokens'],
        output_tokens=usage['completion_tokens'],
        duration_ms=usage['request_time_ms'],
        anchor_id="anchor_001",
        session_id=session_id,
        success=True
    )
    
    print(f"窗口 {i} Token: {usage['total_tokens']}")

# 获取会话统计
session_stats = monitor.get_session_stats(session_id)
print(f"\n=== 会话总计 ===")
print(f"调用次数: {session_stats['calls']}")
print(f"总Token: {session_stats['tokens']}")
print(f"总费用: ¥{session_stats['cost']:.4f}")
```

## REST API 调用示例

### 示例 1：使用 curl 测试连接

```bash
curl -X POST http://localhost:9019/api/ai/xunfei/test \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user"
  }'
```

### 示例 2：氛围分析 API

```bash
curl -X POST http://localhost:9019/api/ai/xunfei/analyze/atmosphere \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "欢迎来到直播间，今天给大家带来新品...",
    "comments": [
      {"user": "观众1", "content": "主播好！"},
      {"user": "观众2", "content": "666"}
    ],
    "context": {
      "duration_minutes": 30,
      "viewer_count": 150
    },
    "user_id": "user_123",
    "anchor_id": "anchor_456",
    "session_id": "session_789"
  }'
```

### 示例 3：话术生成 API

```bash
curl -X POST http://localhost:9019/api/ai/xunfei/generate/script \
  -H "Content-Type: application/json" \
  -d '{
    "script_type": "interaction",
    "context": {
      "current_topic": "产品介绍",
      "atmosphere": "活跃",
      "viewer_count": 200
    },
    "user_id": "user_123",
    "anchor_id": "anchor_456"
  }'
```

### 示例 4：查看使用统计

```bash
# 查看讯飞模型使用统计
curl http://localhost:9019/api/ai/xunfei/usage/stats?days=7

# 查看整体 AI 使用统计
curl http://localhost:9019/api/ai_usage/stats/current

# 查看模型定价
curl http://localhost:9019/api/ai_usage/models/pricing
```

## JavaScript/TypeScript 示例

```typescript
// 氛围分析
async function analyzeAtmosphere(transcript: string, comments: any[]) {
  const response = await fetch('http://localhost:9019/api/ai/xunfei/analyze/atmosphere', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript,
      comments,
      context: {
        duration_minutes: 30,
        viewer_count: 150
      },
      user_id: 'user_123',
      anchor_id: 'anchor_456'
    })
  });
  
  const data = await response.json();
  
  console.log('氛围等级:', data.data.atmosphere.level);
  console.log('氛围评分:', data.data.atmosphere.score);
  console.log('Token消耗:', data.usage.total_tokens);
  
  return data;
}

// 话术生成
async function generateScript(scriptType: string, context: any) {
  const response = await fetch('http://localhost:9019/api/ai/xunfei/generate/script', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_type: scriptType,
      context,
      user_id: 'user_123'
    })
  });
  
  const data = await response.json();
  
  console.log('话术:', data.data.line);
  console.log('语气:', data.data.tone);
  console.log('Token消耗:', data.usage.total_tokens);
  
  return data;
}
```

## 集成到现有服务

### 方式 1：替换现有 AI 客户端

```python
# 在 server/ai/generator.py 或其他服务中
from server.ai.xunfei_lite_client import get_xunfei_client

class AIScriptGenerator:
    def __init__(self, config):
        # 使用讯飞客户端替代
        self.client = get_xunfei_client()
    
    def generate_script(self, script_type, context):
        return self.client.generate_script(script_type, context)
```

### 方式 2：作为备用模型

```python
from server.ai.qwen_openai_compatible import get_qwen_client
from server.ai.xunfei_lite_client import get_xunfei_client

def get_ai_client(prefer_xunfei=False):
    """根据配置选择 AI 客户端"""
    if prefer_xunfei or os.getenv("AI_SERVICE") == "xunfei":
        return get_xunfei_client()
    else:
        return get_qwen_client()
```

## Token 优化建议

### 1. 文本截断

```python
# 截断过长的转写文本
transcript = transcript[-2000:]  # 保留最近 2000 字符

# 限制弹幕数量
comments = comments[-100:]  # 保留最近 100 条
```

### 2. 批量处理

```python
# 累积到一定数量后批量处理
buffer = []
BATCH_SIZE = 5

for comment in comments:
    buffer.append(comment)
    
    if len(buffer) >= BATCH_SIZE:
        result = client.analyze_live_atmosphere(
            transcript=transcript,
            comments=buffer
        )
        buffer.clear()
```

### 3. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_generate_script(script_type: str, context_hash: str):
    return client.generate_script(script_type, json.loads(context_hash))
```

## 完整示例：直播分析系统

```python
"""完整的直播分析系统示例"""

from server.ai.xunfei_lite_client import get_xunfei_client
from server.utils.ai_usage_monitor import get_usage_monitor
import time

class LiveAnalysisSystem:
    def __init__(self, anchor_id: str):
        self.client = get_xunfei_client()
        self.monitor = get_usage_monitor()
        self.anchor_id = anchor_id
        self.session_id = f"live_{int(time.time())}"
        self.previous_summary = None
    
    def analyze_window(self, transcript: str, comments: list):
        """分析一个时间窗口"""
        # 实时分析
        result = self.client.analyze_realtime(
            transcript=transcript,
            comments=comments,
            previous_summary=self.previous_summary,
            anchor_id=self.anchor_id
        )
        
        # 记录使用量
        usage = result.pop('_usage')
        self.monitor.record_usage(
            model=self.client.model,
            function="实时分析",
            input_tokens=usage['prompt_tokens'],
            output_tokens=usage['completion_tokens'],
            duration_ms=usage['request_time_ms'],
            anchor_id=self.anchor_id,
            session_id=self.session_id,
            success=True
        )
        
        # 更新摘要
        self.previous_summary = result.get('summary')
        
        return result
    
    def get_statistics(self):
        """获取会话统计"""
        return self.monitor.get_session_stats(self.session_id)

# 使用示例
system = LiveAnalysisSystem(anchor_id="anchor_001")

# 分析多个窗口
for i in range(3):
    result = system.analyze_window(
        transcript=f"窗口 {i+1} 的转写内容...",
        comments=[{"user": f"观众{j}", "content": "评论"} for j in range(5)]
    )
    
    print(f"\n=== 窗口 {i+1} ===")
    print(f"氛围: {result['atmosphere']['level']}")
    print(f"建议: {result['suggestions']}")

# 查看统计
stats = system.get_statistics()
print(f"\n总Token消耗: {stats['tokens']}")
print(f"总费用: ¥{stats['cost']:.4f}")
```

## 更多资源

- 📖 [完整文档](./讯飞星火Lite模型集成说明.md)
- 🚀 [快速开始](./讯飞Lite快速开始.md)
- 🔧 [API 参考](http://localhost:9019/docs)
- 💰 [Token 优化指南](./讯飞星火Lite模型集成说明.md#最佳实践)

