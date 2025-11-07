---
description: Project-specific AI rules for timao-douyin-live-manager
globs: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.md"]
alwaysApply: true
---

# 项目特定 AI 规则

本规则文件结合了多个编码原则，并适应于 timao-douyin-live-manager 项目。该项目涉及直播管理，包括 admin-dashboard 前端、server 后端服务（如 live_session、live_report、live_audio 等），数据库模型，以及 AI 相关服务（如转写、报告生成）。规则分为几个类别，以指导开发过程。

## 通用原则

### KISS 原则 (Keep It Simple, Stupid)
- 在 live_session_service.py 中，实现简单直接的会话管理逻辑，避免不必要的复杂性。例如，使用基本的 CRUD 操作而非过早引入状态机。
- 对于 admin-dashboard 中的 React 组件，优先使用简单状态管理，除非明确需要复杂的状态库。

### YAGNI 原则 (You Aren't Gonna Need It)
- 避免在 LiveSession 模型中添加预留字段，如"future_analysis"，除非当前需求明确要求。
- 在 API 设计中，只实现当前需要的端点，例如 /api/live/sessions，只支持基本查询而非预留高级过滤。

### DRY 原则 (Don't Repeat Yourself)
- 在 services 目录下，提取公共工具函数，如 format_timestamp，用于多个服务（如 live_report 和 live_audio）。
- 避免在多个组件中重复错误处理逻辑；创建一个共享的 ErrorHandler 组件。

### 单责原则 (Single Responsibility Principle)
- 每个服务类如 LiveSessionService 只负责会话生命周期管理，不包含报告生成（移到 LiveReportService）。
- 前端组件如 LiveSessionList 只负责 UI 渲染，数据获取移到自定义 Hook。

### 最小意外原则 (Principle of Least Surprise)
- 函数命名如 generate_report 应返回预期格式（JSON），并在文档中明确副作用。
- API 端点遵循 RESTful 约定，例如 GET /api/live/sessions 返回列表。

## 性能和优化原则

### 阿姆达尔定律 (Amdahl's Law)
- 识别瓶颈如音频转写服务，优化并行处理（如使用多线程处理直播段落）。
- 在 server/app/services/live_audio_service.py 中，应用性能分析工具如 cProfile 来优化热点。

### 帕累托原则 (Pareto Principle)
- 优先优化高频路径，如报告生成中的数据聚合（80%的性能问题可能来自20%的代码）。
- 聚焦于 admin-dashboard 中最常用的组件，如会话列表的渲染优化。

### 墨菲定律 (Murphy's Law)
- 在所有服务中实现全面错误处理，例如在网络请求中添加重试机制和降级处理。
- 对于数据库操作，使用事务确保数据一致性。

## UI/UX 原则

### 菲茨定律 (Fitts's Law)
- 在 admin-dashboard 中，将常用按钮（如"启动录制"）置于易达位置，并确保按钮大小至少 48x48px。
- 对于移动端适配，确保关键交互元素靠近屏幕底部。

### 希克定律 (Hick's Law)
- 简化导航菜单，限制选项数量；例如，会话管理页面只显示核心动作（启动、停止、报告）。
- 使用渐进式披露，仅在需要时显示高级选项。

### 雅各布定律 (Jakob's Law)
- 采用熟悉的 UI 模式，如使用标准表格组件显示会话列表，类似于常见 dashboard 设计。

### UI 设计规则
- 设计高保真原型时，使用 Tailwind CSS 和 FontAwesome 增强真实感。
- 限制页面数量至核心界面，如首页、会话管理、报告查看。

## 代码结构和维护原则

### 童子军规则 (Boy Scout Rule)
- 每次修改代码时，进行小幅改进，如重命名变量或添加注释；在 live_report_service.py 中应用。

### 切斯特顿围栏 (Chesterton's Fence)
- 修改遗留代码前，调查原因；例如，理解现有数据库结构的理由前勿移除字段。

### 康威定律 (Conway's Law)
- 代码结构应反映团队组织，例如 services 目录对应后端服务团队的责任分工。

### 加尔定律 (Gall's Law)
- 从简单 MVP 开始迭代，例如先实现基本直播录制，再添加 AI 转写。

### 汉隆剃刀 (Hanlon's Razor)
- 在代码审查中，假设问题是由于疏忽而非恶意，提供建设性反馈。

### 霍夫施塔特定律 (Hofstadter's Law)
- 时间估算时添加缓冲，例如为报告生成任务预留 50% 额外时间。

### 帕金森定律 (Parkinson's Law)
- 设定紧凑截止日期，如为新功能开发设置 4 小时时间盒。

### 奥卡姆剃刀 (Occam's Razor)
- 优先简单解决方案，例如使用基本循环而非复杂框架处理数据。

## 其他原则

### 坎宁安定律 (Cunningham's Law)
- 在技术讨论中，使用"故意错误"激发正确反馈，但仅限于非生产代码。

### 数据模型创建
- 在 models 目录下，设计数据模型时使用 Mermaid 类图，确保字段类型映射正确，并考虑项目特定场景如直播会话数据。

### 鸭子类型 (Duck Typing)
- 在 Python 服务中，使用鸭子类型设计接口，例如统一处理不同数据源的处理器。

### Web 开发规则
- 使用 Vite 构建前端，确保相对路径配置；本地预览使用 npx live-server。

通过应用这些规则，确保项目代码简洁、可维护，并适应直播管理需求。