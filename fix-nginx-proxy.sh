#!/bin/bash
# 配置Nginx反向代理到10050端口

echo "🔧 配置Nginx反向代理..."
echo ""

# 创建Nginx配置文件
CONFIG_FILE="/www/server/panel/vhost/nginx/timao-backend.conf"

sudo tee ${CONFIG_FILE} > /dev/null <<'EOF'
server {
    listen 80;
    server_name 129.211.218.135 _;
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:10050/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API代理
    location / {
        proxy_pass http://127.0.0.1:10050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "✅ 配置文件已创建: ${CONFIG_FILE}"
echo ""

# 测试配置
echo "🧪 测试Nginx配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ 配置测试通过"
    echo ""
    echo "🔄 重载Nginx..."
    sudo nginx -s reload
    echo "✅ Nginx已重载"
    echo ""
    echo "📋 现在可以访问："
    echo "   http://129.211.218.135/health"
    echo "   http://129.211.218.135/"
else
    echo "❌ 配置测试失败，请检查配置文件"
    exit 1
fi

