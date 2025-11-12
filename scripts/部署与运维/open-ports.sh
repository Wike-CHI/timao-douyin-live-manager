#!/bin/bash
# 开放必要的防火墙端口

echo "=========================================="
echo "开放防火墙端口"
echo "=========================================="

# 检查使用的防火墙类型
if command -v firewall-cmd &> /dev/null; then
    echo "检测到 firewalld"
    
    # 开放端口
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=8181/tcp
    firewall-cmd --permanent --add-port=10050/tcp
    
    # 重新加载
    firewall-cmd --reload
    
    # 显示当前规则
    echo ""
    echo "当前开放的端口："
    firewall-cmd --list-ports
    
elif command -v ufw &> /dev/null; then
    echo "检测到 ufw"
    
    # 开放端口
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8181/tcp
    ufw allow 10050/tcp
    
    # 显示状态
    echo ""
    echo "防火墙状态："
    ufw status
    
else
    echo "检测到 iptables"
    
    # 开放端口
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8181 -j ACCEPT
    iptables -A INPUT -p tcp --dport 10050 -j ACCEPT
    
    # 保存规则
    if [ -f /etc/debian_version ]; then
        iptables-save > /etc/iptables/rules.v4
    elif [ -f /etc/redhat-release ]; then
        service iptables save
    fi
    
    # 显示当前规则
    echo ""
    echo "当前iptables规则："
    iptables -L -n | grep -E "(80|443|8181|10050)"
fi

echo ""
echo "=========================================="
echo "防火墙端口已开放"
echo "=========================================="
echo ""
echo "⚠️ 云服务器还需要在安全组中开放端口："
echo "  - 80 (HTTP)"
echo "  - 443 (HTTPS)"
echo "  - 10050 (前端端口)"
echo "  - 8181 (后端端口)"

