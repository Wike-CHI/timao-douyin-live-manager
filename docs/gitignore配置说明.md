# .gitignore 配置说明

本文档详细说明了项目 `.gitignore` 文件的配置内容和 rationale，确保只有代码文件和文档文件存入本地仓库。

## 配置目标

确保 Git 仓库中只包含：

1. **源代码文件** - Python、JavaScript、TypeScript、HTML、CSS 等
2. **文档文件** - README、说明文档、设计文档等
3. **配置文件** - 项目配置、构建配置等（不包括敏感信息）

排除以下内容：

1. **环境相关文件** - 环境变量、虚拟环境等
2. **依赖文件** - npm、pip 安装的依赖包
3. **构建输出** - 编译、打包后的文件
4. **日志文件** - 运行时生成的日志
5. **临时文件** - 编辑器、系统生成的临时文件
6. **敏感数据** - API 密钥、密码等
7. **大文件** - 音频文件、模型文件等

## 配置详情

### 1. 环境变量文件

```gitignore
.env
.env.local
.env.*.local
```

**说明**: 环境变量文件通常包含敏感信息，不应提交到代码仓库。

### 2. 依赖目录

```gitignore
node_modules/
__pycache__/
*.py[cod]
*$py.class
```

**说明**: 依赖目录和 Python 编译文件可通过包管理器重新安装，无需提交。

### 3. 构建输出

```gitignore
dist/
build/
out/
*.egg-info/
release/
```

**说明**: 构建输出文件可通过构建过程重新生成，无需提交。

### 4. 日志文件

```gitignore
logs/
*.log
log.txt
```

**说明**: 日志文件是运行时生成的，不应提交到代码仓库。

### 5. 临时文件

```gitignore
*.tmp
*.temp
*.swp
*.swo
.DS_Store
Thumbs.db
```

**说明**: 临时文件和系统生成的文件不应提交。

### 6. IDE 配置

```gitignore
.vscode/
.idea/
```

**说明**: IDE 配置因人而异，不应提交到代码仓库。

### 7. 测试相关

```gitignore
coverage/
.nyc_output/
.coverage
.test_results/
.pytest_cache/
.nyc_output/
.ruff_cache/
```

**说明**: 测试覆盖率报告、缓存文件等不应提交。

### 8. Python 虚拟环境

```gitignore
.venv/
venv/
env/
ENV/
```

**说明**: 虚拟环境应由开发者本地创建，不应提交。

### 9. 音频和模型文件

```gitignore
audio_logs/
models/*/._____temp/
models/*/.lock/
```

**说明**: 音频日志和大型模型文件不应提交到 Git 仓库。

### 10. 敏感数据

```gitignore
secrets/
private/
```

**说明**: 敏感数据目录不应提交。

### 11. 系统和编辑器文件

```gitignore
*.sublime-project
*.sublime-workspace
*.vscode-test/
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
```

**说明**: 系统和编辑器生成的文件不应提交。

### 12. 项目特定文件

```gitignore
comprehensive_test_report.json
```

**说明**: 项目特定的大型输出文件不应提交。

## 验证配置

可以通过以下方式验证 `.gitignore` 配置是否正确：

1. 使用 `git status` 查看是否有不应提交的文件被跟踪
2. 使用 `validate_gitignore.py` 脚本检查大文件是否被正确忽略
3. 定期审查 `.gitignore` 文件，确保配置符合项目需求

## 最佳实践

1. **定期更新**: 随着项目发展，及时更新 `.gitignore` 文件
2. **团队同步**: 确保团队成员使用相同的 `.gitignore` 配置
3. **敏感信息**: 绝不在代码中硬编码敏感信息
4. **模板文件**: 为需要的配置文件提供 `.example` 模板文件

## 参考文档

- [GitHub gitignore templates](https://github.com/github/gitignore)
- [Git documentation on gitignore](https://git-scm.com/docs/gitignore)