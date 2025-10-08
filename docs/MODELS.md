# 模型与本地缓存说明（SenseVoice/VAD/依赖）

本项目仓库不包含任何模型权重或录制产物。请在本地按需下载与配置，确保 Git 仓库只保留代码与文档。

## 目录与环境变量
- 推荐在非系统盘建立统一缓存目录，例如：
  - Windows：`D:\\models`（或任意自定义）
  - macOS/Linux：`$HOME/models`

- 设置环境变量（任选其一：临时或写入系统）：
  - Windows PowerShell：
    - `$env:MODELSCOPE_CACHE='D:\\models'`
    - `$env:HF_HOME='D:\\models\\huggingface'`
  - Bash：
    - `export MODELSCOPE_CACHE="$HOME/models"`
    - `export HF_HOME="$HOME/models/huggingface"`

> MODELSCOPE_CACHE 供 ModelScope 使用；HF_HOME 供 HuggingFace 生态使用。

## SenseVoice Small + VAD（FunASR）
- 默认仅支持 `iic/SenseVoiceSmall` + VAD（本地低延时转写）。
- 首次运行会自动下载；也可在 ModelScope 手动下载后放置到上述缓存目录。
- 如需固定到本地路径，可在 `AST_module/config.py` 中指明本地模型目录，或通过环境变量覆盖。
- 详细说明见：`AST_module/README_SenseVoice.md`。

## FFmpeg
- 需安装系统级 FFmpeg 并确保可执行：
  - Windows：chocolatey / winget 安装或到官网下载 zip，并把 `ffmpeg.exe` 所在目录加入 PATH。
  - macOS：`brew install ffmpeg`
  - Linux：使用发行版包管理器安装。

## 运行产物与日志
- 录制的媒体、转写、弹幕与话术摘要等会写入 `records/`（本地目录）。
- 音频抓取临时片段写入 `AST_module/audio_logs/`。
- 以上目录均被 `.gitignore` 忽略，不会进入仓库。请按需定期清理以释放磁盘空间。

## 常见问题
1) 速度慢/下载失败：
   - 使用国内镜像或手动下载模型到缓存目录。
2) 权限/路径异常（Windows 常见）：
   - 确保缓存目录存在且当前用户有读写权限；避免指向不存在的盘符。
3) 磁盘不足：
   - SenseVoice Small + VAD 约 1–2 GB，请预留足够空间。

