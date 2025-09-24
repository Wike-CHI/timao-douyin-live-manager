# 在腾讯云开发托管 SenseVoice 并自动训练调优实施指南

本文给出一条可落地的路径：将 SenseVoice（基于 FunASR）部署到腾讯云开发（CloudBase/云托管或 TKE/CVM），通过 Electron 端采集主播音频（WS/socket 流式推送），把转写结果与音频分片落 COS，并用 TKE/TI-ONE 做离线微调，最后灰度发布新模型。

结论：完全可行。云函数（SCF）仅建议作为网关鉴权与计量，不适合直接跑常驻推理。

---

## 1. 架构总览

- 客户端（Electron）
  - 音频采集：优先系统回环录音（WASAPI/AVAudioEngine）；也可基于合法来源的 RTMP/FLV 解复用；抓包仅限合规前提。
  - 传输：WebSocket/HTTP 将 16kHz/16bit/mono PCM（或 Opus 解码后 PCM）分片推到云端。
- 推理服务（在线）
  - CloudBase 云托管容器 或 TKE/CVM：FastAPI + FunASR + SenseVoice 提供 `/ws/stream`、`/api/transcribe`。
  - 可选：Redis/MQ 做会话与限流。
- 网关与鉴权
  - 云函数（SCF）签发短期 Token、计量、路由（外网→内网容器/VPC）。
- 数据与流水线
  - COS 存储原始音频分片与转写结果。
  - （可选）CKafka/TDMQ 作为事件总线。
- 训练与发布（离线）
  - TKE GPU Job 或 TI-ONE：数据清洗→伪标过滤→微调→评测。
  - 推理镜像灰度发布（云托管滚动/比例放量），异常自动回滚。

---

## 2. 部署选型与准备

- 云函数（SCF）：不适合大模型推理（冷启动、时长/内存限制、无 GPU），只做网关/鉴权/计费。
- 云托管（CloudBase 容器）：适合常驻推理（CPU/小模型可用）；如需 GPU，优先 TKE/CVM。
- GPU：在线推理建议 GPU；小模型或量化后可 CPU。离线训练必需 GPU。
- 准备项：
  - TCR（镜像仓库），COS（对象存储），CLS（日志），（可选）CKafka/TDMQ。
  - 自定义域名/证书/内网访问策略，VPC 配置。

---

## 3. 推理服务容器化

Dockerfile（示例，按需换基础镜像/版本）：

```Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y python3-pip ffmpeg git && rm -rf /var/lib/apt/lists/*

# FunASR / FastAPI / 推理依赖
RUN pip3 install --no-cache-dir fastapi uvicorn[standard] websockets soundfile numpy torch torchaudio funasr==1.1.3

WORKDIR /app
COPY server /app/server

EXPOSE 8000
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
FastAPI 端点（server/app/main.py）：

python

# server/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional
from server.ai.sensevoice_service import SenseVoiceEngine

app = FastAPI()
engine = SenseVoiceEngine(model_name="sensevoice_small")  # 按需替换

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/transcribe")
async def transcribe(file_path: Optional[str] = None):
    # 支持 COS 临时 URL 或容器内本地路径
    text = await engine.transcribe_file(file_path)
    return JSONResponse({"text": text})

@app.websocket("/ws/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    session = engine.start_stream()
    try:
        while True:
            # 约定客户端发送 16kHz/16bit/mono PCM 二进制帧（100~200ms/帧）
            data = await ws.receive_bytes()
            partial = session.feed_pcm(data)  # 返回增量结果字符串或空
            if partial:
                await ws.send_json({"partial": partial})
    except WebSocketDisconnect:
        final = session.finish()
        await ws.close(code=1000)
    except Exception as e:
        await ws.close(code=1011, reason=str(e))
SenseVoice 封装（server/ai/sensevoice_service.py）：

python

# server/ai/sensevoice_service.py
from funasr import AutoModel
from server.utils.logger import get_logger  # 复用你项目的 logger
from server.utils.ring_buffer import RingBuffer  # 作为流式缓存

log = get_logger(__name__)

class SenseVoiceEngine:
    def __init__(self, model_name="sensevoice_small", device="cuda"):
        # TODO: 按实际可用的 SenseVoice/FunASR 模型名与配置调整
        self.model = AutoModel(model=model_name, device=device)

    async def transcribe_file(self, path_or_url: str) -> str:
        # TODO: 如果是 COS URL，先下载到本地临时文件再送入
        result = self.model.generate(input=path_or_url)
        return result.get("text", "")

    def start_stream(self):
        return _StreamSession(self.model)

class _StreamSession:
    def __init__(self, model):
        self.model = model
        self.buf = RingBuffer(max_bytes=16000 * 2 * 30)  # 约 30s 16k/16bit 单声道
        # TODO: 初始化前端特征/VAD/增量解码器

    def feed_pcm(self, chunk: bytes) -> str:
        self.buf.write(chunk)
        # TODO: 将 PCM 转特征，调用流式接口，返回 partial（空字符串表示无更新）
        return ""

    def finish(self) -> str:
        # TODO: flush 缓存，返回最终结果
        return ""
要点：

模型缓存与预热：镜像构建或容器启动时预下载权重到持久卷，缩短首开。
健康探针：/api/health 就绪后才接流量。
日志：统一走 server/utils/logger，便于 CLS 聚合。
4. 在 CloudBase 云托管/TKE 部署
推镜像到 TCR：构建→docker push 到 TCR。
云托管（推荐起步）
新建服务，选择“从镜像部署”，填写 TCR 镜像地址。
配置环境变量（如 MODEL_DIR=/models、COS 访问、鉴权开关）。
健康检查指向 /api/health；设置实例数与弹性策略。
绑定域名或内网服务发现；若经 SCF 网关，网关内网访问容器。
GPU 需求时
使用 TKE（GPU 节点）或 CVM GPU 自建服务，CLB/Ingress 暴露入口。
流程基本一致（镜像、部署、探针、伸缩）。
5. 客户端（Electron）接入
优先级与稳定性（从高到低）：

系统回环录音（合规、稳）：Win 用 WASAPI loopback；Mac 用 AVAudioEngine。
合法播放源的 RTMP/FLV 解复用（抽音轨→重采样 16k PCM）。
抓包（合规前提下）：对抗性强，不推荐长期依赖。
WebSocket 最小客户端（electron/renderer/src/services/asr.ts）：

ts

export class ASRClient {
  private ws?: WebSocket;
  private url: string;
  constructor(url: string) { this.url = url; }

  connect(onPartial: (t: string) => void) {
    this.ws = new WebSocket(this.url);
    this.ws.binaryType = "arraybuffer";
    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data as string);
        if (msg.partial) onPartial(msg.partial);
      } catch {}
    };
  }

  sendPcm(chunk: ArrayBuffer) {
    this.ws?.readyState === this.ws?.OPEN && this.ws.send(chunk);
  }

  close() { this.ws?.close(); }
}
集成建议：

在 LiveConsolePage.tsx 订阅增量转写并显示。
遇到网路抖动：本地环形缓冲区暂存，恢复后补传。
统一鉴权：通过 cloudfunctions/userAuth 获取短期 JWT，WS 连接时附带 Authorization 头或 ?token=。
音频参数：

采样率 16kHz，16-bit，单声道 PCM（LE）；建议 100~200ms/帧。
6. 数据落地与自动训练
COS 目录结构（示例）：

原始音频：cos://bucket/raw/{anchor_id}/{ts}/{segment_id}.wav
转写结果：cos://bucket/asr/{anchor_id}/{ts}.jsonl（一行一条分片结果，含时间戳/置信度）
样本构建与过滤：

起步阶段用在线推理作为伪标，基于置信度、稳定度、重复率过滤。
引入少量人工校对集提升质量。
训练与发布（TKE/TI-ONE）：

数据准备：VAD/切分→文本清洗（全半角、标点、繁简、脏词）→生成训练/验证清单。
微调：加载 SenseVoice 预训练权重，小学习率（如 1e-53e-5）、13 epoch，必要时冻结前端。
指标：CER/WER、RTF、延迟；输出报告至 CLS/告警。
发布：打包新权重→构建推理镜像→推送 TCR→云托管灰度（5%→50%→100%）。
回滚：异常阈值触发自动回滚上一版本。
触发与编排：

云函数或云托管定时任务：当某主播新增高质量时长达阈值（如 ≥3h），触发训练 Job。
状态写入 COS 标记文件或元数据表，便于可观测与审计。
7. 鉴权与计费（可选）
cloudfunctions/userAuth：签发短期 JWT/STS；前端连接 WS 时带 Authorization: Bearer <token> 或 ?token=...。
推理服务：校验 Token 与配额（用户/主播维度），超限拒绝或排队。
计量：在云函数或服务端记录调用时长/帧数，结合 paymentService 做结算。
8. 监控与运维
CLS：收集 FastAPI/模型日志与调用链；关键指标（RTF、延迟、错误率、OOM）。
健康检查：liveness/readiness 探针，避免未就绪接流量。
伸缩：根据 CPU/GPU 利用率与队列长度弹性扩缩。
配置：模型版本通过环境变量注入并上报，便于灰度观测。
9. 合规与风险
抓包与录音需取得主播授权并符合平台条款与当地法规。
敏感信息脱敏，按地区合规落 COS，设置保留周期与删除机制。
遵循 SenseVoice/FunASR 开源协议；镜像中避免携带私钥/私有权重。
10. 最小可用闭环（建议先跑通）
在仓库新增：
server/app/main.py：HTTP 与 WS 端点
server/ai/sensevoice_service.py：模型封装（流式接口可先留空）
本地用 uvicorn server.app.main:app --reload --port 8000 自测 /api/health。
构建推理镜像→推送 TCR→云托管部署并打通公网或内网访问。
Electron 侧用回环录音采集 16k PCM，通过 WS 推流，页面显示增量转写（LiveConsolePage.tsx）。
将音频与转写落 COS；定时任务汇总高置信度数据，手动触发一次 TKE Job 微调并灰度回滚验证。
11. API 约定与样例
HTTP
POST /api/transcribe body：{ "file_path": "<cos_url_or_local_path>" }
响应：{ "text": "..." }
WebSocket
地址：wss://<asr-domain>/ws/stream?token=<jwt>
入站：二进制 PCM 帧（16k/16bit/mono，100~200ms/帧）
出站：{ "partial": "<增量文本>" }（多次），关闭时客户端可等待最终文本或由服务端另发 { "final": "..." }
错误
业务错误通过 WS close code 1011/原因传递；HTTP 返回 4xx/5xx。
12. 与当前仓库的落点
新增服务端：
server/app/main.py
server/ai/sensevoice_service.py
复用与规范：
server/utils/ring_buffer.py 用于流式缓存
server/utils/logger 做统一日志
前端/Electron：
新增 electron/renderer/src/services/asr.ts（WS 客户端）
在 electron/renderer/src/pages/dashboard/LiveConsolePage.tsx 接入显示
测试（按项目规范）：
Python：server/tests/test_asr_api.py 覆盖 REST/WS
前端：electron/__tests__/asr.spec.js，对 WS 客户端做桩测试
13. 常见问题（FAQ）
Q：CloudBase 是否支持 GPU？
A：以区域与套餐为准；若不可用，转用 TKE/CVM + CLB/Ingress 暴露服务。
Q：为什么不用云函数直接跑推理？
A：冷启动、时长内存限制、无 GPU；只推荐做网关/鉴权。
Q：延迟目标与优化？
A：端到端 < 800ms；预热、量化、小模型、批大小=1、合适分片（100-200ms）、前端缓存与 VAD。
```
