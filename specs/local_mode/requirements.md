# 本地化模式需求文档

## 文档信息
- **版本**：v1.3
- **审查人**：叶维哲
- **创建日期**：2025-01-25
- **更新日期**：2025-11-25
- **状态**：待确认

---

## 介绍

本需求旨在将抖音直播管理系统改造为纯本地化运行模式，移除所有外部数据库依赖（MySQL、Redis），实现：
1. 用户可自行配置AI服务的API Key
2. 所有数据采用本地JSON文件存储
3. 无需登录，直接使用
4. 移除SenseVoice内存占用检查
5. 绕过订阅/付费机制，所有功能免费使用
6. 自动下载SenseVoice语音识别模型
7. 自动配置FFMPEG音视频工具
8. 交付完整源码给甲方

**设计原则**：奥卡姆剃刀 - 如无必要，勿增实体

---

## 需求清单

### 需求 1 - AI服务配置界面（初次启动向导）

**用户故事**：作为用户，我希望在初次启动应用时能够配置AI服务的API Key，以便使用AI分析功能。

#### 功能描述
新建一个独立的AI配置页面，在初次启动应用时引导用户配置AI服务。支持以下AI服务商：
- 通义千问（Qwen）
- 讯飞星火（Xunfei）
- DeepSeek
- 字节豆包（Doubao）
- 智谱ChatGLM（GLM）
- Google Gemini（通过AiHubMix）

#### 验收标准

1. **AC1.1** - When 应用初次启动且 `data/ai_config.json` 不存在或为空时，the 系统 shall 自动跳转到AI配置向导页面。

2. **AC1.2** - When 用户进入AI配置页面时，the 系统 shall 显示所有支持的AI服务商列表，每个服务商显示：服务商名称、当前状态（已配置/未配置）、配置按钮。

3. **AC1.3** - When 用户点击某个服务商的"配置"按钮时，the 系统 shall 弹出配置对话框，包含以下输入项：
   - API Key（密码输入框，支持显示/隐藏切换）
   - Base URL（可选，有默认值）
   - 默认模型（下拉选择，根据服务商提供可选模型列表）

4. **AC1.4** - When 用户填写配置并点击"保存"时，the 系统 shall 将配置直接保存到本地 `data/ai_config.json` 文件中（明文存储，简化实现）。

5. **AC1.5** - When 用户点击"测试连接"时，the 系统 shall 使用当前配置发送一个简单的测试请求，并显示测试结果（成功/失败及原因）。

6. **AC1.6** - When 用户完成至少一个服务商配置后点击"完成配置"时，the 系统 shall 跳转到主界面。

---

### 需求 2 - AI功能模型配置

**用户故事**：作为用户，我希望能够为不同的AI功能（实时分析、风格画像、话术生成、复盘总结）指定使用的服务商和模型，以便灵活控制AI调用。

#### 功能描述
提供功能级别的AI模型配置，让用户可以为每个AI功能指定使用的服务商和模型。

#### 验收标准

1. **AC2.1** - When 用户进入"AI功能配置"页面时，the 系统 shall 显示以下功能列表：
   - 实时分析（live_analysis）
   - 风格画像（style_profile）
   - 话术生成（script_generation）
   - 复盘总结（live_review）
   - 聊天焦点摘要（chat_focus）
   - 智能话题生成（topic_generation）

2. **AC2.2** - When 用户为某功能选择服务商和模型时，the 系统 shall 只显示已配置API Key的服务商供选择。

3. **AC2.3** - When 用户保存功能配置时，the 系统 shall 将配置保存到本地 `data/ai_config.json` 的 `function_models` 字段中。

4. **AC2.4** - While AI服务商未配置或不可用时，when 调用该功能时，the 系统 shall 显示友好的错误提示，建议用户先配置AI服务。

---

### 需求 3 - 本地化数据存储

**用户故事**：作为甲方，我希望系统不依赖MySQL和Redis，所有数据都存储在本地，以便于部署和维护。

#### 功能描述
将所有数据存储改为本地JSON文件，完全移除MySQL和Redis依赖。

#### 验收标准

1. **AC3.1** - When 系统启动时，the 系统 shall 不尝试连接MySQL或Redis，而是直接使用本地文件存储。

2. **AC3.2** - When 需要存储直播会话数据时，the 系统 shall 将数据保存到 `data/sessions/` 目录下，每个会话一个JSON文件。

3. **AC3.3** - When 需要存储AI使用统计时，the 系统 shall 将数据保存到 `data/ai_usage.json`。

4. **AC3.4** - When 需要存储弹幕数据时，the 系统 shall 将数据保存到 `data/sessions/{session_id}/danmaku.json`。

5. **AC3.5** - When 需要存储转写数据时，the 系统 shall 将数据保存到 `data/sessions/{session_id}/transcript.json`。

6. **AC3.6** - The 系统 shall 完全移除 `requirements.txt` 中的 `redis`、`mysql-connector-python`、`PyMySQL`、`SQLAlchemy` 等数据库依赖。

---

### 需求 4 - 移除登录验证

**用户故事**：作为本地用户，我希望无需登录即可使用系统所有功能。

#### 功能描述
完全移除JWT认证和用户系统，简化为纯本地应用。

#### 验收标准

1. **AC4.1** - When 用户访问任何API时，the 系统 shall 不检查Authorization头，允许无token访问。

2. **AC4.2** - When 用户打开应用时，the 系统 shall 直接进入主界面（或AI配置向导，如果是初次启动）。

3. **AC4.3** - The 系统 shall 移除所有JWT相关的依赖注入（`get_current_user`、`optional_auth`等）。

4. **AC4.4** - The 系统 shall 移除前端的登录页面和登录状态检查。

---

### 需求 5 - 移除SenseVoice内存检查

**用户故事**：作为开发者，我希望移除SenseVoice的内存占用检查，避免不必要的警告日志。

#### 功能描述
完全移除 `sensevoice_service.py` 中的内存监控代码。

#### 验收标准

1. **AC5.1** - The 系统 shall 移除 `_transcribe_with_lock` 方法中的内存检查代码块（第377-407行）。

2. **AC5.2** - The 系统 shall 保留 `_call_count` 计数器用于调试，但不再进行内存检查。

3. **AC5.3** - When 转写音频时，the 系统 shall 不输出内存相关的警告日志。

---

### 需求 6 - AI生成失败问题修复

**用户故事**：作为用户，当AI服务商账户欠费或配置错误时，我希望看到清晰的错误提示，而不是"生成失败，请稍后重试"。

#### 功能描述
改进AI调用的错误处理和提示。

#### 验收标准

1. **AC6.1** - When AI服务返回"Arrearage"（欠费）错误时，the 系统 shall 显示"AI服务账户欠费，请充值后重试或切换其他服务商"。

2. **AC6.2** - When AI服务返回401/403错误时，the 系统 shall 显示"API Key无效或已过期，请检查配置"。

3. **AC6.3** - When AI服务返回429错误（限流）时，the 系统 shall 显示"请求过于频繁，请稍后重试"。

4. **AC6.4** - When 所有AI服务都不可用时，the 系统 shall 在界面上明确提示"AI功能暂不可用，请先配置AI服务"。

---

### 需求 7 - 配置文件结构

**用户故事**：作为开发者，我需要明确的配置文件结构来存储AI配置。

#### 功能描述
定义简洁的AI配置文件结构（明文存储，简化实现）。

#### 验收标准

1. **AC7.1** - `data/ai_config.json` 文件结构 shall 符合以下格式：

```json
{
  "providers": {
    "qwen": {
      "api_key": "sk-xxx",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "default_model": "qwen-plus",
      "enabled": true
    },
    "xunfei": {
      "api_key": "xxx",
      "base_url": "https://spark-api-open.xf-yun.com/v1",
      "default_model": "lite",
      "enabled": true
    }
  },
  "function_models": {
    "live_analysis": {
      "provider": "xunfei",
      "model": "lite"
    },
    "style_profile": {
      "provider": "qwen",
      "model": "qwen3-max"
    }
  },
  "active_provider": "xunfei",
  "initialized": true
}
```

2. **AC7.2** - When 配置文件不存在或 `initialized` 为 false 时，the 系统 shall 显示AI配置向导页面。

---

### 需求 8 - 绕过订阅机制

**用户故事**：作为本地用户，我希望无需订阅付费即可使用系统所有功能。

#### 功能描述
完全移除订阅/付费验证机制，所有功能默认可用。

#### 验收标准

1. **AC8.1** - When 用户启动应用时，the 系统 shall 自动设置 `isPaid = true`，无需检查订阅状态。

2. **AC8.2** - The 系统 shall 移除前端 `LiveConsolePage.tsx` 和 `DashboardPage.tsx` 中的付费状态检查逻辑。

3. **AC8.3** - The 系统 shall 移除后端 `SubscriptionService.get_usage_stats()` 的调用和相关订阅验证逻辑。

4. **AC8.4** - The 系统 shall 移除订阅相关的API路由 `/api/subscription/*`。

5. **AC8.5** - The 系统 shall 移除订阅相关的数据库模型（`subscription.py`、`payment.py`）。

6. **AC8.6** - The 系统 shall 移除前端的订阅页面 `SubscriptionPage.tsx` 和相关路由。

7. **AC8.7** - When 用户访问任何功能时，the 系统 shall 不显示"请订阅套餐后使用"等付费相关提示。

---

### 需求 9 - 自动下载SenseVoice模型

**用户故事**：作为用户，我希望系统能自动下载语音识别模型，无需手动配置。

#### 功能描述
在初次启动或模型缺失时，自动检测并下载SenseVoice和VAD模型。

#### 验收标准

1. **AC9.1** - When 系统启动时检测到模型目录 `server/modules/models/.cache/models/iic/SenseVoiceSmall` 不存在时，the 系统 shall 自动触发模型下载流程。

2. **AC9.2** - When 模型下载进行中时，the 系统 shall 在初次启动向导页面显示下载进度（当前步骤、进度百分比、预计剩余时间）。

3. **AC9.3** - When 模型下载完成时，the 系统 shall 显示"模型准备就绪"提示。

4. **AC9.4** - When 模型下载失败时，the 系统 shall 显示详细错误信息，并提供以下选项：
   - "重试下载"
   - "跳过（语音功能将不可用）"
   - "手动放置模型"（显示目标路径）

5. **AC9.5** - The 系统 shall 同时下载VAD模型到 `server/modules/models/.cache/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`。

6. **AC9.6** - The 系统 shall 使用现有的 `server/tools/download_sensevoice.py` 和 `server/tools/download_vad_model.py` 脚本进行模型下载。

---

### 需求 10 - 自动配置FFMPEG

**用户故事**：作为用户，我希望系统能自动检测和配置FFMPEG，无需手动安装。

#### 功能描述
在系统启动时自动检测FFMPEG，如未安装则自动下载配置（Windows平台）。

#### 验收标准

1. **AC10.1** - When 系统启动时，the 系统 shall 首先检查系统PATH中是否已安装FFMPEG。

2. **AC10.2** - When 系统PATH中未找到FFMPEG时，the 系统 shall 检查本地目录 `tools/ffmpeg/{platform}/bin/ffmpeg`。

3. **AC10.3** - When 本地目录也未找到FFMPEG且平台为Windows时，the 系统 shall 自动从官方源下载FFMPEG essentials包并解压到 `tools/ffmpeg/win64/bin/`。

4. **AC10.4** - When FFMPEG下载进行中时，the 系统 shall 在初次启动向导页面显示下载进度。

5. **AC10.5** - When FFMPEG下载完成时，the 系统 shall 自动配置环境变量 `FFMPEG_BIN` 指向下载的可执行文件。

6. **AC10.6** - When FFMPEG下载失败或平台为非Windows时，the 系统 shall 显示友好提示，指导用户手动安装FFMPEG：
   - Windows: "请从 https://www.gyan.dev/ffmpeg/builds/ 下载并解压到 tools/ffmpeg/win64/bin/"
   - Mac: "请运行 `brew install ffmpeg`"
   - Linux: "请运行 `apt install ffmpeg` 或 `yum install ffmpeg`"

7. **AC10.7** - The 系统 shall 使用现有的 `server/utils/bootstrap.py` 中的 `ensure_ffmpeg()` 函数进行FFMPEG检测和下载。

---

## 非功能需求

### NFR1 - 兼容性
- 系统应在Windows 10/11上正常运行
- 系统应支持Electron桌面应用模式
- 自动下载功能应支持离线回退（提供手动安装指引）

### NFR2 - 用户体验
- 配置界面应简洁直观
- 错误提示应清晰明了
- 首次使用应有配置向导引导
- 模型和工具下载应有进度显示

---

## 附录

### A. 当前AI服务商配置模板

| 服务商 | Base URL | 默认模型 | 可用模型 |
|--------|----------|----------|----------|
| Qwen | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus | qwen-plus, qwen-turbo, qwen-max, qwen3-max |
| Xunfei | https://spark-api-open.xf-yun.com/v1 | lite | lite, generalv3, generalv3.5, 4.0Ultra |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat | deepseek-chat, deepseek-coder |
| Doubao | https://ark.cn-beijing.volces.com/api/v3 | doubao-pro | doubao-pro, doubao-lite |
| GLM | https://open.bigmodel.cn/api/paas/v4 | glm-4 | glm-4, glm-3-turbo |
| Gemini | https://aihubmix.com/v1 | gemini-2.5-flash-preview-09-2025 | gemini-2.5-flash-preview-09-2025 |

### B. 当前AI功能映射

| 功能标识 | 功能名称 | 推荐服务商 | 推荐模型 |
|----------|----------|------------|----------|
| live_analysis | 实时分析 | xunfei | lite |
| style_profile | 风格画像与氛围分析 | qwen | qwen3-max |
| script_generation | 话术生成 | qwen | qwen3-max |
| live_review | 复盘总结 | gemini | gemini-2.5-flash-preview-09-2025 |
| chat_focus | 聊天焦点摘要 | qwen | qwen3-max |
| topic_generation | 智能话题生成 | qwen | qwen3-max |

---

**请确认以上需求是否完整和准确。确认后我将进入技术方案设计阶段。**

