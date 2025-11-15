"""
高价值用户检测测试

测试文档：docs/产品使用手册/直播控制台双模式设计文档.md
审查人：叶维哲
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestHighValueUserDetection:
    """测试高价值用户检测功能"""
    
    @pytest.fixture
    def mock_context(self):
        """模拟直播间上下文数据"""
        return {
            'recent_gifts': [
                {
                    'user_name': '土豪A',
                    'gift_name': '嘉年华',
                    'gift_value': 3000,
                    'gift_count': 1,
                    'timestamp': 1700000000
                },
                {
                    'user_name': '用户B',
                    'gift_name': '跑车',
                    'gift_value': 200,
                    'gift_count': 2,
                    'timestamp': 1700000010
                },
                {
                    'user_name': '用户C',
                    'gift_name': '玫瑰',
                    'gift_value': 5,
                    'gift_count': 10,
                    'timestamp': 1700000020
                }
            ],
            'recent_comments': [
                {
                    'user_name': '活跃用户D',
                    'content': '666',
                    'user_level': 35,
                    'timestamp': 1700000030
                },
                {
                    'user_name': '活跃用户D',
                    'content': '主播棒棒哒',
                    'user_level': 35,
                    'timestamp': 1700000035
                },
                {
                    'user_name': '活跃用户D',
                    'content': '点赞',
                    'user_level': 35,
                    'timestamp': 1700000040
                },
                {
                    'user_name': '活跃用户D',
                    'content': '支持',
                    'user_level': 35,
                    'timestamp': 1700000045
                },
                {
                    'user_name': '活跃用户D',
                    'content': '加油',
                    'user_level': 35,
                    'timestamp': 1700000050
                },
                {
                    'user_name': '新用户E',
                    'content': '刚来',
                    'user_level': 5,
                    'timestamp': 1700000055
                }
            ]
        }
    
    def test_big_gift_detection(self, mock_context):
        """测试大额礼物检测（≥1000元应为高优先级）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查是否检测到土豪A
        big_spender = next((u for u in users if u['user_name'] == '土豪A'), None)
        assert big_spender is not None, "应该检测到送大额礼物的用户"
        assert big_spender['priority'] == 'high', "3000元礼物应为高优先级"
        assert big_spender['reason'] == 'big_gift', "原因应为big_gift"
    
    def test_medium_gift_detection(self, mock_context):
        """测试中等礼物检测（100-999元应为中优先级）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查是否检测到用户B（总价值400元）
        medium_spender = next((u for u in users if u['user_name'] == '用户B'), None)
        assert medium_spender is not None, "应该检测到送中等礼物的用户"
        assert medium_spender['priority'] == 'medium', "200元×2礼物应为中优先级"
    
    def test_high_frequency_comment_detection(self, mock_context):
        """测试高频互动检测（5分钟内评论≥5次）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查是否检测到活跃用户D（5条评论）
        active_user = next((u for u in users if u['user_name'] == '活跃用户D'), None)
        assert active_user is not None, "应该检测到高频评论用户"
        assert active_user['reason'] == 'high_engagement', "原因应为high_engagement"
        assert active_user['priority'] == 'medium', "高频互动应为中优先级"
    
    def test_high_level_user_detection(self, mock_context):
        """测试高等级用户检测（等级≥30）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查是否检测到高等级用户
        high_level_user = next(
            (u for u in users if u.get('user_level', 0) >= 30),
            None
        )
        assert high_level_user is not None, "应该检测到高等级用户"
    
    def test_small_gift_not_detected(self, mock_context):
        """测试小额礼物不应被检测为高价值用户（<100元）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 用户C送了50元礼物，不应被检测为高价值用户
        small_spender = next((u for u in users if u['user_name'] == '用户C'), None)
        assert small_spender is None, "小额礼物用户不应被检测为高价值用户"
    
    def test_user_deduplication(self, mock_context):
        """测试用户去重（同一用户不应重复出现）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查用户名是否唯一
        user_names = [u['user_name'] for u in users]
        assert len(user_names) == len(set(user_names)), "用户列表中不应有重复用户"
    
    def test_priority_sorting(self, mock_context):
        """测试优先级排序（高优先级应排在前面）"""
        from server.modules.high_value_detector import detect_high_value_users
        
        users = detect_high_value_users(mock_context)
        
        # 检查排序：high > medium > low
        priority_values = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        for i in range(len(users) - 1):
            current_priority = priority_values.get(users[i]['priority'], 0)
            next_priority = priority_values.get(users[i + 1]['priority'], 0)
            assert current_priority >= next_priority, "用户应按优先级降序排列"
    
    def test_empty_context(self):
        """测试空上下文"""
        from server.modules.high_value_detector import detect_high_value_users
        
        empty_context = {
            'recent_gifts': [],
            'recent_comments': []
        }
        
        users = detect_high_value_users(empty_context)
        assert users == [], "空上下文应返回空列表"
    
    def test_score_calculation(self, mock_context):
        """测试评分计算（礼物价值40%+互动频率30%+用户等级20%+历史贡献10%）"""
        from server.modules.high_value_detector import detect_high_value_users, calculate_score
        
        # 测试礼物价值评分
        gift_score = calculate_score({'gift_value': 1000})
        assert gift_score > 0, "礼物价值应产生评分"
        
        # 测试互动频率评分
        freq_score = calculate_score({'freq': 10})
        assert freq_score > 0, "互动频率应产生评分"
        
        # 测试用户等级评分
        level_score = calculate_score({'level': 50})
        assert level_score > 0, "用户等级应产生评分"


class TestHighValueUserAPI:
    """测试高价值用户API接口"""
    
    @pytest.fixture
    def test_client(self):
        """创建测试客户端"""
        from server.app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_generate_smart_scripts_endpoint(self, test_client):
        """测试智能话术生成接口"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {
                        "user_name": "土豪A",
                        "gift_name": "嘉年华",
                        "gift_value": 3000,
                        "gift_count": 1,
                        "timestamp": 1700000000
                    }
                ],
                "recent_comments": [],
                "silence_duration": 0,
                "current_viewers": 1234,
                "engagement_rate": 8.5,
                "style_profile": {
                    "persona": "专业知识分享者",
                    "tone": "亲切专业",
                    "catchphrases": ["宝宝们", "老铁"]
                }
            },
            "script_types": ["thank", "retain", "interact"],
            "max_scripts": 3,
            "priority_threshold": "medium"
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        
        assert response.status_code == 200, f"API调用失败: {response.text}"
        
        data = response.json()
        assert data['success'] is True, "响应应标记为成功"
        assert 'scripts' in data['data'], "响应应包含scripts字段"
        assert len(data['data']['scripts']) > 0, "应生成至少一条话术"
        
        # 检查话术结构
        script = data['data']['scripts'][0]
        assert 'id' in script, "话术应有id"
        assert 'type' in script, "话术应有type"
        assert 'priority' in script, "话术应有priority"
        assert 'line' in script, "话术应有line"
        assert 'rationale' in script, "话术应有rationale"
    
    def test_generate_thank_script_for_big_gift(self, test_client):
        """测试大额礼物自动生成感谢话术"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {
                        "user_name": "土豪王",
                        "gift_name": "嘉年华",
                        "gift_value": 3000,
                        "gift_count": 1,
                        "timestamp": 1700000000
                    }
                ],
                "style_profile": {
                    "persona": "活泼主播",
                    "tone": "热情",
                    "catchphrases": ["宝宝们", "老铁"]
                }
            },
            "script_types": ["thank"],
            "max_scripts": 1
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        data = response.json()
        
        assert data['success'] is True
        scripts = data['data']['scripts']
        assert len(scripts) > 0, "应生成感谢话术"
        
        thank_script = scripts[0]
        assert thank_script['type'] == 'thank', "话术类型应为thank"
        assert thank_script['priority'] == 'high', "大额礼物应为高优先级"
        assert '土豪王' in thank_script['line'] or '老板' in thank_script['line'], \
            "话术应提及用户或称呼"
    
    def test_max_scripts_limit(self, test_client):
        """测试最大话术数量限制"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {"user_name": f"用户{i}", "gift_value": 100 * i, "timestamp": 1700000000 + i}
                    for i in range(10)
                ],
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["thank"],
            "max_scripts": 3
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        data = response.json()
        
        assert len(data['data']['scripts']) <= 3, "返回的话术数量不应超过max_scripts"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

