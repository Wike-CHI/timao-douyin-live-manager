#!/bin/bash
# 测试后端API返回的数据

echo "=== 测试 /api/douyin/status ==="
curl -s http://127.0.0.1:11111/api/douyin/status | jq '.' | head -30

echo ""
echo "=== 测试 /api/report/live/status ==="
curl -s http://127.0.0.1:11111/api/report/live/status | jq '.' | head -30
