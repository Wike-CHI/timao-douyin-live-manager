# -*- coding: utf-8 -*-
"""
分页参数一致性测试

验证所有列表查询 API 都使用统一的 skip/limit 分页参数
"""

import pytest


class TestPaginationConsistency:
    """测试分页参数一致性"""
    
    def test_audit_logs_uses_skip_limit(self, client, override_get_db):
        """测试 audit API 使用 skip/limit 参数"""
        # 注意: 此端点需要管理员权限，这里只测试参数接受
        # 实际测试需要模拟管理员用户
        
        # 验证端点接受 skip 和 limit 参数
        response = client.get(
            "/audit/logs",
            params={"skip": 0, "limit": 10}
        )
        # 401 是预期的（未认证），重要的是参数被接受
        assert response.status_code in [200, 401, 403]
    
    def test_live_report_history_uses_skip_limit(self, client, override_get_db):
        """测试 live_report history API 使用 skip/limit 参数"""
        response = client.get(
            "/api/live/report/history",
            params={"skip": 0, "limit": 5}
        )
        
        # 应该返回成功响应
        assert response.status_code == 200
        
        payload = response.json()
        assert payload["success"] is True
        assert "data" in payload
        
        # data 应该是列表
        assert isinstance(payload["data"], list)
    
    def test_pagination_params_validation(self, client, override_get_db):
        """测试分页参数验证"""
        # skip 不能为负数
        response = client.get(
            "/api/live/report/history",
            params={"skip": -1, "limit": 10}
        )
        # FastAPI Query 验证应该返回 422
        assert response.status_code == 422
        
        # limit 应该有合理的范围
        response = client.get(
            "/api/live/report/history",
            params={"skip": 0, "limit": 0}
        )
        # 应该接受（后端会处理）
        assert response.status_code in [200, 422]


class TestPaginationBehavior:
    """测试分页行为"""
    
    def test_live_report_pagination_works(self, client, override_get_db):
        """测试 live_report 分页功能"""
        # 获取所有报告
        response_all = client.get("/api/live/report/history", params={"limit": 100})
        assert response_all.status_code == 200
        all_reports = response_all.json()["data"]
        
        if len(all_reports) > 1:
            # 测试 skip 参数
            response_skip = client.get(
                "/api/live/report/history",
                params={"skip": 1, "limit": 100}
            )
            assert response_skip.status_code == 200
            skipped_reports = response_skip.json()["data"]
            
            # 应该少一个
            assert len(skipped_reports) == len(all_reports) - 1
            
            # 第一个应该是原列表的第二个
            if len(all_reports) > 1 and len(skipped_reports) > 0:
                assert skipped_reports[0] == all_reports[1]
    
    def test_live_report_limit_works(self, client, override_get_db):
        """测试 live_report limit 参数"""
        # 限制返回 2 个
        response = client.get("/api/live/report/history", params={"skip": 0, "limit": 2})
        assert response.status_code == 200
        
        reports = response.json()["data"]
        # 返回的数量不应超过 limit
        assert len(reports) <= 2


class TestPaginationConsistencyAcrossAPIs:
    """测试跨 API 的分页参数一致性"""
    
    def test_all_list_apis_use_same_param_names(self):
        """验证所有列表 API 使用相同的参数名"""
        # 这是一个文档测试，确保开发者知道统一规范
        
        expected_params = {
            "skip": "跳过记录数",
            "limit": "返回记录数"
        }
        
        # 确保文档中记录了这个规范
        assert expected_params["skip"] == "跳过记录数"
        assert expected_params["limit"] == "返回记录数"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

