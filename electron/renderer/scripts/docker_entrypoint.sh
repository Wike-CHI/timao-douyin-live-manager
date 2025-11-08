#!/bin/sh
# ============================================
# Docker 入口脚本
# 用于替换 Nginx 配置中的环境变量（如果需要）
# ============================================

# 如果设置了 BACKEND_URL，替换 nginx.conf 中的占位符
if [ -n "$BACKEND_URL" ]; then
    # 使用 envsubst 替换环境变量
    envsubst '${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
fi

# 启动 Nginx
exec nginx -g "daemon off;"

