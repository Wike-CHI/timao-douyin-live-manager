# 此目录已弃用

本模块的代码已迁移到 `server/modules/ast/`。

## 迁移信息

**新位置**: `server/modules/ast/`

**迁移日期**: 2024-11-01

**迁移原因**: 项目结构优化，将所有服务端模块整合到 `server/` 目录下，便于统一管理和打包。

## 如何更新你的代码

**旧导入**:
```python
from AST_module.ast_service import ASTService
from AST_module.sensevoice_service import SenseVoiceConfig
from AST_module.postprocess import ChineseCleaner
```

**新导入**:
```python
from server.modules.ast.ast_service import ASTService
from server.modules.ast.sensevoice_service import SenseVoiceConfig
from server.modules.ast.postprocess import ChineseCleaner
```

## 保留原因

此目录保留仅用于**向后兼容**和**开发参考**。在生产环境中，请使用新路径。

---

**重要**: 如果你在开发新功能，请**务必**使用 `server/modules/ast/` 中的代码。

