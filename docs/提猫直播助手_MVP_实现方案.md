# 提猫直播助手 MVP - 项目结构与实现

## 📁 项目文件结构

```
timao-live-assistant-mvp/
├── frontend/                    # React前端应用
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   │   ├── CommentStream.jsx    # 评论流组件
│   │   │   ├── AIPanel.jsx          # AI建议面板
│   │   │   ├── AudioRecorder.jsx    # 录音组件
│   │   │   └── Dashboard.jsx        # 仪表板
│   │   ├── pages/              # 页面组件
│   │   │   ├── Login.jsx           # 登录页
│   │   │   ├── Home.jsx            # 主页
│   │   │   └── Settings.jsx        # 设置页
│   │   ├── services/           # API服务
│   │   │   ├── api.js              # API封装
│   │   │   └── socket.js           # WebSocket连接
│   │   ├── utils/              # 工具函数
│   │   ├── App.jsx             # 主应用组件
│   │   └── main.jsx            # 入口文件
│   ├── package.json
│   └── vite.config.js
├── server/                      # FastAPI后端
│   ├── app/
│   │   ├── api/                # API路由
│   │   │   ├── auth.py             # 认证相关
│   │   │   ├── rooms.py            # 直播间管理
│   │   │   ├── comments.py         # 评论相关
│   │   │   ├── audio.py            # 音频处理
│   │   │   └── ai.py               # AI分析
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py           # 配置管理
│   │   │   ├── database.py         # 数据库连接
│   │   │   └── security.py         # 安全相关
│   │   ├── models/             # 数据模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── comment.py          # 评论模型
│   │   │   └── suggestion.py       # 建议模型
│   │   ├── services/           # 业务服务
│   │   │   ├── comment_crawler.py  # 评论爬取
│   │   │   ├── audio_service.py    # 音频服务
│   │   │   ├── ai_analyzer.py      # AI分析
│   │   │   └── websocket_manager.py # WebSocket管理
│   │   └── main.py             # 应用入口
│   ├── requirements.txt        # Python依赖
│   └── alembic/               # 数据库迁移
├── docker-compose.yml          # Docker编排
├── Dockerfile                  # Docker构建
├── nginx.conf                  # Nginx配置
├── .env.example               # 环境变量模板
└── README.md                  # 项目说明
```

## 🔧 核心功能实现

### 1. 评论爬取服务

```python
# server/app/services/comment_crawler.py
import asyncio
import random
import time
from datetime import datetime
from typing import AsyncIterator

class CommentCrawler:
    """评论爬取器 - MVP版本使用模拟数据"""
  
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.is_running = False
      
    async def start_crawling(self) -> AsyncIterator[dict]:
        """开始爬取评论"""
        self.is_running = True
      
        # 模拟评论数据
        mock_comments = [
            "主播好棒！", "这个产品怎么样？", "有没有优惠券？",
            "链接在哪里？", "价格多少？", "质量好吗？",
            "支持主播！", "什么时候发货？", "有现货吗？",
            "颜色好看", "尺码怎么选", "包邮吗？"
        ]
      
        while self.is_running:
            comment = {
                "id": f"c_{int(time.time())}{random.randint(100, 999)}",
                "username": f"用户{random.randint(1000, 9999)}",
                "content": random.choice(mock_comments),
                "timestamp": datetime.now().isoformat(),
                "room_id": self.room_id
            }
          
            yield comment
            await asyncio.sleep(random.uniform(1, 4))  # 1-4秒间隔
  
    def stop_crawling(self):
        """停止爬取"""
        self.is_running = False
```

### 2. 音频转录服务

```python
# server/app/services/audio_service.py
import openai
import tempfile
import os
from pathlib import Path

class AudioService:
    """音频转录服务"""
  
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
  
    async def transcribe_audio(self, audio_data: bytes) -> dict:
        """转录音频"""
        try:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
          
            # 调用Whisper API
            with open(temp_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="zh"
                )
          
            # 清理临时文件
            os.unlink(temp_path)
          
            return {
                "success": True,
                "text": transcript.text,
                "language": "zh"
            }
          
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
```

### 3. AI分析引擎

```python
# server/app/services/ai_analyzer.py
import openai
import json
from typing import List, Dict

class AIAnalyzer:
    """AI分析引擎"""
  
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
  
    async def analyze_comments(self, comments: List[str]) -> dict:
        """分析评论情感和话题"""
        if not comments:
            return {"topics": [], "sentiment": 0, "suggestions": []}
          
        comments_text = "\n".join(comments[-20:])  # 最近20条
      
        prompt = f"""
        分析以下直播评论，返回JSON格式结果：
      
        评论内容：
        {comments_text}
      
        请返回：
        {{
            "hot_topics": ["话题1", "话题2"],
            "sentiment_score": 0.8,
            "purchase_intent": 0.6,
            "main_questions": ["问题1", "问题2"]
        }}
        """
      
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
          
            result = json.loads(response.choices[0].message.content)
            return result
          
        except Exception as e:
            print(f"AI分析失败: {e}")
            return {"topics": [], "sentiment": 0, "suggestions": []}
  
    async def generate_suggestions(self, analysis: dict, transcript: str = "") -> List[str]:
        """生成AI建议"""
      
        prompt = f"""
        基于以下分析为主播生成3个实用建议：
      
        评论分析：{json.dumps(analysis, ensure_ascii=False)}
        主播最近说话：{transcript}
      
        请生成简洁实用的建议，每个不超过30字。
        返回JSON数组格式：["建议1", "建议2", "建议3"]
        """
      
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
          
            suggestions = json.loads(response.choices[0].message.content)
            return suggestions if isinstance(suggestions, list) else []
          
        except Exception as e:
            print(f"建议生成失败: {e}")
            return ["关注观众提问", "保持互动热情", "适时介绍产品"]
```

### 4. WebSocket管理器

```python
# server/app/services/websocket_manager.py
from fastapi import WebSocket
from typing import List, Dict
import json

class WebSocketManager:
    """WebSocket连接管理器"""
  
    def __init__(self):
        # room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
  
    async def connect(self, websocket: WebSocket, room_id: str):
        """建立连接"""
        await websocket.accept()
      
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
          
        self.active_connections[room_id].append(websocket)
        print(f"客户端连接到房间 {room_id}")
  
    def disconnect(self, websocket: WebSocket, room_id: str):
        """断开连接"""
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
          
        print(f"客户端从房间 {room_id} 断开")
  
    async def send_to_room(self, room_id: str, message: dict):
        """向房间内所有客户端发送消息"""
        if room_id not in self.active_connections:
            return
          
        disconnected = []
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print(f"发送消息失败: {e}")
                disconnected.append(connection)
      
        # 清理断开的连接
        for conn in disconnected:
            self.active_connections[room_id].remove(conn)

# 全局实例
websocket_manager = WebSocketManager()
```

## 🎨 前端关键组件

### 1. 实时评论流组件

```jsx
// frontend/src/components/CommentStream.jsx
import React, { useState, useEffect } from 'react';
import { Card, List, Tag } from 'antd';
import { useWebSocket } from '../hooks/useWebSocket';

const CommentStream = ({ roomId }) => {
    const [comments, setComments] = useState([]);
    const { socket, isConnected } = useWebSocket();
  
    useEffect(() => {
        if (socket && isConnected) {
            socket.on('new_comment', (comment) => {
                setComments(prev => [comment, ...prev.slice(0, 19)]); // 保持20条
            });
          
            // 加入房间
            socket.emit('join_room', { room_id: roomId });
        }
      
        return () => {
            if (socket) {
                socket.off('new_comment');
            }
        };
    }, [socket, isConnected, roomId]);
  
    return (
        <Card 
            title={
                <span>
                    💬 实时评论
                    <Tag color={isConnected ? 'green' : 'red'} style={{ marginLeft: 8 }}>
                        {isConnected ? '已连接' : '未连接'}
                    </Tag>
                </span>
            }
            size="small"
        >
            <List
                size="small"
                dataSource={comments}
                renderItem={comment => (
                    <List.Item key={comment.id}>
                        <div>
                            <strong>{comment.username}:</strong> {comment.content}
                            <br />
                            <small style={{ color: '#999' }}>
                                {new Date(comment.timestamp).toLocaleTimeString()}
                            </small>
                        </div>
                    </List.Item>
                )}
                style={{ maxHeight: 400, overflow: 'auto' }}
            />
        </Card>
    );
};

export default CommentStream;
```

### 2. AI建议面板

```jsx
// frontend/src/components/AIPanel.jsx
import React, { useState, useEffect } from 'react';
import { Card, List, Button, Tag, message } from 'antd';
import { ReloadOutlined, RobotOutlined } from '@ant-design/icons';
import api from '../services/api';

const AIPanel = ({ roomId }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
  
    const fetchSuggestions = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/ai/suggestions/${roomId}`);
            setSuggestions(response.data.suggestions || []);
        } catch (error) {
            message.error('获取AI建议失败');
        } finally {
            setLoading(false);
        }
    };
  
    useEffect(() => {
        fetchSuggestions();
      
        // 每30秒自动刷新
        const interval = setInterval(fetchSuggestions, 30000);
        return () => clearInterval(interval);
    }, [roomId]);
  
    return (
        <Card 
            title={
                <span>
                    <RobotOutlined /> AI智能建议
                </span>
            }
            extra={
                <Button 
                    type="text" 
                    icon={<ReloadOutlined />} 
                    loading={loading}
                    onClick={fetchSuggestions}
                >
                    刷新
                </Button>
            }
            size="small"
        >
            <List
                size="small"
                dataSource={suggestions}
                renderItem={(suggestion, index) => (
                    <List.Item key={index}>
                        <div style={{ width: '100%' }}>
                            <Tag color="blue" style={{ marginBottom: 4 }}>
                                建议 {index + 1}
                            </Tag>
                            <div>{suggestion}</div>
                        </div>
                    </List.Item>
                )}
                locale={{ emptyText: '暂无AI建议' }}
            />
        </Card>
    );
};

export default AIPanel;
```

### 3. 音频录制组件

```jsx
// frontend/src/components/AudioRecorder.jsx
import React, { useState, useRef } from 'react';
import { Card, Button, message, List } from 'antd';
import { AudioOutlined, StopOutlined } from '@ant-design/icons';
import api from '../services/api';

const AudioRecorder = ({ roomId }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [transcripts, setTranscripts] = useState([]);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
  
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];
          
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };
          
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
                await uploadAudio(audioBlob);
              
                // 停止所有音频轨道
                stream.getTracks().forEach(track => track.stop());
            };
          
            mediaRecorder.start();
            setIsRecording(true);
            message.success('开始录音');
          
        } catch (error) {
            message.error('无法访问麦克风');
        }
    };
  
    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            message.success('录音已停止');
        }
    };
  
    const uploadAudio = async (audioBlob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('room_id', roomId);
      
        try {
            const response = await api.post('/audio/upload', formData);
            const newTranscript = {
                id: Date.now(),
                text: response.data.transcript,
                timestamp: new Date().toLocaleTimeString()
            };
          
            setTranscripts(prev => [newTranscript, ...prev.slice(0, 9)]);
            message.success('音频转录完成');
          
        } catch (error) {
            message.error('音频上传失败');
        }
    };
  
    return (
        <Card 
            title="🎤 语音转录"
            extra={
                <Button
                    type={isRecording ? "danger" : "primary"}
                    icon={isRecording ? <StopOutlined /> : <AudioOutlined />}
                    onClick={isRecording ? stopRecording : startRecording}
                >
                    {isRecording ? '停止录音' : '开始录音'}
                </Button>
            }
            size="small"
        >
            <List
                size="small"
                dataSource={transcripts}
                renderItem={transcript => (
                    <List.Item key={transcript.id}>
                        <div>
                            <div>{transcript.text}</div>
                            <small style={{ color: '#999' }}>
                                {transcript.timestamp}
                            </small>
                        </div>
                    </List.Item>
                )}
                locale={{ emptyText: '暂无转录记录' }}
                style={{ maxHeight: 300, overflow: 'auto' }}
            />
        </Card>
    );
};

export default AudioRecorder;
```

## 🚀 部署配置

### Docker部署

```dockerfile
# Dockerfile
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY server/ .
COPY --from=frontend /app/frontend/dist ./static/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./timao_mvp.db
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 📝 环境配置

```bash
# .env.example
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./timao_mvp.db

# Redis配置
REDIS_URL=redis://localhost:6379

# JWT密钥
SECRET_KEY=your_secret_key_here

# 调试模式
DEBUG=true
```

---

**实现要点**:

1. 使用模拟数据确保3天内可完成
2. 优先核心功能，界面简洁实用
3. 集成现成AI服务，避免重复造轮子
4. Docker化部署，便于演示和测试
