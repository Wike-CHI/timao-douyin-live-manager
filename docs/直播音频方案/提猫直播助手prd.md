提猫直播助手 · 需求对齐（MVP，3天一人版）
目标（MVP 范围）

1. **评论抓取** ：后端采集抖音直播评论（具体适配层可先留接口或用模拟流跑通 UI）。
2. **AI 题词** ：按最近评论聚合→生成 1–2 句可直接说的话术（LLM API）。
3. **基础看板（Electron 桌面端）** ：HTML+CSS（少量JS），三区展示：评论流 / 热词榜 / 题词区；30s 自动刷新题词。
   技术栈与形态

* **桌面端** ：Electron（壳）+ 纯  **HTML + CSS** （少量原生 JS）。
* **后端** ：Python  **Flask** （REST + SSE）
* **数据通道** ：Electron 渲染网页通过 `fetch/SSE` 调用本地 Flask（`http://127.0.0.1:5001`），或 `ipcRenderer` 触发后端启动/停止。
* **AI** ：DeepSeek / OpenAI / 豆包其一（用环境变量切换）。
* **存储** ：内存环形缓冲（最近 200 条评论 / 最近 10 条题词）；无需持久化。
  MVP 成功标准
* 克隆 → `.env` 写 Key 与房间ID → `npm run dev` 一键启动（Electron + Flask）。
* UI 能实时看到评论滚动、Top 热词、最近 3 条题词。
* 评论→题词端到端延迟 ≤ 2s（抓取/网络条件允许的情况下）。
  架构与目录

```
timiao-live-assistant/
  electron/                # Electron 壳（HTML+CSS+少量JS）
    main.js                # 主进程：启动窗口 & 启动Flask子进程
    preload.js             # 预加载（可选：与渲染进程通信）
    renderer/
      index.html           # 三区看板（评论/热词/题词）
      styles.css
      app.js               # 仅负责调用 Flask API/SSE，更新 DOM
  server/                  # Flask 后端
    app.py                 # 路由与SSE
    ingest/                # 评论抓取适配层（可先 mock）
      dy_client.py
    nlp/
      hotwords.py          # 停用词/合并同义/词频
    ai/
      tips.py              # 调 LLM 生成题词（few-shot）
    utils/
      ring_buffer.py
  .env.example
  package.json             # 脚本：启动Electron与Flask
  README.md
```

后端接口（Flask）

* `GET /api/health`：健康检查。
* `GET /api/stream/comments`：**SSE** 推送最新评论（`data: {...}\n\n`）。
* `GET /api/hotwords`：最近 2 分钟热词 Top N（JSON）。
* `GET /api/tips/latest`：最近 3 条题词（JSON）。
* `POST /api/config`：设置房间ID、题词间隔、模型提供商等（JSON）。
  **数据结构**

```
// Comment
{ "id":"c123", "user":"阿强", "text":"有蓝色吗", "ts": 1726800000 }

// HotWord
[{ "word":"价格", "score":0.83 }, { "word":"链接", "score":0.61 }]

// Tip
[{ "text":"问价的多，蓝色款券在小黄车，拍前我教你领～", "ts":1726800030 }]
```

关键流程（数据流）

```
抖音评论抓取(dy_client) → ring_buffer(评论队列)
           ↘ hotwords.py（定时提取 TopN）
             ↘ tips.py（每30s汇总近50条 → LLM→ 1~2句题词）
Flask 提供 /stream/comments (SSE) /hotwords /tips
Electron 渲染页用 fetch/SSE 拉取→更新 DOM
```
