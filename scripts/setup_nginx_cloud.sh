#!/bin/bash
# 提猫直播助手 - Nginx 云端服务配置脚本
# 功能：自动配置Nginx反向代理到timao-cloud服务（端口15000）
# 审查人：叶维哲

set -e

echo "========================================"
echo "🔧 配置Nginx反向代理到云端服务"
echo "========================================"
echo ""

# 检查运行权限
if [ "$EUID" -ne 0 ]; then 
   echo "⚠️  需要root权限运行此脚本"
   echo "请使用: sudo $0"
   exit 1
fi

# 1. 检测Nginx
echo "1️⃣  检测Nginx..."
if ! command -v nginx &> /dev/null; then
    echo "❌ 未安装Nginx"
    echo "请先安装: apt install nginx (Ubuntu) 或 yum install nginx (CentOS)"
    exit 1
fi
NGINX_VERSION=$(nginx -v 2>&1 | cut -d '/' -f 2)
echo "✅ Nginx: $NGINX_VERSION"

# 2. 检测Nginx配置目录
echo ""
echo "2️⃣  检测配置目录..."

# 宝塔面板
if [ -d "/www/server/panel/vhost/nginx" ]; then
    NGINX_CONF_DIR="/www/server/panel/vhost/nginx"
    NGINX_TYPE="宝塔面板"
    CONFIG_FILE="${NGINX_CONF_DIR}/timao-cloud.conf"
    
# 标准Nginx
elif [ -d "/etc/nginx/sites-available" ]; then
    NGINX_CONF_DIR="/etc/nginx/sites-available"
    NGINX_TYPE="标准Nginx"
    CONFIG_FILE="${NGINX_CONF_DIR}/timao-cloud.conf"
    SYMLINK="/etc/nginx/sites-enabled/timao-cloud.conf"
    
# 其他
else
    echo "❌ 未检测到支持的Nginx配置目录"
    echo "请手动配置: nginx-cloud.conf"
    exit 1
fi

echo "✅ 检测到: $NGINX_TYPE"
echo "   配置目录: $NGINX_CONF_DIR"

# 3. 备份旧配置
echo ""
echo "3️⃣  备份旧配置..."

OLD_CONFIGS=(
    "${NGINX_CONF_DIR}/timao-backend.conf"
    "${NGINX_CONF_DIR}/129.211.218.135.conf"
)

for OLD_CONFIG in "${OLD_CONFIGS[@]}"; do
    if [ -f "$OLD_CONFIG" ]; then
        BACKUP_FILE="${OLD_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$OLD_CONFIG" "$BACKUP_FILE"
        echo "✅ 已备份: $(basename $OLD_CONFIG) → $(basename $BACKUP_FILE)"
    fi
done

# 4. 获取服务器IP
echo ""
echo "4️⃣  获取服务器IP..."
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="129.211.218.135"
    echo "⚠️  无法自动获取IP，使用默认: $SERVER_IP"
else
    echo "✅ 服务器IP: $SERVER_IP"
fi

read -p "是否使用此IP？(Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "✅ 使用IP: $SERVER_IP"
else
    read -p "请输入服务器IP或域名: " SERVER_IP
fi

# 5. 创建配置文件
echo ""
echo "5️⃣  创建配置文件..."

cat > ${CONFIG_FILE} <<EOF
# 提猫直播助手 - Nginx 反向代理配置（云端服务）
# 自动生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# 云端服务端口: 15000

server {
    listen 80;
    server_name ${SERVER_IP};
    
    # 日志配置
    access_log /www/wwwlogs/timao-cloud-access.log;
    error_log /www/wwwlogs/timao-cloud-error.log;
    
    # 客户端配置
    client_max_body_size 20M;
    
    # 超时设置
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:15000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 用户认证 API
    location /api/auth/ {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 用户资料 API
    location /profile/ {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 订阅 API
    location /api/subscription/ {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 支付 API
    location /api/payment/ {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 管理后台 API
    location /api/admin/ {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:15000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:15000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # 静态文件（Nginx直接服务，性能更好）
    location /static/ {
        alias /www/wwwroot/wwwroot/timao-douyin-live-manager/server/cloud/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
        access_log off;
        try_files \$uri =404;
    }
    
    # 根路径（控制台）
    location = / {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # API请求
    location / {
        proxy_pass http://127.0.0.1:15000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
    }
    
    # 忽略favicon和robots
    location = /favicon.ico {
        log_not_found off;
        access_log off;
        return 204;
    }
    
    location = /robots.txt {
        log_not_found off;
        access_log off;
        return 200 "User-agent: *\nDisallow: /\n";
    }
}
EOF

echo "✅ 配置文件已创建: $CONFIG_FILE"

# 6. 创建软链接（标准Nginx）
if [ "$NGINX_TYPE" = "标准Nginx" ]; then
    echo ""
    echo "6️⃣  创建软链接..."
    ln -sf $CONFIG_FILE $SYMLINK
    echo "✅ 软链接已创建: $SYMLINK"
fi

# 7. 测试配置
echo ""
echo "7️⃣  测试配置..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ 配置测试通过"
else
    echo "❌ 配置测试失败"
    echo "请检查配置文件: $CONFIG_FILE"
    exit 1
fi

# 8. 重载Nginx
echo ""
echo "8️⃣  重载Nginx..."

if [ "$NGINX_TYPE" = "宝塔面板" ]; then
    # 宝塔面板使用自己的重载命令
    /etc/init.d/nginx reload || nginx -s reload
else
    nginx -s reload
fi

echo "✅ Nginx已重载"

# 9. 验证部署
echo ""
echo "9️⃣  验证部署..."
sleep 2

HEALTH_CHECK=$(curl -s http://localhost:15000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ 云端服务正常运行"
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo "⚠️  云端服务未响应"
    echo "请确保timao-cloud服务已启动: pm2 status timao-cloud"
fi

# 完成
echo ""
echo "========================================"
echo "🎉 Nginx配置完成！"
echo "========================================"
echo ""
echo "📊 配置信息："
echo "  - 配置文件: $CONFIG_FILE"
echo "  - 监听端口: 80"
echo "  - 代理端口: 15000 (timao-cloud)"
echo "  - 服务器: $SERVER_IP"
echo ""
echo "🔗 访问地址："
echo "  - 健康检查: http://${SERVER_IP}/health"
echo "  - 用户登录: http://${SERVER_IP}/api/auth/login"
echo "  - API文档: http://${SERVER_IP}/docs"
echo ""
echo "📝 常用命令："
echo "  - 查看配置: cat $CONFIG_FILE"
echo "  - 测试配置: nginx -t"
echo "  - 重载配置: nginx -s reload"
echo "  - 查看日志: tail -f /www/wwwlogs/timao-cloud-access.log"
echo ""
echo "⚠️  注意事项："
echo "  1. 确保云端服务已启动: pm2 status timao-cloud"
echo "  2. 确保防火墙开放80端口: ufw allow 80/tcp"
echo "  3. 客户端配置API地址: http://${SERVER_IP}"
echo ""

