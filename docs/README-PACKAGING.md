# 提猫直播助手 - 本地化封装方案

## 概述

本文档提供了提猫直播助手的多种本地化封装方案，确保AI功能和互动连接功能在离线或受限网络环境下正常工作。

## 功能特性

### AI功能
- ✅ 智能弹幕分析和情感识别
- ✅ 实时热词提取和统计
- ✅ AI驱动的直播脚本生成
- ✅ 风格记忆和个性化建议
- ✅ 支持多种AI服务提供商（Qwen、OpenAI、DeepSeek）

### 互动连接功能
- ✅ 抖音直播间实时弹幕获取
- ✅ WebSocket实时数据推送
- ✅ 多客户端连接支持
- ✅ 自动重连和错误恢复
- ✅ 弹幕过滤和处理

## 封装方案

### 方案一：标准安装包（推荐）

**适用场景：** 普通用户，需要完整功能和自动更新

**特点：**
- 一键安装，自动配置环境
- 包含所有依赖和运行时
- 支持开机自启动
- 内置AI服务配置

**使用方法：**
```bash
# 构建标准安装包
npm run package:local

# 或直接运行脚本
scripts\package-local.bat
```

**生成文件：** `dist\TalkingCat-Setup-{version}-{arch}.exe`

### 方案二：便携版（绿色版）

**适用场景：** 需要免安装运行，或在多台设备间迁移

**特点：**
- 免安装，解压即用
- 数据文件本地存储
- 支持U盘运行
- 配置文件可自定义

**使用方法：**
```bash
# 构建便携版
npm run package:portable

# 或直接运行脚本
scripts\package-portable.bat
```

**生成目录：** `dist\TalkingCat-Portable\`

**启动方式：** 双击 `启动提猫直播助手.bat`

### 方案三：Docker容器化

**适用场景：** 服务器部署，多用户环境，云端部署

**特点：**
- 容器化部署，环境隔离
- 支持负载均衡和集群
- 自动健康检查
- 数据持久化

**使用方法：**
```bash
# 构建Docker镜像
npm run package:docker

# 或直接运行脚本
scripts\package-docker.bat

# 启动服务
docker-compose up -d
```

**访问地址：**
- 前端界面：http://localhost
- API接口：http://localhost/api

## 配置说明

### AI服务配置

在 `config/local-deployment.json` 中配置AI服务：

```json
{
  "ai_services": {
    "default_provider": "qwen",
    "providers": {
      "qwen": {
        "enabled": true,
        "api_key": "your-api-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3-max"
      }
    }
  }
}
```

### 网络连接配置

```json
{
  "live_connection": {
    "douyin": {
      "enabled": true,
      "websocket_enabled": true,
      "auto_reconnect": true,
      "max_retries": 5
    }
  }
}
```

## 部署步骤

### 1. 环境准备

**系统要求：**
- Windows 10/11 (x64)
- Python 3.8+
- Node.js 16+
- 4GB+ RAM
- 2GB+ 磁盘空间

**依赖安装：**
```bash
# 安装项目依赖
npm run setup:local

# 或手动安装
npm install
pip install -r requirements.txt
```

### 2. 配置设置

1. 复制 `server/.env.example` 为 `server/.env`
2. 配置AI服务API密钥
3. 根据需要修改 `config/local-deployment.json`

### 3. 构建打包

选择合适的封装方案：

```bash
# 标准安装包
npm run package:local

# 便携版
npm run package:portable

# Docker版
npm run package:docker
```

### 4. 部署验证

**功能测试清单：**
- [ ] 应用正常启动
- [ ] AI服务连接正常
- [ ] 弹幕获取功能正常
- [ ] WebSocket连接稳定
- [ ] 数据库读写正常
- [ ] 日志记录正常

## 故障排除

### 常见问题

**1. AI服务连接失败**
- 检查API密钥是否正确
- 确认网络连接正常
- 查看 `logs/app.log` 错误信息

**2. 弹幕获取异常**
- 检查抖音直播间URL格式
- 确认WebSocket连接状态
- 重启应用重新连接

**3. 端口占用问题**
- 修改 `config/local-deployment.json` 中的端口配置
- 使用 `netstat -ano | findstr :10090` 检查端口占用

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# Docker环境查看日志
docker-compose logs -f
```

## 性能优化

### 资源配置

**内存优化：**
- 调整弹幕缓存大小：`comment_processing.max_queue_size`
- 限制WebSocket连接数：`websocket.max_connections`

**网络优化：**
- 启用连接池：`database.connection_pool`
- 调整重连间隔：`live_connection.douyin.max_retries`

### 监控指标

- CPU使用率 < 50%
- 内存使用率 < 80%
- 磁盘I/O < 100MB/s
- 网络延迟 < 100ms

## 安全建议

1. **API密钥保护**
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥
   - 避免在日志中记录密钥

2. **网络安全**
   - 启用CORS保护
   - 配置API访问限制
   - 使用HTTPS（生产环境）

3. **数据安全**
   - 定期备份数据库
   - 启用数据加密（可选）
   - 清理过期日志文件

## 技术支持

如遇到问题，请提供以下信息：
- 操作系统版本
- 错误日志内容
- 复现步骤
- 配置文件内容（隐藏敏感信息）

---

**版本：** 1.0.0  
**更新时间：** 2024年12月  
**维护者：** 提猫直播助手开发团队