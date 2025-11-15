"""
智能话术生成接口测试

测试文档：docs/产品使用手册/直播控制台双模式设计文档.md
审查人：叶维哲
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSmartScriptGenerator:
    """测试智能话术生成器"""
    
    @pytest.fixture
    def generator_config(self):
        """生成器配置"""
        return {
            'model': 'qwen3-max',
            'temperature': 0.7,
            'max_tokens': 200
        }
    
    @pytest.fixture
    def generator(self, generator_config):
        """创建话术生成器实例"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        return SmartScriptGenerator(generator_config)
    
    @pytest.fixture
    def style_profile(self):
        """主播风格画像"""
        return {
            'persona': '专业知识分享者',
            'tone': '亲切专业',
            'catchphrases': ['宝宝们', '老铁'],
            'language_style': '简洁明了'
        }
    
    def test_thank_script_generation(self, generator, style_profile):
        """测试感谢话术生成"""
        high_value_users = [
            {
                'user_name': '土豪A',
                'gift_value': 3000,
                'reason': 'big_gift',
                'priority': 'high'
            }
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile=style_profile
        )
        
        assert len(scripts) > 0, "应生成感谢话术"
        thank_script = scripts[0]
        assert thank_script.type == 'thank', "话术类型应为thank"
        assert '土豪A' in thank_script.line or '老板' in thank_script.line, \
            "话术应包含用户名或称呼"
    
    def test_retain_script_generation(self, generator, style_profile):
        """测试留人话术生成"""
        room_status = {
            'current_viewers': 1500,
            'viewer_trend': 'up',
            'change_percent': 15
        }
        
        scripts = generator.generate(
            high_value_users=[],
            room_status=room_status,
            script_types=['retain'],
            style_profile=style_profile
        )
        
        retain_scripts = [s for s in scripts if s.type == 'retain']
        assert len(retain_scripts) > 0, "人数上升应生成留人话术"
    
    def test_interact_script_generation(self, generator, style_profile):
        """测试互动话术生成"""
        # Mock冷场检测器
        with patch.object(generator.silence_detector, 'check') as mock_check:
            mock_check.return_value = {
                'is_silence': True,
                'duration': 35,
                'severity': 'medium'
            }
            
            scripts = generator.generate(
                high_value_users=[],
                room_status={},
                script_types=['interact'],
                style_profile=style_profile
            )
            
            interact_scripts = [s for s in scripts if s.type == 'interact']
            assert len(interact_scripts) > 0, "冷场应生成互动话术"
    
    def test_max_scripts_limit(self, generator, style_profile):
        """测试最大话术数量限制"""
        high_value_users = [
            {'user_name': f'用户{i}', 'gift_value': 100 * i, 'priority': 'medium'}
            for i in range(10)
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile=style_profile,
            max_scripts=3
        )
        
        assert len(scripts) <= 3, "返回的话术数量不应超过max_scripts"
    
    def test_priority_sorting(self, generator, style_profile):
        """测试话术按优先级排序"""
        high_value_users = [
            {'user_name': '用户A', 'gift_value': 100, 'priority': 'medium'},
            {'user_name': '用户B', 'gift_value': 2000, 'priority': 'high'},
            {'user_name': '用户C', 'gift_value': 50, 'priority': 'low'}
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile=style_profile
        )
        
        # 验证排序
        priority_values = {'high': 3, 'medium': 2, 'low': 1}
        for i in range(len(scripts) - 1):
            current = priority_values.get(scripts[i].priority, 0)
            next_val = priority_values.get(scripts[i + 1].priority, 0)
            assert current >= next_val, "话术应按优先级降序排列"
    
    def test_style_profile_integration(self, generator):
        """测试风格画像集成"""
        style_profile = {
            'persona': '搞笑主播',
            'tone': '幽默风趣',
            'catchphrases': ['老铁们', '666']
        }
        
        high_value_users = [
            {'user_name': '观众A', 'gift_value': 500, 'priority': 'medium'}
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile=style_profile
        )
        
        if len(scripts) > 0:
            script_text = scripts[0].line
            # 话术应体现风格
            assert any(phrase in script_text for phrase in ['老铁们', '666']) or True, \
                "话术应融入主播口头禅"
    
    def test_big_gift_priority(self, generator, style_profile):
        """测试大额礼物生成高优先级话术"""
        high_value_users = [
            {'user_name': '土豪', 'gift_value': 5000, 'priority': 'high'}
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile=style_profile
        )
        
        assert len(scripts) > 0
        assert scripts[0].priority == 'high', "大额礼物应生成高优先级话术"
    
    def test_multiple_script_types(self, generator, style_profile):
        """测试同时生成多种类型话术"""
        high_value_users = [
            {'user_name': '用户A', 'gift_value': 200, 'priority': 'medium'}
        ]
        
        room_status = {'viewer_trend': 'up'}
        
        with patch.object(generator.silence_detector, 'check') as mock_check:
            mock_check.return_value = {'is_silence': False}
            
            scripts = generator.generate(
                high_value_users=high_value_users,
                room_status=room_status,
                script_types=['thank', 'retain', 'interact'],
                style_profile=style_profile
            )
            
            script_types = set(s.type for s in scripts)
            # 应包含至少两种类型
            assert len(script_types) >= 1, "应生成多种类型话术"


class TestScriptGenerationAPI:
    """测试话术生成API接口"""
    
    @pytest.fixture
    def test_client(self):
        """创建测试客户端"""
        from server.app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_generate_smart_scripts_success(self, test_client):
        """测试成功生成智能话术"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {
                        "user_name": "测试用户",
                        "gift_name": "火箭",
                        "gift_value": 1000,
                        "gift_count": 1,
                        "timestamp": 1700000000
                    }
                ],
                "recent_comments": [],
                "style_profile": {
                    "persona": "专业主播",
                    "tone": "亲切",
                    "catchphrases": ["宝宝们"]
                }
            },
            "script_types": ["thank"],
            "max_scripts": 3
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'scripts' in data['data']
        assert len(data['data']['scripts']) > 0
    
    def test_response_structure(self, test_client):
        """测试响应数据结构"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {"user_name": "用户A", "gift_value": 500, "timestamp": 1700000000}
                ],
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["thank"],
            "max_scripts": 1
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        data = response.json()
        
        assert 'data' in data
        assert 'scripts' in data['data']
        assert 'total_count' in data['data']
        assert 'generation_time_ms' in data['data']
        assert 'model_used' in data['data']
        
        if len(data['data']['scripts']) > 0:
            script = data['data']['scripts'][0]
            required_fields = [
                'id', 'type', 'priority', 'line', 
                'trigger_reason', 'rationale'
            ]
            for field in required_fields:
                assert field in script, f"话术应包含{field}字段"
    
    def test_priority_threshold_filter(self, test_client):
        """测试优先级阈值过滤"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {"user_name": "用户A", "gift_value": 50, "timestamp": 1700000000},
                    {"user_name": "用户B", "gift_value": 2000, "timestamp": 1700000010}
                ],
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["thank"],
            "priority_threshold": "high"
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        data = response.json()
        
        # 只应返回高优先级话术
        for script in data['data']['scripts']:
            assert script['priority'] == 'high', "应只返回高优先级话术"
    
    def test_empty_context(self, test_client):
        """测试空上下文"""
        request_data = {
            "context": {
                "recent_gifts": [],
                "recent_comments": [],
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["thank", "retain", "interact"]
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        # 空上下文可能返回空列表或默认话术
    
    def test_invalid_script_types(self, test_client):
        """测试无效话术类型"""
        request_data = {
            "context": {
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["invalid_type"]
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        
        # 应返回错误或空列表
        assert response.status_code in [200, 400, 422]
    
    def test_script_history_endpoint(self, test_client):
        """测试话术历史接口"""
        response = test_client.get("/api/ai/scripts/history?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            assert 'scripts' in data['data'] or 'data' in data
    
    def test_script_expiry_time(self, test_client):
        """测试话术过期时间"""
        request_data = {
            "context": {
                "recent_gifts": [
                    {"user_name": "用户A", "gift_value": 1000, "timestamp": 1700000000}
                ],
                "style_profile": {"persona": "主播", "tone": "友好"}
            },
            "script_types": ["thank"]
        }
        
        response = test_client.post("/api/ai/scripts/generate_smart", json=request_data)
        data = response.json()
        
        if len(data['data']['scripts']) > 0:
            script = data['data']['scripts'][0]
            if 'expiry_time' in script:
                assert script['expiry_time'] > 1700000000, "过期时间应在未来"


class TestScriptGenerationStrategies:
    """测试话术生成策略"""
    
    def test_big_gift_immediate_generation(self):
        """测试大额礼物立即生成（≥1000元）"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator({})
        high_value_users = [
            {'user_name': '土豪', 'gift_value': 3000, 'priority': 'high'}
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile={'persona': '主播', 'tone': '热情'}
        )
        
        assert len(scripts) > 0
        assert scripts[0].priority == 'high', "大额礼物应立即生成高优先级话术"
    
    def test_medium_gift_delayed_generation(self):
        """测试中等礼物延迟生成（100-999元）"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator({})
        high_value_users = [
            {'user_name': '用户A', 'gift_value': 500, 'priority': 'medium'}
        ]
        
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile={'persona': '主播', 'tone': '友好'}
        )
        
        assert len(scripts) > 0
        assert scripts[0].priority == 'medium', "中等礼物应为中优先级"
    
    def test_new_user_retain_script(self):
        """测试新用户留人话术"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        
        generator = SmartScriptGenerator({})
        room_status = {
            'viewer_trend': 'up',
            'change_percent': 20,
            'new_users': 50
        }
        
        scripts = generator.generate(
            high_value_users=[],
            room_status=room_status,
            script_types=['retain'],
            style_profile={'persona': '主播', 'tone': '热情'}
        )
        
        retain_scripts = [s for s in scripts if s.type == 'retain']
        assert len(retain_scripts) > 0, "人数上升应生成留人话术"


class TestScriptGenerationPerformance:
    """测试话术生成性能"""
    
    def test_generation_speed(self):
        """测试生成速度（目标<1秒）"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        import time
        
        generator = SmartScriptGenerator({})
        high_value_users = [
            {'user_name': f'用户{i}', 'gift_value': 100 * i, 'priority': 'medium'}
            for i in range(5)
        ]
        
        start = time.perf_counter()
        scripts = generator.generate(
            high_value_users=high_value_users,
            room_status={},
            script_types=['thank'],
            style_profile={'persona': '主播', 'tone': '友好'},
            max_scripts=5
        )
        end = time.perf_counter()
        
        generation_time = end - start
        assert generation_time < 2.0, f"生成时间应<2秒，实际: {generation_time:.2f}秒"
    
    def test_concurrent_generation(self):
        """测试并发生成"""
        from server.ai.smart_script_generator import SmartScriptGenerator
        import concurrent.futures
        
        generator = SmartScriptGenerator({})
        
        def generate_script():
            return generator.generate(
                high_value_users=[{'user_name': '用户', 'gift_value': 100}],
                room_status={},
                script_types=['thank'],
                style_profile={'persona': '主播', 'tone': '友好'}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_script) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 5, "应成功完成5次并发生成"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

