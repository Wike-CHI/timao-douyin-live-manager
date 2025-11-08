# 🔧 pyaudio 安装失败修复

**错误信息：**
```
fatal error: portaudio.h: No such file or directory
```

**原因：** 缺少系统依赖 `portaudio-devel`

---

## 🚀 快速修复（2步）

### 步骤1：安装系统依赖

```bash
# CentOS/RHEL（你的系统）
yum install -y portaudio-devel gcc python3-devel

# 如果 yum 没有，尝试 dnf
dnf install -y portaudio-devel gcc python3-devel
```

### 步骤2：重新安装 pyaudio

```bash
# 激活环境
source /www/server/python_project/vhost/env/timao-douyin-live-manager.env

# 使用镜像源安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyaudio
```

---

## 📋 完整命令

```bash
# 1. 安装系统依赖
yum install -y portaudio-devel gcc python3-devel

# 2. 激活虚拟环境
source /www/server/python_project/vhost/env/timao-douyin-live-manager.env

# 3. 安装 pyaudio
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyaudio

# 4. 验证
python -c "import pyaudio; print('✅ pyaudio 安装成功')"
```

---

## ⚠️ 如果 yum 找不到 portaudio-devel

### 方法1：使用 EPEL 源

```bash
# 安装 EPEL 源
yum install -y epel-release

# 再安装
yum install -y portaudio-devel gcc python3-devel
```

### 方法2：从源码编译

```bash
# 下载 portaudio 源码
cd /tmp
wget http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz
tar -xzf pa_stable_v190700_20210406.tgz
cd portaudio

# 编译安装
./configure
make
make install

# 然后再安装 pyaudio
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyaudio
```

---

## 💡 如果不需要音频功能

**如果不需要音频捕获功能，可以跳过 pyaudio：**

```bash
# 只安装必需的 email-validator
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple email-validator
```

**影响：**
- ✅ 其他功能正常
- ❌ 联合测试功能无法使用
- ❌ 音频捕获功能无法使用

---

## 🎯 推荐操作

**现在就执行：**

```bash
# 安装系统依赖
yum install -y portaudio-devel gcc python3-devel

# 安装 pyaudio
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyaudio
```

