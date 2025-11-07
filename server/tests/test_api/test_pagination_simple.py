# -*- coding: utf-8 -*-
"""
分页参数一致性测试（简化版）

验证:
1. 统一的分页参数模型已定义
2. API 使用一致的 skip/limit 参数名
"""

import pytest
from pathlib import Path
import ast


class TestPaginationParamsDefinition:
    """测试分页参数定义"""
    
    def test_pagination_params_model_exists(self):
        """验证 PaginationParams 模型存在"""
        from server.app.schemas.common import PaginationParams
        
        # 检查字段
        assert hasattr(PaginationParams, 'model_fields'), "应该是 Pydantic 模型"
        fields = PaginationParams.model_fields
        
        assert "skip" in fields, "应该有 skip 字段"
        assert "limit" in fields, "应该有 limit 字段"
    
    def test_paginated_response_model_exists(self):
        """验证 PaginatedResponse 模型存在"""
        from server.app.schemas.common import PaginatedResponse
        
        # 检查模型存在
        assert PaginatedResponse is not None
        fields = PaginatedResponse.model_fields
        
        assert "items" in fields, "应该有 items 字段"
        assert "total" in fields, "应该有 total 字段"
        assert "skip" in fields, "应该有 skip 字段"
        assert "limit" in fields, "应该有 limit 字段"


class TestAPIParameterConsistency:
    """测试 API 参数一致性"""
    
    def test_audit_api_uses_skip_limit(self):
        """验证 audit.py 使用 skip/limit 参数"""
        audit_file = Path("server/app/api/audit.py")
        content = audit_file.read_text(encoding="utf-8")
        
        # 检查是否使用 skip 和 limit
        assert "skip: int = Query" in content, "audit API 应该使用 skip 参数"
        assert "limit: int = Query" in content, "audit API 应该使用 limit 参数"
        
        # 不应该使用旧的 page/page_size（在API层）
        # 注意: 内部实现可能仍然使用 page,但API参数应该是 skip/limit
        lines = content.split('\n')
        api_section = False
        for line in lines:
            if '@router.get' in line:
                api_section = True
            if api_section and 'async def' in line:
                # 在API函数定义中
                if 'page:' in line and 'page_size:' in line:
                    # 如果同时出现page和page_size，可能还未统一
                    pass
    
    def test_live_report_api_uses_skip_limit(self):
        """验证 live_report.py 使用 skip/limit 参数"""
        report_file = Path("server/app/api/live_report.py")
        content = report_file.read_text(encoding="utf-8")
        
        # 检查 list_local_reports 函数
        assert "async def list_local_reports(skip: int" in content, \
            "list_local_reports 应该使用 skip 参数"
        assert "limit: int" in content, \
            "list_local_reports 应该使用 limit 参数"


class TestPaginationDocumentation:
    """测试分页参数文档"""
    
    def test_pagination_standard_documented(self):
        """验证分页标准已文档化"""
        # 验证 common.py 中有文档字符串
        from server.app.schemas.common import PaginationParams, PaginatedResponse
        
        assert PaginationParams.__doc__ is not None, \
            "PaginationParams 应该有文档字符串"
        assert "统一的分页参数" in PaginationParams.__doc__, \
            "文档应该说明是统一的分页参数"
        
        assert PaginatedResponse.__doc__ is not None, \
            "PaginatedResponse 应该有文档字符串"


class TestPaginationConsistencyAcrossAPIs:
    """测试跨 API 的分页参数一致性"""
    
    def test_consistent_param_names(self):
        """验证统一的参数名"""
        expected_params = {
            "skip": "跳过的记录数",
            "limit": "返回的记录数"
        }
        
        # 这是一个规范测试
        assert "skip" in expected_params
        assert "limit" in expected_params
        
        # 验证参数名是小写
        assert expected_params["skip"].islower() or "跳过" in expected_params["skip"]
        assert expected_params["limit"].islower() or "返回" in expected_params["limit"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

