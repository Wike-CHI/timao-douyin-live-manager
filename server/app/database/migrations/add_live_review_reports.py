"""数据库迁移：添加直播复盘报告表

Revision ID: add_live_review_reports
Revises: 
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_live_review_reports'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库：创建 live_review_reports 表"""
    
    # 创建直播复盘报告表
    op.create_table(
        'live_review_reports',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('session_id', sa.Integer(), nullable=False, comment='直播会话ID'),
        sa.Column('overall_score', sa.Float(), nullable=True, comment='综合评分 0-100'),
        sa.Column('performance_analysis', sa.JSON(), nullable=True, comment='表现分析'),
        sa.Column('key_highlights', sa.JSON(), nullable=True, comment='亮点时刻列表'),
        sa.Column('key_issues', sa.JSON(), nullable=True, comment='主要问题列表'),
        sa.Column('improvement_suggestions', sa.JSON(), nullable=True, comment='改进建议列表'),
        sa.Column('full_report_text', sa.Text(), nullable=True, comment='完整报告文本（Markdown）'),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='报告生成时间'),
        sa.Column('ai_model', sa.String(50), nullable=False, server_default='gemini-2.5-flash', comment='使用的AI模型'),
        sa.Column('generation_cost', sa.Numeric(10, 6), nullable=True, server_default='0', comment='生成成本（美元）'),
        sa.Column('generation_tokens', sa.Integer(), nullable=True, server_default='0', comment='消耗的Token数'),
        sa.Column('generation_duration', sa.Float(), nullable=True, server_default='0', comment='生成耗时（秒）'),
        sa.Column('status', sa.String(20), nullable=False, server_default='completed', comment='状态: pending, completed, failed'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息（如果生成失败）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['session_id'], ['live_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', name='uq_live_review_session'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='直播复盘报告表'
    )
    
    # 创建索引
    op.create_index('idx_live_review_session_id', 'live_review_reports', ['session_id'])
    op.create_index('idx_live_review_generated_at', 'live_review_reports', ['generated_at'])
    op.create_index('idx_live_review_status', 'live_review_reports', ['status'])
    
    print("✅ 数据库升级成功：已创建 live_review_reports 表")


def downgrade():
    """降级数据库：删除 live_review_reports 表"""
    
    # 删除索引
    op.drop_index('idx_live_review_status', table_name='live_review_reports')
    op.drop_index('idx_live_review_generated_at', table_name='live_review_reports')
    op.drop_index('idx_live_review_session_id', table_name='live_review_reports')
    
    # 删除表
    op.drop_table('live_review_reports')
    
    print("✅ 数据库降级成功：已删除 live_review_reports 表")
