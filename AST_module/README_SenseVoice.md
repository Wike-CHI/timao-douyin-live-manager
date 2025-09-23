# SenseVoice 模型使用说明

## 问题描述

在Windows系统上运行SenseVoice模型时，可能会遇到以下错误：

```
Download: iic/SenseVoiceSmall failed!: [WinError 3] 系统找不到指定的路径。: 'E:\\'
```

这是因为FunASR库默认尝试将模型下载到系统盘（通常是C盘），但在某些系统配置中可能会尝试访问不存在的盘符（如E盘）。

## 解决方案

### 方法1：设置环境变量（推荐）

在运行测试服务器之前，设置以下环境变量：

```bash
set MODELSCOPE_CACHE=D:\gsxm\timao-douyin-live-manager\models
set HF_HOME=D:\gsxm\timao-douyin-live-manager\models\huggingface
```

或者在Python代码中设置：

```python
import os
os.environ['MODELSCOPE_CACHE'] = 'D:\\gsxm\\timao-douyin-live-manager\\models'
os.environ['HF_HOME'] = 'D:\\gsxm\\timao-douyin-live-manager\\models\\huggingface'
```

### 方法2：手动下载模型

1. 访问ModelScope网站：https://modelscope.cn/models/iic/SenseVoiceSmall
2. 手动下载模型文件
3. 将模型文件放置在指定目录中
4. 修改配置文件指向本地模型路径

### 方法3：使用本地模型路径

在[config.py](file://d:/gsxm/timao-douyin-live-manager/AST_module/config.py)中修改默认配置：

```python
# 修改SenseVoiceConfig中的model_id为本地路径
model_id: str = "./models/SenseVoiceSmall"
```

## 首次运行

首次运行时，模型会自动从ModelScope下载并缓存到指定目录。请确保：

1. 网络连接正常
2. 指定的缓存目录有写入权限
3. 磁盘空间充足（模型文件大约1-2GB）

## 测试模型加载

可以使用以下代码测试模型是否能正常加载：

```python
from funasr import AutoModel

model = AutoModel(model="iic/SenseVoiceSmall", hub="ms")
print("模型加载成功")
```

## 常见问题

### 1. 下载速度慢
可以考虑使用国内镜像源或手动下载模型。

### 2. 权限问题
确保运行Python的用户对模型缓存目录有读写权限。

### 3. 磁盘空间不足
确保有足够的磁盘空间存储模型文件。

## 相关配置文件

- [sensevoice_service.py](file://d:/gsxm/timao-douyin-live-manager/AST_module/sensevoice_service.py) - SenseVoice服务实现
- [ast_service.py](file://d:/gsxm/timao-douyin-live-manager/AST_module/ast_service.py) - AST主服务
- [config.py](file://d:/gsxm/timao-douyin-live-manager/AST_module/config.py) - 配置文件