# 开发日志 - 2025-09-22

## 概述

- 建立多主题（紫罗兰 / 猫爪粉）的桌面端 UI 框架，涵盖登录、注册、支付验证与主壳布局。
- 调整 Electron 主进程，使开发模式自动加载 Vite Renderer，生产环境读取 `renderer/dist/index.html`。
- 引入 Zustand 持久化存储登录/付费状态；搭建 `HashRouter` 路由守卫。
- 实现真实接入 SenseVoice 的直播转写面板，通过 FastAPI `/api/live_audio` 接口启动/停止、订阅 WebSocket 实时字幕。

## 主要工作

1. **UI 主题体系**

   - 在 `src/theme/global.css` 定义 `timao-*` 卡片、按钮、输入框等组件风格，对应原型文档的双主题效果。
   - 登录、注册、支付页面整体套用可爱风样式，并复用主题切换组件。
2. **Electron / Vite 联调**

   - 修改 `electron/main.js`：开发环境指向 `http://127.0.0.1:30013`，生产模式加载构建产物，必要时回退旧界面。
   - 更新根 `package.json` 脚本，使用 `concurrently` 启动 Renderer + Electron；新增 `postinstall` 自动安装子项目依赖。
   - Renderer 侧配置 Vite 端口、TypeScript 别名和 Tailwind.
3. **认证与支付流程**

   - 编写登录/注册表单（`mockAuth` 服务暂时支撑），注册成功自动引导登录。
   - 支付验证页实现截图上传模拟审核，更新 `isPaid` 权限后主界面解锁。
   - 积累状态存储，保证刷新后仍保持登录信息。
4. **AST/SenseVoice 集成**

- 新增 `services/liveAudio.ts` 调用 FastAPI `/api/live_audio` Start/Stop/Status + WebSocket，默认基于 `http://127.0.0.1:8007`；支持 `VITE_FASTAPI_URL`。
   - “直播控制台”页面 `LiveConsolePage` 重建：提供 Room ID、启停按钮、实时字幕、日志、统计卡片同步真实服务。

## 尚待事项

- 衔接实际用户认证/支付后端；替换 mock 登录 & 激活逻辑。
- 将 Douyin 弹幕抓取输出接入主界面，与 AST 结果同屏展示。
- 增加错误提示与 SenseVoice 运行状态检测（模型未加载、ffmpeg 不可用等）。
- 规划 ESlint 配置、自动化测试，完善桌面端打包流程。

---

**记录人**: 开发团队
**日期**: 2025-01-20
