# StreamCap 导入问题修复报告

## 问题描述

服务启动时出现 `No module named 'server.modules.utils'` 错误，影响以下路由加载：
- 直播音频转写
- 直播复盘
- NLP 管理
- AI 实时分析
- AI 话术生成

## 根本原因

StreamCap 模块迁移后，`handlers.py` 和 `direct_downloader.py` 中的导入路径不正确，导致找不到 `utils` 模块。

## 修复方案

### 1. 创建缺失的 utils 模块
```bash
# 创建目录
New-Item -ItemType Directory -Force -Path server\modules\streamcap\utils

# 复制文件
Copy-Item -Path StreamCap\app\utils\utils.py -Destination server\modules\streamcap\utils\utils.py
```

### 2. 修复导入路径

#### server/modules/streamcap/platforms/platform_handlers/handlers.py
```python
# 修复前
from ....utils.utils import trace_error_decorator

# 修复后
from ...utils.utils import trace_error_decorator
```

#### server/modules/streamcap/platforms/platform_handlers/__init__.py
```python
# 修复前
from ...logger import logger

# 修复后
import logging
logger = logging.getLogger(__name__)
```

#### server/modules/streamcap/media/direct_downloader.py
```python
# 修复前
from ...utils.logger import logger

# 修复后
import logging
logger = logging.getLogger(__name__)
```

#### server/modules/streamcap/utils/utils.py
```python
# 修复前
from .logger import logger

# 修复后
import logging
logger = logging.getLogger(__name__)
```

### 3. 创建 __init__.py
```python
# server/modules/streamcap/utils/__init__.py
from .utils import trace_error_decorator
import logging

logger = logging.getLogger(__name__)

__all__ = ["trace_error_decorator", "logger"]
```

### 4. 统一日志系统
将所有 StreamCap 模块中的 loguru 替换为标准 logging，与项目其他部分保持一致。

## 验证结果

✅ **无 linter 错误**  
✅ **导入路径正确**  
✅ **与现有代码结构一致**

## 文件变更列表

### 新增文件
- `server/modules/streamcap/utils/__init__.py`
- `server/modules/streamcap/utils/utils.py`

### 修改文件
- `server/modules/streamcap/platforms/platform_handlers/handlers.py`
- `server/modules/streamcap/platforms/platform_handlers/__init__.py`
- `server/modules/streamcap/media/direct_downloader.py`
- `server/modules/streamcap/utils/utils.py`
- `server/modules/streamcap/__init__.py`

## 待测试

启动服务验证以下路由是否正常加载：
- [ ] 直播音频转写
- [ ] 直播复盘
- [ ] NLP 管理
- [ ] AI 实时分析
- [ ] AI 话术生成

## 注意事项

1. `streamget` 包需要安装才能使用 StreamCap 功能
2. 所有导入路径已使用相对路径，便于维护
3. 统一使用标准 logging 而不是 loguru

## 后续建议

1. 测试所有受影响的路由功能
2. 验证 StreamCap 平台处理器的正常工作
3. 考虑是否需要进一步提取更多 StreamCap 功能

