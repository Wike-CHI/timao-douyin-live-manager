# Bug 修复测试指南

## 修复的问题

### 1. ✅ JSON 导入冲突错误
**错误信息**: `cannot access local variable 'json' where it is not associated with a value`

**根本原因**: 在 `live_report_service.py` 中重复导入了 `json` 模块
- 文件顶部已经有 `import json`
- 第 423 行又有一个 `import json`
- 导致局部作用域冲突

**修复方法**: 删除第 423 行的重复导入

### 2. ✅ 前端状态管理问题
**问题**: `viewReview` 函数中，当 `artifacts` 为 `null` 时，展开操作 `{ ...prev }` 会失败

**修复方法**: 改为 `{ ...(prev || {}) }` 来处理 `null` 情况

## 测试步骤

### 测试 1: 验证生成报告功能
```bash
# 1. 重启后端服务
# 在 PowerShell 中按 Ctrl+C 停止现有服务，然后重新运行：
npm run dev

# 2. 在前端操作：
- 输入直播地址（例如：https://live.douyin.com/xxxxx）
- 点击"开始录制"
- 等待 1-2 分钟
- 点击"停止"
- 点击"生成报告"

# 预期结果：
✅ 不再出现 "cannot access local variable 'json'" 错误
✅ 报告生成成功
✅ 自动跳转到复盘页面
✅ 在 artifacts/ 目录下生成 review_data.json 文件
```

### 测试 2: 验证查看历史报告功能
```bash
# 在前端操作：
- 找到之前生成的报告路径
- 点击"查看复盘"按钮

# 预期结果：
✅ 正确加载历史数据
✅ 显示复盘页面
✅ 不会出现空白或错误
```

### 测试 3: 验证界面切换
```bash
# 在前端操作：
1. 生成一个报告（或已有报告）
2. 切换到其他页面（如"实时分析"或"设置"）
3. 切换回"整场复盘"页面
4. 再次点击"查看复盘"按钮

# 预期结果：
✅ 按钮可以正常点击
✅ 报告路径依然可见
✅ 复盘页面正常显示
```

## 文件变更清单

### 后端修复
- `server/app/services/live_report_service.py` (第 423 行)
  - 删除: `import json`
  - 原因: 文件顶部已有该导入

### 前端修复
- `electron/renderer/src/pages/dashboard/ReportsPage.tsx` (第 86-88 行)
  - 修改前: `setArtifacts(prev => ({ ...prev, review_data: data.data.review_data }))`
  - 修改后: `setArtifacts(prev => ({ ...(prev || {}), review_data: data.data.review_data }))`
  - 原因: 防止 `prev` 为 `null` 时的展开操作失败

## 常见问题排查

### Q1: 仍然出现 JSON 错误
**检查**: 确保后端服务已重启
```bash
# 停止现有服务 (Ctrl+C)
# 重新启动
npm run dev
```

### Q2: 点击按钮无反应
**检查**: 
1. 打开浏览器控制台 (F12)
2. 查看 Console 标签是否有错误
3. 查看 Network 标签是否有 API 请求失败

### Q3: 报告路径不显示
**可能原因**:
- 未生成报告（需要先录制、停止、然后生成）
- `status` 或 `artifacts` 状态未正确获取

**解决方法**:
1. 确保完整流程：开始录制 → 停止 → 生成报告
2. 刷新页面重新获取状态

## 调试信息

### 后端日志位置
查看后端控制台输出，关键日志包括：
- `🔄 开始使用 Gemini 生成复盘报告...`
- `✅ Gemini 复盘完成 - 评分: XX/100, 成本: $0.XXXXXX`
- `❌ Gemini 复盘失败: ...` (如果出错)

### 前端错误信息
打开浏览器控制台 (F12)，查看：
- Console 标签：JavaScript 错误
- Network 标签：API 请求状态
- 红色错误框：用户友好的错误提示

## 验证成功标准

✅ 所有测试步骤均通过
✅ 不再出现 JSON 相关错误
✅ 界面切换后功能正常
✅ 历史报告可以正常查看
✅ 生成的 review_data.json 文件结构完整

## 下一步

如果所有测试通过，可以提交代码：
```bash
git add server/app/services/live_report_service.py
git add electron/renderer/src/pages/dashboard/ReportsPage.tsx
git commit -m "fix: 修复生成报告的 JSON 导入冲突和状态管理问题

- 删除 live_report_service.py 中重复的 json 导入
- 修复 viewReview 函数中 null 状态的展开操作
- 确保界面切换后功能正常"
git push
```
