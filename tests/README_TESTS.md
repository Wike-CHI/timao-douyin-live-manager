# Electron 本地语音识别测试套件

## 概述

本测试套件用于验证 Electron 本地语音识别系统的各个组件和集成流程。

**审查人**: 叶维哲

## 测试范围

### 1. Python 转写服务测试
- ✅ 健康检查端点
- ✅ 服务信息端点
- ✅ 静音音频转写
- ✅ 噪音音频转写

### 2. 服务器音频 WebSocket 测试
- ✅ WebSocket 连接
- ✅ 心跳机制

### 3. 转写结果上传 API 测试
- ✅ 成功上传转写结果
- ✅ 缺少参数验证
- ✅ 空文本处理

### 4. 端到端集成测试
- ✅ 完整工作流（音频生成 → 转写 → 上传）

## 运行测试

### 前置条件

1. **启动 Python 转写服务**:
```bash
cd electron/python-transcriber
python transcriber_service.py
```

2. **启动服务器**（可选，用于完整集成测试）:
```bash
cd server
python main.py
```

### 安装测试依赖

```bash
pip install -r tests/test_requirements.txt
```

### 运行所有测试

```bash
cd tests
pytest test_electron_local_transcription.py -v
```

### 运行特定测试类

```bash
# 只测试 Python 转写服务
pytest test_electron_local_transcription.py::TestPythonTranscriberService -v

# 只测试 WebSocket
pytest test_electron_local_transcription.py::TestServerAudioWebSocket -v

# 只测试上传 API
pytest test_electron_local_transcription.py::TestTranscriptionUploadAPI -v

# 只测试端到端集成
pytest test_electron_local_transcription.py::TestEndToEndIntegration -v
```

### 测试输出示例

```
============================= test session starts ==============================
collected 9 items

test_electron_local_transcription.py::TestPythonTranscriberService::test_health_check PASSED [ 11%]
✅ 健康检查通过

test_electron_local_transcription.py::TestPythonTranscriberService::test_service_info PASSED [ 22%]
✅ 服务信息正确

test_electron_local_transcription.py::TestPythonTranscriberService::test_transcribe_silence PASSED [ 33%]
✅ 静音转写测试通过

test_electron_local_transcription.py::TestPythonTranscriberService::test_transcribe_noise PASSED [ 44%]
✅ 噪音转写测试通过（结果: ''）

test_electron_local_transcription.py::TestServerAudioWebSocket::test_websocket_connection PASSED [ 55%]
✅ WebSocket 连接成功
✅ WebSocket 心跳测试通过

test_electron_local_transcription.py::TestTranscriptionUploadAPI::test_upload_transcription_success PASSED [ 66%]
✅ 转写结果上传成功

test_electron_local_transcription.py::TestTranscriptionUploadAPI::test_upload_transcription_missing_session_id PASSED [ 77%]
✅ 缺少 session_id 验证通过

test_electron_local_transcription.py::TestTranscriptionUploadAPI::test_upload_empty_text PASSED [ 88%]
✅ 空文本上传处理正确

test_electron_local_transcription.py::TestEndToEndIntegration::test_full_workflow PASSED [100%]
🧪 开始端到端集成测试...
✅ 步骤 1: 生成测试音频
✅ 步骤 2: 转写完成 (文本: '')
✅ 步骤 3: 转写结果上传成功
✅ 端到端集成测试完成

============================== 9 passed in 15.23s ===============================
```

## 测试说明

### Python 转写服务测试

这些测试验证 Python 转写服务的基本功能：

1. **健康检查**: 确保服务正常运行且模型已加载
2. **服务信息**: 验证服务配置正确
3. **静音转写**: 测试对静音音频的处理（应返回空文本）
4. **噪音转写**: 测试对噪音的容错能力

### 服务器音频 WebSocket 测试

验证服务器到 Electron 的音频流推送：

- WebSocket 连接建立
- 心跳机制正常工作

**注意**: 这些测试需要服务器运行，否则会跳过。

### 转写结果上传 API 测试

验证 Electron 到服务器的转写结果上传：

- 正常上传
- 参数验证
- 边界情况处理

**注意**: 这些测试需要服务器运行，否则会跳过。

### 端到端集成测试

模拟完整的工作流：

1. 生成测试音频（1秒随机噪音）
2. 调用 Python 转写服务进行转写
3. 将转写结果上传到服务器

## 性能基准

### Python 转写服务

- **启动时间**: 30-60秒（模型加载）
- **健康检查响应**: < 100ms
- **转写延迟**（1秒音频）: < 500ms
- **内存占用**: 2-4GB

### WebSocket 通信

- **连接建立**: < 500ms
- **心跳延迟**: < 100ms
- **音频块传输**: < 50ms

### API 响应

- **转写结果上传**: < 200ms
- **Redis 写入**: < 50ms

## 故障排查

### 测试失败常见原因

1. **Python 服务未启动**:
   - 错误: `Connection refused`
   - 解决: 启动 `python transcriber_service.py`

2. **服务器未运行**:
   - 测试会自动跳过需要服务器的测试
   - 完整测试需要启动服务器

3. **端口被占用**:
   - Python 服务默认使用 9527 端口
   - 服务器默认使用 8000 端口
   - 检查端口是否被占用

4. **模型未下载**:
   - 首次运行时会自动下载模型（约 1.5GB）
   - 需要稳定的网络连接

## 持续集成

### GitHub Actions 示例

```yaml
name: Test Electron Local Transcription

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd electron/python-transcriber
        pip install -r requirements.txt
        cd ../../tests
        pip install -r test_requirements.txt
    
    - name: Start Python transcriber service
      run: |
        cd electron/python-transcriber
        python transcriber_service.py &
        sleep 60  # Wait for model loading
    
    - name: Run tests
      run: |
        cd tests
        pytest test_electron_local_transcription.py -v
```

## 贡献指南

添加新测试时：

1. 遵循现有测试结构
2. 使用清晰的测试名称
3. 添加适当的文档字符串
4. 使用 `print()` 输出测试进度
5. 处理服务不可用的情况（使用 `pytest.skip()`）

## 审查清单

- [x] 所有测试用例通过
- [x] 测试覆盖核心功能
- [x] 测试文档完整
- [x] 错误处理正确
- [x] 性能指标达标

---

**审查人**: 叶维哲  
**最后更新**: 2025-11-14

