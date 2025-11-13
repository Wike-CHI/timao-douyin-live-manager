"""
初始化支付套餐数据 (plans表)
"""
import sys
import os
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from server.app.database import DatabaseManager
from server.app.models.payment import Plan, PlanType, PlanDuration
from server.config import config_manager

def init_payment_plans():
    """初始化默认套餐到plans表"""
    # 初始化数据库
    db_config = config_manager.config.database
    db_manager = DatabaseManager(db_config)
    db_manager.initialize()
    
    # 创建session
    session = db_manager.get_session_sync()
    
    try:
        # 检查是否已有套餐
        existing_count = session.query(Plan).count()
        if existing_count > 0:
            print(f"✅ plans表中已有 {existing_count} 个套餐")
            plans = session.query(Plan).all()
            for p in plans:
                print(f"  - {p.name} ({p.plan_type}): ¥{p.price}/{p.duration}")
            return
        
        print("🔄 开始初始化默认套餐到plans表...")
        
        # 创建默认套餐
        plans = [
            {
                "name": "免费体验版",
                "description": "体验基础功能，7天免费试用",
                "plan_type": PlanType.FREE.value,
                "duration": PlanDuration.MONTHLY.value,
                "price": Decimal("0.00"),
                "original_price": Decimal("0.00"),
                "currency": "CNY",
                "features": {
                    "ai_analysis": True,
                    "recording": True,
                    "export": False,
                    "support": "社区支持"
                },
                "limits": {
                    "max_ai_requests": 10,
                    "max_streams": 1,
                    "max_storage_gb": 1,
                    "max_export_count": 5
                },
                "is_active": True,
                "sort_order": 0
            },
            {
                "name": "基础版",
                "description": "适合个人主播，满足基本直播分析需求",
                "plan_type": PlanType.BASIC.value,
                "duration": PlanDuration.MONTHLY.value,
                "price": Decimal("29.00"),
                "original_price": Decimal("49.00"),
                "currency": "CNY",
                "features": {
                    "ai_analysis": True,
                    "recording": True,
                    "export": True,
                    "support": "邮件支持"
                },
                "limits": {
                    "max_ai_requests": 100,
                    "max_streams": 3,
                    "max_storage_gb": 10,
                    "max_export_count": 50
                },
                "is_active": True,
                "sort_order": 1
            },
            {
                "name": "专业版",
                "description": "适合专业主播，提供高级分析功能",
                "plan_type": PlanType.PREMIUM.value,
                "duration": PlanDuration.MONTHLY.value,
                "price": Decimal("99.00"),
                "original_price": Decimal("149.00"),
                "currency": "CNY",
                "features": {
                    "ai_analysis": True,
                    "recording": True,
                    "export": True,
                    "advanced_analytics": True,
                    "support": "优先支持"
                },
                "limits": {
                    "max_ai_requests": 500,
                    "max_streams": 10,
                    "max_storage_gb": 50,
                    "max_export_count": 200
                },
                "is_active": True,
                "sort_order": 2
            },
            {
                "name": "企业版",
                "description": "适合MCN机构和团队，无限制使用所有功能",
                "plan_type": PlanType.ENTERPRISE.value,
                "duration": PlanDuration.YEARLY.value,
                "price": Decimal("299.00"),
                "original_price": Decimal("499.00"),
                "currency": "CNY",
                "features": {
                    "ai_analysis": True,
                    "recording": True,
                    "export": True,
                    "advanced_analytics": True,
                    "team_collaboration": True,
                    "support": "专属客服"
                },
                "limits": {
                    "max_ai_requests": None,
                    "max_streams": None,
                    "max_storage_gb": None,
                    "max_export_count": None
                },
                "is_active": True,
                "sort_order": 3
            }
        ]
        
        for plan_data in plans:
            plan = Plan(**plan_data)
            session.add(plan)
            print(f"✅ 创建套餐: {plan_data['name']}")
        
        session.commit()
        print(f"\n🎉 成功创建 {len(plans)} 个套餐到plans表！")
        
        # 显示创建的套餐
        print("\n📋 套餐列表:")
        created_plans = session.query(Plan).all()
        for p in created_plans:
            print(f"  ID: {p.id} | {p.name} ({p.plan_type}) | ¥{p.price}/{p.duration}")
    
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
        init_payment_plans()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
