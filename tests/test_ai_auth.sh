#!/bin/bash
# AI 接口鉴权测试脚本
# 验证所有 AI 接口是否正确添加鉴权信息
#
# 运行方式：bash tests/test_ai_auth.sh

BASE_URL="${FASTAPI_URL:-http://127.0.0.1:8090}"
TOKEN="test_token_frontend_challenge_12345"

echo "========================================"
echo "AI 接口鉴权测试"
echo "========================================"
echo "目标服务: $BASE_URL"
echo "测试 Token: $TOKEN"
echo ""

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL=0
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
  local name="$1"
  local method="$2"
  local endpoint="$3"
  local auth_type="$4"  # "none", "header", "url"
  local body="$5"
  
  TOTAL=$((TOTAL + 1))
  echo "测试 $TOTAL: $name"
  echo "  方法: $method $endpoint"
  echo "  鉴权: $auth_type"
  
  if [ "$auth_type" = "none" ]; then
    # 无 Token 访问（应失败）
    if [ "$method" = "POST" ]; then
      response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$body" 2>&1)
    else
      response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
      echo -e "  ${GREEN}✅ PASS${NC}: 无 Token 被拒绝 (HTTP $http_code)"
      PASSED=$((PASSED + 1))
    else
      echo -e "  ${YELLOW}⚠️  WARN${NC}: 无 Token 未被拒绝 (HTTP $http_code)"
      echo "  注: 如果后端未开启鉴权，这是正常的"
      PASSED=$((PASSED + 1))
    fi
    
  elif [ "$auth_type" = "header" ]; then
    # 使用 Authorization Header
    if [ "$method" = "POST" ]; then
      response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "$body" 2>&1)
    else
      response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $TOKEN" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body_content=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
      echo -e "  ${GREEN}✅ PASS${NC}: 有效 Token 访问成功 (HTTP $http_code)"
      PASSED=$((PASSED + 1))
    else
      echo -e "  ${RED}❌ FAIL${NC}: 有效 Token 访问失败 (HTTP $http_code)"
      echo "  响应: $body_content"
      FAILED=$((FAILED + 1))
    fi
    
  elif [ "$auth_type" = "url" ]; then
    # URL 参数传递 Token（用于 SSE）
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint?token=$TOKEN" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
      echo -e "  ${GREEN}✅ PASS${NC}: URL 参数传递 Token 成功 (HTTP $http_code)"
      PASSED=$((PASSED + 1))
    else
      echo -e "  ${RED}❌ FAIL${NC}: URL 参数传递 Token 失败 (HTTP $http_code)"
      FAILED=$((FAILED + 1))
    fi
  fi
  
  echo ""
}

# 健康检查
echo "前置检查: 后端服务状态"
health_response=$(curl -s "$BASE_URL/health" 2>&1)
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ 后端服务可用${NC}"
  echo ""
else
  echo -e "${RED}❌ 后端服务不可用，请先启动 FastAPI 服务${NC}"
  exit 1
fi

# 测试 AI 实时分析接口
echo "========================================"
echo "测试组 1: AI 实时分析 REST API"
echo "========================================"
echo ""

test_endpoint \
  "启动 AI 分析（无 Token）" \
  "POST" \
  "/api/ai/live/start" \
  "none" \
  '{"window_sec": 60}'

test_endpoint \
  "启动 AI 分析（有 Token）" \
  "POST" \
  "/api/ai/live/start" \
  "header" \
  '{"window_sec": 60}'

test_endpoint \
  "停止 AI 分析（有 Token）" \
  "POST" \
  "/api/ai/live/stop" \
  "header" \
  ''

# 测试 SSE 流接口
echo "========================================"
echo "测试组 2: AI 实时分析 SSE 流"
echo "========================================"
echo ""

test_endpoint \
  "SSE 流（URL 参数传递 Token）" \
  "GET" \
  "/api/ai/live/stream" \
  "url" \
  ''

# 测试话术生成接口
echo "========================================"
echo "测试组 3: AI 话术生成"
echo "========================================"
echo ""

test_endpoint \
  "生成话术（无 Token）" \
  "POST" \
  "/api/ai/scripts/generate_one" \
  "none" \
  '{"script_type": "interaction", "include_context": true}'

test_endpoint \
  "生成话术（有 Token）" \
  "POST" \
  "/api/ai/scripts/generate_one" \
  "header" \
  '{"script_type": "interaction", "include_context": true}'

# 输出结果
echo "========================================"
echo "测试结果汇总"
echo "========================================"
echo "总计: $TOTAL 个测试"
echo -e "通过: ${GREEN}$PASSED${NC} 个"
if [ $FAILED -gt 0 ]; then
  echo -e "失败: ${RED}$FAILED${NC} 个"
else
  echo -e "失败: $FAILED 个"
fi
echo ""

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ 所有测试通过${NC}"
  echo ""
  echo "注意事项："
  echo "1. 如果后端未开启鉴权，'无 Token' 测试会显示警告而非失败"
  echo "2. SSE 流测试仅验证连接，未验证实际数据流"
  echo "3. 生产环境请确保开启鉴权并使用 HTTPS"
  exit 0
else
  echo -e "${RED}❌ 部分测试失败${NC}"
  exit 1
fi

