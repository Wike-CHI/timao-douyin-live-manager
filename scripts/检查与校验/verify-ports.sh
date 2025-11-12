#!/bin/bash
# 验证端口是否正常开放和监听

echo "=========================================="
echo "端口验证检查"
echo "=========================================="

echo ""
echo "1. 检查端口监听状态："
echo "-------------------------------------------"
netstat -tulnp | grep -E ":(80|443|8181|10050)" || echo "⚠️ 没有发现监听端口"

echo ""
echo "2. 检查防火墙规则："
echo "-------------------------------------------"
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --list-ports
elif command -v ufw &> /dev/null; then
    ufw status | grep -E "(80|443|8181|10050)"
else
    iptables -L -n | grep -E "(80|443|8181|10050)"
fi

echo ""
echo "3. 测试本地端口连接："
echo "-------------------------------------------"
for port in 80 10050 8181; do
    if timeout 2 bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null; then
        echo "✓ 端口 $port 可访问"
    else
        echo "❌ 端口 $port 不可访问"
    fi
done

echo ""
echo "4. 测试外网端口（从服务器本地测试）："
echo "-------------------------------------------"
SERVER_IP=$(curl -s ifconfig.me)
echo "服务器公网IP: $SERVER_IP"

for port in 80 10050 8181; do
    if timeout 3 curl -s http://$SERVER_IP:$port >/dev/null 2>&1; then
        echo "✓ 端口 $port 外网可访问"
    else
        echo "❌ 端口 $port 外网不可访问（可能需要在云服务器安全组开放）"
    fi
done

echo ""
echo "=========================================="
echo "验证完成"
echo "=========================================="

