#!/bin/bash
# 检查Nginx配置

echo "🔍 检查Nginx配置..."
echo ""

# 1. 查看Nginx主配置
echo "1️⃣ Nginx配置文件位置："
echo "   /www/server/nginx/conf/nginx.conf"
echo ""

# 2. 检查80端口是否被Nginx占用
echo "2️⃣ 检查80端口监听..."
netstat -tlnp | grep ":80 " || ss -tlnp | grep ":80 "
echo ""

# 3. 检查是否有server块监听80端口
echo "3️⃣ 检查Nginx server配置..."
grep -r "listen.*80" /www/server/nginx/conf/ 2>/dev/null | head -10
echo ""

# 4. 检查是否有proxy_pass配置
echo "4️⃣ 检查proxy_pass配置..."
grep -r "proxy_pass" /www/server/nginx/conf/ 2>/dev/null | head -10
echo ""

# 5. 检查访问日志
echo "5️⃣ 检查Nginx访问日志（最近10行）..."
if [ -f /www/server/nginx/logs/access.log ]; then
    tail -10 /www/server/nginx/logs/access.log
else
    echo "   未找到访问日志"
fi
echo ""

# 6. 检查错误日志
echo "6️⃣ 检查Nginx错误日志（最近10行）..."
if [ -f /www/server/nginx/logs/error.log ]; then
    tail -10 /www/server/nginx/logs/error.log
else
    echo "   未找到错误日志"
fi

echo ""
echo "💡 如果访问 http://129.211.218.135（无端口），会走80端口，需要配置Nginx代理"
echo "   如果访问 http://129.211.218.135:10050，应该直接访问后端，不经过Nginx"

