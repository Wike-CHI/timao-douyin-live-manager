# 大文件管理说明

## 概述

提猫直播助手涉及本地语音识别与音频调试场景，仓库中不直接存放推理模型或体积巨大的测试音频。为方便协作，请遵循以下约定。

## 大文件类型

### 1. SenseVoice/FunASR 模型
- 建议路径：`models/sensevoice/`
- 大小：约 1.5GB（取决于模型版本）
- 用途：本地语音识别

### 2. 调试音频样例
- 推荐路径：`tests/audio_samples/`
- 大小：单个文件数十 MB
- 用途：离线回放与算法验证

## 管理策略

1. **Git 忽略**
   - 使用仓库自带的 `.gitignore`，保持模型与原始音频不被提交。
2. **下载指引**
   - 在团队知识库记录 SenseVoice/FunASR 模型下载链接与校验信息。
   - 建议将模型压缩包存放在共享网盘或对象存储，按版本归档。
3. **同步脚本**
   - 如需自动化拉取，可编写私有脚本（示例：`scripts/sync_models.py`），但脚本中避免硬编码凭证。

## 常用检查

```bash
# 查找超过 50MB 的文件
find . -type f -size +50M -not -path './.git/*'

# 使用项目脚本扫描临时大文件
python cleanup_large_files.py
```

## Git LFS 建议

若团队计划共享部分音频样例，可考虑 Git LFS：
```bash
git lfs install
git lfs track "tests/audio_samples/*.wav"
git add .gitattributes
```
提交前请确认仓库策略允许 LFS 资源。

## 注意事项

- **许可证**：SenseVoice/FunASR 模型遵循官方条款，下载与分发需遵守许可协议。
- **磁盘空间**：模型与缓存文件较大，建议定期清理 `~/.cache/funasr`。
- **性能**：首次加载模型耗时较长，可提前预热并复用服务实例。

---

如需新增模型或共享样本，请在 PR 中说明存储位置及校验方式，确保团队成员能够复现相同的推理环境。
