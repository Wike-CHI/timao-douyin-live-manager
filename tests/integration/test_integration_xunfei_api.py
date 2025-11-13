
import unittest
import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Explicitly load the .env file from the server directory
dotenv_path = os.path.join(project_root, 'server', '.env')
if os.path.exists(dotenv_path):
    print(f"--- Loading .env file from: {dotenv_path} ---")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"--- Warning: .env file not found at {dotenv_path} ---")

from server.ai.ai_gateway import get_gateway

class TestIntegrationXunfeiAPI(unittest.TestCase):

    @unittest.skipIf(not os.getenv("XUNFEI_API_KEY"), "XUNFEI_API_KEY not set, skipping integration test.")
    def test_real_live_analysis_call(self):
        """
        Tests a real API call to the live_analysis function via the AIGateway.
        This requires a valid XUNFEI_API_KEY and network access.
        """
        print("\\n" + "="*70)
        print("--- Running REAL integration test for live_analysis (Xunfei API) ---")
        print("="*70)
        
        gateway = get_gateway()
        
        # 1. Verify that the xunfei provider is registered and enabled
        providers = gateway.list_providers()
        self.assertIn("xunfei", providers, "Xunfei provider is not registered in the gateway.")
        self.assertTrue(providers["xunfei"]["enabled"], "Xunfei provider is not enabled.")
        
        print("✅ Xunfei provider is registered and enabled.")
        
        # 2. Prepare a simple context for the call
        messages = [
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请说 '测试成功'"}
        ]
        
        print("🚀 Calling gateway.chat_completion with function='live_analysis'...")
        
        try:
            # 3. Make the actual API call
            response = gateway.chat_completion(
                messages=messages,
                function="live_analysis",  # This should trigger the xunfei model
            )
            
            # 4. Assert the response
            self.assertIsNotNone(response, "Gateway returned a None response.")
            
            print(f"✔️ API call finished. Success: {response.success}")
            
            if response.success:
                print(f"🤖 Model: {response.model}")
                print(f"💬 Response Content: {response.content}")
                # Try to parse content if it's a JSON string
                try:
                    parsed_content = json.loads(response.content)
                    print("📦 Parsed JSON response:")
                    print(json.dumps(parsed_content, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print("(Response is not a JSON string, showing as raw text)")
            else:
                print(f"❌ Error: {response.error}")

            self.assertTrue(response.success, f"The API call failed with error: {response.error}")
            self.assertIn("测试成功", response.content, "Response content does not contain expected text '测试成功'")

        except Exception as e:
            self.fail(f"An unexpected exception occurred during the API call: {e}")

if __name__ == '__main__':
    unittest.main()
