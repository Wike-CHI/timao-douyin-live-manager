# 前端招聘挑战 - 验证测试文档

## 任务一：转写流模式切换恢复

### 问题描述
`deltaModeRef` 在 WebSocket 重连或新会话启动时没有正确重置，导致：
- 从增量模式切换回全文模式时，全文消息被忽略
- 停止再启动后，字幕可能卡死

### 修复方案
在三个关键位置重置 `deltaModeRef`：
1. **connectWebSocket()**: WebSocket 连接/重连时重置
2. **handleStart()**: 新会话启动时重置
3. **handleStop()**: 停止会话时重置

### 代码变更
**文件**: `electron/renderer/src/pages/dashboard/LiveConsolePage.tsx`

```typescript
// 1. connectWebSocket - 第140-178行
const connectWebSocket = useCallback(() => {
  if (socketRef.current) socketRef.current.close();
  // ✅ 新增：重置 deltaModeRef，确保新连接能正常接收所有消息类型
  deltaModeRef.current = false;
  const socket = openLiveAudioWebSocket(...);
  socketRef.current = socket;
}, [handleSocketMessage, appendLog]);

// 2. handleStart - 第284-287行
// 3) 录制整场（30 分钟分段）
try { await startLiveReport(liveUrl, 30, FASTAPI_BASE_URL); } catch {}

// ✅ 新增：重置 deltaModeRef，确保新会话能正常接收全文消息
deltaModeRef.current = false;
await refreshStatus();
connectWebSocket();

// 3. handleStop - 第322-323行
if (socketRef.current) {
  socketRef.current.close();
  socketRef.current = null;
}
// ✅ 新增：重置 deltaModeRef，确保下次会话能正常接收全文消息
deltaModeRef.current = false;
setSaveInfo(null);
```

### 验证步骤

#### 场景1：正常启动与停止
```bash
1. 启动应用：npm run dev
2. 打开 LiveConsolePage
3. 输入直播地址，点击"开始转写"
4. ✅ 验证点：字幕正常显示（观察 Console 无错误）
5. 点击"停止"
6. ✅ 验证点：deltaModeRef 被重置为 false
```

#### 场景2：WebSocket 重连
```bash
1. 启动应用并开始转写
2. 模拟网络中断（Chrome DevTools > Network > Offline）
3. 等待 5 秒后恢复网络
4. ✅ 验证点：WebSocket 自动重连，字幕继续显示
5. ✅ 验证点：重连后能正常接收 transcription 消息（不被忽略）
```

#### 场景3：连续启动多次
```bash
1. 启动转写
2. 停止转写
3. 再次启动转写（同一直播间或不同直播间）
4. ✅ 验证点：第二次启动时字幕正常显示
5. ✅ 验证点：不会因 deltaModeRef 残留而卡死
```

#### 场景4：增量模式与全文模式切换
```bash
1. 启动转写
2. 等待收到 transcription_delta 消息（deltaModeRef 变为 true）
3. 停止转写
4. 重新启动转写
5. ✅ 验证点：新会话能正常接收 transcription 全文消息
6. ✅ 验证点：不会因为之前的 deltaModeRef=true 而忽略消息
```

### 测试脚本
创建文件 `tests/test_deltamode_lifecycle.js`:

```javascript
// 测试 deltaModeRef 生命周期
// 运行方式：node tests/test_deltamode_lifecycle.js

const WebSocket = require('ws');

const FASTAPI_BASE_URL = 'http://127.0.0.1:8090';
const WS_URL = 'ws://127.0.0.1:8090/api/live_audio/ws';

async function testDeltaModeLifecycle() {
  console.log('测试一：正常启动与停止');
  
  // 1. 启动转写
  const startRes = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ live_url: 'test_room_id' }),
  });
  const startData = await startRes.json();
  console.log('✅ 启动成功:', startData);

  // 2. 连接 WebSocket
  const ws = new WebSocket(WS_URL);
  let receivedMessages = [];

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    receivedMessages.push(msg);
    console.log('📨 收到消息:', msg.type);
  });

  await new Promise(resolve => setTimeout(resolve, 5000));

  // 3. 停止转写
  const stopRes = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/stop`, {
    method: 'POST',
  });
  console.log('✅ 停止成功');

  // 4. 再次启动
  const restartRes = await fetch(`${FASTAPI_BASE_URL}/api/live_audio/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ live_url: 'test_room_id_2' }),
  });
  console.log('✅ 重启成功');

  await new Promise(resolve => setTimeout(resolve, 3000));

  // 验证：检查是否收到 transcription 消息
  const hasTranscription = receivedMessages.some(m => m.type === 'transcription');
  console.log(`\n验证结果: ${hasTranscription ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`收到消息类型: ${receivedMessages.map(m => m.type).join(', ')}`);

  ws.close();
  process.exit(hasTranscription ? 0 : 1);
}

testDeltaModeLifecycle().catch(console.error);
```

### 预期结果
- ✅ 所有场景下字幕正常显示
- ✅ 没有"消息被忽略"的警告
- ✅ deltaModeRef 在关键时刻正确重置

---

## 任务二：AI 功能鉴权一致性

### 问题描述
LiveConsolePage 中的 AI 接口调用未统一添加鉴权信息：
- REST 请求缺少 `Authorization` 头
- SSE (EventSource) 无法自定义 headers
- 可能导致鉴权开启后功能失效

### 修复方案
1. 创建统一的 AI 服务模块 (`services/ai.ts`)
2. 实现 `authFetch` 包装函数，自动添加 Bearer Token
3. 为 EventSource 实现 URL 参数传递 token（因其不支持自定义 headers）
4. 更新所有 AI 接口调用

### 代码变更

#### 1. 新建文件: `electron/renderer/src/services/ai.ts`
```typescript
import useAuthStore from '../store/useAuthStore';

/**
 * 构建包含鉴权信息的请求头
 */
const buildHeaders = (): Record<string, string> => {
  const { token } = useAuthStore.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

/**
 * 构建包含 token 的 URL（用于 EventSource）
 */
const buildAuthUrl = (url: string): string => {
  const { token } = useAuthStore.getState();
  if (!token) return url;
  
  const urlObj = new URL(url);
  urlObj.searchParams.set('token', token);
  return urlObj.toString();
};

/**
 * 统一的 fetch 包装函数，自动添加鉴权头
 */
const authFetch = async (url: string, options?: RequestInit): Promise<Response> => {
  const headers = {
    ...buildHeaders(),
    ...(options?.headers || {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
};

// ... 导出 API 函数
export const startAILiveAnalysis = async (payload, baseUrl) => {
  const response = await authFetch(`${baseUrl}/api/ai/live/start`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};

export const openAILiveStream = (onMessage, onError, baseUrl) => {
  // EventSource 不支持自定义 headers，通过 URL 参数传递 token
  const url = buildAuthUrl(`${baseUrl}/api/ai/live/stream`);
  const eventSource = new EventSource(url);
  eventSource.onmessage = onMessage;
  if (onError) eventSource.onerror = onError;
  return eventSource;
};
```

#### 2. 更新: `LiveConsolePage.tsx`
```typescript
// 添加导入
import { startAILiveAnalysis, stopAILiveAnalysis, openAILiveStream, generateOneScript } from '../../services/ai';

// 更新 AI 流连接（第393-418行）
const connectAIStream = useCallback(() => {
  if (aiSourceRef.current) return;
  // ✅ 使用统一的鉴权 SSE 流
  const es = openAILiveStream(
    (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data?.type === 'ai') {
          setAiEvents((prev) => [data.payload, ...prev].slice(0, 10));
          // ...
        }
      } catch {}
    },
    () => {
      // 错误处理
      try { if (aiSourceRef.current) aiSourceRef.current.close(); } catch {}
      aiSourceRef.current = null;
      setTimeout(connectAIStream, 1500);
    },
    FASTAPI_BASE_URL
  );
  aiSourceRef.current = es;
}, []);

// 更新启动/停止 AI 分析（第420-431行）
useEffect(() => {
  if (isRunning) {
    const ws = Math.max(30, Math.min(600, Number(aiWindowSec) || 60));
    // ✅ 使用统一的鉴权接口
    startAILiveAnalysis({ window_sec: ws }, FASTAPI_BASE_URL).catch(() => {});
    connectAIStream();
  } else {
    try { stopAILiveAnalysis(FASTAPI_BASE_URL).catch(() => {}); } catch {}
    if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; }
  }
  return () => { if (aiSourceRef.current) { aiSourceRef.current.close(); aiSourceRef.current = null; } };
}, [isRunning, connectAIStream]);

// 更新话术生成（第433-450行）
const handleGenerateOne = useCallback(async () => {
  try {
    setGenBusy(true);
    setOneScript('');
    // ✅ 使用统一鉴权接口
    const res = await generateOneScript(
      { script_type: oneType, include_context: true },
      FASTAPI_BASE_URL
    );
    const text = res?.data?.content || '';
    if (text) setOneScript(String(text));
  } catch (e) {
    console.error(e);
    setOneScript('生成失败，请稍后再试');
  } finally {
    setGenBusy(false);
  }
}, [oneType]);
```

### 鉴权策略说明

#### 1. REST API 鉴权
- 通过 `Authorization: Bearer <token>` 请求头
- token 从 `useAuthStore` 获取
- 所有 AI 相关 REST 请求自动添加

#### 2. SSE (EventSource) 鉴权
- EventSource 不支持自定义 headers
- 解决方案：通过 URL 参数传递 token
- 格式：`/api/ai/live/stream?token=<token>`

#### 3. WebSocket 鉴权（预留）
- WebSocket 支持在握手时传递 headers 或 URL 参数
- 当前 `liveAudio.ts` 中的 `openLiveAudioWebSocket` 已实现 token 传递
- 如需扩展，可参考 `buildAuthUrl` 实现

### 配置方式

#### 环境变量配置
```bash
# .env 文件
VITE_AUTH_ENABLED=true  # 是否启用鉴权
VITE_FASTAPI_URL=http://127.0.0.1:8090  # API 地址
```

#### 后端配置（FastAPI）
```python
# server/app/api/*.py
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token: str = Query(None)  # 支持 URL 参数（用于 SSE）
):
    """统一鉴权中间件"""
    # 优先使用 Authorization header
    if credentials:
        token_str = credentials.credentials
    # 其次使用 URL 参数（用于 EventSource）
    elif token:
        token_str = token
    else:
        raise HTTPException(status_code=401, detail="未授权")
    
    # 验证 token
    if not validate_token(token_str):
        raise HTTPException(status_code=401, detail="Token 无效")
    
    return token_str

# 在路由中使用
@router.get("/api/ai/live/stream")
async def ai_live_stream(token_data: str = Depends(verify_token)):
    # ...鉴权通过后的逻辑
```

### 验证步骤

#### 场景1：未开启鉴权（兼容性测试）
```bash
1. 后端不启用鉴权中间件
2. 启动应用，使用 AI 功能
3. ✅ 验证点：所有 AI 功能正常工作
4. ✅ 验证点：即使没有 token，也不影响功能
```

#### 场景2：开启鉴权 - 有效 Token
```bash
1. 后端启用鉴权中间件
2. 登录获取有效 token
3. 使用 AI 实时分析
4. ✅ 验证点：SSE 连接成功，URL 包含 token 参数
5. 使用 AI 话术生成
6. ✅ 验证点：请求头包含 Authorization: Bearer <token>
7. ✅ 验证点：所有 AI 功能正常
```

#### 场景3：开启鉴权 - 无效 Token
```bash
1. 后端启用鉴权中间件
2. 不登录或使用过期 token
3. 尝试使用 AI 功能
4. ✅ 验证点：收到 401 Unauthorized 错误
5. ✅ 验证点：前端显示友好的错误提示
6. ✅ 验证点：不会因鉴权失败而崩溃
```

#### 场景4：Token 更新
```bash
1. 登录并使用 AI 功能
2. Token 更新（重新登录或刷新 token）
3. 继续使用 AI 功能
4. ✅ 验证点：新请求自动使用新 token
5. ✅ 验证点：不需要刷新页面
```

### 测试脚本
创建文件 `tests/test_ai_auth.sh`:

```bash
#!/bin/bash
# AI 接口鉴权测试

BASE_URL="http://127.0.0.1:8090"
TOKEN="test_token_12345"

echo "测试一：无 Token 访问（应失败）"
curl -X POST "$BASE_URL/api/ai/live/start" \
  -H "Content-Type: application/json" \
  -d '{"window_sec": 60}'
echo "\n"

echo "测试二：有效 Token 访问（应成功）"
curl -X POST "$BASE_URL/api/ai/live/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"window_sec": 60}'
echo "\n"

echo "测试三：SSE 流 - URL 参数传递 Token"
curl "$BASE_URL/api/ai/live/stream?token=$TOKEN"
echo "\n"

echo "测试四：生成话术（有 Token）"
curl -X POST "$BASE_URL/api/ai/scripts/generate_one" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"script_type": "interaction", "include_context": true}'
echo "\n"
```

### 预期结果
- ✅ 所有 AI 接口请求包含鉴权信息
- ✅ 鉴权开启时，有效 token 可正常访问
- ✅ 鉴权开启时，无效 token 被拒绝
- ✅ SSE 流通过 URL 参数传递 token

---

## 任务三：支付审核状态机优化

### 问题描述
原实现一次性轮询，无法处理人工审核延迟：
- 提交后立即轮询一次，如果未审核则误报失败
- 没有 PENDING 状态的持续轮询
- 用户体验差，无法感知审核进度

### 修复方案
实现完整的状态机：
1. **四种状态**: UNPAID → PENDING → APPROVED/REJECTED
2. **循环轮询**: 每 3 秒轮询一次，最多 5 分钟
3. **进度指示**: 显示轮询次数和进度条
4. **超时处理**: 达到超时或最大次数后提示用户
5. **用户控制**: 可取消轮询并重新提交

### 状态流转图

```
           上传成功
UNPAID ──────────────> PENDING ──────────────> APPROVED (审核通过)
  │                       │                         │
  │                       │                         ↓
  │                       └──────> timeout       结束流程
  │                       │
  │                       └──────> REJECTED (审核拒绝)
  │                                   │
  │                                   ↓
  └───────────────────────────────> UNPAID (重新提交)

轮询策略：
- 间隔：3 秒
- 最大次数：100 次
- 总超时：5 分钟
- 进度显示：实时更新
```

### 代码变更
**文件**: `electron/renderer/src/pages/payment/PaymentVerifyPage.tsx`

#### 1. 类型定义
```typescript
type PaymentStatus = 'UNPAID' | 'PENDING' | 'APPROVED' | 'REJECTED';

interface PollConfig {
  interval: number; // 轮询间隔（毫秒）
  maxAttempts: number; // 最大轮询次数
  timeout: number; // 总超时时间（毫秒）
}

const DEFAULT_POLL_CONFIG: PollConfig = {
  interval: 3000, // 每3秒轮询一次
  maxAttempts: 100, // 最多轮询100次
  timeout: 5 * 60 * 1000, // 总超时5分钟
};
```

#### 2. 状态管理
```typescript
const [status, setStatus] = useState<PaymentStatus>('UNPAID');
const [pollAttempts, setPollAttempts] = useState(0);
const [pollProgress, setPollProgress] = useState(0); // 0-100

const pollingRef = useRef<NodeJS.Timeout | null>(null);
const startTimeRef = useRef<number>(0);
```

#### 3. 轮询逻辑
```typescript
const startPolling = (config: PollConfig = DEFAULT_POLL_CONFIG) => {
  // 清理之前的轮询
  if (pollingRef.current) {
    clearInterval(pollingRef.current);
    pollingRef.current = null;
  }

  startTimeRef.current = Date.now();
  let attempts = 0;

  const poll = async () => {
    try {
      attempts += 1;
      setPollAttempts(attempts);

      // 计算进度
      const elapsed = Date.now() - startTimeRef.current;
      const timeProgress = Math.min((elapsed / config.timeout) * 100, 100);
      const attemptProgress = Math.min((attempts / config.maxAttempts) * 100, 100);
      setPollProgress(Math.max(timeProgress, attemptProgress));

      // 检查超时
      if (elapsed >= config.timeout) {
        stopPolling();
        setStatus('PENDING');
        setMessage(`审核超时（已轮询 ${attempts} 次）。请稍后刷新查看结果。`);
        return;
      }

      // 检查最大次数
      if (attempts >= config.maxAttempts) {
        stopPolling();
        setStatus('PENDING');
        setMessage(`已达最大轮询次数（${attempts} 次）。请稍后刷新查看结果。`);
        return;
      }

      // 调用后端查询
      const pollResult = await pollPayment();
      
      if (pollResult.success) {
        const paymentStatus = (pollResult.status || 'pending').toLowerCase();
        
        if (paymentStatus === 'approved' || paymentStatus === 'paid') {
          // ✅ 审核通过
          stopPolling();
          setStatus('APPROVED');
          setMessage('审核通过！');
          setPaid(true);
          setPollProgress(100);
        } else if (paymentStatus === 'rejected' || paymentStatus === 'failed') {
          // ❌ 审核拒绝
          stopPolling();
          setStatus('REJECTED');
          setMessage(pollResult.message || '审核未通过，请重新提交。');
          setPollProgress(0);
        } else {
          // ⏳ 仍在审核中
          setStatus('PENDING');
          setMessage(`审核中...（已等待 ${Math.floor(elapsed / 1000)} 秒）`);
        }
      } else {
        // 查询失败，继续轮询
        console.warn('轮询失败:', pollResult.message);
      }
    } catch (err) {
      console.error('轮询错误:', err);
    }
  };

  // 立即执行第一次
  poll();
  // 启动定时轮询
  pollingRef.current = setInterval(poll, config.interval);
};
```

#### 4. UI 优化
```typescript
// 状态指示器
<div className={`flex items-center gap-3 mb-4 p-4 rounded-2xl ${
  status === 'APPROVED' ? 'bg-green-50 border border-green-200' :
  status === 'REJECTED' ? 'bg-red-50 border border-red-200' :
  status === 'PENDING' ? 'bg-purple-50 border border-purple-200' :
  'bg-slate-50 border border-slate-200'
}`}>
  <span className="text-2xl">{statusConfig.icon}</span>
  <div className="flex-1">
    <div className={`font-semibold ${statusConfig.color}`}>{statusConfig.title}</div>
    <p className={`text-sm ${statusConfig.color}`}>{message}</p>
  </div>
</div>

// 进度条（PENDING 状态）
{status === 'PENDING' && pollProgress > 0 && (
  <div className="mb-4">
    <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
      <span>审核进度</span>
      <span>{pollAttempts} 次查询 · {Math.round(pollProgress)}%</span>
    </div>
    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
      <div 
        className="h-full bg-purple-500 transition-all duration-300"
        style={{ width: `${Math.min(pollProgress, 100)}%` }}
      />
    </div>
  </div>
)}
```

### 验证步骤

#### 场景1：审核通过（正常流程）
```bash
1. 上传支付凭证
2. ✅ 验证点：状态变为 PENDING
3. ✅ 验证点：开始轮询，进度条显示
4. 后台将审核状态设为 APPROVED
5. ✅ 验证点：轮询检测到 APPROVED，停止轮询
6. ✅ 验证点：状态变为 APPROVED，显示成功提示
7. ✅ 验证点：setPaid(true) 被调用
```

#### 场景2：审核拒绝
```bash
1. 上传支付凭证
2. 状态变为 PENDING，开始轮询
3. 后台将审核状态设为 REJECTED
4. ✅ 验证点：轮询检测到 REJECTED，停止轮询
5. ✅ 验证点：状态变为 REJECTED，显示拒绝原因
6. ✅ 验证点：表单重新显示，允许重新提交
```

#### 场景3：审核超时
```bash
1. 上传支付凭证
2. 状态变为 PENDING，开始轮询
3. 等待 5 分钟（或修改 timeout 为 10 秒快速测试）
4. ✅ 验证点：达到超时时间，停止轮询
5. ✅ 验证点：显示超时提示，状态保持 PENDING
6. ✅ 验证点：提示用户稍后刷新或联系客服
```

#### 场景4：用户取消轮询
```bash
1. 上传支付凭证，开始轮询
2. 轮询进行中，用户点击"取消审核并重新提交"
3. ✅ 验证点：轮询停止
4. ✅ 验证点：状态变回 UNPAID
5. ✅ 验证点：表单重新显示
```

#### 场景5：网络故障恢复
```bash
1. 上传支付凭证，开始轮询
2. 轮询过程中网络故障
3. ✅ 验证点：轮询失败但不停止，继续尝试
4. 网络恢复
5. ✅ 验证点：轮询继续，最终检测到审核结果
```

### 测试脚本
创建文件 `tests/test_payment_state_machine.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>支付审核状态机测试</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
    .pending { background: #f0e7ff; }
    .approved { background: #e7ffe7; }
    .rejected { background: #ffe7e7; }
    button { margin: 5px; padding: 8px 16px; cursor: pointer; }
  </style>
</head>
<body>
  <h1>支付审核状态机测试</h1>
  
  <div id="status" class="status">状态：UNPAID</div>
  <div id="progress"></div>
  <div id="attempts"></div>
  
  <h3>模拟操作：</h3>
  <button onclick="submitPayment()">1. 提交支付凭证</button>
  <button onclick="approvePayment()">2. 后台批准审核</button>
  <button onclick="rejectPayment()">3. 后台拒绝审核</button>
  <button onclick="cancelPolling()">4. 用户取消轮询</button>
  
  <h3>日志：</h3>
  <div id="log" style="background: #f5f5f5; padding: 10px; height: 300px; overflow-y: scroll;"></div>

  <script>
    let status = 'UNPAID';
    let polling = null;
    let attempts = 0;
    let backendStatus = 'pending'; // 模拟后端状态

    function log(msg) {
      const logDiv = document.getElementById('log');
      const time = new Date().toLocaleTimeString();
      logDiv.innerHTML += `[${time}] ${msg}<br>`;
      logDiv.scrollTop = logDiv.scrollHeight;
    }

    function updateUI() {
      const statusDiv = document.getElementById('status');
      statusDiv.textContent = `状态：${status}`;
      statusDiv.className = `status ${status.toLowerCase()}`;
      
      document.getElementById('progress').textContent = 
        polling ? `轮询中... 第 ${attempts} 次查询` : '';
    }

    function submitPayment() {
      status = 'PENDING';
      attempts = 0;
      backendStatus = 'pending';
      log('📤 提交支付凭证成功');
      updateUI();
      startPolling();
    }

    function startPolling() {
      log('🔄 开始轮询审核状态');
      if (polling) clearInterval(polling);
      
      polling = setInterval(() => {
        attempts++;
        log(`🔍 查询审核状态 (第 ${attempts} 次)`);
        
        // 模拟查询后端
        if (backendStatus === 'approved') {
          stopPolling();
          status = 'APPROVED';
          log('✅ 审核通过！');
          updateUI();
        } else if (backendStatus === 'rejected') {
          stopPolling();
          status = 'REJECTED';
          log('❌ 审核未通过');
          updateUI();
        } else {
          log(`⏳ 仍在审核中...`);
        }
        
        // 模拟超时（10次后）
        if (attempts >= 10) {
          stopPolling();
          log('⏱️ 轮询超时');
        }
        
        updateUI();
      }, 1000); // 1秒轮询一次（测试用）
    }

    function stopPolling() {
      if (polling) {
        clearInterval(polling);
        polling = null;
        log('⏹️ 停止轮询');
      }
    }

    function approvePayment() {
      backendStatus = 'approved';
      log('🎯 [后台操作] 审核状态设为 APPROVED');
    }

    function rejectPayment() {
      backendStatus = 'rejected';
      log('🎯 [后台操作] 审核状态设为 REJECTED');
    }

    function cancelPolling() {
      stopPolling();
      status = 'UNPAID';
      attempts = 0;
      log('🚫 用户取消轮询');
      updateUI();
    }

    log('✨ 测试工具已就绪');
    updateUI();
  </script>
</body>
</html>
```

**运行方式**: 在浏览器中打开 `test_payment_state_machine.html`

### 预期结果
- ✅ 完整的状态流转：UNPAID → PENDING → APPROVED/REJECTED
- ✅ 循环轮询直到得到最终状态
- ✅ 进度条实时显示轮询进度
- ✅ 超时和最大次数限制生效
- ✅ 用户可取消轮询并重新提交
- ✅ 不同状态下 UI 显示正确

---

## 总体验证检查清单

### 功能完整性
- [ ] 任务一：deltaModeRef 在所有场景下正确重置
- [ ] 任务二：所有 AI 接口包含鉴权信息
- [ ] 任务三：支付审核支持完整状态机

### 容错性
- [ ] 网络中断后能自动恢复
- [ ] 鉴权失败不会导致崩溃
- [ ] 轮询超时有友好提示

### 用户体验
- [ ] 字幕显示流畅无卡顿
- [ ] AI 功能响应及时
- [ ] 审核进度可见，操作可控

### 安全性
- [ ] 鉴权 token 正确传递
- [ ] 未授权请求被拒绝
- [ ] 敏感信息不泄露

---

## 环境要求

### 前端
- Node.js >= 16.0.0
- npm >= 8.0.0
- React 18+
- TypeScript 4.9+

### 后端
- Python 3.9+
- FastAPI 0.100+
- uvicorn

### 测试工具
- Chrome DevTools（网络模拟）
- Postman / curl（API 测试）
- 浏览器（状态机可视化测试）

---

## 遗留风险与改进建议

### 任务一
**风险**: 
- 如果后端同时发送 delta 和 全文消息，可能仍有竞态条件
  
**建议**: 
- 后端明确消息类型，避免混合发送
- 前端增加消息序列号验证

### 任务二
**风险**:
- EventSource 通过 URL 传递 token 可能在日志中泄露

**建议**:
- 生产环境使用 HTTPS
- 考虑实现 WebSocket 替代 EventSource（支持自定义 headers）
- 后端日志脱敏

### 任务三
**风险**:
- 长时间轮询消耗资源
- 后端审核状态可能不一致

**建议**:
- 实现 WebSocket 推送替代轮询
- 后端增加审核状态变更通知机制
- 添加指数退避策略（首次快速轮询，后续放慢）

---

**文档版本**: 1.0.0  
**最后更新**: 2025-10-11  
**作者**: 前端负责人

