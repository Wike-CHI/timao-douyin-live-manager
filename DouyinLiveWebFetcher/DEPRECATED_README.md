# 此目录已弃用

本模块的代码已迁移到 `server/modules/douyin/`。

## 迁移信息

**新位置**: `server/modules/douyin/`

**迁移日期**: 2024-11-01

**迁移原因**: 项目结构优化，将所有服务端模块整合到 `server/` 目录下，便于统一管理和打包。

## 如何更新你的代码

**旧导入**:
```python
from DouyinLiveWebFetcher.liveMan import DouyinLiveWebFetcher
from DouyinLiveWebFetcher.ac_signature import get__ac_signature
```

**新导入**:
```python
from server.modules.douyin.liveMan import DouyinLiveWebFetcher
from server.modules.douyin.ac_signature import get__ac_signature
```

## 保留原因

此目录保留仅用于**向后兼容**和**开发参考**。在生产环境中，请使用新路径。

---

**重要**: 如果你在开发新功能，请**务必**使用 `server/modules/douyin/` 中的代码。

