# 直播控制台双模式功能测试说明

> **测试文档**: `docs/产品使用手册/直播控制台双模式设计文档.md`  
> **审查人**: 叶维哲  
> **测试创建日期**: 2025-11-15

---

## 📋 测试概览

本测试套件为直播控制台双模式设计文档中描述的功能提供自动化测试，包括：

1. **高价值用户检测** (`test_high_value_detection.py`)
2. **冷场检测** (`test_silence_detection.py`)
3. **智能话术生成** (`test_script_generation.py`)
4. **信息轮播系统** (`test_carousel.py`)

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
pip install -r tests/test_requirements.txt
```

### 2. 运行所有测试

```bash
# 运行所有双模式相关测试
pytest tests/test_high_value_detection.py \
       tests/test_silence_detection.py \
       tests/test_script_generation.py \
       tests/test_carousel.py \
       -v --tb=short

# 或使用简化命令
bash tests/run_live_mode_tests.sh
```

### 3. 运行单个测试文件

```bash
# 测试高价值用户检测
pytest tests/test_high_value_detection.py -v

# 测试冷场检测
pytest tests/test_silence_detection.py -v

# 测试话术生成
pytest tests/test_script_generation.py -v

# 测试信息轮播
pytest tests/test_carousel.py -v
```

---

## 📂 测试文件说明

### 1. `test_high_value_detection.py` - 高价值用户检测

**测试内容**:
- ✅ 大额礼物检测（≥1000元为高优先级）
- ✅ 中等礼物检测（100-999元为中优先级）
- ✅ 高频互动检测（5分钟内评论≥5次）
- ✅ 高等级用户检测（等级≥30）
- ✅ 小额礼物过滤（<100元不检测）
- ✅ 用户去重
- ✅ 优先级排序
- ✅ 评分计算（礼物40%+互动30%+等级20%+历史10%）

**API测试**:
- `POST /api/ai/scripts/generate_smart` - 智能话术生成接口
- 请求/响应结构验证
- 最大话术数量限制

**运行**:
```bash
pytest tests/test_high_value_detection.py -v
```

---

### 2. `test_silence_detection.py` - 冷场检测

**测试内容**:
- ✅ 冷场阈值检测
  - 20秒预警（低严重度）
  - 30秒中度冷场
  - 60秒严重冷场
- ✅ 主播说话时不冷场
- ✅ 互动记录功能
- ✅ 互动历史自动清理（5分钟）
- ✅ 破冰建议生成（3个严重度级别）
- ✅ 性能测试（检测<10ms，记录1000次<1秒）

**API测试**:
- `GET /api/ai/live/silence_check` - 冷场检测接口
- `POST /api/ai/live/record_interaction` - 记录互动接口
- `GET /api/live/room_status` - 直播间状态（包含冷场状态）

**运行**:
```bash
pytest tests/test_silence_detection.py -v
```

---

### 3. `test_script_generation.py` - 智能话术生成

**测试内容**:
- ✅ 感谢话术生成
- ✅ 留人话术生成
- ✅ 互动话术生成
- ✅ 话术类型策略
  - 大额礼物（≥1000元）→ 立即生成高优先级
  - 中等礼物（100-999元）→ 延迟生成中优先级
  - 小额礼物（10-99元）→ 合并感谢低优先级
- ✅ 最大话术数量限制
- ✅ 优先级排序
- ✅ 风格画像集成
- ✅ 多种类型同时生成
- ✅ 性能测试（生成<2秒，支持并发）

**API测试**:
- `POST /api/ai/scripts/generate_smart` - 完整功能测试
- `GET /api/ai/scripts/history` - 话术历史查询
- 优先级阈值过滤
- 空上下文处理
- 无效类型处理

**运行**:
```bash
pytest tests/test_script_generation.py -v
```

---

### 4. `test_carousel.py` - 信息轮播系统

**测试内容**:
- ✅ 轮播顺序（①AI分析 → ②话术 → ③氛围）
- ✅ 轮播间隔
  - 默认5秒
  - 范围3-10秒
  - 自适应间隔（根据内容长度）
- ✅ 轮播控制
  - 启动/停止
  - 暂停/恢复
  - 跳转到指定类型
- ✅ 优先级队列
  - 入队/出队
  - 优先级排序
  - peek操作
- ✅ 信息调度
  - 高优先级立即显示
  - 中优先级加入队列
  - 手动切换暂停轮播
  - 超时后自动恢复
- ✅ 性能测试
  - 时间准确性
  - 队列性能（1000次操作<1秒）
  - 内存使用

**运行**:
```bash
pytest tests/test_carousel.py -v
```

---

## 🎯 测试覆盖率

### 高价值用户检测模块
- **单元测试**: 10个测试用例
- **API测试**: 4个测试用例
- **覆盖率目标**: >90%

### 冷场检测模块
- **单元测试**: 12个测试用例
- **API测试**: 3个测试用例
- **集成测试**: 2个测试用例
- **性能测试**: 2个测试用例
- **覆盖率目标**: >90%

### 智能话术生成模块
- **单元测试**: 11个测试用例
- **API测试**: 7个测试用例
- **策略测试**: 3个测试用例
- **性能测试**: 2个测试用例
- **覆盖率目标**: >85%

### 信息轮播模块
- **单元测试**: 18个测试用例
- **集成测试**: 3个测试用例
- **性能测试**: 3个测试用例
- **边界测试**: 3个测试用例
- **覆盖率目标**: >85%

---

## 📊 测试报告

### 生成测试报告

```bash
# 生成HTML报告
pytest tests/test_high_value_detection.py \
       tests/test_silence_detection.py \
       tests/test_script_generation.py \
       tests/test_carousel.py \
       --html=tests/reports/live_mode_test_report.html \
       --self-contained-html

# 生成覆盖率报告
pytest tests/test_*.py --cov=server --cov-report=html
```

### 查看报告

```bash
# HTML测试报告
open tests/reports/live_mode_test_report.html

# 覆盖率报告
open htmlcov/index.html
```

---

## 🔧 前置条件

### 后端服务要求

测试部分功能需要后端服务运行：

```bash
# 启动后端服务
cd /www/wwwroot/wwwroot/timao-douyin-live-manager/server
uvicorn app.main:app --reload --port 8090
```

### 数据库要求

某些测试可能需要数据库连接，确保配置正确：

```bash
# 检查数据库连接
python -c "from server.db.database import engine; print('DB OK')"
```

### Mock数据

测试使用Mock数据，无需真实直播间数据。

---

## ⚠️ 注意事项

### 1. 性能测试

性能测试对系统资源敏感，建议在相对空闲时运行：

```bash
# 跳过性能测试
pytest tests/ -v -m "not performance"
```

### 2. API测试

API测试需要后端服务运行，如果服务未运行会跳过部分测试：

```bash
# 只运行单元测试（不需要服务）
pytest tests/ -v -m "not api"
```

### 3. 超时设置

某些测试涉及时间延迟，可能需要较长时间：

```bash
# 设置超时时间
pytest tests/ -v --timeout=30
```

---

## 🐛 故障排除

### 问题1: 导入错误

**现象**: `ModuleNotFoundError: No module named 'server'`

**解决**:
```bash
# 确保在项目根目录
cd /www/wwwroot/wwwroot/timao-douyin-live-manager

# 设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 或在测试文件中已自动添加
```

### 问题2: API测试失败

**现象**: `Connection refused` 或 `502 Bad Gateway`

**解决**:
```bash
# 检查后端服务
ps aux | grep uvicorn

# 启动后端服务
cd server && uvicorn app.main:app --reload --port 8090
```

### 问题3: 数据库连接错误

**现象**: `OperationalError: (...)  could not connect`

**解决**:
```bash
# 检查数据库配置
cat server/.env | grep DATABASE

# 测试数据库连接
python -c "from server.db.database import SessionLocal; db = SessionLocal(); print('OK')"
```

### 问题4: Mock对象错误

**现象**: `AttributeError: Mock object has no attribute...`

**解决**: 检查mock对象设置，参考测试文件中的正确用法

---

## 📝 编写新测试

### 测试模板

```python
"""
新功能测试

测试文档：docs/产品使用手册/直播控制台双模式设计文档.md
审查人：叶维哲
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestNewFeature:
    """测试新功能"""
    
    @pytest.fixture
    def setup_data(self):
        """准备测试数据"""
        return {'key': 'value'}
    
    def test_basic_functionality(self, setup_data):
        """测试基本功能"""
        # Arrange
        expected = 'expected_result'
        
        # Act
        result = some_function(setup_data)
        
        # Assert
        assert result == expected, "错误消息"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
```

### 测试命名规范

- 测试文件: `test_<模块名>.py`
- 测试类: `Test<功能名>`
- 测试方法: `test_<具体测试内容>`

### Fixtures使用

```python
@pytest.fixture
def mock_client():
    """创建模拟客户端"""
    from fastapi.testclient import TestClient
    from server.app.main import app
    return TestClient(app)

def test_endpoint(mock_client):
    """使用fixture"""
    response = mock_client.get("/api/endpoint")
    assert response.status_code == 200
```

---

## 🎓 最佳实践

### 1. 测试隔离

每个测试应独立运行，不依赖其他测试：

```python
@pytest.fixture(autouse=True)
def cleanup():
    """自动清理"""
    yield
    # 测试后清理
    clear_cache()
```

### 2. Mock外部依赖

```python
@patch('server.external_api.call')
def test_with_mock(mock_call):
    mock_call.return_value = {'status': 'success'}
    result = function_that_calls_api()
    assert result is not None
```

### 3. 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    (100, 'medium'),
    (1000, 'high'),
    (10, 'low')
])
def test_priority_calculation(input, expected):
    assert calculate_priority(input) == expected
```

### 4. 性能测试标记

```python
@pytest.mark.performance
def test_performance():
    """性能测试"""
    import time
    start = time.perf_counter()
    heavy_operation()
    duration = time.perf_counter() - start
    assert duration < 1.0
```

---

## 📞 联系方式

如有测试相关问题，请联系：

- **审查人**: 叶维哲
- **文档**: `docs/产品使用手册/直播控制台双模式设计文档.md`
- **问题反馈**: 在项目issue中提交

---

## 📅 测试维护

### 更新频率

- 功能更新后立即更新测试
- 每周review测试覆盖率
- 每月review测试性能

### 版本记录

| 版本 | 日期 | 说明 | 审查人 |
|------|------|------|--------|
| v1.0 | 2025-11-15 | 初始版本，创建4个测试文件 | 叶维哲 |

---

**测试愉快！🎉**

