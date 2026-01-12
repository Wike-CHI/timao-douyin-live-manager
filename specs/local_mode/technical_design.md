# 本地化模式技术方案

## 文档信息
- **版本**：v1.0
- **审查人**：叶维哲
- **创建日期**：2025-11-25
- **状态**：待确认

---

## 1. 整体架构变更

### 1.1 当前架构
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Electron      │────▶│   FastAPI       │────▶│   MySQL         │
│   Frontend      │     │   Backend       │     │   + Redis       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   AI Services   │
                        │   (云端API)     │
                        └─────────────────┘
```

### 1.2 目标架构
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Electron      │────▶│   FastAPI       │────▶│   Local JSON    │
│   Frontend      │     │   Backend       │     │   Files         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                      │
       │                      ▼
       │                ┌─────────────────┐
       │                │   AI Services   │
       │                │   (用户配置)    │
       │                └─────────────────┘
       │
       ▼
┌─────────────────┐
│   初次启动向导   │
│   (配置AI/下载)  │
└─────────────────┘
```

---

## 2. 模块变更清单

### 2.1 需要移除的模块

| 模块 | 文件路径 | 说明 |
|------|----------|------|
| 数据库管理器 | `server/app/database.py` | 替换为本地存储 |
| 数据库模型 | `server/app/models/*.py` | 简化为JSON结构 |
| 订阅服务 | `server/app/services/subscription_service.py` | 完全移除 |
| 支付服务 | `server/app/services/payment_service.py` | 完全移除 |
| 订阅API | `server/app/api/subscription.py` | 完全移除 |
| Redis管理器 | `server/utils/redis_manager.py` | 替换为内存缓存 |
| JWT认证 | `server/app/core/security.py` | 简化为无认证 |
| 订阅页面 | `electron/renderer/src/pages/payment/` | 完全移除 |
| 登录页面 | `electron/renderer/src/pages/auth/` | 完全移除 |

### 2.2 需要新增的模块

| 模块 | 文件路径 | 说明 |
|------|----------|------|
| 本地存储服务 | `server/local/local_storage.py` | JSON文件读写 |
| 本地配置服务 | `server/local/local_config.py` | AI配置管理 |
| 初次启动向导 | `electron/renderer/src/pages/setup/SetupWizard.tsx` | 配置向导 |
| 引导检测API | `server/app/api/bootstrap.py` | 启动检测API |

### 2.3 需要修改的模块

| 模块 | 文件路径 | 修改内容 |
|------|----------|----------|
| AI网关 | `server/ai/ai_gateway.py` | 从本地配置读取 |
| SenseVoice服务 | `server/modules/ast/sensevoice_service.py` | 移除内存检查 |
| 主入口 | `server/app/main.py` | 移除数据库初始化 |
| 前端入口 | `electron/renderer/src/main.tsx` | 默认已付费状态 |
| 认证store | `electron/renderer/src/store/useAuthStore.ts` | 简化为本地用户 |
| 前端路由 | `electron/renderer/src/App.tsx` | 移除订阅路由 |

---

## 3. 详细技术方案

### 3.1 本地存储服务设计

#### 3.1.1 目录结构
```
data/
├── ai_config.json          # AI服务配置
├── app_config.json         # 应用配置
├── ai_usage.json           # AI使用统计
├── hotwords.json           # 热词配置
└── sessions/               # 直播会话数据
    └── {session_id}/
        ├── info.json       # 会话基本信息
        ├── danmaku.json    # 弹幕数据
        ├── transcript.json # 转写数据
        └── report.json     # 报告数据
```

#### 3.1.2 本地存储服务实现

```python
# server/local/local_storage.py
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import threading

class LocalStorage:
    """本地JSON文件存储服务"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = {}
        self._file_locks: Dict[str, threading.Lock] = {}
    
    def _get_file_lock(self, filename: str) -> threading.Lock:
        if filename not in self._file_locks:
            self._file_locks[filename] = threading.Lock()
        return self._file_locks[filename]
    
    def read(self, filename: str, default: Any = None) -> Any:
        """读取JSON文件"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return default
        
        with self._get_file_lock(filename):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
    
    def write(self, filename: str, data: Any) -> bool:
        """写入JSON文件"""
        filepath = self.data_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_file_lock(filename):
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            except IOError:
                return False
    
    def append_to_list(self, filename: str, item: Any) -> bool:
        """向JSON数组追加元素"""
        data = self.read(filename, [])
        if not isinstance(data, list):
            data = []
        data.append(item)
        return self.write(filename, data)
    
    def update_dict(self, filename: str, updates: Dict) -> bool:
        """更新JSON对象"""
        data = self.read(filename, {})
        if not isinstance(data, dict):
            data = {}
        data.update(updates)
        return self.write(filename, data)


# 全局实例
local_storage = LocalStorage()
```

### 3.2 AI配置服务设计

#### 3.2.1 配置文件格式

```json
// data/ai_config.json
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
    "live_analysis": { "provider": "xunfei", "model": "lite" },
    "style_profile": { "provider": "qwen", "model": "qwen3-max" },
    "script_generation": { "provider": "qwen", "model": "qwen3-max" },
    "live_review": { "provider": "gemini", "model": "gemini-2.5-flash" },
    "chat_focus": { "provider": "qwen", "model": "qwen3-max" },
    "topic_generation": { "provider": "qwen", "model": "qwen3-max" }
  },
  "active_provider": "xunfei",
  "initialized": true
}
```

#### 3.2.2 AI配置服务实现

```python
# server/local/local_config.py
from typing import Dict, Optional, Any
from server.local.local_storage import local_storage

class LocalAIConfig:
    """本地AI配置管理"""
    
    CONFIG_FILE = "ai_config.json"
    
    PROVIDER_TEMPLATES = {
        "qwen": {
            "name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen3-max"]
        },
        "xunfei": {
            "name": "讯飞星火",
            "base_url": "https://spark-api-open.xf-yun.com/v1",
            "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"]
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-coder"]
        },
        "doubao": {
            "name": "字节豆包",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "models": ["doubao-pro", "doubao-lite"]
        },
        "glm": {
            "name": "智谱ChatGLM",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-3-turbo"]
        },
        "gemini": {
            "name": "Google Gemini",
            "base_url": "https://aihubmix.com/v1",
            "models": ["gemini-2.5-flash-preview-09-2025"]
        }
    }
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查是否已初始化"""
        config = local_storage.read(cls.CONFIG_FILE, {})
        return config.get("initialized", False)
    
    @classmethod
    def get_config(cls) -> Dict:
        """获取完整配置"""
        return local_storage.read(cls.CONFIG_FILE, {
            "providers": {},
            "function_models": {},
            "active_provider": None,
            "initialized": False
        })
    
    @classmethod
    def save_provider(cls, provider_id: str, api_key: str, 
                      base_url: Optional[str] = None,
                      default_model: Optional[str] = None) -> bool:
        """保存服务商配置"""
        config = cls.get_config()
        
        template = cls.PROVIDER_TEMPLATES.get(provider_id, {})
        config["providers"][provider_id] = {
            "api_key": api_key,
            "base_url": base_url or template.get("base_url", ""),
            "default_model": default_model or (template.get("models", [""])[0]),
            "enabled": True
        }
        
        return local_storage.write(cls.CONFIG_FILE, config)
    
    @classmethod
    def set_function_model(cls, function_id: str, provider: str, model: str) -> bool:
        """设置功能使用的模型"""
        config = cls.get_config()
        if "function_models" not in config:
            config["function_models"] = {}
        
        config["function_models"][function_id] = {
            "provider": provider,
            "model": model
        }
        
        return local_storage.write(cls.CONFIG_FILE, config)
    
    @classmethod
    def mark_initialized(cls) -> bool:
        """标记为已初始化"""
        config = cls.get_config()
        config["initialized"] = True
        return local_storage.write(cls.CONFIG_FILE, config)
    
    @classmethod
    def get_provider_for_function(cls, function_id: str) -> Optional[Dict]:
        """获取指定功能使用的服务商和模型"""
        config = cls.get_config()
        func_config = config.get("function_models", {}).get(function_id)
        
        if not func_config:
            return None
        
        provider_id = func_config.get("provider")
        provider_config = config.get("providers", {}).get(provider_id)
        
        if not provider_config or not provider_config.get("enabled"):
            return None
        
        return {
            "provider": provider_id,
            "model": func_config.get("model"),
            "api_key": provider_config.get("api_key"),
            "base_url": provider_config.get("base_url")
        }
```

### 3.3 移除登录验证方案

#### 3.3.1 后端依赖注入替换

```python
# server/app/core/dependencies.py (修改后)
from typing import Dict, Any

def get_current_user() -> Dict[str, Any]:
    """
    返回固定的本地用户 - 无需认证
    """
    return {
        "id": 1,
        "username": "local_user",
        "email": "local@localhost",
        "nickname": "本地用户",
        "role": "super_admin",
        "is_active": True
    }

# 兼容旧代码的别名
async def get_current_user_async() -> Dict[str, Any]:
    return get_current_user()

class OptionalAuth:
    """可选认证 - 总是返回本地用户"""
    async def __call__(self) -> Dict[str, Any]:
        return get_current_user()
```

#### 3.3.2 前端状态初始化

```typescript
// electron/renderer/src/main.tsx (修改后)
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './theme/global.css';
import useAuthStore from './store/useAuthStore';
import './services/appCleanup';

// 本地化模式：启动时自动设置本地用户状态
(() => {
  const { setAuth, setPaid } = useAuthStore.getState();
  
  // 设置永久有效的本地用户
  setAuth({
    user: {
      id: 1,
      username: 'local_user',
      email: 'local@localhost',
      nickname: '本地用户',
      avatar_url: '',
      role: 'super_admin',
      status: 'active',
      email_verified: true,
      phone_verified: true,
      created_at: new Date().toISOString(),
    },
    token: 'local_mode_token',
    refreshToken: 'local_mode_token',
    isPaid: true,
  });
  setPaid(true);
})();

const rootElement = document.getElementById('root') as HTMLElement;
const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### 3.4 绕过订阅机制方案

#### 3.4.1 移除前端付费检查

```typescript
// electron/renderer/src/pages/dashboard/LiveConsolePage.tsx
// 删除以下代码块：
// if (!isPaid && !isSuperAdmin) {
//   setError('功能暂时不可用，请订阅套餐后使用');
//   ...
// }
```

#### 3.4.2 移除订阅路由

```typescript
// electron/renderer/src/App.tsx
// 删除以下路由：
// <Route path="subscription" element={<SubscriptionPage />} />
```

### 3.5 移除SenseVoice内存检查

#### 3.5.1 修改位置

```python
# server/modules/ast/sensevoice_service.py
# 在 _transcribe_with_lock 方法中删除以下代码块（约第377-407行）：

# 删除：
# memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
# if memory_mb > 2000:
#     self.logger.warning(f"[内存警告] 当前内存使用: {memory_mb:.0f}MB")
# if memory_mb > 2500:
#     ...
# if memory_mb > 3000:
#     ...
```

### 3.6 AI错误处理优化

#### 3.6.1 错误码映射

```python
# server/ai/ai_gateway.py (添加)
AI_ERROR_MESSAGES = {
    "Arrearage": "AI服务账户欠费，请充值后重试或切换其他服务商",
    "401": "API Key无效或已过期，请检查配置",
    "403": "API Key权限不足，请检查配置",
    "429": "请求过于频繁，请稍后重试",
    "500": "AI服务暂时不可用，请稍后重试",
    "timeout": "请求超时，请检查网络连接",
    "no_provider": "AI功能暂不可用，请先配置AI服务"
}

def get_user_friendly_error(error: Exception) -> str:
    """将异常转换为用户友好的错误提示"""
    error_str = str(error).lower()
    
    if "arrearage" in error_str or "insufficient" in error_str:
        return AI_ERROR_MESSAGES["Arrearage"]
    elif "401" in error_str or "unauthorized" in error_str:
        return AI_ERROR_MESSAGES["401"]
    elif "403" in error_str or "forbidden" in error_str:
        return AI_ERROR_MESSAGES["403"]
    elif "429" in error_str or "rate" in error_str:
        return AI_ERROR_MESSAGES["429"]
    elif "timeout" in error_str:
        return AI_ERROR_MESSAGES["timeout"]
    elif "500" in error_str or "server" in error_str:
        return AI_ERROR_MESSAGES["500"]
    
    return f"AI服务调用失败: {str(error)[:100]}"
```

### 3.7 初次启动向导设计

#### 3.7.1 向导流程

```
┌─────────────────────────────────────────────────────────────┐
│                    初次启动向导                              │
├─────────────────────────────────────────────────────────────┤
│  Step 1: 环境检查                                           │
│  ├── 检测FFMPEG  [✓ 已安装 / ⟳ 下载中 / ✗ 需手动安装]       │
│  ├── 检测SenseVoice模型 [✓ 已安装 / ⟳ 下载中 / ⚠ 可跳过]   │
│  └── 检测VAD模型 [✓ 已安装 / ⟳ 下载中 / ⚠ 可跳过]          │
├─────────────────────────────────────────────────────────────┤
│  Step 2: AI服务配置                                         │
│  ├── 通义千问 [配置] [测试]                                  │
│  ├── 讯飞星火 [配置] [测试]                                  │
│  ├── DeepSeek [配置] [测试]                                  │
│  └── ... 其他服务商                                          │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 功能配置（可选）                                    │
│  ├── 实时分析 → 选择服务商/模型                              │
│  ├── 话术生成 → 选择服务商/模型                              │
│  └── ... 其他功能                                            │
├─────────────────────────────────────────────────────────────┤
│                    [跳过] [完成配置]                         │
└─────────────────────────────────────────────────────────────┘
```

#### 3.7.2 启动检测API

```python
# server/app/api/bootstrap.py
from fastapi import APIRouter
from server.local.local_config import LocalAIConfig
from server.utils.bootstrap import get_status, bootstrap_all

router = APIRouter(prefix="/api/bootstrap", tags=["启动检测"])

@router.get("/status")
async def get_bootstrap_status():
    """获取启动检测状态"""
    status = get_status()
    ai_initialized = LocalAIConfig.is_initialized()
    
    return {
        "ffmpeg": status.get("ffmpeg", {}),
        "models": status.get("models", {}),
        "ai_configured": ai_initialized,
        "need_setup": not ai_initialized,
        "suggestions": status.get("suggestions", [])
    }

@router.post("/start")
async def start_bootstrap():
    """开始环境检测和下载"""
    result = bootstrap_all()
    return {
        "success": True,
        "result": result
    }
```

---

## 4. 依赖变更

### 4.1 移除的依赖

从 `requirements.txt` 中移除：
```
pymysql>=1.1.0
sqlalchemy>=2.0.0
redis-py-cluster>=2.1.3
redis==3.5.3
```

### 4.2 保留的依赖

保留所有AI相关、语音识别相关、直播抓取相关的依赖。

---

## 5. 迁移步骤

### Phase 1: 后端本地化
1. 创建 `server/local/` 目录和本地存储服务
2. 修改 `server/app/main.py` 移除数据库初始化
3. 修改 `server/app/core/dependencies.py` 简化认证
4. 修改 `server/ai/ai_gateway.py` 从本地配置读取

### Phase 2: 移除订阅机制
1. 删除 `server/app/api/subscription.py`
2. 删除 `server/app/services/subscription_service.py`
3. 修改前端移除付费检查

### Phase 3: 前端本地化
1. 修改 `main.tsx` 设置本地用户
2. 删除登录页面和订阅页面
3. 创建初次启动向导组件

### Phase 4: 功能优化
1. 移除SenseVoice内存检查
2. 优化AI错误提示
3. 集成自动下载功能

### Phase 5: 清理和测试
1. 移除未使用的数据库依赖
2. 编写测试脚本
3. 验证所有功能

---

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据迁移 | 现有数据丢失 | 提供数据导出工具 |
| 并发写入 | JSON文件损坏 | 使用文件锁 |
| 模型下载失败 | 语音功能不可用 | 提供手动安装指引 |
| AI服务不可用 | 分析功能失效 | 友好错误提示 |

---

**请确认技术方案是否合理。确认后我将进入任务拆分和实施阶段。**

