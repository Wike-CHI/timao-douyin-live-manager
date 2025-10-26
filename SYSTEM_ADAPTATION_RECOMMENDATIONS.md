# 用户系统适配提猫直播助手 - 改进建议

## 📋 当前评估

### ✅ 优势
1. **完整的认证体系**：JWT + Session，密码加密，登录保护
2. **适配的角色系统**：已有 STREAMER（主播）和 ASSISTANT（助理）角色
3. **订阅管理完善**：支付、发票、会员系统完整
4. **审计日志完善**：所有操作可追溯

### ⚠️ 不足
1. **缺少直播场景专属字段**
2. **缺少团队协作功能**
3. **缺少直播业务数据关联**
4. **邮件/短信服务未实现**

---

## 🚀 改进方案

### P0 - 必须改进（核心功能）

#### 1. 扩展 User 模型 - 添加直播字段

```python
# server/app/models/user.py

class User(BaseModel):
    # ... 现有字段 ...
    
    # 直播账号绑定
    douyin_user_id = Column(String(100), unique=True, nullable=True, comment="抖音用户ID")
    douyin_nickname = Column(String(100), nullable=True, comment="抖音昵称")
    douyin_avatar = Column(String(500), nullable=True, comment="抖音头像")
    douyin_room_id = Column(String(100), nullable=True, comment="抖音直播间ID")
    douyin_cookies = Column(Text, nullable=True, comment="抖音Cookies（加密存储）")
    
    # 主播认证
    streamer_verified = Column(Boolean, default=False, comment="主播认证")
    streamer_level = Column(Integer, default=0, comment="主播等级")
    streamer_followers = Column(Integer, default=0, comment="粉丝数")
    
    # 直播偏好
    live_settings = Column(JSON, nullable=True, comment="直播设置")
    # 示例: {
    #   "auto_transcribe": true,
    #   "ai_assistant_enabled": true,
    #   "ai_model": "qwen-plus",
    #   "hotword_track": true
    # }
```

#### 2. 创建 LiveSession 模型

```python
# server/app/models/live.py

class LiveSession(BaseModel):
    """直播会话模型"""
    
    __tablename__ = "live_sessions"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    room_id = Column(String(100), nullable=False, comment="直播间ID")
    
    # 直播信息
    title = Column(String(200), nullable=True, comment="直播标题")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    duration = Column(Integer, default=0, comment="时长（秒）")
    
    # 数据统计
    total_viewers = Column(Integer, default=0, comment="总观看人数")
    peak_viewers = Column(Integer, default=0, comment="峰值在线")
    comment_count = Column(Integer, default=0, comment="评论数")
    gift_count = Column(Integer, default=0, comment="礼物数")
    gift_value = Column(Numeric(10, 2), default=0, comment="礼物价值")
    
    # AI 使用统计
    ai_usage_count = Column(Integer, default=0, comment="AI调用次数")
    ai_usage_cost = Column(Numeric(10, 4), default=0, comment="AI成本")
    transcribe_duration = Column(Integer, default=0, comment="转写时长（秒）")
    
    # 数据文件
    comment_file = Column(String(500), nullable=True, comment="评论文件路径")
    transcript_file = Column(String(500), nullable=True, comment="转写文件路径")
    report_file = Column(String(500), nullable=True, comment="报告文件路径")
    
    # 关联
    user = relationship("User", back_populates="live_sessions")
```

#### 3. 创建 Team 模型（团队协作）

```python
# server/app/models/team.py

class Team(BaseModel):
    """团队/工作室模型"""
    
    __tablename__ = "teams"
    
    name = Column(String(100), nullable=False, comment="团队名称")
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=True, comment="团队描述")
    
    # 关联
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team")


class TeamMember(BaseModel):
    """团队成员"""
    
    __tablename__ = "team_members"
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum(TeamRoleEnum), nullable=False, comment="团队角色")
    
    # 关联
    team = relationship("Team", back_populates="members")
    user = relationship("User")


class TeamRoleEnum(enum.Enum):
    """团队角色"""
    OWNER = "owner"          # 所有者
    MANAGER = "manager"      # 管理员
    STREAMER = "streamer"    # 主播
    ASSISTANT = "assistant"  # 助理
    VIEWER = "viewer"        # 观察者（只读）
```

#### 4. 实现邮件/短信服务

```python
# server/utils/notification.py

class EmailService:
    """邮件服务"""
    
    @staticmethod
    def send_verification_email(user: User, token: str):
        """发送验证邮件"""
        # 使用 SMTP 或第三方服务（SendGrid, Mailgun等）
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        # TODO: 集成实际邮件服务
        pass
    
    @staticmethod
    def send_password_reset_email(user: User, token: str):
        """发送密码重置邮件"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # TODO: 集成实际邮件服务
        pass


class SMSService:
    """短信服务"""
    
    @staticmethod
    def send_verification_code(phone: str, code: str):
        """发送验证码"""
        # 集成阿里云、腾讯云等短信服务
        pass
```

---

### P1 - 应该改进（增强功能）

#### 5. 直播数据仪表板

```python
# server/app/services/live_analytics.py

class LiveAnalyticsService:
    """直播数据分析服务"""
    
    @staticmethod
    def get_streamer_stats(user_id: int, days: int = 7):
        """获取主播统计数据"""
        return {
            "total_sessions": 15,
            "total_duration": 45000,  # 秒
            "total_viewers": 12500,
            "avg_viewers": 833,
            "total_comments": 3500,
            "total_gifts": 850,
            "total_revenue": 1250.50,
            "ai_usage": {
                "total_calls": 450,
                "total_cost": 12.35
            },
            "top_fans": [...],
            "trending_keywords": [...]
        }
```

#### 6. AI 使用量管理

```python
# 在 User 模型中添加

class User(BaseModel):
    # ... 现有字段 ...
    
    # AI 配额管理
    ai_quota_monthly = Column(Integer, default=1000, comment="每月AI配额")
    ai_quota_used = Column(Integer, default=0, comment="已使用配额")
    ai_quota_reset_at = Column(DateTime, nullable=True, comment="配额重置时间")
    
    def check_ai_quota(self, required: int = 1) -> bool:
        """检查 AI 配额"""
        if self.ai_quota_monthly == -1:  # 无限配额
            return True
        return self.ai_quota_used + required <= self.ai_quota_monthly
```

---

### P2 - 可以改进（优化体验）

#### 7. 社交功能

```python
# server/app/models/social.py

class UserFollow(BaseModel):
    """用户关注"""
    
    follower_id = Column(Integer, ForeignKey('users.id'))  # 关注者
    following_id = Column(Integer, ForeignKey('users.id'))  # 被关注者
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBlock(BaseModel):
    """用户屏蔽"""
    
    user_id = Column(Integer, ForeignKey('users.id'))
    blocked_user_id = Column(Integer, ForeignKey('users.id'))
    reason = Column(Text, nullable=True)
```

#### 8. 设备管理

```python
# server/app/models/device.py

class UserDevice(BaseModel):
    """用户设备管理"""
    
    user_id = Column(Integer, ForeignKey('users.id'))
    device_id = Column(String(100), unique=True)
    device_name = Column(String(100))
    device_type = Column(String(50))  # desktop, mobile, tablet
    os = Column(String(50))
    browser = Column(String(50))
    last_used_at = Column(DateTime)
    is_trusted = Column(Boolean, default=False)
```

---

## 📝 实施建议

### 阶段一（1-2天）
1. ✅ 扩展 User 模型（添加直播字段）
2. ✅ 创建 LiveSession 模型
3. ✅ 更新 UserService 支持新字段

### 阶段二（2-3天）
1. 实现 Team/TeamMember 模型
2. 创建团队管理 API
3. 实现邮件服务集成

### 阶段三（3-5天）
1. 直播数据分析服务
2. AI 配额管理
3. 前端集成新功能

---

## 🎯 总结

**当前用户系统完成度：70%**

### 优势
- ✅ 认证体系完善
- ✅ 角色系统适配
- ✅ 订阅管理完整

### 待改进
- ⚠️ 缺少直播专属功能（优先级最高）
- ⚠️ 缺少团队协作（重要）
- ⚠️ 通知服务未实现（重要）

**建议**：先完成阶段一的改进，快速适配直播场景，再逐步完善其他功能。

---

## 📚 参考资料

- 用户模型：`server/app/models/user.py`
- 用户服务：`server/app/services/user_service.py`
- 认证API：`server/app/api/auth.py`
- 数据库配置：`.env`
