#  移动端应用与后端服务集成技术方案设计

## 架构设计

### 1. 整体架构图

```mermaid
graph TB
    subgraph "移动端应用层"
        A[iOS App<br/>React Native]
        B[Android App<br/>React Native]
    end
  
    subgraph "网关层"
        C[Nginx 反向代理<br/>负载均衡]
        D[SSL/TLS 终端]
    end
  
    subgraph "API 服务层"
        E[FastAPI 服务实例1<br/>端口 9019]
        F[FastAPI 服务实例2<br/>端口 9020]
        G[FastAPI 服务实例N<br/>端口 9021+]
    end
  
    subgraph "业务服务层"
        H[认证服务<br/>JWT]
        I[直播监控服务<br/>WebSocket/SSE]
        J[AI分析服务<br/>LangChain]
        K[数据统计服务<br/>SQL查询]
    end
  
    subgraph "数据层"
        L[MySQL 主库<br/>用户/支付/订阅]
        M[MySQL 从库<br/>只读查询]
        N[Redis 集群<br/>缓存/会话]
        O[对象存储<br/>OSS/MinIO<br/>音频/图片]
    end
  
    subgraph "外部服务"
        P[推送服务<br/>FCM/APNs]
        Q[支付服务<br/>支付宝/微信]
        R[AI服务商<br/>Qwen/OpenAI等]
    end
  
    A -->|HTTPS| C
    B -->|HTTPS| C
    C --> D
    D --> E
    D --> F
    D --> G
  
    E --> H
    E --> I
    E --> J
    E --> K
  
    H --> L
    I --> L
    I --> N
    J --> R
    K --> M
    K --> N
  
    E --> P
    E --> Q
  
    I --> O
```

### 2. 移动端架构图

```mermaid
graph TB
    subgraph "React Native 应用层"
        A[App.tsx<br/>应用入口]
        B[导航层<br/>React Navigation]
        C[状态管理<br/>Redux Toolkit]
        D[API客户端<br/>Axios + Interceptor]
    end
  
    subgraph "功能模块"
        E[认证模块<br/>Login/Register]
        F[直播监控模块<br/>LiveMonitor]
        G[数据统计模块<br/>Analytics]
        H[订阅管理模块<br/>Subscription]
        I[设置模块<br/>Settings]
    end
  
    subgraph "公共服务"
        J[推送服务<br/>FCM/APNs]
        K[本地存储<br/>AsyncStorage]
        L[WebSocket客户端<br/>实时数据]
        M[错误处理<br/>Error Boundary]
    end
  
    A --> B
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
  
    E --> C
    F --> C
    G --> C
    H --> C
    I --> C
  
    C --> D
    D -->|HTTPS API| N[后端服务器]
  
    F --> L
    L -->|WebSocket| N
  
    A --> J
    J --> P[推送服务器]
  
    E --> K
    F --> K
    H --> K
```

---

## 技术栈选型

### 后端技术栈

#### 核心框架

- **FastAPI 0.100+**：异步 Web 框架，高性能 API 服务
- **Uvicorn**：ASGI 服务器，支持多进程部署
- **Python 3.11+**：运行环境

#### 数据库

- **MySQL 8.0+**：主数据库（用户、支付、订阅、直播记录）
- **Redis 7.0+**：缓存、会话存储、实时数据队列
- **SQLAlchemy 2.0+**：ORM 框架
- **Alembic**：数据库迁移工具

#### 部署与运维

- **Docker + Docker Compose**：容器化部署
- **Nginx 1.24+**：反向代理、负载均衡、SSL 终端
- **Supervisor / systemd**：进程管理
- **Let's Encrypt**：SSL 证书自动续期

#### 监控与日志

- **Prometheus + Grafana**：性能监控（可选）
- **ELK Stack**：日志收集与分析（可选）
- **Sentry**：错误追踪（可选）

### 移动端技术栈

#### 核心框架

- **React Native 0.73+**：跨平台框架
- **TypeScript 5.0+**：类型安全
- **React Navigation 6.x**：路由管理

#### 状态管理

- **Redux Toolkit 2.0+**：状态管理
- **React Query (TanStack Query)**：数据获取与缓存

#### UI 组件库

- **React Native Paper 5.x**：Material Design 组件库
- **React Native Vector Icons**：图标库

#### 网络请求

- **Axios 1.6+**：HTTP 客户端
- **React Native WebSocket**：WebSocket 客户端
- **React Native EventSource**：SSE 客户端（如需要）

#### 本地存储

- **@react-native-async-storage/async-storage**：键值存储
- **react-native-keychain**：安全存储（Token、密码）
- **react-native-mmkv**：高性能存储（可选）

#### 推送通知

- **@react-native-firebase/messaging**：FCM（Android）
- **@react-native-community/push-notification-ios**：APNs（iOS）

#### 图表与可视化

- **react-native-chart-kit** 或 **victory-native**：图表库

#### 工具库

- **date-fns**：日期处理
- **react-hook-form**：表单管理
- **zod**：数据验证
- **react-native-safe-area-context**：安全区域适配

---

## 后端服务部署方案

### 1. Docker 容器化部署

#### Dockerfile 结构

```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.all.txt .
RUN pip install --user -r requirements.all.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY server/ ./server/
COPY AST_module/ ./AST_module/
COPY config.json .env ./
ENV PATH=/root/.local/bin:$PATH
EXPOSE 9019
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "9019"]
```

#### Docker Compose 配置

```yaml
version: '3.8'

services:
  fastapi:
    build: .
    ports:
      - "9019:9019"
    environment:
      - DATABASE_URL=mysql://user:pass@mysql:3306/dbname
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./records:/app/records
  
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpass
      - MYSQL_DATABASE=timao_db
    volumes:
      - mysql_data:/var/lib/mysql
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### 2. Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/timao-api
upstream fastapi_backend {
    least_conn;
    server 127.0.0.1:9019;
    server 127.0.0.1:9020;
    server 127.0.0.1:9021;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.timao.com;
  
    ssl_certificate /etc/letsencrypt/live/api.timao.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.timao.com/privkey.pem;
  
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
  
    # 日志
    access_log /var/log/nginx/timao-api-access.log;
    error_log /var/log/nginx/timao-api-error.log;
  
    # 客户端配置
    client_max_body_size 50M;
    client_body_timeout 60s;
  
    # API 路由
    location /api/ {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
  
    # 静态文件（API 文档）
    location /docs {
        proxy_pass http://fastapi_backend/docs;
    }
  
    # 健康检查
    location /health {
        proxy_pass http://fastapi_backend/health;
        access_log off;
    }
}
```

### 3. 进程管理（systemd）

```ini
# /etc/systemd/system/timao-api.service
[Unit]
Description=Timao FastAPI Service
After=network.target mysql.service redis.service

[Service]
Type=simple
User=timao
WorkingDirectory=/opt/timao/backend
Environment="PATH=/opt/timao/backend/venv/bin"
ExecStart=/opt/timao/backend/venv/bin/uvicorn server.app.main:app \
    --host 0.0.0.0 \
    --port 9019 \
    --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. 环境变量配置

```bash
# .env (生产环境)
# 数据库
DATABASE_URL=mysql+pymysql://user:password@mysql:3306/timao_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_ENABLED=true

# API 配置
BACKEND_PORT=9019
CORS_ORIGINS=https://app.timao.com,https://admin.timao.com

# AI 服务
AI_SERVICE=qwen
AI_API_KEY=sk-xxx
QWEN_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx

# 安全
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=365
```

---

## API 接口设计

### 1. 统一响应格式

```typescript
// 成功响应
interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
}

// 错误响应
interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
```

### 2. 认证接口（已存在，需适配移动端）

```python
# server/app/api/auth.py
# POST /api/auth/login
# POST /api/auth/register
# POST /api/auth/refresh
# GET /api/auth/me
# PUT /api/auth/profile
```

### 3. 移动端专用接口（新增）

```python
# server/app/api/mobile.py

@router.get("/mobile/config")
async def get_mobile_config(current_user: User = Depends(get_current_user)):
    """获取移动端配置"""
    return {
        "version": "1.0.0",
        "features": {
            "live_monitor": True,
            "analytics": True,
            "subscription": True,
            "floating_window": True,  # 悬浮窗支持
        },
        "websocket_url": "wss://api.timao.com/api/live_audio/ws",
        "hide_transcript": True,  # 移动端隐藏转录字幕
    }

@router.get("/mobile/notifications/register")
async def register_push_token(
    token: str,
    platform: Literal["ios", "android"],
    current_user: User = Depends(get_current_user)
):
    """注册推送令牌"""
    # 保存 FCM/APNs token 到数据库
    pass

@router.post("/mobile/notifications/unregister")
async def unregister_push_token(
    current_user: User = Depends(get_current_user)
):
    """取消注册推送令牌"""
    pass
```

### 4. 复盘生成接口（新增/扩展）

```python
# server/app/api/live_review.py (扩展)

@router.post("/live_review/generate")
async def generate_review(
    live_id: str,
    current_user: User = Depends(get_current_user)
):
    """手动触发复盘生成（前期版本使用完整复盘能力）
    
    Args:
        live_id: 直播ID
    
    注意：前期版本所有用户都使用完整复盘（enterprise级别），不按会员类型限制。
         未来版本可能会根据会员类型限制复盘级别。
    """
    # 前期版本：统一使用完整复盘级别（enterprise）
    # 未来版本：可根据会员类型调整
    review_level = "enterprise"  # 完整复盘
    
    # 生成复盘（异步任务）
    task = generate_review_task.delay(live_id, review_level, current_user.id)
    
    return {
        "task_id": task.id,
        "status": "processing",
        "review_level": review_level,
        "message": "复盘生成中，完成后将通过推送通知您",
    }

@router.get("/live_review/status/{task_id}")
async def get_review_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """查询复盘生成状态"""
    # 查询 Celery 任务状态
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.state,  # PENDING, STARTED, SUCCESS, FAILURE
        "result": task.result if task.ready() else None,
    }

# 注意：停止监控不再自动生成复盘
# 复盘生成改为用户手动触发（见 /api/live_review/generate）
# 自动生成功能暂不实现，但接口设计已预留
```

### 4. CORS 配置更新

```python
# server/app/main.py
allowed_origins = [
    "https://app.timao.com",  # 移动端域名（如 WebView）
    "https://admin.timao.com",
    # ... 其他域名
]
```

---

## 移动端应用结构

### 目录结构

```
mobile-app/
├── src/
│   ├── App.tsx                 # 应用入口
│   ├── navigation/
│   │   ├── AppNavigator.tsx   # 导航配置
│   │   └── types.ts           # 路由类型
│   ├── store/
│   │   ├── index.ts           # Store 配置
│   │   ├── slices/
│   │   │   ├── authSlice.ts   # 认证状态
│   │   │   ├── liveSlice.ts   # 直播状态
│   │   │   └── userSlice.ts   # 用户状态
│   ├── services/
│   │   ├── api.ts             # API 客户端
│   │   ├── websocket.ts       # WebSocket 客户端
│   │   ├── storage.ts         # 本地存储
│   │   └── push.ts            # 推送服务
│   ├── screens/
│   │   ├── Auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   └── RegisterScreen.tsx
│   │   ├── Live/
│   │   │   ├── MonitorScreen.tsx
│   │   │   └── DetailScreen.tsx
│   │   ├── Analytics/
│   │   │   ├── StatsScreen.tsx
│   │   │   └── ReportScreen.tsx
│   │   ├── Subscription/
│   │   │   ├── PlansScreen.tsx
│   │   │   └── PaymentScreen.tsx
│   │   └── Settings/
│   │       └── SettingsScreen.tsx
│   ├── components/
│   │   ├── common/            # 通用组件
│   │   ├── live/             # 直播相关组件
│   │   │   ├── FloatingWindow.tsx  # 悬浮窗组件
│   │   │   ├── AIAnalysisPopup.tsx # AI分析悬浮窗
│   │   │   └── ScriptPopup.tsx    # 话术生成悬浮窗
│   │   └── charts/           # 图表组件
│   ├── hooks/                 # 自定义 Hooks
│   ├── utils/                 # 工具函数
│   └── types/                 # TypeScript 类型
├── android/                   # Android 原生代码
├── ios/                       # iOS 原生代码
├── package.json
├── tsconfig.json
└── babel.config.js
```

### 核心模块设计

#### 1. API 客户端

```typescript
// src/services/api.ts
import axios from 'axios';
import { getToken, refreshToken } from './storage';

const api = axios.create({
  baseURL: 'https://api.timao.com/api',
  timeout: 30000,
});

// 请求拦截器：添加 Token
api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：自动刷新 Token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return api.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

#### 2. WebSocket 客户端

```typescript
// src/services/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketManager {
  private socket: Socket | null = null;
  private listeners: Map<string, Function[]> = new Map();
  
  connect(token: string) {
    this.socket = io('wss://api.timao.com', {
      auth: { token },
      transports: ['websocket'],
    });
  
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });
  
    this.socket.on('comment', (data) => {
      // 处理新弹幕
      this.emit('comment', data);
    });
  
    this.socket.on('gift', (data) => {
      // 处理礼物
      this.emit('gift', data);
    });
  
    // AI 分析结果
    this.socket.on('ai_analysis', (data) => {
      // 触发悬浮窗显示 AI 分析
      this.emit('ai_analysis', data);
    });
  
    // AI 话术建议
    this.socket.on('ai_script', (data) => {
      // 触发悬浮窗显示话术
      this.emit('ai_script', data);
    });
  }
  
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)?.push(callback);
  }
  
  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(callback => callback(data));
  }
  
  disconnect() {
    this.socket?.disconnect();
    this.listeners.clear();
  }
}

export default new WebSocketManager();
```

#### 3. 悬浮窗组件

```typescript
// src/components/live/FloatingWindow.tsx
import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated, PanResponder } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface FloatingWindowProps {
  title: string;
  content: string;
  onClose?: () => void;
  onCopy?: (text: string) => void;
  initialPosition?: { x: number; y: number };
}

export const FloatingWindow: React.FC<FloatingWindowProps> = ({
  title,
  content,
  onClose,
  onCopy,
  initialPosition = { x: 20, y: 100 },
}) => {
  const [expanded, setExpanded] = useState(false);
  const insets = useSafeAreaInsets();
  const pan = useRef(new Animated.ValueXY(initialPosition)).current;
  
  // 拖拽响应器
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onPanResponderGrant: () => {
        pan.setOffset({
          x: pan.x._value,
          y: pan.y._value,
        });
      },
      onPanResponderMove: Animated.event(
        [null, { dx: pan.x, dy: pan.y }],
        { useNativeDriver: false }
      ),
      onPanResponderRelease: (e, gesture) => {
        pan.flattenOffset();
        // 屏幕边缘吸附
        const screenWidth = e.nativeEvent.pageX;
        const screenHeight = e.nativeEvent.pageY;
        const windowWidth = expanded ? 300 : 80;
        const windowHeight = expanded ? 200 : 80;
    
        let finalX = pan.x._value;
        let finalY = pan.y._value;
    
        // 左边缘吸附
        if (finalX < screenWidth / 2) {
          finalX = 0;
        } else {
          finalX = screenWidth - windowWidth;
        }
    
        // 上下边缘限制
        if (finalY < insets.top) finalY = insets.top;
        if (finalY > screenHeight - windowHeight - insets.bottom) {
          finalY = screenHeight - windowHeight - insets.bottom;
        }
    
        Animated.spring(pan, {
          toValue: { x: finalX, y: finalY },
          useNativeDriver: false,
        }).start();
      },
    })
  ).current;
  
  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          width: expanded ? 300 : 80,
          height: expanded ? 200 : 80,
          backgroundColor: 'rgba(102, 126, 234, 0.95)',
          borderRadius: 12,
          padding: 12,
          zIndex: 9999,
          elevation: 10, // Android shadow
          shadowColor: '#000', // iOS shadow
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
        },
        {
          transform: [{ translateX: pan.x }, { translateY: pan.y }],
        },
      ]}
      {...panResponder.panHandlers}
    >
      <TouchableOpacity
        onPress={() => setExpanded(!expanded)}
        style={{ flex: 1 }}
      >
        <Text style={{ color: '#fff', fontWeight: 'bold', marginBottom: 8 }}>
          {title}
        </Text>
        {expanded && (
          <View>
            <Text style={{ color: '#fff', fontSize: 12 }} numberOfLines={4}>
              {content}
            </Text>
            <View style={{ flexDirection: 'row', marginTop: 8, gap: 8 }}>
              {onCopy && (
                <TouchableOpacity
                  onPress={() => onCopy(content)}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.3)',
                    padding: 6,
                    borderRadius: 6,
                  }}
                >
                  <Text style={{ color: '#fff', fontSize: 12 }}>复制</Text>
                </TouchableOpacity>
              )}
              {onClose && (
                <TouchableOpacity
                  onPress={onClose}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.3)',
                    padding: 6,
                    borderRadius: 6,
                  }}
                >
                  <Text style={{ color: '#fff', fontSize: 12 }}>关闭</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
};
```

#### 4. AI 分析悬浮窗管理器

```typescript
// src/components/live/AIAnalysisPopup.tsx
import React, { useEffect } from 'react';
import { FloatingWindow } from './FloatingWindow';
import { useDispatch, useSelector } from 'react-redux';
import websocketManager from '../../services/websocket';
import Clipboard from '@react-native-clipboard/clipboard';
import { showMessage } from 'react-native-flash-message';

export const AIAnalysisPopup: React.FC = () => {
  const dispatch = useDispatch();
  const [aiAnalysis, setAiAnalysis] = useState<{ title: string; content: string } | null>(null);
  
  useEffect(() => {
    const handleAIAnalysis = (data: any) => {
      setAiAnalysis({
        title: 'AI 分析',
        content: data.analysis || data.summary || '暂无分析结果',
      });
    };
  
    websocketManager.on('ai_analysis', handleAIAnalysis);
  
    return () => {
      websocketManager.off('ai_analysis', handleAIAnalysis);
    };
  }, []);
  
  const handleCopy = (text: string) => {
    Clipboard.setString(text);
    showMessage({
      message: '已复制到剪贴板',
      type: 'success',
    });
  };
  
  if (!aiAnalysis) return null;
  
  return (
    <FloatingWindow
      title={aiAnalysis.title}
      content={aiAnalysis.content}
      onCopy={handleCopy}
      onClose={() => setAiAnalysis(null)}
    />
  );
};
```

#### 3. 状态管理（Redux Toolkit）

```typescript
// src/store/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { username: string; password: string }) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false,
  } as AuthState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(login.fulfilled, (state, action) => {
      state.user = action.payload.user;
      state.token = action.payload.access_token;
      state.isAuthenticated = true;
    });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

---

## 数据库设计

### 新增表结构

```sql
-- 推送令牌表
CREATE TABLE push_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    platform ENUM('ios', 'android') NOT NULL,
    device_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_platform_token (user_id, platform, token),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 移动端会话表（可选，用于追踪在线状态）
CREATE TABLE mobile_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    platform ENUM('ios', 'android') NOT NULL,
    app_version VARCHAR(50),
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 安全性设计

### 1. API 安全

- **HTTPS 强制**：所有 API 请求使用 HTTPS
- **Token 安全存储**：使用 Keychain（iOS）/ Keystore（Android）
- **证书固定**：移动端实现 Certificate Pinning
- **API 限流**：使用 Redis 实现速率限制（如 100 请求/分钟/用户）

### 2. 数据加密

- **传输加密**：TLS 1.2+
- **存储加密**：敏感数据（Token）使用系统 Keychain/Keystore
- **密码加密**：后端使用 bcrypt 加密存储

### 3. 认证与授权

- **JWT Token**：短期 Access Token（1-8小时）+ 长期 Refresh Token（1-3650天）
- **Token 刷新机制**：自动刷新即将过期的 Token
- **权限检查**：基于角色的访问控制（RBAC）

---

## 部署流程

### 1. 后端部署步骤

```bash
# 1. 克隆代码
git clone https://github.com/timao/timao-douyin-live-manager.git
cd timao-douyin-live-manager

# 2. 构建 Docker 镜像
docker build -t timao-api:latest .

# 3. 配置环境变量
cp .env.example .env
vim .env  # 编辑配置

# 4. 启动服务
docker-compose up -d

# 5. 运行数据库迁移
docker-compose exec fastapi alembic upgrade head

# 6. 配置 Nginx
sudo cp nginx.conf /etc/nginx/sites-available/timao-api
sudo ln -s /etc/nginx/sites-available/timao-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 7. 配置 SSL 证书（Let's Encrypt）
sudo certbot --nginx -d api.timao.com
```

### 2. 移动端构建步骤

```bash
# iOS
cd mobile-app
npm install
cd ios
pod install
cd ..
npm run ios

# Android
cd mobile-app
npm install
npm run android

# 构建生产版本
npm run build:ios     # iOS
npm run build:android # Android
```

---

## 测试策略

### 1. 后端测试

- **单元测试**：pytest 测试业务逻辑
- **集成测试**：测试 API 接口
- **压力测试**：使用 Locust 或 JMeter

### 2. 移动端测试

- **单元测试**：Jest + React Native Testing Library
- **集成测试**：Detox（E2E 测试）
- **真机测试**：iOS TestFlight、Android Beta

---

---

## 复盘功能设计

### 1. 复盘级别定义

```python
# 复盘级别映射
REVIEW_LEVELS = {
    "basic": {
        "name": "基础复盘",
        "description": "文本摘要，包含直播时长、弹幕总数、礼物总额",
        "features": ["summary", "statistics"],
        "subscription_type": "free",
    },
    "standard": {
        "name": "标准复盘",
        "description": "基础复盘 + 数据统计图表",
        "features": ["summary", "statistics", "charts"],
        "subscription_type": "basic",
    },
    "premium": {
        "name": "详细复盘",
        "description": "标准复盘 + AI 分析和热词提取",
        "features": ["summary", "statistics", "charts", "ai_analysis", "hotwords"],
        "subscription_type": "premium",
    },
    "enterprise": {
        "name": "完整复盘",
        "description": "详细复盘 + 深度分析和优化建议",
        "features": ["summary", "statistics", "charts", "ai_analysis", "hotwords", "deep_analysis", "suggestions"],
        "subscription_type": "enterprise",
    },
}
```

### 2. 复盘生成流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant App as 移动端
    participant API as 后端API
    participant Task as 异步任务
    participant DB as 数据库
  
    User->>App: 结束直播监控
    App->>API: POST /api/douyin/stop
    API->>API: 获取用户会员类型
    API->>Task: 触发异步复盘生成任务
    API->>App: 返回任务ID和复盘级别
    App->>App: 显示"复盘生成中..."
  
    Task->>DB: 读取直播数据
    Task->>Task: 按级别生成复盘内容
    Task->>DB: 保存复盘结果
    Task->>App: 推送通知（完成）
  
    User->>App: 点击"查看复盘"
    App->>API: GET /api/live_review/{id}
    API->>DB: 查询复盘数据
    API->>App: 返回复盘内容（按权限）
```

### 3. 移动端复盘展示

```typescript
// src/screens/Analytics/ReportScreen.tsx 扩展
interface ReviewReport {
  id: string;
  live_id: string;
  review_level: 'enterprise';  // 前期版本统一使用完整复盘
  status: 'pending' | 'processing' | 'completed' | 'failed';
  content: {
    summary: string;            // 摘要
    statistics: StatisticsData; // 数据统计
    charts: ChartData[];        // 统计图表
    ai_analysis: AIAnalysis;    // AI分析
    hotwords: HotwordData[];    // 热词提取
    deep_analysis: DeepAnalysis; // 深度分析
    suggestions: Suggestion[];  // 优化建议
  };
  created_at: string;
  updated_at: string;
}

// 前期版本：直接显示完整内容，不进行过滤
// 未来版本：可添加按会员类型过滤的逻辑
const displayReviewContent = (review: ReviewReport) => {
  // 直接返回完整内容
  return review.content;
};

// 未来版本的过滤逻辑（暂不使用，已预留）
const filterReviewContent = (
  review: ReviewReport,
  userSubscription: SubscriptionType
): Partial<ReviewReport['content']> => {
  // 此函数暂时不使用，未来版本按会员类型限制时可启用
  const levelMap = {
    free: ['summary'],
    basic: ['summary', 'statistics', 'charts'],
    premium: ['summary', 'statistics', 'charts', 'ai_analysis', 'hotwords'],
    enterprise: ['summary', 'statistics', 'charts', 'ai_analysis', 'hotwords', 'deep_analysis', 'suggestions'],
  };
  
  const allowedFeatures = levelMap[userSubscription] || [];
  const filteredContent: Partial<ReviewReport['content']> = {};
  
  allowedFeatures.forEach(feature => {
    if (review.content[feature]) {
      filteredContent[feature] = review.content[feature];
    }
  });
  
  return filteredContent;
};
```

---

**文档版本**：v1.2  
**创建日期**：2025-01-27  
**最后更新**：2025-01-27  
**更新内容**：
- v1.2: 修改复盘功能 - 改为手动触发，前期版本使用完整复盘（不按会员类型限制），移除自动生成逻辑
- v1.1: 添加悬浮窗组件设计和实现代码
- v1.1: 添加复盘功能设计和级别定义
- v1.1: 添加移动端隐藏转录字幕配置
- v1.1: 扩展复盘生成接口设计
