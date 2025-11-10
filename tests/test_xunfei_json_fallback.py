import unittest
import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

dotenv_path = os.path.join(project_root, 'server', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

from server.ai.ai_gateway import get_gateway

class TestXunfeiJsonFallback(unittest.TestCase):
    @unittest.skipIf(not os.getenv("XUNFEI_API_KEY"), "XUNFEI_API_KEY not set")
    def test_xunfei_live_analysis_no_404_with_json_object(self):
        """Ensure that live_analysis call does not raise 404 when response_format is requested.
        Fallback logic should retry without response_format if provider is xunfei and initial call fails."""
        gateway = get_gateway()
        messages = [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "请输出一个简短JSON，字段analysis_overview='测试成功'"}
        ]
        # We call generate logic indirectly via chat_completion to exercise fallback
        response = gateway.chat_completion(
            messages=messages,
            function="live_analysis",  # triggers xunfei provider & model selection
            temperature=0.2,
            response_format={"type": "json_object"},  # intentionally request json_object
            max_tokens=100,
        )
        self.assertTrue(response.success, f"Xunfei fallback failed: {response.error}")
        self.assertIn("测试", response.content, "Response should contain test marker")

if __name__ == '__main__':
    unittest.main()
