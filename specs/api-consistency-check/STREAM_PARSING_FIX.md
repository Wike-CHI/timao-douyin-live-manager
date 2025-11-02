# 🔧 直播流解析失败修复

## 问题描述

### 错误信息
```
'NoneType' object has no attribute 'group' in function get_stream_info at line: 133
Failed to resolve record URL (streams unavailable)
```

### 影响
- 无法启动直播录制服务
- 无法启动实时音频转写服务

---

## 🔍 根本原因

### 1. 外部依赖问题
错误来自外部 Python 包 `streamget`，它负责解析各个直播平台的流地址。

### 2. 具体原因
当 `streamget.DouyinLiveStream` 尝试从抖音网页提取流 URL 时：
1. 使用正则表达式匹配网页内容
2. 如果匹配失败返回 `None`
3. 代码尝试调用 `None.group()` 导致错误

### 3. 可能触发场景
- **直播间未开播**: 抖音直播间已关闭
- **网页结构变化**: 抖音更新了网页结构，正则表达式失效
- **网络问题**: 无法访问抖音网页或需要代理
- **Cookie过期**: 某些直播间需要登录状态

---

## ✅ 修复方案

### 修复 1: 改进错误处理

**文件**: `server/modules/streamcap/utils/utils.py`

#### 修改前
```python
def trace_error_decorator(func: callable) -> callable:
    @functools.wraps(func)
    async def wrapper(*args: list, **kwargs: dict) -> Any:
        try:
            return await func(*args, **kwargs)
        except execjs.ProgramError:
            logger.warning("Failed to execute JS code...")
        except Exception as e:
            error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
            error_info = f"Type: {type(e).__name__}, {e} in function {func.__name__} at line: {error_line}"
            logger.error(error_info)
            return []  # ❌ 返回空列表，但调用代码期望 StreamData 对象

    return wrapper
```

#### 修改后
```python
def trace_error_decorator(func: callable) -> callable:
    @functools.wraps(func)
    async def wrapper(*args: list, **kwargs: dict) -> Any:
        try:
            return await func(*args, **kwargs)
        except execjs.ProgramError as e:
            logger.warning(f"Failed to execute JS code: {e}")
            raise RuntimeError(f"JS execution failed: {e}")  # ✅ 抛出异常
        except Exception as e:
            error_line = traceback.extract_tb(e.__traceback__)[-1].lineno
            error_info = f"Type: {type(e).__name__}, {e} in function {func.__name__} at line: {error_line}"
            logger.error(error_info)
            
            # ✅ 修复：提供更清晰的错误信息
            if "'NoneType' object has no attribute 'group'" in str(e):
                error_msg = (
                    "无法解析直播流地址，可能原因：\n"
                    "1. 直播间已关闭或未开播\n"
                    "2. 抖音网页结构已更新，请更新 streamget 包: pip install -U streamget\n"
                    "3. 网络连接问题或需要配置代理\n"
                    f"详细错误: {e}"
                )
                raise RuntimeError(error_msg)
            
            # ✅ 其他错误也应该抛出
            raise RuntimeError(f"Fetch failed: {args[1] if len(args) > 1 else 'unknown URL'}, {e}")

    return wrapper
```

#### 改进点
1. ✅ 不再返回空列表，而是抛出清晰的异常
2. ✅ 针对 `'NoneType' object has no attribute 'group'` 提供详细的解决方案
3. ✅ 包含URL信息便于调试
4. ✅ 保持异常传播，让上层代码正确处理

---

## 🧪 测试步骤

### 1. 测试未开播的直播间
```python
# 使用一个已关闭的直播间
live_url = "https://live.douyin.com/746237489390"
# 应该看到清晰的错误提示
```

### 2. 测试正常直播间
```python
# 使用一个正在直播的直播间
# 应该能正常解析流地址
```

### 3. 更新 streamget
```bash
pip install -U streamget
```

---

## 💡 用户解决方案

### 方案 1: 检查直播间状态
**确认直播间是否正在直播**
1. 打开抖音直播间链接
2. 确认主播正在直播
3. 如果未开播，等待主播开播后再启动服务

### 方案 2: 更新 streamget 包
**如果是网页结构变化导致**
```bash
pip install -U streamget
```

### 方案 3: 配置代理
**如果是网络问题**
1. 在配置文件中设置代理
2. 确保能访问抖音网站

### 方案 4: 配置 Cookie
**如果需要登录状态**
1. 登录抖音网页版
2. 获取 Cookie
3. 在配置中添加 Cookie

---

## 📊 影响范围

### 直接影响
- ✅ 直播录制服务启动失败 → 现在提供清晰错误提示
- ✅ 实时音频转写服务启动失败 → 现在提供清晰错误提示

### 间接影响
- ✅ 所有使用 `streamget` 的平台处理器都受益于改进的错误处理

---

## 🎯 长期解决方案

### 1. 添加直播状态检查
在解析流地址前，先检查直播间是否正在直播

### 2. 降级机制
如果一种解析方法失败，尝试其他方法

### 3. 缓存机制
缓存最近成功的解析结果

### 4. 监控和告警
- 监控解析失败率
- 当失败率超过阈值时告警
- 自动检测是否需要更新依赖

---

## 📝 相关 Issue

### streamget 包更新
如果问题持续，可能需要：
1. 向 `streamget` 仓库报告问题
2. 检查是否有更新版本
3. 查看是否有替代方案

### 抖音 API 变化
抖音经常更新其网页结构，需要：
1. 定期更新 `streamget`
2. 关注 `streamget` 仓库的更新
3. 准备应急方案

---

## ✅ 验收标准

### 修复后
- ✅ 错误信息清晰明确
- ✅ 提供具体的解决方案
- ✅ 包含足够的调试信息
- ✅ 不会返回错误的数据类型

### 用户体验
- ✅ 用户知道为什么失败
- ✅ 用户知道如何解决
- ✅ 用户能够判断是临时问题还是需要更新

---

**修复时间**: 2025-11-02  
**状态**: ✅ 已完成  
**优先级**: 🔴 高

