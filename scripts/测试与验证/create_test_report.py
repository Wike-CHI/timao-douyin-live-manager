"""
创建一个测试复盘报告（包含 trend_charts）

用于测试前端显示功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from server.app.database import DatabaseManager
from server.config import DatabaseConfig
from server.app.models.live_review import LiveReviewReport
from server.app.models.live import LiveSession
from datetime import datetime
import json

def create_test_report():
    """创建测试报告"""
    config = DatabaseConfig()
    dm = DatabaseManager(config)
    dm.initialize()
    
    with dm.get_session() as db:
        # 0. 获取或创建一个用户
        from server.app.models.user import User
        user = db.query(User).first()
        if not user:
            print("❌ 数据库中没有用户，请先创建用户")
            print("提示：运行 python create_admin_user.py")
            return
        
        print(f"✅ 使用用户: {user.username} (ID: {user.id})")
        
        # 1. 创建或获取一个测试会话
        session = db.query(LiveSession).filter(
            LiveSession.room_id == "test_room_001"
        ).first()
        
        if not session:
            session = LiveSession(
                user_id=user.id,
                room_id="test_room_001",
                platform="douyin",
                title="测试直播间",
                status="ended",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=900,  # 15分钟
                total_viewers=1500,
                peak_viewers=520,
                comment_count=350,
                like_count=5180,
                new_followers=195,
                gift_value=1888.88
            )
            db.add(session)
            db.flush()
            print(f"✅ 创建测试会话: session_id={session.id}")
        else:
            # 更新会话数据
            session.user_id = user.id
            session.duration = 900
            session.total_viewers = 1500
            session.peak_viewers = 520
            session.comment_count = 350
            session.like_count = 5180
            session.new_followers = 195
            session.status = "ended"
            db.flush()
            print(f"✅ 使用现有会话: session_id={session.id}")
        
        # 2. 创建包含 trend_charts 的测试报告
        trend_charts = {
            "follows": {
                "title": "新增关注趋势",
                "description": "直播期间新增关注数的变化趋势（每分钟采样）",
                "chart_data": [
                    {"time": "0分", "value": 0},
                    {"time": "1分", "value": 5},
                    {"time": "2分", "value": 12},
                    {"time": "3分", "value": 18},
                    {"time": "4分", "value": 25},
                    {"time": "5分", "value": 38},
                    {"time": "6分", "value": 52},
                    {"time": "7分", "value": 68},
                    {"time": "8分", "value": 85},
                    {"time": "9分", "value": 102},
                    {"time": "10分", "value": 118},
                    {"time": "11分", "value": 135},
                    {"time": "12分", "value": 150},
                    {"time": "13分", "value": 168},
                    {"time": "14分", "value": 180},
                    {"time": "结束", "value": 195}
                ],
                "insights": "第5-8分钟增长最快，说明开场话术和内容吸引力较好。后期增速放缓，建议优化中后段留人策略。"
            },
            "entries": {
                "title": "进场人数趋势",
                "description": "累计进场观众数量变化（每分钟采样）",
                "chart_data": [
                    {"time": "0分", "value": 0},
                    {"time": "1分", "value": 45},
                    {"time": "2分", "value": 120},
                    {"time": "3分", "value": 235},
                    {"time": "4分", "value": 380},
                    {"time": "5分", "value": 520},
                    {"time": "6分", "value": 680},
                    {"time": "7分", "value": 820},
                    {"time": "8分", "value": 950},
                    {"time": "9分", "value": 1080},
                    {"time": "10分", "value": 1200},
                    {"time": "11分", "value": 1310},
                    {"time": "12分", "value": 1400},
                    {"time": "13分", "value": 1455},
                    {"time": "14分", "value": 1485},
                    {"time": "结束", "value": 1500}
                ],
                "insights": "前8分钟进场速度快，说明推流效果好。后期进场放缓属正常现象，但可通过互动活动提升。"
            },
            "peak_viewers": {
                "title": "在线人数趋势",
                "description": "实时在线人数的波动情况（每分钟采样）",
                "chart_data": [
                    {"time": "0分", "value": 0},
                    {"time": "1分", "value": 42},
                    {"time": "2分", "value": 95},
                    {"time": "3分", "value": 168},
                    {"time": "4分", "value": 245},
                    {"time": "5分", "value": 320},
                    {"time": "6分", "value": 398},
                    {"time": "7分", "value": 465},
                    {"time": "8分", "value": 520},
                    {"time": "9分", "value": 495},
                    {"time": "10分", "value": 460},
                    {"time": "11分", "value": 425},
                    {"time": "12分", "value": 390},
                    {"time": "13分", "value": 355},
                    {"time": "14分", "value": 320},
                    {"time": "结束", "value": 285}
                ],
                "insights": "第8分钟达到峰值520人，之后持续流失。建议在中后期增加互动环节、抽奖活动或福利发放，提升留存率。"
            },
            "like_total": {
                "title": "点赞数趋势",
                "description": "直播间点赞数累计变化（每分钟采样）",
                "chart_data": [
                    {"time": "0分", "value": 0},
                    {"time": "1分", "value": 120},
                    {"time": "2分", "value": 280},
                    {"time": "3分", "value": 520},
                    {"time": "4分", "value": 850},
                    {"time": "5分", "value": 1250},
                    {"time": "6分", "value": 1680},
                    {"time": "7分", "value": 2150},
                    {"time": "8分", "value": 2680},
                    {"time": "9分", "value": 3200},
                    {"time": "10分", "value": 3650},
                    {"time": "11分", "value": 4050},
                    {"time": "12分", "value": 4400},
                    {"time": "13分", "value": 4700},
                    {"time": "14分", "value": 4950},
                    {"time": "结束", "value": 5180}
                ],
                "insights": "点赞增长稳定，互动氛围良好。前8分钟增速最快，与在线人数峰值吻合。建议在点赞高峰期及时引导转化。"
            }
        }
        
        performance_analysis = {
            "overall_assessment": "本场直播整体表现良好，开场吸引力强，互动氛围活跃。主要问题是中后期留存率下降明显，需优化内容节奏和互动策略。",
            "content_quality": {
                "score": 82,
                "comments": "话术自然流畅，产品讲解清晰，但中后段内容重复度较高。"
            },
            "engagement": {
                "score": 78,
                "comments": "前期互动积极，点赞和弹幕活跃度高，但后期互动明显减弱。"
            },
            "conversion_potential": {
                "score": 75,
                "comments": "新增关注195人，转化率中等。建议在高峰期加强转化引导。"
            }
        }
        
        key_highlights = [
            "开播后快速吸引流量，3分钟内在线人数破百",
            "第8分钟达到在线人数峰值520人，流量表现优秀",
            "点赞互动积极，累计获得5180个赞",
            "新增关注195人，转化效果中上",
            "直播间氛围热烈，弹幕活跃"
        ]
        
        key_issues = [
            "中后期留存率持续下降，从峰值520人降至结束时285人",
            "第10分钟后内容重复，观众新鲜感下降",
            "缺少中后期的互动环节和福利刺激",
            "转化引导时机把握不够精准",
            "部分话术过于生硬，需要更自然的表达"
        ]
        
        improvement_suggestions = [
            {
                "priority": "high",
                "category": "留存优化",
                "action": "在第8-10分钟增加抽奖环节或限时福利",
                "expected_impact": "预计可提升15-20%的中后期留存率"
            },
            {
                "priority": "high",
                "category": "内容策划",
                "action": "优化直播脚本，每3-5分钟设置一个话题高潮点",
                "expected_impact": "保持观众注意力，减少流失"
            },
            {
                "priority": "medium",
                "category": "互动技巧",
                "action": "定时发起弹幕互动话题，引导观众参与",
                "expected_impact": "提升互动氛围，增强粘性"
            },
            {
                "priority": "medium",
                "category": "转化策略",
                "action": "在在线人数高峰期（第7-9分钟）强化关注引导",
                "expected_impact": "关注转化率可提升20-30%"
            }
        ]
        
        # 检查是否已存在报告
        existing_report = db.query(LiveReviewReport).filter(
            LiveReviewReport.session_id == session.id
        ).first()
        
        if existing_report:
            # 更新现有报告
            existing_report.overall_score = 85
            existing_report.performance_analysis = performance_analysis
            existing_report.key_highlights = key_highlights
            existing_report.key_issues = key_issues
            existing_report.improvement_suggestions = improvement_suggestions
            existing_report.trend_charts = trend_charts
            existing_report.status = "completed"
            print(f"✅ 更新现有报告: report_id={existing_report.id}")
        else:
            # 创建新报告
            report = LiveReviewReport(
                session_id=session.id,
                overall_score=85,
                performance_analysis=performance_analysis,
                key_highlights=key_highlights,
                key_issues=key_issues,
                improvement_suggestions=improvement_suggestions,
                trend_charts=trend_charts,
                full_report_text="# 测试报告\n\n这是一个包含趋势图的测试报告。",
                status="completed",
                ai_model="test-model",
                generation_cost=0.0001,
                generation_tokens=1500,
                generation_duration=2.5
            )
            db.add(report)
            db.flush()
            print(f"✅ 创建新报告: report_id={report.id}")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ 测试报告创建成功！")
        print("="*60)
        print(f"📊 会话ID: {session.id}")
        print(f"🏠 房间号: {session.room_id}")
        print(f"👤 用户: {user.username}")
        print(f"⏱️  时长: {session.duration}秒")
        print(f"👥 总观看: {session.total_viewers}人")
        print(f"🔥 峰值: {session.peak_viewers}人")
        print(f"💬 弹幕数: {session.comment_count}条")
        print(f"❤️  点赞数: {session.like_count}个")
        print(f"➕ 新增关注: {session.new_followers}人")
        print(f"📈 趋势图: {len(trend_charts)}个")
        print("\n现在可以在前端查看这个报告了！")
        print("="*60)


if __name__ == "__main__":
    create_test_report()
