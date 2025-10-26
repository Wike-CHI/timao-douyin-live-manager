#!/usr/bin/env python3
"""测试话题生成功能"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_topic_generation():
    """测试话题生成功能"""
    try:
        print("开始导入模块...")
        from server.ai.knowledge_service import get_knowledge_base
        print("成功导入 knowledge_service")
        
        # 初始化知识库
        print("初始化知识库...")
        kb = get_knowledge_base()
        print("知识库初始化完成")
        
        # 测试传统话题生成（基于关键词）
        print("\n=== 测试传统话题生成 ===")
        traditional_topics = kb.topic_suggestions(
            limit=5,
            keywords=["美食", "旅行", "音乐"],
            use_ai=False
        )
        print(f"传统话题生成结果（{len(traditional_topics)}条）:")
        for i, topic in enumerate(traditional_topics, 1):
            print(f"  {i}. {topic['topic']} ({topic['category']})")
        
        # 测试AI驱动的话题生成
        print("\n=== 测试AI驱动话题生成 ===")
        context = {
            'transcript': '主播正在介绍今天的直播内容，聊到了最近的天气变化和季节性穿搭',
            'chat_messages': [
                {'content': '主播今天穿得好好看', 'user': 'user1'},
                {'content': '这个颜色很适合你', 'user': 'user2'},
                {'content': '能推荐一些秋季搭配吗', 'user': 'user3'}
            ],
            'persona': {
                'style': '时尚达人',
                'tone': '亲切友好',
                'expertise': ['穿搭', '美妆', '生活方式']
            },
            'vibe': {
                'energy': 'high',
                'mood': 'positive',
                'interaction_level': 'active'
            }
        }
        
        ai_topics = kb.topic_suggestions(
            limit=5,
            context=context,
            use_ai=True
        )
        print(f"AI话题生成结果（{len(ai_topics)}条）:")
        for i, topic in enumerate(ai_topics, 1):
            print(f"  {i}. {topic['topic']} ({topic['category']})")
        
        # 测试敏感话题过滤
        print("\n=== 测试敏感话题过滤 ===")
        sensitive_context = {
            'transcript': '有观众问到彩礼和房价的问题',
            'chat_messages': [
                {'content': '彩礼要多少钱啊', 'user': 'user1'},
                {'content': '你们那边房价怎么样', 'user': 'user2'}
            ],
            'persona': {'style': '生活分享'},
            'vibe': {'energy': 'medium', 'mood': 'neutral'}
        }
        
        filtered_topics = kb.topic_suggestions(
            limit=5,
            context=sensitive_context,
            use_ai=True
        )
        print(f"敏感话题过滤后结果（{len(filtered_topics)}条）:")
        for i, topic in enumerate(filtered_topics, 1):
            print(f"  {i}. {topic['topic']} ({topic['category']})")
            
        print("\n话题生成测试完成！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_topic_generation()