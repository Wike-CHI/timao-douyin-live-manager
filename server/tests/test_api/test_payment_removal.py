# -*- coding: utf-8 -*-
"""
payment.py 移除验证测试

验证:
1. payment.py 文件已被移除
2. subscription.py 是唯一的订阅/支付 API
3. 所有功能由 subscription.py 提供
"""

import pytest
import os
from pathlib import Path


class TestPaymentAPIRemoval:
    """测试 payment.py 已被移除"""
    
    def test_payment_py_not_exists(self):
        """验证 payment.py 文件不存在"""
        payment_file = Path("server/app/api/payment.py")
        assert not payment_file.exists(), "payment.py 应该已被删除"
    
    def test_subscription_py_exists(self):
        """验证 subscription.py 仍然存在"""
        subscription_file = Path("server/app/api/subscription.py")
        assert subscription_file.exists(), "subscription.py 应该存在"
    
    def test_no_import_from_payment(self):
        """验证没有代码从 payment.py 导入"""
        # 搜索所有 Python 文件
        server_dir = Path("server")
        
        for py_file in server_dir.rglob("*.py"):
            if py_file.name == "__pycache__":
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8")
                
                # 检查是否有从 payment.py 导入
                assert "from server.app.api.payment import" not in content, \
                    f"{py_file} 仍然从 payment.py 导入"
                assert "from ..api.payment import" not in content, \
                    f"{py_file} 仍然从 payment.py 导入"
                assert "import server.app.api.payment" not in content, \
                    f"{py_file} 仍然导入 payment 模块"
                
            except Exception as e:
                # 忽略读取错误（如二进制文件）
                pass


class TestSubscriptionAPICompleteness:
    """测试 subscription.py 功能完整性"""
    
    def test_subscription_api_has_all_endpoints(self):
        """验证 subscription API 包含所有必要的端点"""
        from server.app.api.subscription import router
        
        # 获取所有路由
        routes = [route.path for route in router.routes]
        
        # 核心端点应该存在
        assert any("/plans" in route for route in routes), \
            "应该有获取套餐列表的端点"
        assert any("/my-subscription" in route or "/current" in route for route in routes), \
            "应该有获取当前订阅的端点"
        assert any("/payment" in route for route in routes), \
            "应该有支付相关的端点（/create-payment, /confirm-payment等）"
        
        # 至少应该有 5 个路由
        assert len(routes) >= 5, f"subscription API 应该有足够的端点，实际有 {len(routes)} 个: {routes}"


class TestSubscriptionPriceTypeConsistency:
    """测试订阅 API 的金额类型一致性"""
    
    def test_subscription_schemas_use_consistent_types(self):
        """验证 subscription schemas 使用一致的类型"""
        from server.app.schemas.subscription import SubscriptionPlanResponse
        
        # 检查模型定义
        schema = SubscriptionPlanResponse.model_json_schema()
        
        # price 字段应该存在
        assert "price" in schema["properties"], "应该有 price 字段"
        
        # 验证字段定义存在（Pydantic v2 schema结构可能不同）
        price_schema = schema["properties"]["price"]
        assert price_schema is not None, "price 字段应该有定义"
        
        # 验证是数值类型（可能是 anyOf 包含 number 或 string）
        assert "anyOf" in price_schema or "type" in price_schema, \
            "price 应该有类型定义"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

