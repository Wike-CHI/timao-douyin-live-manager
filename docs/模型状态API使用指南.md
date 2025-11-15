# 模型状态 API 使用指南

**审查人**: 叶维哲  
**最后更新**: 2025-11-14  
**版本**: 1.0

---

## 📋 API 概述

提供 SenseVoice + VAD 模型的实时状态查询接口，用于监控模型加载情况、配置信息和系统资源。

### 核心功能

- ✅ 实时查询模型加载状态
- ✅ 验证模型文件完整性
- ✅ 查看环境变量配置
- ✅ 监控系统资源使用
- ✅ 获取健康检查报告
- ✅ 智能问题诊断和建议

---

## 🔌 API 端点

### 1. 完整模型状态

```http
GET /api/model/status
```

**功能**: 返回完整的模型状态信息

**响应示例**:

```json
{
  "status": "warning",
  "timestamp": "2025-11-14 17:35:46",
  "sensevoice": {
    "name": "SenseVoice Small",
    "path": "/www/wwwroot/.../SenseVoiceSmall",
    "exists": true,
    "size_mb": 892.9,
    "env_var": "SENSEVOICE_MODEL_PATH",
    "env_value": "/www/wwwroot/.../SenseVoiceSmall"
  },
  "vad": {
    "name": "VAD (FSMN)",
    "path": "/www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "exists": true,
    "size_mb": 1.6,
    "env_var": "VAD_MODEL_PATH",
    "env_value": "/www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch"
  },
  "vad_config": {
    "chunk_sec": "1.6",
    "min_silence_sec": "0.50",
    "min_speech_sec": "0.30",
    "hangover_sec": "0.40",
    "min_rms": "0.015",
    "music_detect": "1"
  },
  "pytorch_config": {
    "omp_threads": "4",
    "mkl_threads": "4",
    "cpu_alloc_conf": "max_split_size_mb:512"
  },
  "system": {
    "total_memory_gb": 7.38,
    "available_memory_gb": 3.52,
    "memory_percent": 52.4,
    "cpu_percent": 2.6,
    "disk_usage_percent": 76.2,
    "disk_available_gb": 16.67
  },
  "model_cache_dir": "/www/wwwroot/.../.cache/modelscope",
  "enable_preload": "1",
  "checks": {
    "sensevoice_exists": true,
    "vad_exists": true,
    "sensevoice_env_set": true,
    "vad_env_set": true,
    "vad_config_set": true,
    "pytorch_config_set": true,
    "memory_sufficient": true,
    "disk_space_ok": true
  },
  "warnings": [
    "VAD 模型大小异常 (1.6 MB，预期 ~140 MB)"
  ],
  "recommendations": [
    "模型文件可能不完整，建议重新下载"
  ]
}
```

**状态码说明**:

- `healthy` - 所有检查通过，模型配置正常
- `warning` - 模型存在但有配置问题或警告
- `error` - 模型文件缺失或系统资源不足

---

### 2. 简单健康检查

```http
GET /api/model/health
```

**功能**: 快速检查模型健康状态

**响应示例**:

```json
{
  "status": "warning",
  "timestamp": "2025-11-14 17:35:46",
  "checks": {
    "sensevoice_exists": true,
    "vad_exists": true,
    "sensevoice_env_set": true,
    "vad_env_set": true,
    "vad_config_set": true,
    "pytorch_config_set": true,
    "memory_sufficient": true,
    "disk_space_ok": true
  },
  "warnings_count": 1,
  "message": "发现 1 个警告"
}
```

**适用场景**:
- 快速健康检查
- 监控告警
- 定时巡检

---

### 3. 环境变量配置

```http
GET /api/model/config
```

**功能**: 获取所有模型相关的环境变量

**响应示例**:

```json
{
  "status": "success",
  "timestamp": "2025-11-14 17:36:01",
  "config": {
    "model_paths": {
      "SENSEVOICE_MODEL_PATH": "/www/wwwroot/.../SenseVoiceSmall",
      "VAD_MODEL_PATH": "/www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch",
      "MODEL_ROOT": "/www/wwwroot/.../server/models/models/iic",
      "MODEL_CACHE_DIR": "/www/wwwroot/.../.cache/modelscope",
      "MODELSCOPE_CACHE": "/www/wwwroot/.../.cache/modelscope"
    },
    "vad_params": {
      "LIVE_VAD_CHUNK_SEC": "1.6",
      "LIVE_VAD_MIN_SILENCE_SEC": "0.50",
      "LIVE_VAD_MIN_SPEECH_SEC": "0.30",
      "LIVE_VAD_HANGOVER_SEC": "0.40",
      "LIVE_VAD_MIN_RMS": "0.015",
      "LIVE_VAD_MUSIC_DETECT": "1"
    },
    "pytorch_optimization": {
      "OMP_NUM_THREADS": "4",
      "MKL_NUM_THREADS": "4",
      "PYTORCH_CPU_ALLOC_CONF": "max_split_size_mb:512"
    },
    "other": {
      "ENABLE_MODEL_PRELOAD": "1",
      "MODELSCOPE_SDK_DEBUG": "0",
      "LOG_LEVEL": "INFO",
      "ENABLE_MODEL_LOG": "1"
    }
  }
}
```

**适用场景**:
- 配置验证
- 故障排除
- 环境检查

---

## 💻 使用示例

### 命令行 (curl)

```bash
# 1. 查看完整模型状态
curl http://127.0.0.1:11111/api/model/status | python3 -m json.tool

# 2. 快速健康检查
curl http://127.0.0.1:11111/api/model/health | python3 -m json.tool

# 3. 查看配置
curl http://127.0.0.1:11111/api/model/config | python3 -m json.tool

# 4. 只看状态（精简输出）
curl -s http://127.0.0.1:11111/api/model/health | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"状态: {data['status']}, 警告: {data['warnings_count']} 条\")"

# 5. 检查特定项（如内存）
curl -s http://127.0.0.1:11111/api/model/status | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"可用内存: {data['system']['available_memory_gb']} GB\")"
```

### Python 脚本

```python
import requests

# 查询模型状态
response = requests.get("http://127.0.0.1:11111/api/model/status")
data = response.json()

# 检查状态
if data["status"] == "healthy":
    print("✅ 模型配置正常")
elif data["status"] == "warning":
    print(f"⚠️  发现 {len(data['warnings'])} 个警告:")
    for warning in data["warnings"]:
        print(f"   • {warning}")
else:
    print("❌ 模型配置有严重问题")

# 检查内存
available_mem = data["system"]["available_memory_gb"]
if available_mem < 3.0:
    print(f"⚠️  内存不足: {available_mem:.2f} GB")
else:
    print(f"✅ 内存充足: {available_mem:.2f} GB")
```

### JavaScript (前端)

```javascript
// 查询模型状态
async function checkModelStatus() {
  const response = await fetch('http://127.0.0.1:11111/api/model/status');
  const data = await response.json();
  
  console.log('状态:', data.status);
  console.log('SenseVoice:', data.sensevoice.exists ? '✅' : '❌');
  console.log('VAD:', data.vad.exists ? '✅' : '❌');
  console.log('可用内存:', data.system.available_memory_gb, 'GB');
  
  if (data.warnings.length > 0) {
    console.warn('警告:', data.warnings);
  }
  
  return data;
}

// 定时健康检查
setInterval(async () => {
  const health = await fetch('http://127.0.0.1:11111/api/model/health')
    .then(r => r.json());
  console.log(`[${health.timestamp}] 状态: ${health.status}`);
}, 60000); // 每分钟检查一次
```

---

## 🔍 使用场景

### 场景 1: 部署后验证

```bash
# 部署完成后，验证模型配置
curl http://127.0.0.1:11111/api/model/status | python3 -m json.tool

# 检查关键项
curl -s http://127.0.0.1:11111/api/model/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"状态: {data['status']}\")
print(f\"SenseVoice: {'✅' if data['sensevoice']['exists'] else '❌'}\")
print(f\"VAD: {'✅' if data['vad']['exists'] else '❌'}\")
print(f\"VAD配置: {'✅' if data['checks']['vad_config_set'] else '❌'}\")
print(f\"内存: {data['system']['available_memory_gb']:.2f} GB\")
"
```

### 场景 2: 监控告警

```bash
# 创建监控脚本 /usr/local/bin/check-model-health.sh
#!/bin/bash
STATUS=$(curl -s http://127.0.0.1:11111/api/model/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

if [ "$STATUS" == "error" ]; then
    echo "❌ 模型状态异常，发送告警..."
    # 发送告警通知（邮件/钉钉/企业微信等）
fi
```

### 场景 3: 自动化测试

```python
# 集成到 CI/CD 测试脚本
import requests
import sys

def test_model_api():
    # 检查服务可用
    response = requests.get("http://127.0.0.1:11111/api/model/health")
    assert response.status_code == 200, "API 不可用"
    
    data = response.json()
    
    # 验证模型文件存在
    status_response = requests.get("http://127.0.0.1:11111/api/model/status")
    status_data = status_response.json()
    
    assert status_data["sensevoice"]["exists"], "SenseVoice 模型缺失"
    assert status_data["vad"]["exists"], "VAD 模型缺失"
    assert status_data["checks"]["vad_config_set"], "VAD 配置缺失"
    
    print("✅ 所有检查通过")
    return 0

if __name__ == '__main__':
    sys.exit(test_model_api())
```

### 场景 4: 故障排查

```bash
# 当服务出现问题时，快速定位
echo "=== 模型状态检查 ==="
curl -s http://127.0.0.1:11111/api/model/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"总体状态: {data['status']}\")
print(f\"\n模型文件:\")
print(f\"  SenseVoice: {data['sensevoice']['exists']} ({data['sensevoice']['size_mb']:.1f} MB)\")
print(f\"  VAD: {data['vad']['exists']} ({data['vad']['size_mb']:.1f} MB)\")
print(f\"\n系统资源:\")
print(f\"  内存: {data['system']['available_memory_gb']:.2f} GB 可用\")
print(f\"  磁盘: {data['system']['disk_available_gb']:.2f} GB 可用\")
if data['warnings']:
    print(f\"\n⚠️  警告 ({len(data['warnings'])} 条):\")
    for w in data['warnings']:
        print(f\"  • {w}\")
if data['recommendations']:
    print(f\"\n💡 建议 ({len(data['recommendations'])} 条):\")
    for r in data['recommendations']:
        print(f\"  • {r}\")
"
```

---

## 📊 响应字段说明

### 模型信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 模型名称 |
| `path` | string | 模型路径 |
| `exists` | boolean | 文件是否存在 |
| `size_mb` | float | 文件大小(MB) |
| `env_var` | string | 环境变量名 |
| `env_value` | string | 环境变量值 |

### 系统资源字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_memory_gb` | float | 总内存(GB) |
| `available_memory_gb` | float | 可用内存(GB) |
| `memory_percent` | float | 内存使用率(%) |
| `cpu_percent` | float | CPU 使用率(%) |
| `disk_usage_percent` | float | 磁盘使用率(%) |
| `disk_available_gb` | float | 磁盘可用空间(GB) |

### 检查项字段

| 字段 | 说明 |
|------|------|
| `sensevoice_exists` | SenseVoice 模型文件存在 |
| `vad_exists` | VAD 模型文件存在 |
| `sensevoice_env_set` | SenseVoice 环境变量已设置 |
| `vad_env_set` | VAD 环境变量已设置 |
| `vad_config_set` | VAD 参数已配置 |
| `pytorch_config_set` | PyTorch 优化已配置 |
| `memory_sufficient` | 内存充足(≥3GB) |
| `disk_space_ok` | 磁盘空间充足(<90%) |

---

## 🔧 自动化测试

### 运行自动测试脚本

```bash
# 执行 API 自动测试
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
python scripts/检查与校验/test-model-api.py
```

**预期输出**:

```
============================================================
模型状态 API 自动测试
============================================================

=== 1. API 端点连接测试 ===
[1] 测试: 健康检查端点
   ✅ 通过
[2] 测试: 配置查询端点
   ✅ 通过
[3] 测试: 完整状态端点
   ✅ 通过

=== 2. 模型状态详细验证 ===
[4] 测试: 模型状态详细验证
   ✅ SenseVoice 存在 (892.9 MB)
   ✅ VAD 存在 (1.6 MB)
   ✅ VAD 参数已配置
   ✅ PyTorch 优化已配置
   ✅ 内存充足 (3.40 GB)

============================================================
测试总结
============================================================
测试结果: 4/4 项通过
✅ 所有测试通过！API 运行正常。
```

---

## 🔗 集成到前端

### React 示例

```jsx
import { useEffect, useState } from 'react';

function ModelStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 初次加载
    fetchStatus();
    
    // 定时刷新（每30秒）
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:11111/api/model/status');
      const data = await response.json();
      setStatus(data);
      setLoading(false);
    } catch (error) {
      console.error('获取模型状态失败:', error);
      setLoading(false);
    }
  };

  if (loading) return <div>加载中...</div>;
  if (!status) return <div>无法获取模型状态</div>;

  return (
    <div className="model-status">
      <h3>模型状态: 
        <span className={`status-${status.status}`}>
          {status.status === 'healthy' ? '✅ 正常' :
           status.status === 'warning' ? '⚠️ 警告' : '❌ 错误'}
        </span>
      </h3>
      
      <div className="models">
        <div>SenseVoice: {status.sensevoice.exists ? '✅' : '❌'} 
          ({status.sensevoice.size_mb?.toFixed(1)} MB)</div>
        <div>VAD: {status.vad.exists ? '✅' : '❌'} 
          ({status.vad.size_mb?.toFixed(1)} MB)</div>
      </div>
      
      <div className="resources">
        <div>内存: {status.system.available_memory_gb.toFixed(2)} GB 可用</div>
        <div>CPU: {status.system.cpu_percent}%</div>
      </div>
      
      {status.warnings.length > 0 && (
        <div className="warnings">
          <h4>⚠️ 警告</h4>
          <ul>
            {status.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## 📚 相关文档

- [SenseVoice模型配置指南.md](./SenseVoice模型配置指南.md)
- [PM2使用指南.md](./PM2使用指南.md)
- [模型配置完成报告.md](../模型配置完成报告.md)

---

## 💡 最佳实践

1. **定期监控**: 每分钟调用 `/health` 端点
2. **详细诊断**: 出现问题时调用 `/status` 端点
3. **配置验证**: 部署后调用 `/config` 端点验证
4. **自动化测试**: CI/CD 中集成 API 测试
5. **告警集成**: 将 `error` 状态接入监控系统

---

## 🎯 快速开始

```bash
# 1. 确认服务运行
pm2 list

# 2. 测试 API
curl http://127.0.0.1:11111/api/model/health

# 3. 查看详细状态
curl http://127.0.0.1:11111/api/model/status | python3 -m json.tool

# 4. 运行自动测试
python scripts/检查与校验/test-model-api.py
```

---

**版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.0 | 2025-11-14 | 初始版本，添加三个 API 端点 |

**问题反馈**: 如遇到问题，请检查后端日志 `pm2 logs timao-backend`

