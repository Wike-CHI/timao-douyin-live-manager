#!/bin/bash
# 修复防火墙配置，开放10050端口

BACKEND_PORT="10050"

echo "🔥 配置防火墙，开放端口 ${BACKEND_PORT}..."
echo ""

# 检测防火墙类型并配置
if command -v ufw &> /dev/null; then
    echo "检测到 ufw 防火墙"
    echo "开放端口..."
    sudo ufw allow ${BACKEND_PORT}/tcp
    sudo ufw reload
    echo "✅ ufw 配置完成"
    
elif command -v firewall-cmd &> /dev/null; then
    echo "检测到 firewalld 防火墙"
    echo "开放端口..."
    sudo firewall-cmd --permanent --add-port=${BACKEND_PORT}/tcp
    sudo firewall-cmd --reload
    echo "✅ firewalld 配置完成"
    
elif [ -f /etc/redhat-release ]; then
    echo "检测到 CentOS/RHEL 系统"
    echo "尝试使用 iptables..."
    sudo iptables -I INPUT -p tcp --dport ${BACKEND_PORT} -j ACCEPT
    sudo service iptables save 2>/dev/null || echo "⚠️  请手动保存iptables规则"
    echo "✅ iptables 配置完成"
    
else
    echo "⚠️  未检测到常见防火墙，请手动配置："
    echo "   端口: ${BACKEND_PORT}/tcp"
fi

echo ""
echo "📋 检查端口监听状态..."
netstat -tlnp | grep ${BACKEND_PORT} || ss -tlnp | grep ${BACKEND_PORT}

echo ""
echo "✅ 防火墙配置完成"
echo ""
echo "⚠️  重要提示："
echo "   如果仍然无法访问，请检查："
echo "   1. 云服务器安全组是否开放端口 ${BACKEND_PORT}"
echo "   2. 阿里云/腾讯云等控制台 -> 安全组 -> 添加入站规则"
echo "   3. 规则：TCP协议，端口 ${BACKEND_PORT}，源地址 0.0.0.0/0"

