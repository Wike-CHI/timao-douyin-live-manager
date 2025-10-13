# 2025-10-13 · 直播录制落盘修复记录

## 背景
- 用户反馈后台触发的直播录制结束后，`records/<主播>/...` 目录下没有生成分段视频。
- 调查发现 `LiveReportService` 内部的 ffmpeg 命令与 StreamCap 主流程不一致：仅做 `-c copy` 简易分段，缺少 UA、缓冲与重连参数，且未开启 `-strftime`，导致文件名无法解析时间戳。

## 处理内容
- 复用 StreamCap 的 `create_builder("mp4", …)` 构建器，保持与桌面端一致的 ffmpeg 启动参数。
- 对输出添加 `-strftime 1`，以 `主播_YYYYmmdd_HHMMSS_###.mp4` 的方式滚动写入，方便 `_infer_start_ts` 与后续多模态分析。
- 调整 referer 传递逻辑，保证 Douyin 录制源被正确拉取。

## 验证步骤
1. 启动后端：`uvicorn server.app.main:app --reload`.
2. 调用 `POST /api/report/live/start`，等待至少一个分段周期。
3. 检查 `records/抖音/<主播名>/<当天日期>/<session_id>/`，确认生成 mp4 分段文件。
4. 调用 `GET /api/report/live/status`，`recording_dir` 字段应指向上述目录并列出 `segments` 元数据。

## 后续跟进
- 结合多模态识别需求，在窗口分析阶段对新分段抽帧，向 Qwen3-Max 提供直播画面上下文。
- 可考虑增加磁盘空间监控，避免长时间录制导致落盘失败。

