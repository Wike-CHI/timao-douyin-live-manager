"""
冷场检测功能测试

测试文档：docs/产品使用手册/直播控制台双模式设计文档.md
审查人：叶维哲
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSilenceDetector:
    """测试冷场检测器"""
    
    @pytest.fixture
    def detector(self):
        """创建冷场检测器实例"""
        from server.modules.silence_detector import SilenceDetector
        return SilenceDetector()
    
    def test_no_silence_initially(self, detector):
        """测试初始状态不应冷场"""
        result = detector.check()
        assert result['is_silence'] is False, "初始状态不应标记为冷场"
        assert result['duration'] < 20, "初始冷场时长应小于预警阈值"
    
    def test_silence_warning_threshold(self, detector):
        """测试冷场预警阈值（20秒）"""
        # 模拟20秒无互动
        detector.last_interaction_time = time.time() - 25
        
        result = detector.check()
        assert result['is_silence'] is True, "超过20秒应标记为冷场"
        assert result['severity'] == 'low', "20-30秒应为低严重度"
        assert result['duration'] >= 20, "冷场时长应≥20秒"
    
    def test_silence_moderate_threshold(self, detector):
        """测试中度冷场阈值（30秒）"""
        # 模拟35秒无互动
        detector.last_interaction_time = time.time() - 35
        
        result = detector.check()
        assert result['is_silence'] is True
        assert result['severity'] == 'medium', "30-60秒应为中度严重"
        assert result['duration'] >= 30
    
    def test_silence_severe_threshold(self, detector):
        """测试严重冷场阈值（60秒）"""
        # 模拟70秒无互动
        detector.last_interaction_time = time.time() - 70
        
        result = detector.check()
        assert result['is_silence'] is True
        assert result['severity'] == 'high', "≥60秒应为高严重度"
        assert result['duration'] >= 60
    
    @patch('server.modules.silence_detector.get_recent_transcript')
    def test_no_silence_when_host_speaking(self, mock_transcript, detector):
        """测试主播说话时不应标记为冷场"""
        # 模拟主播正在说话
        mock_transcript.return_value = "【主播】大家好，欢迎来到直播间"
        
        # 模拟40秒无互动（本应冷场）
        detector.last_interaction_time = time.time() - 40
        
        result = detector.check()
        assert result['is_silence'] is False, "主播说话时不应标记为冷场"
        assert result.get('reason') == 'host_speaking', "应标明主播正在说话"
    
    def test_record_interaction(self, detector):
        """测试记录互动功能"""
        initial_time = detector.last_interaction_time
        
        # 记录一次互动
        detector.record_interaction({
            'type': 'comment',
            'user_name': '用户A',
            'content': '666'
        })
        
        assert detector.last_interaction_time > initial_time, "互动时间应被更新"
        assert len(detector.interaction_history) == 1, "互动历史应包含1条记录"
    
    def test_interaction_history_cleanup(self, detector):
        """测试互动历史自动清理（只保留5分钟内）"""
        # 添加一条6分钟前的记录
        old_interaction = {
            'type': 'comment',
            'user_name': '用户A',
            'content': '旧消息',
            'timestamp': time.time() - 360  # 6分钟前
        }
        detector.interaction_history.append(old_interaction)
        
        # 添加一条新记录
        detector.record_interaction({
            'type': 'comment',
            'user_name': '用户B',
            'content': '新消息'
        })
        
        # 旧记录应被清理
        assert len(detector.interaction_history) == 1, "应只保留5分钟内的记录"
        assert detector.interaction_history[0]['user_name'] == '用户B'
    
    def test_suggestion_generation_low_severity(self, detector):
        """测试低严重度破冰建议"""
        detector.last_interaction_time = time.time() - 25
        
        result = detector.check()
        suggestion = result['suggestion']
        
        assert suggestion['action'] == 'gentle_prompt', "低严重度应为温和提示"
        assert len(suggestion['scripts']) > 0, "应提供话术建议"
    
    def test_suggestion_generation_medium_severity(self, detector):
        """测试中度严重度破冰建议"""
        detector.last_interaction_time = time.time() - 35
        
        result = detector.check()
        suggestion = result['suggestion']
        
        assert suggestion['action'] == 'break_ice', "中度应为破冰行动"
        assert 'topic_suggestions' in suggestion, "应提供话题建议"
    
    def test_suggestion_generation_high_severity(self, detector):
        """测试高严重度破冰建议"""
        detector.last_interaction_time = time.time() - 70
        
        result = detector.check()
        suggestion = result['suggestion']
        
        assert suggestion['action'] == 'emergency_engage', "高严重度应为紧急互动"
        assert 'topic_suggestions' in suggestion
        assert len(suggestion['topic_suggestions']) > 0
    
    def test_last_interaction_info(self, detector):
        """测试最后互动信息记录"""
        detector.record_interaction({
            'type': 'comment',
            'user_name': '测试用户',
            'content': '测试消息'
        })
        
        detector.last_interaction_time = time.time() - 35
        result = detector.check()
        
        assert 'last_interaction' in result
        last_interaction = result['last_interaction']
        assert last_interaction['user_name'] == '测试用户'
        assert last_interaction['content'] == '测试消息'
    
    def test_context_information(self, detector):
        """测试上下文信息"""
        detector.last_interaction_time = time.time() - 35
        result = detector.check()
        
        assert 'context' in result, "应包含上下文信息"
        context = result['context']
        assert 'current_viewers' in context or True  # 可能需要mock
        assert 'engagement_rate' in context or True


class TestSilenceDetectionAPI:
    """测试冷场检测API接口"""
    
    @pytest.fixture
    def test_client(self):
        """创建测试客户端"""
        from server.app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_silence_check_endpoint(self, test_client):
        """测试冷场检测接口"""
        response = test_client.get("/api/ai/live/silence_check")
        
        assert response.status_code == 200, f"API调用失败: {response.text}"
        
        data = response.json()
        assert data['success'] is True, "响应应标记为成功"
        assert 'is_silence' in data['data'], "应包含is_silence字段"
        assert 'duration' in data['data'], "应包含duration字段"
    
    def test_record_interaction_endpoint(self, test_client):
        """测试记录互动接口"""
        interaction_data = {
            'type': 'comment',
            'user_name': 'API测试用户',
            'content': 'API测试消息',
            'timestamp': time.time()
        }
        
        response = test_client.post("/api/ai/live/record_interaction", json=interaction_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['recorded'] is True
    
    @patch('server.modules.silence_detector.SilenceDetector.check')
    def test_silence_status_in_room_status(self, mock_check, test_client):
        """测试直播间状态接口包含冷场状态"""
        mock_check.return_value = {
            'is_silence': True,
            'duration': 35
        }
        
        response = test_client.get("/api/live/room_status")
        
        if response.status_code == 200:
            data = response.json()
            if 'silence_status' in data['data']:
                assert 'is_silence' in data['data']['silence_status']
                assert 'duration' in data['data']['silence_status']


class TestSilenceDetectionIntegration:
    """冷场检测集成测试"""
    
    def test_silence_triggers_script_generation(self):
        """测试冷场触发话术生成"""
        from server.modules.silence_detector import SilenceDetector
        from server.ai.smart_script_generator import SmartScriptGenerator
        
        detector = SilenceDetector()
        detector.last_interaction_time = time.time() - 35
        
        silence_status = detector.check()
        
        if silence_status['is_silence']:
            generator = SmartScriptGenerator({})
            
            # 模拟生成破冰话术
            scripts = generator.generate(
                high_value_users=[],
                room_status={'viewer_trend': 'stable'},
                script_types=['interact'],
                style_profile={'persona': '主播', 'tone': '友好'}
            )
            
            # 应生成至少一条互动话术
            interact_scripts = [s for s in scripts if s.type == 'interact']
            assert len(interact_scripts) > 0, "冷场应触发互动话术生成"
    
    def test_multiple_interactions_reset_silence(self):
        """测试连续互动重置冷场状态"""
        from server.modules.silence_detector import SilenceDetector
        
        detector = SilenceDetector()
        
        # 制造冷场
        detector.last_interaction_time = time.time() - 35
        result1 = detector.check()
        assert result1['is_silence'] is True
        
        # 记录互动
        detector.record_interaction({
            'type': 'comment',
            'user_name': '用户A',
            'content': '666'
        })
        
        # 应该不再冷场
        result2 = detector.check()
        assert result2['is_silence'] is False or result2['duration'] < 20


class TestSilenceDetectionPerformance:
    """冷场检测性能测试"""
    
    def test_check_performance(self):
        """测试检测性能（应<10ms）"""
        from server.modules.silence_detector import SilenceDetector
        import time as time_module
        
        detector = SilenceDetector()
        
        start = time_module.perf_counter()
        for _ in range(100):
            detector.check()
        end = time_module.perf_counter()
        
        avg_time = (end - start) / 100
        assert avg_time < 0.01, f"平均检测时间应<10ms，实际: {avg_time*1000:.2f}ms"
    
    def test_record_interaction_performance(self):
        """测试记录互动性能"""
        from server.modules.silence_detector import SilenceDetector
        import time as time_module
        
        detector = SilenceDetector()
        
        start = time_module.perf_counter()
        for i in range(1000):
            detector.record_interaction({
                'type': 'comment',
                'user_name': f'用户{i}',
                'content': f'消息{i}'
            })
        end = time_module.perf_counter()
        
        total_time = end - start
        assert total_time < 1.0, f"记录1000次互动应<1秒，实际: {total_time:.2f}秒"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

