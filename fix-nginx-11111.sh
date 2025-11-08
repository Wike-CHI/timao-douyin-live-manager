#!/bin/bash
# 更新Nginx反向代理到11111端口（后端新端口）

echo "🔧 更新Nginx反向代理配置到端口11111..."
echo ""

# 配置文件路径
CONFIG_FILE="/www/server/panel/vhost/nginx/timao-backend.conf"

# 备份现有配置
if [ -f "${CONFIG_FILE}" ]; then
    echo "📦 备份现有配置..."
    sudo cp ${CONFIG_FILE} ${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)
fi

# 创建新的Nginx配置文件
sudo tee ${CONFIG_FILE} > /dev/null <<'EOF'
server {
    listen 80;
    server_name 129.211.218.135 _;
    
    # 日志配置
    access_log /www/wwwlogs/timao-backend-access.log;
    error_log /www/wwwlogs/timao-backend-error.log;
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:11111/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API文档
    location /docs {
        proxy_pass http://127.0.0.1:11111/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:11111/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API代理
    location / {
        proxy_pass http://127.0.0.1:11111;
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
        
        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

echo "✅ 配置文件已更新: ${CONFIG_FILE}"
echo ""

# 测试配置
echo "🧪 测试Nginx配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ 配置测试通过"
    echo ""
    echo "🔄 重载Nginx..."
    sudo nginx -s reload
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx已重载成功"
        echo ""
        echo "📋 现在可以访问："
        echo "   - 健康检查: http://129.211.218.135/health"
        echo "   - API文档:  http://129.211.218.135/docs"
        echo "   - API接口:  http://129.211.218.135/api/..."
        echo ""
        echo "🔍 验证连接："
        echo "   curl http://129.211.218.135/health"
    else
        echo "❌ Nginx重载失败"
        exit 1
    fi
else
    echo "❌ 配置测试失败，请检查配置文件"
    echo "配置文件位置: ${CONFIG_FILE}"
    exit 1
fi

