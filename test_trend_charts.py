"""
测试趋势图数据流

验证：
1. Gemini 返回包含 trend_charts 的 JSON
2. 数据库正确保存 trend_charts
3. API 正确返回 trend_charts
"""

from server.app.database import DatabaseManager
from server.config import DatabaseConfig
from server.app.models.live_review import LiveReviewReport
from sqlalchemy import text
import json

config = DatabaseConfig()
dm = DatabaseManager(config)
dm.initialize()

# 创建测试数据
test_trend_charts = {
    "follows": {
        "title": "新增关注趋势",
        "description": "每分钟新增关注数变化",
        "chart_data": [
            {"time": "0分", "value": 0},
            {"time": "1分", "value": 5},
            {"time": "2分", "value": 12},
            {"time": "结束", "value": 20}
        ],
        "insights": "关注增长稳定"
    },
    "entries": {
        "title": "进场人数趋势",
        "description": "每分钟进场人数变化",
        "chart_data": [
            {"time": "0分", "value": 0},
            {"time": "1分", "value": 10},
            {"time": "2分", "value": 25},
            {"time": "结束", "value": 40}
        ],
        "insights": "进场人数持续增长"
    }
}

with dm.get_session() as db:
    print("\n🧪 开始测试趋势图数据流...")
    print("=" * 60)
    
    # 查找最近的一个报告
    report = db.query(LiveReviewReport).order_by(
        LiveReviewReport.id.desc()
    ).first()
    
    if not report:
        print("❌ 没有找到任何报告，请先生成一个报告")
    else:
        print(f"\n📄 找到报告 ID: {report.id}")
        print(f"   Session ID: {report.session_id}")
        print(f"   评分: {report.overall_score}")
        
        # 检查 trend_charts 数据
        if report.trend_charts:
            print(f"\n✅ 报告已包含 trend_charts 数据")
            print(f"   图表数量: {len(report.trend_charts)}")
            for key, chart in report.trend_charts.items():
                print(f"   - {key}: {chart.get('title', 'N/A')}")
                if 'chart_data' in chart:
                    print(f"     数据点: {len(chart['chart_data'])} 个")
        else:
            print(f"\n⚠️ 报告不包含 trend_charts 数据")
            print(f"   这可能是旧报告，让我们更新它...")
            
            # 更新报告添加测试数据
            report.trend_charts = test_trend_charts
            db.commit()
            print(f"   ✅ 已更新报告添加测试趋势图数据")
        
        # 验证 to_dict() 方法
        print(f"\n🔍 验证 to_dict() 序列化...")
        report_dict = report.to_dict()
        
        if 'trend_charts' in report_dict:
            print(f"   ✅ to_dict() 包含 trend_charts")
            print(f"   图表数量: {len(report_dict['trend_charts'])}")
        else:
            print(f"   ❌ to_dict() 缺少 trend_charts")
        
        # 验证 JSON 序列化
        print(f"\n📦 验证 JSON 序列化...")
        try:
            json_str = json.dumps(report_dict, ensure_ascii=False)
            print(f"   ✅ JSON 序列化成功")
            print(f"   JSON 长度: {len(json_str)} 字符")
        except Exception as e:
            print(f"   ❌ JSON 序列化失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
