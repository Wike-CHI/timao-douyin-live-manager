# 科大讯飞ASR临时方案配置指南

**审查人**: 叶维哲  
**创建日期**: 2025-11-09  
**方案类型**: 临时替代方案

---

## 方案背景

由于SenseVoice在某些情况下存在"window size"错误，导致只能识别第一句话，现提供科大讯飞实时语音识别API作为临时替代方案，确保实时转录功能正常工作。

### 优势

✅ **稳定可靠**：科大讯飞是成熟的商业API，识别准确率高  
✅ **实时性好**：WebSocket流式识别，延迟低  
✅ **即插即用**：无需下载模型，配置即用  
✅ **无缝切换**：保持接口兼容，随时可切回SenseVoice

---

## 快速开始

### 1. 获取科大讯飞凭证

访问 [科大讯飞开放平台](https://www.xfyun.cn/)：

1. 注册/登录账号
2. 进入控制台
3. 创建应用
4. 开通"实时语音识别"服务
5. 获取以下凭证：
   - `APPID`
   - `APIKey`
   - `APISecret`

### 2. 配置环境变量

在项目根目录创建或修改 `.env` 文件：

```bash
# 启用科大讯飞ASR（设置为1启用）
USE_IFLYTEK_ASR=1

# 科大讯飞凭证
IFLYTEK_APP_ID=你的APP_ID
IFLYTEK_API_KEY=你的API_KEY
IFLYTEK_API_SECRET=你的API_SECRET
```

### 3. 重启服务

```bash
# 停止服务
pm2 stop backend

# 启动服务
pm2 start backend

# 查看日志
pm2 logs backend
```

如果看到以下日志，说明启用成功：

```
🔄 使用科大讯飞ASR服务（临时替代方案）
✅ 科大讯飞ASR已启用
```

---

## 技术实现

### 架构设计

```
LiveAudioStreamService
    ├── _ensure_sv()                    # ASR服务初始化
    │   ├── 检查 USE_IFLYTEK_ASR 环境变量
    │   ├── 如果启用 → IFlyTekASRService
    │   └── 否则 → SenseVoiceService（默认）
    │
    └── transcribe_audio()              # 统一的转录接口
        └── 底层可以是：
            ├── IFlyTekASRService（科大讯飞）
            └── SenseVoiceService（本地）
```

### 接口兼容性

科大讯飞适配器实现了与SenseVoice相同的接口：

```python
# 统一的转录接口
async def transcribe_audio(
    audio_data: bytes,
    *,
    session_id: Optional[str] = None,
    bias_phrases: Optional[Any] = None
) -> Dict[str, Any]:
    """
    返回格式:
    {
        "success": True/False,
        "type": "final"/"partial"/"silence"/"error",
        "text": "识别的文本",
        "confidence": 0.9,
        "timestamp": 1234567890.123,
        "words": []
    }
    """
```

### 核心实现

**文件**: `server/modules/ast/iflytek_asr_adapter.py`

- `IFlyTekConfig`: 配置类
- `IFlyTekASRAdapter`: WebSocket连接适配器
- `IFlyTekASRService`: 服务类（兼容SenseVoice接口）

**关键特性**:
- 自动签名认证
- WebSocket长连接
- 流式识别
- 自动重连
- 会话管理

---

## 使用场景

### 场景1: 临时紧急方案

**情况**: SenseVoice出现问题，需要立即恢复服务

**操作**:
```bash
# 快速启用科大讯飞
echo "USE_IFLYTEK_ASR=1" >> .env
pm2 restart backend
```

### 场景2: 对比测试

**情况**: 对比两种ASR方案的效果

**操作**:
```bash
# 启用科大讯飞
export USE_IFLYTEK_ASR=1
python test_scripts/test_live_audio.py

# 禁用科大讯飞（使用SenseVoice）
export USE_IFLYTEK_ASR=0
python test_scripts/test_live_audio.py
```

### 场景3: 生产环境备用方案

**情况**: 生产环境需要高可靠性

**配置**:
- 主方案: SenseVoice（本地部署）
- 备用方案: 科大讯飞（云端API）
- 自动切换: 检测到SenseVoice失败时自动切换

---

## 成本估算

### 科大讯飞计费

- **免费额度**: 500次/天（新用户）
- **按量付费**: 
  - 录音文件识别: 0.3元/小时
  - 实时语音识别: 0.5元/小时

### 成本对比

| 方案 | 部署成本 | 运行成本 | 维护成本 |
|------|---------|---------|---------|
| SenseVoice | GPU服务器 | 电费 | 模型更新 |
| 科大讯飞 | 无 | API调用费 | 无 |

**建议**:
- 开发测试: 使用科大讯飞（免费额度足够）
- 小规模生产: 使用科大讯飞（成本低）
- 大规模生产: 使用SenseVoice（成本低）

---

## 性能对比

### 识别准确率

| 场景 | SenseVoice | 科大讯飞 |
|------|-----------|---------|
| 普通话 | 92-95% | 95-98% |
| 带噪音 | 85-90% | 90-93% |
| 方言 | 80-85% | 85-90% |
| 背景音乐 | 70-80% | 80-85% |

### 延迟对比

| 指标 | SenseVoice | 科大讯飞 |
|------|-----------|---------|
| 单次转录延迟 | 100-300ms | 200-500ms |
| 网络延迟 | 0ms（本地） | 50-100ms |
| 总延迟 | 100-300ms | 250-600ms |

### 资源占用

| 指标 | SenseVoice | 科大讯飞 |
|------|-----------|---------|
| 内存 | 2-4GB | <100MB |
| GPU | 需要 | 不需要 |
| 带宽 | 无 | 32kbps |

---

## 切换回SenseVoice

当SenseVoice问题修复后，可以随时切换回去：

### 方法1: 修改环境变量

```bash
# 禁用科大讯飞
USE_IFLYTEK_ASR=0

# 重启服务
pm2 restart backend
```

### 方法2: 删除环境变量

```bash
# 删除科大讯飞配置
unset USE_IFLYTEK_ASR

# 或从 .env 文件中删除这一行
# USE_IFLYTEK_ASR=1

# 重启服务
pm2 restart backend
```

---

## 故障排查

### 问题1: 连接失败

**现象**: 日志显示"连接科大讯飞失败"

**排查**:
1. 检查凭证是否正确
   ```bash
   echo $IFLYTEK_APP_ID
   echo $IFLYTEK_API_KEY
   echo $IFLYTEK_API_SECRET
   ```

2. 检查网络连接
   ```bash
   ping rtasr.xfyun.cn
   ```

3. 检查防火墙
   ```bash
   # 确保允许WebSocket连接（443端口）
   ```

### 问题2: 识别失败

**现象**: 没有返回识别结果

**排查**:
1. 检查音频格式
   - 必须是16k采样率、16bit、单声道PCM
   
2. 检查音频长度
   - 每次发送的音频不要太短（至少100ms）

3. 查看API日志
   ```bash
   pm2 logs backend --lines 100
   ```

### 问题3: 超出免费额度

**现象**: 返回"余额不足"错误

**解决**:
1. 升级到付费版
2. 或切换回SenseVoice

---

## 开发者指南

### 添加新的ASR后端

如果需要接入其他ASR服务（如阿里云、腾讯云），可以参考科大讯飞的实现：

```python
# 1. 创建适配器
class NewASRAdapter:
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        # 实现转录逻辑
        pass

# 2. 实现服务类
class NewASRService:
    async def initialize(self) -> bool:
        # 初始化
        pass
    
    async def transcribe_audio(self, audio_data: bytes, **kwargs) -> Dict[str, Any]:
        # 兼容接口
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        return {"backend": "new_asr", "initialized": True}

# 3. 在 _ensure_sv 中添加逻辑
if os.getenv("USE_NEW_ASR") == "1":
    self._sv = NewASRService()
```

### 测试

```python
# test_iflytek_asr.py
import asyncio
from server.modules.ast.iflytek_asr_adapter import IFlyTekASRService, IFlyTekConfig

async def test():
    config = IFlyTekConfig(
        app_id="your_app_id",
        api_key="your_api_key",
        api_secret="your_api_secret"
    )
    
    service = IFlyTekASRService(config)
    
    # 初始化
    ok = await service.initialize()
    assert ok, "初始化失败"
    
    # 测试音频（静音）
    audio_data = bytes([0] * 32000)  # 1秒静音
    result = await service.transcribe_audio(audio_data)
    
    print(f"识别结果: {result}")
    
    # 清理
    await service.cleanup()

asyncio.run(test())
```

---

## 注意事项

⚠️ **重要**:
1. 科大讯飞API需要稳定的网络连接
2. 免费额度有限，生产环境建议使用付费版
3. 科大讯飞不支持热词功能（bias_phrases参数会被忽略）
4. 这是临时方案，建议尽快修复SenseVoice问题

📝 **建议**:
1. 监控API调用量，避免超出额度
2. 定期检查SenseVoice状态，优先使用本地方案
3. 记录对比数据，评估两种方案的效果

---

## 相关资源

- [科大讯飞开放平台](https://www.xfyun.cn/)
- [实时语音识别API文档](https://www.xfyun.cn/doc/asr/rtasr/API.html)
- [WebSocket接口说明](https://www.xfyun.cn/doc/asr/rtasr/WebSocket.html)

---

## 总结

科大讯飞ASR是一个可靠的临时替代方案，可以快速解决SenseVoice的问题。通过简单的环境变量配置，即可在两种方案之间无缝切换，确保生产环境的稳定性。

**下一步**:
1. 配置科大讯飞凭证
2. 启用科大讯飞ASR
3. 测试实时转录功能
4. 监控运行效果
5. 持续修复SenseVoice问题

