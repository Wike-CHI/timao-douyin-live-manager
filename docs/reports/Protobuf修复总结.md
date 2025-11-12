# Protobuf 兼容性修复总结

**审查人：** 叶维哲  
**修复完成：** 2025-11-09  
**最终方案：** ✅ 移除 ONNX + 固定 Protobuf 3.20.3

---

## 🎯 核心问题

实时音频转写服务启动失败，报错：
```
TypeError: Descriptors cannot be created directly
```

**根本原因：** tensorboardX 2.6 与 protobuf 4.x+ 不兼容

---

## ✅ 最终解决方案

### 1. 修改 `requirements.txt`

```diff
- onnx>=1.19.0
- onnxruntime>=1.23.0  
- onnxconverter-common>=1.16.0
+ protobuf<=3.20.3  # 新增版本约束
```

### 2. 清理不必要的依赖

经过代码检查发现：
- ❌ `onnx` - 项目中未使用
- ❌ `onnxruntime` - 项目中未使用  
- ❌ `onnxconverter-common` - 项目中未使用

**决策：** 移除这些未使用的依赖，避免版本冲突

### 3. 执行修复

```bash
# 自动修复脚本
./scripts/诊断与排障/fix-protobuf.sh
```

---

## 🧪 测试结果

```
✅ protobuf 版本: 3.20.3
✅ tensorboardX 导入成功
✅ FunASR 依赖链正常
✅ 所有测试通过 (3/3)
```

---

## 📦 依赖关系说明

### 为什么移除 ONNX？

1. **代码中未使用**
   ```bash
   $ grep -r "import onnx" server/
   # 无结果
   ```

2. **版本冲突严重**
   - onnx 1.19.1 要求 protobuf >= 4.25.1
   - tensorboardX 2.6 要求 protobuf < 4
   - **无法同时满足**

3. **编译困难**
   - onnx 1.12.0（兼容版本）是源码分发
   - 需要系统安装 protobuf 编译器
   - 编译成本高，不值得

### FunASR 是否需要 ONNX？

FunASR 的 ONNX 依赖是**可选的**：
- ✅ **推理后端**：支持 PyTorch（默认）和 ONNX
- ✅ **当前使用**：PyTorch 后端（不需要 ONNX）
- ⚠️ **如需 ONNX**：手动安装预编译版本

---

## 🚀 启动验证

修复后重启服务：

```bash
./stop-backend.sh
./scripts/构建与启动/start-backend.sh
```

**预期结果：**
```
✅ 实时音频转写服务启动成功
✅ tensorboardX 正常工作
✅ 所有服务健康
```

---

## 📝 童子军军规清单

- [x] 修复了 protobuf 兼容性问题
- [x] 清理了未使用的依赖（onnx 相关）
- [x] 添加了版本约束（protobuf<=3.20.3）
- [x] 创建了自动化测试（`tests/regression/test_protobuf_fix.py`）
- [x] 创建了修复脚本（scripts/诊断与排障/fix-protobuf.sh）
- [x] 编写了详细文档（本文件）
- [x] 让代码库更干净、更易维护

---

## ⚠️ 注意事项

### 如果需要使用 ONNX

如果未来需要 ONNX 推理功能：

```bash
# 安装预编译的兼容版本（Linux x86_64）
pip install https://github.com/microsoft/onnxruntime/releases/download/v1.15.0/onnxruntime-1.15.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

**但目前不需要！**

---

## 📚 相关文件

- `requirements.txt` - 依赖配置
- `tests/regression/test_protobuf_fix.py` - 自动化测试
- `scripts/诊断与排障/fix-protobuf.sh` - 自动化修复
- `docs/reports/Protobuf兼容性修复报告.md` - 详细报告

---

## ✨ 最终状态

| 组件 | 版本 | 状态 |
|------|------|------|
| protobuf | 3.20.3 | ✅ 固定 |
| tensorboardX | 2.6 | ✅ 正常 |
| FunASR | 1.2.0+ | ✅ PyTorch 后端 |
| ONNX | 已移除 | ⚪ 不需要 |

**问题已彻底解决！** 🎉
