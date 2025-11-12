# DouyinLiveWebFetcher 模块解析与改造指引

> 目标：帮助快速理解 `DouyinLiveWebFetcher` 的实现细节，并给出在提猫直播助手中二次封装与扩展的建议。

## 1. 模块概览
- **核心入口**：`DouyinLiveWebFetcher/liveMan.py` 定义 `DouyinLiveWebFetcher` 类，负责获取直播间凭据、建立 WebSocket 连接、解析抖音弹幕消息。
- **示例脚本**：`DouyinLiveWebFetcher/main.py` 通过 CLI/交互式输入 `live_id`，触发状态检查与抓取启动。
- **辅助资源**：
  - `ac_signature.py`：计算 `__ac_signature`，绕过抖音风控参数校验。
  - `a_bogus.js`、`sign.js`：通过嵌入式 JS 环境计算 `a_bogus` 和 WebSocket `signature`。
  - `protobuf/douyin.py`：基于 `betterproto` 自动生成的消息模型，用于解析压缩后的二进制负载。

## 2. 运行时依赖与外部接口
- **Python 依赖**：`requests`、`websocket-client`、`py_mini_racer`、`execjs`、`betterproto`。
- **JS 运行环境**：MiniRacer/Node.js 用于执行签名脚本；若算法升级，仅需替换同名 JS 文件。
- **网络交互**：
  1. `https://live.douyin.com/` 拉取 `ttwid` 等 Cookie。
  2. `https://live.douyin.com/{live_id}` 抓取 `roomId`。
  3. `webcast/room/web/enter` REST 接口确认房间状态。
  4. `wss://webcast100-ws-web-lq.douyin.com/...` 建立 WebSocket 获取实时消息。

## 3. 启动流程（握手顺序）
1. **实例化**：保存用户输入的 `live_id`，初始化 `requests.Session` 与默认 UA。
2. **获取 Cookie**：访问主页读取 `ttwid`（`DouyinLiveWebFetcher.ttwid` 属性）。
3. **解析真实 `room_id`**：请求直播间页面，组合 `ttwid + msToken + __ac_nonce`。
4. **生成风控参数**：
   - `get_ac_nonce()` 访问首页拿 `__ac_nonce`。
   - `get_ac_signature()` 使用 `ac_signature.py` 计算签名。
   - `get_a_bogus()` 载入 `a_bogus.js` 生成 query 级别校验参数。
5. **检查房间状态**：`get_room_status()` 调用 REST 接口，附带 `a_bogus` 与 Cookie。
6. **准备 WebSocket URL**：拼装连接串后，调用 `generateSignature()` 执行 `sign.js` 获取 `signature`。
7. **启动 WebSocket**：`websocket.WebSocketApp` 注册回调，`start()` -> `_connectWebSocket()`。
8. **心跳与 ACK**：
   - `_sendHeartbeat()`：每 5 秒发送 `PushFrame` ping。
   - `_wsOnMessage()`：收到 `Response` 后判断 `need_ack` 并回写确认帧。

## 4. 消息解析与分发
- `_wsOnMessage()` 解压 GZip 负载，使用 `protobuf/douyin.py` 中的 `PushFrame`、`Response`、`Message` 等模型进行结构化解析。
- 通过方法字典将 `msg.method` 映射到对应处理器：
  - 聊天：`_parseChatMsg`
  - 礼物：`_parseGiftMsg`
  - 点赞：`_parseLikeMsg`
  - 进场：`_parseMemberMsg`
  - 关注、粉丝团、房间状态、统计等均有专门解析函数。
- 当前实现直接 `print()`，适合调试；在生产环境应改为发布事件或写入队列。

## 5. 可扩展的设计点
- **分层包装**：在 `server/` 或 `douyin_live_fecter_module/` 下编写自定义 API 层（参见 `tests/test_douyin_api.py` 设想），将 `DouyinLiveWebFetcher` 作为底层适配器。
- **事件分发**：
  1. 在 `_wsOnMessage()` 中引入 `callback`/`asyncio.Queue` 将结构化消息抛出。
  2. 使用枚举 `MessageType` 与数据类封装统一对象，便于下游（AI、存储）消费。
- **重连策略**：包装 `_connectWebSocket()`，在 `_wsOnError/_wsOnClose` 内触发指数退避重连，结合 `RoomStateManager` 更新状态。
- **配置注入**：将 UA、心跳间隔、签名脚本路径通过 `ConfigManager` 管理，支持灰度调整。
- **A/B 模拟与回放**：保留原始二进制帧或 JSON 结构，写入 `tests/fixtures/`，为离线调试和 `pytest` 回放提供数据源。

## 6. 典型改造方案
### 6.1 将 print 输出替换为标准事件
```python
# server/nlp/douyin_stream.py (示例)
from queue import Queue
from server.modules.douyin.liveMan import DouyinLiveWebFetcher

class StreamingFetcher(DouyinLiveWebFetcher):
    def __init__(self, live_id, event_queue: Queue):
        super().__init__(live_id)
        self.events = event_queue

    def _publish(self, kind, payload):
        self.events.put({"type": kind, "payload": payload, "ts": time.time()})

    def _parseChatMsg(self, payload):
        message = ChatMessage().parse(payload)
        self._publish("chat", {
            "user_id": message.user.id,
            "nickname": message.user.nick_name,
            "content": message.content,
        })
```
- 新增 `_publish` 将消息写入线程安全队列。
- 其他解析函数可复用同一发布机制，减少重复代码。

### 6.2 引入异步封装
```python
# server/ingest/douyin/fetcher.py
class AsyncFetcher:
    def __init__(self, live_id):
        self.loop = asyncio.get_event_loop()
        self.fetcher = DouyinLiveWebFetcher(live_id)

    async def start(self):
        await self.loop.run_in_executor(None, self.fetcher.start)
```
- 利用线程池把同步 WebSocket 客户端嵌入 FastAPI/Flask 事件循环。
- 在停止时调用 `self.fetcher.stop()` 并回收线程。

### 6.3 抽象参数生成策略
- 将 `generateSignature`、`get_a_bogus`、`get_ac_signature` 封装为策略对象：
  ```python
  class SignatureProvider:
      def __init__(self, abogus_js, sign_js):
          self.abogus_js = abogus_js
          self.sign_js = sign_js
      def a_bogus(self, params): ...
      def signature(self, wss_url): ...
  ```
- 方便在 API 更新时替换脚本或接入远程签名服务。

## 7. 版本升级与问题排查
- **脚本失效**：当抖音风控逻辑更新，优先替换 `a_bogus.js` / `sign.js`；如 MiniRacer 报错，确认 Node 版本或改用 `execjs`。
- **房间号解析失败**：检查正则 `roomId": "(\d+)"`，必要时改成基于 `json.loads` 解析页面内的 `render_data`。
- **WebSocket 403/签名错误**：确认 UA、`signature`、`ttwid`、`msToken` 是否同步更新；尝试重新获取 `__ac_nonce`。
- **消息解码异常**：更新 `protobuf/douyin.proto` 后重新生成 `douyin.py` (`betterproto`)，确保与线上字段一致。

## 8. 测试建议
- 使用 `pytest` 录制的离线帧验证消息解析，覆盖常见消息类型。
- 在 CI 中运行 `tests/test_douyin_api.py` 计划中的高级封装测试，确保事件管道、缓存、状态管理兼容。
- 对关键改造点添加集成测试，模拟断线重连、签名异常、消息溢出等边界场景。

---
通过以上拆解，可以在保持原始抓取能力的前提下，将 `DouyinLiveWebFetcher` 平滑接入 Electron+FastAPI 的项目结构，并为后续 NLP、AI 分析模块提供稳定的数据输入。
