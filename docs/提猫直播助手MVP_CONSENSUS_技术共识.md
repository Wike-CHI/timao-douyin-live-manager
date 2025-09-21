# 提猫直播助手MVP - 技术共识文档

## 核心技术选型

基于DouyinLiveWebFetcher项目分析和用户需求，最终技术选型：

### 前端技术栈
- **框架**: Electron + Vue.js 3
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **样式**: Tailwind CSS

### 后端技术栈
- **框架**: FastAPI (Python)
- **数据库**: SQLite (本地存储)
- **WebSocket**: FastAPI WebSocket
- **语音识别**: VOSK (离线)

### 数据抓取 - DouyinLiveWebFetcher项目

**选择理由**: 
工具: DouyinLiveWebFetcher (项目内置实现)
- ✅ 纯Python实现，无需额外依赖
- ✅ WebSocket连接稳定
- ✅ 支持实时弹幕抓取
- ✅ 内置反爬虫机制

### 语音识别 - VOSK
**选择理由**:
- ✅ 离线运行，保护隐私
- ✅ 中文支持良好
- ✅ 轻量级，适合桌面应用

## 功能需求确认

### 核心功能
1. **抖音直播弹幕抓取**
   - 实时连接抖音直播间
   - 解析弹幕、礼物、点赞等消息
   - 数据格式化和存储

2. **语音转文字**
   - 实时麦克风音频采集
   - VOSK离线语音识别
   - 识别结果实时显示

3. **数据展示界面**
   - 弹幕实时滚动显示
   - 语音转文字结果显示
   - 基础统计信息

### 验收标准

#### 功能验收
- [ ] DouyinLiveWebFetcher成功连接抖音直播间，实时抓取弹幕 (延迟<3秒)
- [ ] VOSK语音识别准确率 > 85% (中文普通话)
- [ ] 界面响应流畅，无明显卡顿
- [ ] 数据持久化存储正常

#### 技术验收
1. **DouyinLiveWebFetcher集成**：
   - 成功导入DouyinLiveWebFetcher模块
   - 使用内置的WebSocket连接和消息解析
   - 实现弹幕数据的实时获取和处理

2. **VOSK集成**：
   - 成功加载中文语音模型
   - 实时音频流处理
   - 识别结果准确输出

3. **前后端通信**：
   - WebSocket连接稳定
   - 数据传输实时性
   - 错误处理机制

## 技术依赖

### Python依赖
```
fastapi >= 0.104.0
uvicorn >= 0.24.0
websockets >= 12.0
vosk >= 0.3.45
pyaudio >= 0.2.11
requests >= 2.31.0
execjs >= 1.5.1  # DouyinLiveWebFetcher依赖
```

### 风险评估

| 风险项                | 等级 | 应对策略                         |
|---------------------|------|--------------------------------|
| DouyinLiveWebFetcher更新导致API变化 | 中   | 锁定稳定版本，监控更新           |
| VOSK模型文件过大      | 低   | 选择轻量级模型，优化加载         |
| Electron打包体积     | 低   | 优化依赖，使用asar压缩           |
| 抖音平台反爬升级      | 低   | DouyinLiveWebFetcher项目持续维护，社区响应快       |

## 开发约定

### 代码规范
- Python: PEP 8
- JavaScript: ESLint + Prettier
- 组件命名: PascalCase
- 文件命名: kebab-case

### Git工作流
- 主分支: main
- 功能分支: feature/功能名
- 提交信息: type(scope): description

### 测试策略
- 单元测试: pytest (Python) + Jest (JS)
- 集成测试: 手动测试 + 自动化脚本
- 性能测试: 内存占用 + 响应时间

## 技术选型理由总结

### 为什么选择DouyinLiveWebFetcher？
- ✅ DouyinLiveWebFetcher项目成熟可靠，是最佳的抖音数据抓取方案
- ✅ 纯Python实现，集成简单
- ✅ 支持实时WebSocket连接
- ✅ 内置反爬虫机制，稳定性高

### 为什么选择VOSK？
- ✅ 离线运行，无需网络依赖
- ✅ 中文识别效果好
- ✅ 资源占用合理
- ✅ 开源免费，商业友好

### 为什么选择Electron？
- ✅ 跨平台支持
- ✅ 前端技术栈统一
- ✅ 丰富的生态系统
- ✅ 快速开发和部署

## 最终确认

✅ **技术栈确定**: Electron + FastAPI + DouyinLiveWebFetcher + VOSK
✅ **功能范围明确**: 弹幕抓取 + 语音转文字 + 数据展示
✅ **验收标准清晰**: 性能指标和功能要求已量化
✅ **风险可控**: 主要风险已识别并有应对策略

**项目可以开始实施** 🚀
