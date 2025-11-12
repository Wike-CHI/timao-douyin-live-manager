"""
检查数据库中的所有直播会话和复盘报告
"""

from server.app.database import DatabaseManager
from server.config import DatabaseConfig
from server.app.models.live import LiveSession
from server.app.models.live_review import LiveReviewReport

config = DatabaseConfig()
dm = DatabaseManager(config)
dm.initialize()

with dm.get_session() as db:
    print("\n" + "="*80)
    print("📊 直播会话列表")
    print("="*80)
    
    sessions = db.query(LiveSession).all()
    if not sessions:
        print("❌ 数据库中没有直播会话记录")
    else:
        for s in sessions:
            print(f"\n会话 ID: {s.id}")
            print(f"  房间号: {s.room_id}")
            print(f"  标题: {s.title or 'N/A'}")
            print(f"  状态: {s.status}")
            print(f"  平台: {s.platform}")
            print(f"  开始时间: {s.start_time}")
            print(f"  结束时间: {s.end_time}")
            print(f"  时长: {s.duration}秒 ({s.duration//60}分钟)" if s.duration else "  时长: 未记录")
            print(f"  总观看: {s.total_viewers}人")
            print(f"  峰值: {s.peak_viewers}人")
            print(f"  弹幕数: {s.comment_count}条")
            print(f"  点赞数: {s.like_count}个")
            print(f"  新增关注: {s.new_followers}人")
            print(f"  转写启用: {s.transcribe_enabled}")
            print(f"  转写时长: {s.transcribe_duration}秒" if s.transcribe_duration else "  转写时长: 未记录")
            print(f"  数据文件:")
            print(f"    - 弹幕文件: {s.comment_file or 'N/A'}")
            print(f"    - 转写文件: {s.transcript_file or 'N/A'}")
            print(f"    - 报告文件: {s.report_file or 'N/A'}")
            print(f"    - 录制文件: {s.recording_file or 'N/A'}")
    
    print("\n" + "="*80)
    print("📝 复盘报告列表")
    print("="*80)
    
    reports = db.query(LiveReviewReport).all()
    if not reports:
        print("❌ 数据库中没有复盘报告")
    else:
        for r in reports:
            print(f"\n报告 ID: {r.id}")
            print(f"  会话 ID: {r.session_id}")
            print(f"  状态: {r.status}")
            print(f"  评分: {r.overall_score}/100" if r.overall_score else "  评分: 未评分")
            print(f"  生成时间: {r.generated_at}")
            print(f"  AI模型: {r.ai_model}")
            print(f"  生成成本: ${r.generation_cost}" if r.generation_cost else "  生成成本: N/A")
            print(f"  Token数: {r.generation_tokens}")
            print(f"  亮点数: {len(r.key_highlights or [])}")
            print(f"  问题数: {len(r.key_issues or [])}")
            print(f"  建议数: {len(r.improvement_suggestions or [])}")
            print(f"  趋势图: {len(r.trend_charts or {})}个" if r.trend_charts else "  趋势图: 无")
            if r.error_message:
                print(f"  ❌ 错误: {r.error_message}")
    
    print("\n" + "="*80)
    print(f"总计: {len(sessions)} 个会话, {len(reports)} 个报告")
    print("="*80 + "\n")
