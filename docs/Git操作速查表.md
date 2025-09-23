# Git 操作速查表

本文档提供了 Git 常用操作的快速参考，帮助您高效地管理提猫直播助手项目的版本控制。

## 基础操作

### 初始化与克隆
```bash
# 初始化新仓库
git init

# 克隆远程仓库
git clone <仓库地址>
```

### 查看状态
```bash
# 查看工作区状态
git status

# 查看简洁状态
git status -s
```

### 添加与提交
```bash
# 添加文件到暂存区
git add <文件名>     # 添加单个文件
git add .            # 添加所有文件
git add *.py         # 添加特定类型文件

# 提交更改
git commit -m "提交信息"
git commit -am "提交信息"  # 添加并提交修改文件
```

## 分支操作

### 查看分支
```bash
git branch      # 查看本地分支
git branch -a   # 查看所有分支
git branch -r   # 查看远程分支
```

### 创建与切换
```bash
git branch <分支名>           # 创建分支
git checkout <分支名>         # 切换分支
git checkout -b <分支名>      # 创建并切换分支
git switch -c <分支名>        # 新语法创建并切换
```

### 合并与删除
```bash
git merge <分支名>    # 合并分支
git branch -d <分支名>  # 删除本地分支
git push origin --delete <分支名>  # 删除远程分支
```

## 远程操作

### 推送与拉取
```bash
git push                    # 推送到远程仓库
git push origin <分支名>     # 推送到指定分支
git push -u origin <分支名>  # 推送并设置上游分支

git pull                    # 拉取远程更改
git pull origin <分支名>     # 拉取指定分支
```

### 远程仓库管理
```bash
git remote -v               # 查看远程仓库信息
git fetch                   # 获取远程更新（不合并）
```

## 提交历史

```bash
git log                     # 查看提交历史
git log --oneline           # 简洁提交历史
git log --graph --oneline --all  # 图形化分支历史
```

## 撤销操作

```bash
# 撤销工作区更改
git checkout -- <文件名>

# 撤销暂存区文件
git reset HEAD <文件名>

# 撤销提交
git reset --hard HEAD~1     # 撤销最后一次提交
git revert <提交哈希>        # 创建新提交来撤销指定提交
```

## 标签操作

```bash
git tag v1.0.0              # 创建轻量标签
git tag -a v1.0.0 -m "发布说明"  # 创建附注标签
git push origin v1.0.0      # 推送标签
git push origin --tags      # 推送所有标签
```

## 项目特定操作

### 检查 .gitignore
```bash
git status --ignored        # 查看被忽略的文件
git check-ignore -v <文件名>  # 检查文件是否被忽略
```

### 查看跟踪的文件
```bash
git ls-files                # 查看被跟踪的文件
git ls-files --others --exclude-standard  # 查看未被忽略的文件
```

## 常用别名

```bash
# 设置常用别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
```

使用别名：
```bash
git st      # 等同于 git status
git co      # 等同于 git checkout
git br      # 等同于 git branch
git ci      # 等同于 git commit
```

## 日常工作流程

```bash
# 1. 同步主分支
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/新功能

# 3. 开发并提交
git add .
git commit -m "feat: 实现新功能"

# 4. 推送分支
git push -u origin feature/新功能

# 5. 合并后清理
git checkout main
git pull origin main
git branch -d feature/新功能
```

## 提交类型规范

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

## 提交信息示例

```bash
git commit -m "feat: 添加实时语音转录功能"
git commit -m "fix: 修复FastAPI端口冲突问题"
git commit -m "docs: 更新启动说明文档"
git commit -m "refactor: 优化AST模块代码结构"
```

通过使用这些命令，您可以高效地管理项目的版本控制，确保代码的安全性和团队协作的效率。