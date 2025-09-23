# 云端最小鉴权/支付后端（Node + Express）

用途：作为“登录/注册/支付”最小接口示例部署到腾讯云云托管（CloudBase Run）。请接入真实用户体系/数据库/鉴权逻辑后再用于生产。

## 目录

- `index.js` Express 程序，暴露 `/api/auth/*` 与 `/api/payment/*`
- `package.json` 依赖与启动脚本
- `Dockerfile` 用于构建容器镜像（端口 8080）

## 本地运行

```
npm ci
npm start
# http://127.0.0.1:8080/health
```

## 环境变量

- `ALLOW_ORIGINS` 允许跨域来源，逗号分隔，例如：
  - `ALLOW_ORIGINS=http://127.0.0.1:5173,https://auth.company.com`
- `PORT` 服务端口（默认 8080）

## 镜像构建与部署（TCR + 云托管）

1) 构建镜像

```
docker build -t ccr.ccs.tencentyun.com/<namespace>/auth-backend-node:latest .
```

2) 登录并推送到 TCR（在腾讯云控制台创建命名空间并获取登录命令）

```
docker login ccr.ccs.tencentyun.com
docker push ccr.ccs.tencentyun.com/<namespace>/auth-backend-node:latest
```

3) 云托管创建服务

- 选择镜像来源 TCR；容器端口 8080；设置 `ALLOW_ORIGINS`
- 开启公网访问

4) 绑定自定义域名

- 绑定 `auth.company.com` 到该服务；按提示添加域名 CNAME 记录；证书可自动签发

5) 验证

- `https://auth.company.com/health` 应返回 `{ ok: true }`

> 提示：生产环境请替换内存状态为数据库（MySQL/Redis/COS 等），并对登录密码使用哈希（如 bcrypt），上传图片存储到 COS 并添加访问鉴权。
