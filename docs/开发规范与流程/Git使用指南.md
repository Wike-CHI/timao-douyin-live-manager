# Git 使用指南

本文档详细说明了如何在提猫直播助手项目中使用 Git 进行版本控制，包括基本操作、分支管理、提交规范等内容。

## 基本 Git 操作

### 1. 初始化仓库

如果需要初始化新的 Git 仓库：

```bash
# 在项目根目录执行
git init
```

### 2. 克隆远程仓库

```bash
# 克隆远程仓库到本地
git clone <仓库地址>
```

### 3. 查看仓库状态

```bash
# 查看工作区状态
git status

# 查看简洁状态
git status -s
```

### 4. 添加文件到暂存区

```bash
# 添加单个文件
git add <文件名>

# 添加所有文件
git add .

# 添加特定类型文件
git add *.py
git add *.md

# 添加目录
git add docs/
```

### 5. 提交更改

```bash
# 提交暂存区的更改
git commit -m "提交信息"

# 添加并提交（适用于修改文件）
git commit -am "提交信息"

# 修改最后一次提交
git commit --amend -m "新的提交信息"
```

### 6. 查看提交历史

```bash
# 查看提交历史
git log

# 查看简洁提交历史
git log --oneline

# 查看图形化分支历史
git log --graph --oneline --all
```

## 分支管理

### 1. 查看分支

```bash
# 查看本地分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 查看远程分支
git branch -r
```

### 2. 创建和切换分支

```bash
# 创建新分支
git branch <分支名>

# 切换分支
git checkout <分支名>

# 创建并切换到新分支
git checkout -b <分支名>

# 使用新语法创建并切换分支
git switch -c <分支名>
```

### 3. 合并分支

```bash
# 合并指定分支到当前分支
git merge <分支名>

# 使用 rebase 合并
git rebase <分支名>
```

### 4. 删除分支

```bash
# 删除本地分支
git branch -d <分支名>

# 强制删除本地分支
git branch -D <分支名>

# 删除远程分支
git push origin --delete <分支名>
```

## 远程仓库操作

### 1. 查看远程仓库

```bash
# 查看远程仓库信息
git remote -v
```

### 2. 推送更改

```bash
# 推送到远程仓库
git push

# 推送到指定远程仓库和分支
git push origin <分支名>

# 推送并设置上游分支
git push -u origin <分支名>

# 推送所有分支
git push --all origin
```

### 3. 拉取更改

```bash
# 拉取远程更改
git pull

# 拉取指定远程仓库和分支
git pull origin <分支名>

# 使用 rebase 方式拉取
git pull --rebase
```

### 4. 获取远程信息

```bash
# 获取远程仓库更新（不合并）
git fetch

# 获取指定远程仓库更新
git fetch origin
```

## 提交规范

### 1. 提交信息格式

遵循约定的提交信息格式，便于生成变更日志：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 2. 提交类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响代码运行）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 3. 提交示例

```bash
# 新功能提交
git commit -m "feat: 添加实时语音转录功能"

# 修复提交
git commit -m "fix: 修复FastAPI端口冲突问题"

# 文档更新
git commit -m "docs: 更新启动说明文档"
```

## 项目特定操作

### 1. 检查 .gitignore 配置

```bash
# 查看哪些文件被忽略
git status --ignored

# 查看特定文件是否被忽略
git check-ignore -v <文件名>
```

### 2. 处理大文件

对于大文件，建议使用 Git LFS：

```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件类型
git lfs track "*.wav"
git lfs track "*.bin"
git lfs track "*.model"

# 提交 .gitattributes 文件
git add .gitattributes
git commit -m "docs: 添加 Git LFS 配置"
```

### 3. 清理历史提交中的敏感信息

如果意外提交了敏感信息：

```bash
# 使用 git filter-branch 清理（谨慎使用）
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch <敏感文件>' \
--prune-empty --tag-name-filter cat -- --all

# 强制推送更改
git push origin --force --all
```

## 常用 Git 别名

为了提高效率，可以设置 Git 别名：

```bash
# 设置别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
```

使用别名：

```bash
# 等同于 git status
git st

# 等同于 git checkout
git co <分支名>

# 等同于 git commit
git ci -m "提交信息"
```

## 解决冲突

### 1. 合并冲突

当合并分支时出现冲突：

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突后
git add <冲突文件>

# 完成合并
git commit
```

### 2. 放弃合并

```bash
# 放弃合并操作
git merge --abort
```

## 标签管理

### 1. 创建标签

```bash
# 创建轻量标签
git tag v1.0.0

# 创建附注标签
git tag -a v1.0.0 -m "发布版本 1.0.0"

# 为特定提交创建标签
git tag -a v1.0.0 <提交哈希> -m "发布版本 1.0.0"
```

### 2. 查看标签

```bash
# 查看所有标签
git tag

# 查看特定标签信息
git show v1.0.0
```

### 3. 推送标签

```bash
# 推送单个标签
git push origin v1.0.0

# 推送所有标签
git push origin --tags
```

### 4. 删除标签

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0
```

## 最佳实践

### 1. 日常工作流程

```bash
# 1. 开始工作前，确保代码是最新的
git checkout main
git pull origin main

# 2. 为新功能创建分支
git checkout -b feature/new-feature

# 3. 进行开发工作
# 编辑文件...

# 4. 提交更改
git add .
git commit -m "feat: 实现新功能"

# 5. 推送分支到远程
git push -u origin feature/new-feature

# 6. 创建 Pull Request 进行代码审查

# 7. 合并后删除本地和远程分支
git checkout main
git pull origin main
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

### 2. 保持提交历史整洁

- 频繁提交小的更改，而不是一次提交大量更改
- 编写清晰、有意义的提交信息
- 在推送前使用 `git rebase -i` 整理提交历史
- 避免提交敏感信息或大文件

### 3. 团队协作

- 使用 Pull Request 进行代码审查
- 遵循团队的分支命名约定
- 在合并前确保通过所有测试
- 及时更新本地分支以避免冲突

## 故障排除

### 1. 恢复文件

```bash
# 恢复工作区文件
git checkout -- <文件名>

# 恢复暂存区文件
git reset HEAD <文件名>

# 恢复到特定提交
git reset --hard <提交哈希>
```

### 2. 查找提交

```bash
# 查找包含特定内容的提交
git log -S "内容"

# 查找修改特定文件的提交
git log --follow <文件名>
```

### 3. 比较差异

```bash
# 比较工作区与暂存区
git diff

# 比较暂存区与最近提交
git diff --cached

# 比较两个提交
git diff <提交1> <提交2>
```

## 项目配置验证

### 1. 验证 .gitignore 配置

```bash
# 查看被 Git 跟踪的文件
git ls-files

# 查看未被忽略的文件
git ls-files --others --exclude-standard

# 检查特定文件是否被忽略
git check-ignore -v <文件路径>
```

### 2. 验证仓库状态

```bash
# 检查仓库完整性
git fsck

# 查看仓库统计信息
git count-objects -v
```

通过遵循这些指南，您可以有效地使用 Git 管理提猫直播助手项目的版本控制，确保代码的安全性和团队协作的效率。
