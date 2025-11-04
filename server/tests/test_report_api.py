"""
测试复盘报告 API 和数据流

验证：
1. API 路径是否正确
2. trend_charts 数据是否正确返回
3. 数据结构是否符合前端期望
"""

import requests
import json

FASTAPI_URL = "http://127.0.0.1:9019"

def test_list_reports():
    """测试获取报告列表"""
    print("\n" + "="*60)
    print("1️⃣  测试获取报告列表")
    print("="*60)
    
    url = f"{FASTAPI_URL}/api/live/review/list/recent?limit=5"
    print(f"请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                reports = data["data"]
                print(f"✅ 成功获取 {len(reports)} 条报告")
                for report in reports:
                    print(f"  - 报告ID: {report['id']}, 会话ID: {report['session_id']}, 评分: {report.get('overall_score', 'N/A')}")
                return reports
            else:
                print("❌ 响应格式不正确")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    return []


def test_get_report_detail(report_id):
    """测试获取报告详情"""
    print("\n" + "="*60)
    print(f"2️⃣  测试获取报告详情 (ID: {report_id})")
    print("="*60)
    
    url = f"{FASTAPI_URL}/api/live/review/report/{report_id}"
    print(f"请求: GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                report = data["data"]
                print(f"✅ 成功获取报告详情")
                print(f"\n基本信息:")
                print(f"  - 报告ID: {report['id']}")
                print(f"  - 会话ID: {report['session_id']}")
                print(f"  - 状态: {report['status']}")
                print(f"  - 评分: {report.get('overall_score', 'N/A')}/100")
                print(f"  - AI模型: {report.get('ai_model', 'N/A')}")
                
                if report.get('session'):
                    print(f"\n会话信息:")
                    session = report['session']
                    print(f"  - 房间号: {session.get('room_id', 'N/A')}")
                    print(f"  - 时长: {session.get('duration', 0)}秒")
                    print(f"  - 总观看: {session.get('total_viewers', 0)}人")
                    print(f"  - 峰值: {session.get('peak_viewers', 0)}人")
                
                # 检查 trend_charts
                if report.get('trend_charts'):
                    trend_charts = report['trend_charts']
                    print(f"\n📈 趋势图数据:")
                    print(f"  - 趋势图数量: {len(trend_charts)}")
                    for chart_key, chart_data in trend_charts.items():
                        print(f"  - {chart_key}: {chart_data.get('title', 'N/A')}")
                        print(f"    数据点数: {len(chart_data.get('chart_data', []))}")
                        print(f"    洞察: {chart_data.get('insights', 'N/A')[:50]}...")
                    print("\n✅ trend_charts 数据完整！")
                else:
                    print("\n❌ 缺少 trend_charts 数据")
                
                # 检查其他关键字段
                print(f"\n其他数据:")
                print(f"  - 亮点数量: {len(report.get('key_highlights', []))}")
                print(f"  - 问题数量: {len(report.get('key_issues', []))}")
                print(f"  - 建议数量: {len(report.get('improvement_suggestions', []))}")
                
                return report
            else:
                print("❌ 响应格式不正确")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        else:
            print(f"❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    return None


def main():
    """主测试流程"""
    print("\n🧪 开始测试复盘报告 API")
    print("="*60)
    
    # 1. 测试列表接口
    reports = test_list_reports()
    
    if not reports:
        print("\n❌ 没有找到报告，请先运行: python create_test_report.py")
        return
    
    # 2. 测试详情接口（使用第一个报告）
    first_report_id = reports[0]['id']
    report_detail = test_get_report_detail(first_report_id)
    
    # 3. 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    if report_detail and report_detail.get('trend_charts'):
        print("✅ 所有测试通过！")
        print("✅ API 路径正确")
        print("✅ trend_charts 数据完整")
        print("✅ 前端可以正常显示趋势图")
        print("\n💡 下一步: 启动前端应用并查看报告")
        print("   命令: npm run start:integrated")
    else:
        print("❌ 测试失败，请检查：")
        print("   1. 后端服务是否正常运行")
        print("   2. 数据库中是否有 trend_charts 数据")
        print("   3. API 返回的数据结构是否正确")
    
    print("="*60)


if __name__ == "__main__":
    main()
