# 大文件管理总结

## 核心要点
- SenseVoice/FunASR 模型与原始音频样例保持仓库外管理。
- `.gitignore` 已覆盖常见媒体文件与临时输出，避免误提交。
- 提供脚本 `cleanup_large_files.py` 与 `validate_gitignore.py` 辅助排查大文件。

## 主要资产
1. **语音模型**
   - 推荐目录：`models/sensevoice/`
   - 下载来源：团队共享存储或官方模型仓库
   - 需要在交付文档中记录版本与校验信息
2. **测试音频**
   - 推荐目录：`tests/audio_samples/`
   - 仅在本地保留，必要时通过共享盘同步

## 操作建议
- 初始化环境时，先同步模型资源，再运行 `pip install -r AST_module/requirements.txt`。
- 通过 `find` 或项目脚本定期扫描大于 50MB 的临时文件。
- 若需共享音频样例，可走 Git LFS 或对象存储，并在 README 标注下载方式。

## 风险提示
- 模型与缓存体积较大，注意清理 `~/.cache/funasr` 等目录。
- 关注 SenseVoice 官方许可约束，避免将模型直接打包进发行版。
- 变更模型版本时同步更新配置与文档，确保团队一致性。

通过以上策略，项目在不引入额外依赖的情况下，保持了大文件的可控与可追溯性。
