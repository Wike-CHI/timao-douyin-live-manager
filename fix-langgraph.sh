#!/bin/bash
# 修复 LangGraph workflow 问题

echo "=========================================="
echo "LangGraph Workflow 问题诊断与修复"
echo "=========================================="

cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 1. 检查虚拟环境
echo ""
echo "1. 检查虚拟环境..."
if [ -d "venv" ]; then
    echo "✓ 虚拟环境存在"
    source venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 2. 检查LangGraph是否安装
echo ""
echo "2. 检查LangGraph安装状态..."
if python -c "import langgraph" 2>/dev/null; then
    echo "✓ LangGraph已安装"
    python -c "import langgraph; print(f'  版本: {langgraph.__version__}')" 2>/dev/null || echo "  (无法获取版本)"
else
    echo "❌ LangGraph未安装或导入失败"
    echo "正在安装LangGraph..."
    pip install langgraph langchain-core langchain-community
    if [ $? -eq 0 ]; then
        echo "✓ LangGraph安装成功"
    else
        echo "❌ LangGraph安装失败"
        exit 1
    fi
fi

# 3. 检查相关依赖
echo ""
echo "3. 检查相关依赖..."
DEPS=("langchain-core" "langchain-community" "langsmith")
for dep in "${DEPS[@]}"; do
    if python -c "import ${dep//-/_}" 2>/dev/null; then
        echo "✓ $dep 已安装"
    else
        echo "⚠️  $dep 未安装，正在安装..."
        pip install "$dep"
    fi
done

# 4. 测试LangGraph导入
echo ""
echo "4. 测试LangGraph导入..."
python << 'EOF'
try:
    from langgraph.graph import END, StateGraph
    from langgraph.checkpoint.memory import MemorySaver
    print("✓ LangGraph 导入成功")
    print(f"  StateGraph: {StateGraph}")
    print(f"  MemorySaver: {MemorySaver}")
except Exception as e:
    print(f"❌ LangGraph 导入失败: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ LangGraph导入测试失败"
    exit 1
fi

# 5. 检查Qwen3-Max配置
echo ""
echo "5. 检查AI配置..."
if [ -f "config/ai.json" ]; then
    echo "✓ AI配置文件存在"
    if grep -q "qwen3-max" config/ai.json; then
        echo "✓ Qwen3-Max配置已找到"
    else
        echo "⚠️  未找到Qwen3-Max配置"
    fi
else
    echo "❌ AI配置文件不存在: config/ai.json"
fi

# 6. 测试workflow初始化
echo ""
echo "6. 测试workflow初始化..."
python << 'EOF'
import sys
sys.path.insert(0, '/www/wwwroot/wwwroot/timao-douyin-live-manager')

try:
    from server.ai.langgraph_live_workflow import ensure_workflow, LiveWorkflowConfig
    from server.ai.live_analysis_generator import LiveAnalysisGenerator
    
    print("✓ 模块导入成功")
    
    # 测试创建generator
    try:
        generator = LiveAnalysisGenerator()
        print("✓ LiveAnalysisGenerator 创建成功")
    except Exception as e:
        print(f"⚠️  LiveAnalysisGenerator 创建失败: {e}")
        print("   这通常是因为Qwen3-Max API配置问题")
    
    # 测试workflow
    try:
        config = LiveWorkflowConfig(anchor_id="test")
        workflow = ensure_workflow(analysis_generator=None, config=config)
        print("✓ Workflow 创建成功")
    except Exception as e:
        print(f"❌ Workflow 创建失败: {e}")
        exit(1)
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Workflow初始化测试失败"
    echo ""
    echo "可能的原因："
    echo "  1. Qwen3-Max API配置错误"
    echo "  2. API密钥无效或过期"
    echo "  3. 网络连接问题"
    echo ""
    echo "请检查 config/ai.json 中的配置："
    echo "  - qwen3_max_api_key"
    echo "  - qwen3_max_base_url"
    exit 1
fi

# 7. 检查后端服务日志
echo ""
echo "7. 检查最近的错误日志..."
if [ -f "logs/main.log" ]; then
    echo "最近的LangGraph相关错误："
    grep -i "langgraph\|workflow" logs/main.log | tail -n 5 || echo "  (无相关错误)"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "✅ 修复建议："
echo "  1. 如果LangGraph已安装，重启后端服务："
echo "     ./restart-all-services.sh"
echo ""
echo "  2. 如果Qwen3-Max配置有问题，编辑配置："
echo "     vi config/ai.json"
echo ""
echo "  3. 查看详细日志："
echo "     tail -f logs/main.log"

