"""
初始化订阅套餐数据
"""
import sys
import os
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from server.app.database import DatabaseManager
from server.app.models.subscription import SubscriptionPlan, SubscriptionPlanTypeEnum
from server.config import config_manager

def init_plans():
    """初始化默认套餐"""
    # 初始化数据库
    db_config = config_manager.config.database
    db_manager = DatabaseManager(db_config)
    db_manager.initialize()
    
    # 创建session
    session = db_manager.get_session_sync()
    
    try:
        # 检查是否已有套餐
        existing_count = session.query(SubscriptionPlan).count()
        if existing_count > 0:
            print(f"✅ 数据库中已有 {existing_count} 个套餐")
            plans = session.query(SubscriptionPlan).all()
            for p in plans:
                print(f"  - {p.name} ({p.plan_type.value}): ¥{p.price}/月")
            return
        
        print("🔄 开始初始化默认套餐...")
        
        # 创建默认套餐
        plans = [
            {
                "name": "免费体验版",
                "display_name": "免费体验版",
                "plan_type": SubscriptionPlanTypeEnum.FREE,
                "price": Decimal("0.00"),
                "billing_cycle": 7,
                "max_ai_requests": 10,
                "max_streams": 1,
                "max_storage_gb": 1,
                "max_export_count": 5,
                "features": '{"ai_analysis": true, "recording": true, "export": false, "support": "社区支持"}',
                "description": "体验基础功能，7天免费试用",
                "is_active": True
            },
            {
                "name": "基础版",
                "display_name": "基础版",
                "plan_type": SubscriptionPlanTypeEnum.BASIC,
                "price": Decimal("29.00"),
                "billing_cycle": 30,
                "max_ai_requests": 100,
                "max_streams": 3,
                "max_storage_gb": 10,
                "max_export_count": 50,
                "features": '{"ai_analysis": true, "recording": true, "export": true, "support": "邮件支持"}',
                "description": "适合个人主播，满足基本直播分析需求",
                "is_active": True
            },
            {
                "name": "专业版",
                "display_name": "专业版",
                "plan_type": SubscriptionPlanTypeEnum.PREMIUM,
                "price": Decimal("99.00"),
                "billing_cycle": 30,
                "max_ai_requests": 500,
                "max_streams": 10,
                "max_storage_gb": 50,
                "max_export_count": 200,
                "features": '{"ai_analysis": true, "recording": true, "export": true, "advanced_analytics": true, "support": "优先支持"}',
                "description": "适合专业主播，提供高级分析功能",
                "is_active": True,
                "is_popular": True
            },
            {
                "name": "企业版",
                "display_name": "企业版",
                "plan_type": SubscriptionPlanTypeEnum.ENTERPRISE,
                "price": Decimal("299.00"),
                "billing_cycle": 30,
                "max_ai_requests": None,
                "max_streams": None,
                "max_storage_gb": None,
                "max_export_count": None,
                "features": '{"ai_analysis": true, "recording": true, "export": true, "advanced_analytics": true, "team_collaboration": true, "support": "专属客服"}',
                "description": "适合MCN机构和团队，无限制使用所有功能",
                "is_active": True
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            session.add(plan)
            print(f"✅ 创建套餐: {plan_data['name']}")
        
        session.commit()
        print(f"\n🎉 成功创建 {len(plans)} 个套餐！")
        
        # 显示创建的套餐
        print("\n📋 套餐列表:")
        created_plans = session.query(SubscriptionPlan).all()
        for p in created_plans:
            print(f"  ID: {p.id} | {p.name} ({p.plan_type.value}) | ¥{p.price}/月 | AI请求: {p.max_ai_requests}")
    
    except Exception as e:
        session.rollback()
        print(f"❌ 创建套餐失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    try:
        init_plans()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
