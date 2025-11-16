# 云端数据库CRUD使用指南

**文件**: `server/cloud/db/crud.py`  
**数据库**: 阿里云RDS MySQL 8.0.36  
**主机**: rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com:3306  
**生成时间**: 2025-11-16

## 1. 功能概述

提供3个CRUD类,针对云端MySQL数据库:

### 1.1 UserCRUD - 用户管理
- **只读操作**: `get_by_id()`, `get_by_email()`, `get_by_username()`, `list_users()`
- **写操作**: `update_ai_quota()`, `reset_monthly_quota()`, `update_login_info()`, `soft_delete()`

### 1.2 SubscriptionCRUD - 订阅管理
- **只读操作**: `get_plan_by_id()`, `list_active_plans()`, `get_user_subscription()`
- **写操作**: `create_subscription()`, `cancel_subscription()`

### 1.3 PaymentCRUD - 支付管理
- **只读操作**: `get_user_payments()`
- **写操作**: `create_payment()`, `update_payment_status()`

## 2. 使用示例

### 2.1 查询用户(只读)

```python
from server.cloud.db.crud import UserCRUD

user_crud = UserCRUD()

# 根据用户名查询
user = user_crud.get_by_username("dev_admin")
print(f"用户: {user['username']}, AI配额: {user['ai_quota_used']}/{user['ai_quota_monthly']}")

# 列出所有用户
users = user_crud.list_users(limit=10, role="USER", status="ACTIVE")
for u in users:
    print(f"- {u['username']} ({u['email']})")
```

### 2.2 查询套餐(只读)

```python
from server.cloud.db.crud import SubscriptionCRUD

sub_crud = SubscriptionCRUD()

# 列出所有激活的套餐
plans = sub_crud.list_active_plans()
for plan in plans:
    print(f"{plan['display_name']}: {plan['price']}元/{plan['billing_cycle']}天")

# 查询用户当前订阅
subscription = sub_crud.get_user_subscription(user_id=1)
if subscription:
    print(f"订阅状态: {subscription['status']}, 到期: {subscription['expires_at']}")
```

### 2.3 更新AI配额(写操作,需确认)

```python
user_crud = UserCRUD()

# ⚠️ 写操作,确保理解影响!
success = user_crud.update_ai_quota(user_id=2, used=10)
if success:
    print("AI配额更新成功")
else:
    print("配额不足或用户不存在")
```

### 2.4 创建订阅(写操作,需确认)

```python
sub_crud = SubscriptionCRUD()

# ⚠️ 写操作,确保理解影响!
subscription = sub_crud.create_subscription(
    user_id=1,
    plan_id=2,  # 基础版
    auto_renew=True,
    trial=False
)
if subscription:
    print(f"订阅创建成功: {subscription['id']}")
```

## 3. 安全机制

### 3.1 自动事务管理
- ✅ 成功时自动commit
- ⚠️ 异常时自动rollback
- 📝 详细日志记录

### 3.2 连接池配置
- `pool_size=5`: 最大5个连接
- `pool_pre_ping=True`: 连接前检查有效性
- `pool_recycle=3600`: 1小时回收连接(防止RDS超时)

### 3.3 返回类型
- 所有方法返回**字典**(不是ORM对象)
- 避免Session关闭后无法访问属性

### 3.4 日志脱敏
- 密码自动脱敏: `*****************`
- 详细操作日志: 用户/套餐/支付查询

## 4. 测试结果

### 4.1 测试命令
```bash
python server\cloud\db\crud.py
```

### 4.2 测试输出
```
✅ 云端数据库连接: rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com:3306/timao

[1] 测试用户CRUD(只读操作)
  ✅ 查询用户: id=2, username=dev_admin, role=UserRoleEnum.SUPER_ADMIN
  ✅ 用户列表: total=4
    - jay (748974300@qq.com), AI配额: 0/1000
    - dev_admin (dev_admin@timao.local), AI配额: 0/1000
    - tc1102Admin (tc1102admin@timao.com), AI配额: 0/1000

[2] 测试订阅CRUD(只读操作)
  ✅ 套餐列表: total=4
    - 免费体验版: 0.0元/7天
    - 基础版: 29.0元/30天
    - 专业版: 99.0元/30天
    - 企业版: 299.0元/30天

[3] 测试支付CRUD(只读操作)
  ✅ 支付记录: user_id=2, total=0

✅ 只读测试完成! 云端数据库连接正常
```

## 5. 注意事项

### 5.1 数据库位置
- ⚠️ **所有操作针对云端阿里云RDS,不是本地数据库!**
- 配置来源: `server/.env` (MYSQL_HOST/MYSQL_USER等)
- 自动检查: 如果配置中有localhost会发出警告

### 5.2 写操作原则
- ✅ 所有写操作(create/update/delete)都需要明确调用
- ✅ 建议在执行前review代码逻辑
- ✅ 重要操作建议先在测试环境验证

### 5.3 错误处理
- 数据库连接失败: 抛出异常,检查RDS配置
- 用户不存在: 返回None
- 配额不足: 返回False
- 重复订阅: 返回None并记录warning日志

## 6. 下一步

1. **单元测试**(可选): 创建`tests/test_db_crud.py`
2. **集成到API**: 在FastAPI路由中调用CRUD方法
3. **监控告警**: 添加数据库操作监控(慢查询/连接池)
4. **备份方案**: 实现数据库备份/恢复脚本

---

**完成时间**: 2025-11-16 17:58  
**测试状态**: ✅ 只读操作通过,写操作待业务需求时调用
