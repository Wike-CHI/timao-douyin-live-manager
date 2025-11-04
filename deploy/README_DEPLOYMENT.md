# 提猫直播助手 - 部署指南

## 快速开始

### Windows 用户

#### 方式一：简化启动脚本（推荐）
```bash
# 批处理版本 - 双击运行或在命令行执行
.\quick_start.bat

# PowerShell版本 - 在 PowerShell 中执行
.\simple_start.ps1
```

#### 方式二：完整安装脚本
```bash
# 批处理脚本（可能存在编码问题）
install_and_start.bat

# PowerShell 脚本
.\install_and_start.ps1
```

### Linux/macOS 用户

```bash
# 添加执行权限（首次运行）
chmod +x install_and_start.sh

# 运行脚本
./install_and_start.sh

# 带参数运行
./install_and_start.sh --skip-dependencies  # 跳过依赖安装
./install_and_start.sh --production         # 生产模式
./install_and_start.sh --quick-start        # 快速启动
./install_and_start.sh --help               # 显示帮助
```

## 📋 系统要求

### 必需环境
- **Python 3.8+** - 后端服务运行环境
- **Node.js LTS** - 前端构建和运行环境
- **npm** - Node.js包管理器（通常随Node.js一起安装）

### 推荐配置
- **内存**: 4GB以上
- **存储**: 2GB可用空间
- **网络**: 稳定的互联网连接（用于下载依赖）

## 🔧 脚本功能

### 自动化安装流程

1. **环境检查**
   - 检测Python和Node.js是否已安装
   - 验证版本兼容性
   - 检查必要的命令行工具

2. **虚拟环境配置**
   - 自动创建Python虚拟环境
   - 激活虚拟环境
   - 隔离项目依赖

3. **依赖安装**
   - 安装Python依赖包（requirements.txt）
   - 安装Node.js项目依赖（package.json）
   - 安装前端依赖（electron/renderer/package.json）

4. **服务启动**
   - 启动后端API服务（端口9019）
   - 启动前端开发服务器（端口10030）
   - 启动Electron桌面应用

5. **健康检查**
   - 检查端口占用情况
   - 验证服务启动状态
   - 提供故障排除建议

## 🌐 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| 主API服务 | 9019 | 后端主要API接口 |
| AI服务 | 9020 | AI相关服务 |
| 音频服务 | 9021 | 音频处理服务 |
| 前端开发服务器 | 10030 | 前端开发热重载服务器 |

## 📁 部署包结构

```
timao-douyin-live-manager/
├── install_and_start.bat      # Windows批处理启动脚本
├── install_and_start.ps1      # Windows PowerShell启动脚本
├── install_and_start.sh       # Linux/macOS启动脚本
├── package.json               # Node.js项目配置
├── requirements.txt           # Python依赖配置
├── service_launcher.py        # 服务启动器
├── server/                    # 后端服务代码
├── electron/                  # 前端Electron应用
├── docs/                      # 文档目录
└── ...                        # 其他项目文件
```

## 🛠️ 故障排除

### 常见问题

#### 1. Python 未安装或版本过低
```bash
# 错误信息：'python' 不是内部或外部命令
# 解决方案：
# 1. 下载并安装 Python 3.8+: https://www.python.org/downloads/
# 2. 安装时勾选 "Add Python to PATH"
# 3. 重启命令行窗口
```

#### 2. Node.js 未安装或版本过低
```bash
# 错误信息：'node' 不是内部或外部命令
# 解决方案：
# 1. 下载并安装 Node.js 16+: https://nodejs.org/
# 2. 重启命令行窗口
```

#### 3. 端口被占用
```bash
# 错误信息：Port 9019/9020/9021/10030 is already in use
# 解决方案：
# 1. 关闭占用端口的程序
# 2. 或修改 config.json 中的端口配置
```

#### 4. 依赖安装失败
```bash
# Python 依赖问题：
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Node.js 依赖问题：
npm cache clean --force
npm install
```

#### 5. Redis 版本冲突问题
```bash
# 错误信息：redis-py-cluster 2.1.3 depends on redis<4.0.0 and >=3.0.0
# 解决方案：
# 1. 卸载冲突的包
pip uninstall redis redis-py-cluster
# 2. 重新安装兼容版本
pip install redis==3.5.3 redis-py-cluster==2.1.3
```

#### 6. 权限问题（Linux/macOS）
```bash
# 给脚本执行权限
chmod +x install_and_start.sh
```

#### 7. 脚本编码问题
```bash
# 如果批处理脚本出现乱码，请使用 PowerShell 版本：
.\simple_start.ps1
```

### 手动启动

如果自动脚本失败，可以手动启动：

```bash
# 1. 激活虚拟环境
# Windows
.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate

# 2. 启动服务
npm run dev
```

## 🔒 安全注意事项

1. **防火墙配置**: 确保必要端口（9019-9021, 10030）在防火墙中开放
2. **网络安全**: 生产环境中建议配置HTTPS和访问控制
3. **依赖更新**: 定期更新依赖包以修复安全漏洞
4. **日志监控**: 监控应用日志以发现异常行为

## 📞 技术支持

如果遇到问题，请：

1. 查看控制台错误信息
2. 检查日志文件（logs/目录）
3. 参考本文档的故障排除部分
4. 联系技术支持团队

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。