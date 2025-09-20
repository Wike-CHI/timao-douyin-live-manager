# 提猫直播助手MVP - 系统架构设计

## 整体架构图

```mermaid
graph TB
    subgraph "前端层 - Element UI + HTML"
        A[直播监控面板] --> B[弹幕流展示]
        A --> C[语音转录面板]
        A --> D[AI建议面板]
        B --> E[WebSocket客户端]
        C --> F[录音控件]
        D --> G[建议刷新]
    end
    
    subgraph "WebSocket通信层"
        H[WebSocket服务器] --> I[消息广播]
    end
    
    subgraph "后端服务层 - FastAPI"
        J[API网关] --> K[直播监控服务]
        J --> L[音频处理服务]
        J --> M[AI分析服务]
        K --> N[F2弹幕抓取]
        L --> O[AST语音转录模块]
        O --> P[VOSK中文识别引擎]
        M --> Q[情感分析引擎]
    end
    
    subgraph "数据存储层"
        R[SQLite数据库] --> S[弹幕记录表]
        R --> T[转录记录表]
        R --> U[AI建议表]
    end
    
    subgraph "外部依赖"
        V[抖音直播间] --> W[F2 WebSocket连接]
        X[麦克风音频] --> Y[AST音频采集器]
    end
    
    subgraph "AST_module组件"
        Y --> Z[音频预处理器]
        Z --> AA[VOSK服务管理器]
        AA --> BB[语音识别结果]
    end
    
    E -.->|WebSocket| H
    K --> W
    L --> Y
    N --> W
    O --> Y
    J --> R
    
    style A fill:#FFE6CC
    style N fill:#E6F3FF
    style O fill:#E6FFE6
    style Q fill:#F0E6FF
    style Y fill:#FFE6E6
```

## 系统分层设计

### 1. 前端展示层 (Presentation Layer)

#### 1.1 技术选型
- **基础框架**: HTML5 + CSS3 + 原生JavaScript
- **UI组件库**: Element UI 2.15 (CDN引入)
- **样式风格**: 可爱猫咪主题 + 圆角设计
- **通信方式**: WebSocket + Fetch API

#### 1.2 页面结构
```html
<!DOCTYPE html>
<html>
<head>
    <title>🐱 提猫直播助手</title>
    <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    <script src="https://unpkg.com/vue@2/dist/vue.js"></script>
    <script src="https://unpkg.com/element-ui/lib/index.js"></script>
</head>
<body>
    <div id="app">
        <!-- 主布局组件 -->
    </div>
</body>
</html>
```

#### 1.3 核心组件
```javascript
// 主应用组件
const App = {
    data() {
        return {
            liveRoomId: '',
            isMonitoring: false,
            isRecording: false,
            comments: [],
            transcripts: [],
            suggestions: [],
            stats: {
                commentCount: 0,
                avgSentiment: 0
            }
        }
    },
    
    mounted() {
        this.initWebSocket();
    },
    
    methods: {
        // WebSocket连接管理
        initWebSocket() {
            this.ws = new WebSocket('ws://localhost:8000/ws');
            this.ws.onmessage = this.handleWebSocketMessage;
        },
        
        // 开始监控直播间
        async startMonitoring() {
            const response = await fetch('/api/rooms/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({room_id: this.liveRoomId})
            });
        },
        
        // 开始录音
        async startRecording() {
            const stream = await navigator.mediaDevices.getUserMedia({audio: true});
            this.mediaRecorder = new MediaRecorder(stream);
            // 录音处理逻辑
        }
    }
}
```

### 2. WebSocket通信层

#### 2.1 连接管理
```python
# websocket_manager.py
from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # 移除失效连接
                    self.active_connections[room_id].remove(connection)
```

#### 2.2 消息类型定义
```python
# 消息类型枚举
class MessageType(str, Enum):
    NEW_COMMENT = "new_comment"
    NEW_TRANSCRIPT = "new_transcript" 
    NEW_SUGGESTION = "new_suggestion"
    STATS_UPDATE = "stats_update"
    SYSTEM_STATUS = "system_status"

# 消息格式
class WebSocketMessage(BaseModel):
    type: MessageType
    data: dict
    timestamp: datetime
    room_id: str
```

### 3. 业务服务层 (Service Layer)

#### 3.1 F2弹幕抓取服务
```python
# douyin_service.py
from f2.apps.douyin.handler import DouyinHandler
from f2.apps.douyin.crawler import DouyinWebSocketCrawler
from f2.apps.douyin.utils import TokenManager

class DouyinLiveService:
    """抖音直播服务 - 基于F2项目"""
    
    def __init__(self):
        # F2项目配置
        self.http_kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.douyin.com/",
            },
            "cookie": f"ttwid={TokenManager.gen_ttwid()}; __live_version__=\"1.1.2.6631\";",
        }
        
        # WebSocket回调配置
        self.wss_callbacks = {
            "WebcastChatMessage": self._handle_chat_message,
            "WebcastGiftMessage": self._handle_gift_message,
        }
```

#### 3.2 AST语音转录服务 (新增)
```python
# ast_service.py - 基于AST_module
from AST_module import ASTService, TranscriptionResult, create_ast_config

class LiveTranscriptionService:
    """直播语音转录服务"""
    
    def __init__(self):
        # 创建AST配置
        self.ast_config = create_ast_config(
            model_path="./vosk-api/vosk-model-cn-0.22",
            chunk_duration=1.0,  # 1秒转录间隔
            min_confidence=0.6,  # 置信度阈值
            save_audio=False     # 生产环境不保存音频
        )
        
        # 初始化AST服务
        self.ast_service = ASTService(self.ast_config)
        self.transcription_callbacks = {}
        self.current_session = None
    
    async def start_transcription(self, room_id: str) -> Dict[str, Any]:
        """开始语音转录"""
        try:
            # 初始化AST服务
            if not await self.ast_service.initialize():
                return {"success": False, "error": "AST服务初始化失败"}
            
            # 设置转录回调
            self.ast_service.add_transcription_callback(
                "live_transcription", 
                self._handle_transcription_result
            )
            
            # 开始转录
            if await self.ast_service.start_transcription(room_id):
                self.current_session = room_id
                return {"success": True, "session_id": room_id}
            else:
                return {"success": False, "error": "转录启动失败"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_transcription_result(self, result: TranscriptionResult):
        """处理转录结果"""
        # 广播转录结果到WebSocket客户端
        message = {
            "type": "transcript",
            "data": {
                "text": result.text,
                "confidence": result.confidence,
                "timestamp": result.timestamp,
                "room_id": result.room_id
            }
        }
        
        # 调用外部回调
        for callback in self.transcription_callbacks.values():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback("transcript", message["data"])
                else:
                    callback("transcript", message["data"])
            except Exception as e:
                logging.error(f"转录回调失败: {e}")
```

#### 3.3 AI分析服务
            "WebcastChatMessage": self._handle_chat_message,
            "WebcastGiftMessage": self._handle_gift_message,
            "WebcastLikeMessage": self._handle_like_message,
            "WebcastMemberMessage": self._handle_member_message,
        }
    
    async def start_monitoring(self, live_id: str) -> Dict[str, Any]:
        """开始监控直播间"""
        # 1. 获取游客信息
        user = await DouyinHandler(self.http_kwargs).fetch_query_user()
        
        # 2. 获取直播间信息
        room = await DouyinHandler(self.http_kwargs).fetch_user_live_videos(live_id)
        
        # 3. 检查直播状态
        if room.live_status != 2:
            raise Exception("直播间未开播")
        
        # 4. 获取WebSocket连接信息
        live_im = await DouyinHandler(self.http_kwargs).fetch_live_im(
            room_id=room.room_id,
            unique_id=user.user_unique_id
        )
        
        # 5. 开始WebSocket监控
        await DouyinHandler(self.wss_kwargs).fetch_live_danmaku(
            room_id=room.room_id,
            user_unique_id=user.user_unique_id,
            internal_ext=live_im.internal_ext,
            cursor=live_im.cursor,
            wss_callbacks=self.wss_callbacks,
        )
    
    async def _handle_chat_message(self, message):
        """处理聊天消息"""
        chat_data = {
            "type": "chat",
            "id": str(message.msgId),
            "username": message.user.nickName,
            "content": message.content,
            "user_level": getattr(message.user, 'level', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        # 存储到数据库并推送
        await self.save_and_broadcast(chat_data)
```

#### 3.2 VOSK语音转录服务
```python
# vosk_service.py
import sys
from pathlib import Path

# 导入本地VOSK模块
VOSK_PATH = Path(__file__).parent.parent.parent / "vosk-api" / "python"
sys.path.insert(0, str(VOSK_PATH))

from vosk import Model, KaldiRecognizer

class VoskService:
    """VOSK语音转录服务 - 基于本地中文模型"""
    
    def __init__(self, model_path: Optional[str] = None):
        # 使用项目中的中文模型
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.recognizer = None
        self.sample_rate = 16000  # VOSK推荐采样率
        self.is_initialized = False
    
    def _get_default_model_path(self) -> str:
        """获取默认中文模型路径"""
        current_dir = Path(__file__).parent.parent.parent
        model_path = current_dir / "vosk-api" / "vosk-model-cn-0.22"
        
        if not model_path.exists():
            raise FileNotFoundError(f"VOSK中文模型未找到: {model_path}")
            
        return str(model_path)
    
    async def initialize(self) -> bool:
        """异步初始化VOSK模型"""
        try:
            # 在线程池中加载模型(避免阻塞)
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, lambda: Model(self.model_path)
            )
            
            # 创建识别器
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # 启用词级时间戳
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"VOSK模型加载失败: {e}")
            return False
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """转录音频数据"""
        if not self.is_initialized:
            raise RuntimeError("VOSK服务未初始化")
        
        try:
            # 处理音频数据
            if self.recognizer.AcceptWaveform(audio_data):
                # 完整识别结果
                result = json.loads(self.recognizer.Result())
                return {
                    "success": True,
                    "type": "final",
                    "text": result.get("text", ""),
                    "confidence": self._calculate_confidence(result),
                    "words": result.get("result", []),
                    "timestamp": time.time()
                }
            else:
                # 部分识别结果
                partial = json.loads(self.recognizer.PartialResult())
                return {
                    "success": True,
                    "type": "partial",
                    "text": partial.get("partial", ""),
                    "confidence": 0.5,
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def _calculate_confidence(self, result: Dict) -> float:
        """计算识别置信度"""
        if not result.get("result"):
            return 0.0
            
        words = result["result"]
        if not words:
            return 0.0
            
        # 计算平均置信度
        confidences = [word.get("conf", 0.0) for word in words]
        return sum(confidences) / len(confidences)
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_path": self.model_path,
            "sample_rate": self.sample_rate,
            "is_initialized": self.is_initialized,
            "model_type": "vosk-model-cn-0.22",
            "language": "zh-CN"
        }
```

#### 3.3 AI分析服务
```python
# ai_service.py
import jieba
from snownlp import SnowNLP
from collections import Counter
from typing import List, Dict

class AIAnalysisService:
    def __init__(self):
        # 加载停用词
        self.stopwords = self.load_stopwords()
        # 初始化情感分析
        self.sentiment_analyzer = SnowNLP
    
    async def analyze_comments(self, comments: List[str]) -> Dict:
        """分析评论数据"""
        if not comments:
            return {"hot_words": [], "sentiment": 0.5, "suggestions": []}
        
        # 提取热词
        hot_words = self.extract_hot_words(comments)
        
        # 情感分析
        sentiment_score = self.analyze_sentiment(comments)
        
        # 生成建议
        suggestions = self.generate_suggestions(hot_words, sentiment_score)
        
        return {
            "hot_words": hot_words[:10],  # 前10个热词
            "sentiment": sentiment_score,
            "suggestions": suggestions
        }
    
    def extract_hot_words(self, comments: List[str]) -> List[Dict]:
        """提取热词"""
        all_words = []
        
        for comment in comments:
            words = jieba.cut(comment)
            filtered_words = [
                word for word in words 
                if len(word) > 1 and word not in self.stopwords
            ]
            all_words.extend(filtered_words)
        
        word_count = Counter(all_words)
        
        return [
            {"word": word, "count": count, "score": count/len(comments)}
            for word, count in word_count.most_common(20)
        ]
    
    def analyze_sentiment(self, comments: List[str]) -> float:
        """分析情感倾向"""
        if not comments:
            return 0.5
            
        sentiments = []
        for comment in comments:
            s = SnowNLP(comment)
            sentiments.append(s.sentiments)
        
        return sum(sentiments) / len(sentiments)
    
    def generate_suggestions(self, hot_words: List[Dict], sentiment: float) -> List[str]:
        """生成AI建议"""
        suggestions = []
        
        # 基于热词生成建议
        top_words = [w['word'] for w in hot_words[:3]]
        if top_words:
            suggestions.append(f"观众关注：{', '.join(top_words)}，建议重点介绍")
        
        # 基于情感生成建议
        if sentiment > 0.7:
            suggestions.append("观众情绪很积极！保持当前互动风格")
        elif sentiment < 0.3:
            suggestions.append("观众情绪偏低，建议增加互动或调整内容")
        else:
            suggestions.append("观众情绪平稳，可以适当增加一些互动环节")
        
        # 通用建议
        suggestions.append("记得提醒观众点赞关注哦~")
        
        return suggestions[:3]  # 返回最多3条建议
```

### 核心技术集成说明

#### F2项目集成优势
- ✅ **成熟稳定**: F2项目持续维护，支持最新抖音API
- ✅ **功能完善**: 支持多种消息类型(聊天、礼物、点赞等)
- ✅ **反爬处理**: 已处理抖音平台反爬机制
- ✅ **WebSocket实时**: 原生支持实时弹幕流

#### VOSK本地语音识别优势
- ✅ **本地运行**: 无需网络调用，降低成本
- ✅ **中文优化**: vosk-model-cn-0.22专门中文模型
- ✅ **实时处理**: 支持流式音频实时识别
- ✅ **轻量级**: 模型大小适中，占用资源少

#### 技术架构集成路径
```
项目根目录
├── f2/                    # F2项目(已存在)
│   ├── apps/douyin/        # 抖音应用模块
│   └── ...
├── vosk-api/              # VOSK语音识别(已存在)
│   ├── python/vosk/        # Python API
│   └── vosk-model-cn-0.22/ # 中文模型
└── server/               # MVP应用服务
    ├── app/services/
    │   ├── douyin_service.py  # F2集成服务
    │   └── vosk_service.py    # VOSK集成服务
    └── ...
```

#### 4.1 数据库设计
```sql
-- 弹幕记录表
CREATE TABLE comments (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    username TEXT NOT NULL,
    content TEXT NOT NULL,
    user_level INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    sentiment_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 语音转录表  
CREATE TABLE transcripts (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    text TEXT NOT NULL,
    confidence REAL DEFAULT 0.8,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI建议表
CREATE TABLE suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    type TEXT DEFAULT 'general',
    content TEXT NOT NULL,
    confidence REAL DEFAULT 0.8,
    is_used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 直播间配置表
CREATE TABLE room_configs (
    room_id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL,
    room_name TEXT,
    status TEXT DEFAULT 'inactive',
    config JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.2 数据访问层
```python
# database.py
import aiosqlite
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "timao_mvp.db"):
        self.db_path = db_path
    
    async def init_database(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as db:
            # 执行建表SQL
            await db.executescript(CREATE_TABLES_SQL)
            await db.commit()
    
    async def save_comment(self, comment_data: Dict):
        """保存评论"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO comments (id, room_id, username, content, user_level, sentiment_score) VALUES (?, ?, ?, ?, ?, ?)",
                (comment_data['id'], comment_data['room_id'], comment_data['username'], 
                 comment_data['content'], comment_data.get('user_level', 0), 
                 comment_data.get('sentiment_score'))
            )
            await db.commit()
    
    async def get_recent_comments(self, room_id: str, limit: int = 50) -> List[Dict]:
        """获取最近评论"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM comments WHERE room_id = ? ORDER BY timestamp DESC LIMIT ?",
                (room_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
```

## 接口契约设计

### REST API接口
```python
# API路由定义
from fastapi import FastAPI, WebSocket

app = FastAPI(title="提猫直播助手MVP")

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# 开始监控直播间
@app.post("/api/rooms/{room_id}/start")
async def start_monitoring(room_id: str, live_id: str):
    await douyin_service.start_monitoring(live_id)
    return {"status": "started", "room_id": room_id}

# 停止监控
@app.post("/api/rooms/{room_id}/stop")
async def stop_monitoring(room_id: str):
    await douyin_service.stop_monitoring()
    return {"status": "stopped", "room_id": room_id}

# 获取最近评论
@app.get("/api/comments/{room_id}")
async def get_comments(room_id: str, limit: int = 20):
    comments = await db_manager.get_recent_comments(room_id, limit)
    return {"comments": comments}

# 获取AI建议
@app.get("/api/suggestions/{room_id}")
async def get_suggestions(room_id: str):
    suggestions = await db_manager.get_recent_suggestions(room_id)
    return {"suggestions": suggestions}

# 上传音频文件
@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile, room_id: str):
    result = await vosk_service.transcribe_audio_stream(await file.read())
    return {"transcript": result}

# WebSocket连接
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket_manager.connect(websocket, room_id)
    try:
        while True:
            await websocket.receive_text()
    except:
        websocket_manager.disconnect(websocket, room_id)
```

## 部署架构

### 开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./vosk-model:/app/vosk-model
    environment:
      - DEBUG=True
      - DATABASE_URL=sqlite:///./timao_mvp.db
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 错误处理策略

#### 1. F2连接错误
- 直播间不存在或未开播
- 网络连接中断
- Cookie失效

#### 2. VOSK转录错误  
- 音频格式不支持
- 模型文件损坏
- 内存不足

#### 3. WebSocket连接错误
- 客户端断开重连
- 服务端重启恢复
- 消息队列溢出处理

---

**架构设计完成**
- ✅ 分层清晰，职责明确
- ✅ 接口定义完整，支持扩展
- ✅ 数据流设计合理，性能可控
- ✅ 错误处理完善，稳定性高
- ✅ 符合MVP快速开发要求

**下一步**：进入任务原子化阶段 (Atomize)