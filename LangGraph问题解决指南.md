# LangGraph Workflow 问题解决指南

**审查人：叶维哲**  
**更新日期：2025-01-10**

---

## 🚨 错误信息

```
分析卡片生成失败：LangGraph workflow not available
workflow_error: LangGraph workflow not available
建议：请检查 Qwen3-Max 接口配置后重试。
```

---

## 🔍 问题原因

LangGraph workflow 无法初始化，通常由以下原因导致：

### 1. LangGraph 库未安装
Python环境中缺少 `langgraph` 包。

### 2. Qwen3-Max API 配置错误
- API密钥无效或过期
- Base URL 配置错误
- 网络无法访问API

### 3. 相关依赖缺失
- `langchain-core`
- `langchain-community`
- `langsmith`

---

## ✅ 快速修复

### 方法一：自动修复（推荐）

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
chmod +x fix-langgraph.sh
./fix-langgraph.sh
```

脚本会自动：
1. ✅ 检查并安装 LangGraph
2. ✅ 检查相关依赖
3. ✅ 测试导入和初始化
4. ✅ 检查 Qwen3-Max 配置

### 方法二：手动修复

#### 步骤1：安装 LangGraph

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
source venv/bin/activate

# 安装 LangGraph 及依赖
pip install langgraph langchain-core langchain-community langsmith
```

#### 步骤2：验证安装

```bash
python -c "from langgraph.graph import StateGraph; print('✓ LangGraph安装成功')"
```

#### 步骤3：检查 Qwen3-Max 配置

编辑配置文件：
```bash
vi config/ai.json
```

确保有以下配置：
```json
{
  "qwen3_max": {
    "enabled": true,
    "api_key": "YOUR_API_KEY_HERE",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3-max"
  }
}
```

#### 步骤4：重启后端服务

```bash
./restart-all-services.sh
```

---

## 🔧 详细排查步骤

### 1. 检查 LangGraph 安装

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查是否安装
pip list | grep langgraph

# 测试导入
python << EOF
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
print("LangGraph 导入成功")
EOF
```

**预期输出**：
```
LangGraph 导入成功
```

**如果失败**：
```bash
pip install langgraph
```

### 2. 检查相关依赖

```bash
# 检查依赖
pip list | grep -E "langchain|langsmith"

# 如果缺失，安装
pip install langchain-core langchain-community langsmith
```

### 3. 检查 AI 配置

```bash
# 查看配置
cat config/ai.json | grep -A 10 "qwen3_max"

# 或使用 Python 检查
python << EOF
import json
with open('config/ai.json') as f:
    config = json.load(f)
    qwen_config = config.get('qwen3_max', {})
    print(f"Enabled: {qwen_config.get('enabled')}")
    print(f"API Key: {'***' if qwen_config.get('api_key') else 'MISSING'}")
    print(f"Base URL: {qwen_config.get('base_url')}")
EOF
```

### 4. 测试 API 连接

```bash
python << EOF
import sys
sys.path.insert(0, '/www/wwwroot/wwwroot/timao-douyin-live-manager')

from server.ai.live_analysis_generator import LiveAnalysisGenerator

try:
    generator = LiveAnalysisGenerator()
    print("✓ Generator 创建成功")
    print("✓ Qwen3-Max API 配置正确")
except Exception as e:
    print(f"❌ 创建失败: {e}")
EOF
```

### 5. 测试 Workflow 初始化

```bash
python << EOF
import sys
sys.path.insert(0, '/www/wwwroot/wwwroot/timao-douyin-live-manager')

from server.ai.langgraph_live_workflow import ensure_workflow, LiveWorkflowConfig

config = LiveWorkflowConfig(anchor_id="test")
try:
    workflow = ensure_workflow(analysis_generator=None, config=config)
    print("✓ Workflow 创建成功")
except Exception as e:
    print(f"❌ Workflow 创建失败: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### 6. 查看后端日志

```bash
# 查看最近的错误
tail -f logs/main.log | grep -i "langgraph\|workflow"

# 或查看完整日志
tail -f logs/main.log
```

---

## 📝 配置模板

### config/ai.json 配置示例

```json
{
  "qwen3_max": {
    "enabled": true,
    "api_key": "sk-xxx",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen3-max",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30
  },
  "gemini": {
    "enabled": false,
    "api_key": "YOUR_GEMINI_API_KEY"
  }
}
```

---

## ⚠️ 常见问题

### Q1: pip install langgraph 失败

**可能原因**：网络问题或依赖冲突

**解决方法**：
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple langgraph

# 或更新 pip
pip install --upgrade pip
pip install langgraph
```

### Q2: LangGraph 导入成功但 workflow 初始化失败

**可能原因**：Qwen3-Max API 配置问题

**解决方法**：
1. 检查 API Key 是否有效
2. 测试 API 连接：
```bash
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-max","messages":[{"role":"user","content":"测试"}]}'
```

### Q3: 服务重启后问题仍存在

**可能原因**：代码未重新加载

**解决方法**：
```bash
# 完全停止服务
pkill -f "python.*server"
sleep 3

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 重新启动
./restart-all-services.sh
```

### Q4: 虚拟环境问题

**解决方法**：重建虚拟环境
```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 备份 requirements.txt
cp requirements.txt requirements.txt.bak

# 删除旧虚拟环境
rm -rf venv

# 创建新虚拟环境
python3 -m venv venv
source venv/bin/activate

# 重新安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install langgraph langchain-core langchain-community
```

---

## 🔍 调试技巧

### 启用详细日志

编辑 `server/app/services/ai_live_analyzer.py`，临时添加调试日志：

```python
# 在 __init__ 方法中
logger.setLevel(logging.DEBUG)
logger.debug(f"Initializing workflow with anchor_id: {self._anchor_id}")
```

### 测试单个组件

```bash
# 测试 Generator
python -c "
from server.ai.live_analysis_generator import LiveAnalysisGenerator
g = LiveAnalysisGenerator()
print('Generator OK')
"

# 测试 Workflow
python -c "
from server.ai.langgraph_live_workflow import ensure_workflow, LiveWorkflowConfig
w = ensure_workflow(None, LiveWorkflowConfig(anchor_id='test'))
print('Workflow OK')
"
```

---

## 📞 获取帮助

如果以上方法都无法解决问题：

1. **查看完整日志**：
```bash
tail -n 100 logs/main.log > debug.log
cat debug.log
```

2. **收集环境信息**：
```bash
python --version
pip list | grep -E "langgraph|langchain"
cat config/ai.json | grep -v "api_key"
```

3. **联系技术支持**：
   - 审查人：叶维哲
   - 提供：错误日志、环境信息、配置文件（隐藏密钥）

---

## ✅ 验证修复

修复完成后，运行以下命令验证：

```bash
# 1. 验证 LangGraph 安装
python -c "from langgraph.graph import StateGraph; print('OK')"

# 2. 验证 Workflow 初始化
./fix-langgraph.sh

# 3. 重启服务
./restart-all-services.sh

# 4. 测试前端功能
# 打开前端，开始直播录制，查看是否能正常生成分析卡片
```

---

## 📚 相关文档

- LangGraph 工作流设计：`docs/AI处理工作流/直播AI话术LangGraph规划.md`
- AI 配置指南：`docs/AI模型配置指南.md`
- 快速命令参考：`快速命令参考.md`

