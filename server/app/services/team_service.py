# -*- coding: utf-8 -*-
"""
团队管理服务
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from server.app.models import Team, TeamMember, User, TeamRoleEnum
from server.app.models.permission import AuditLog
from server.app.database import db_session


class TeamService:
    """团队管理服务"""
    
    @staticmethod
    def create_team(
        name: str,
        owner_id: int,
        description: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Team:
        """
        创建团队
        
        Args:
            name: 团队名称
            owner_id: 所有者ID
            description: 团队描述
            slug: 团队标识
            
        Returns:
            团队对象
        """
        with db_session() as session:
            # 生成 slug
            if not slug:
                import re
                slug = re.sub(r'[^a-z0-9-]', '-', name.lower())
                slug = re.sub(r'-+', '-', slug).strip('-')
                
                # 检查slug是否已存在
                counter = 1
                original_slug = slug
                while session.query(Team).filter(Team.slug == slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
            
            # 创建团队
            team = Team(
                name=name,
                slug=slug,
                description=description,
                owner_id=owner_id
            )
            
            session.add(team)
            session.flush()
            
            # 添加所有者为成员
            owner_member = TeamMember(
                team_id=team.id,
                user_id=owner_id,
                role=TeamRoleEnum.OWNER,
                invited_by=owner_id
            )
            session.add(owner_member)
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=owner_id,
                action="team_created",
                resource_type="team",
                resource_id=str(team.id),
                description=f"创建团队: {name}"
            )
            session.add(audit_log)
            
            session.commit()
            session.refresh(team)
            
            return team
    
    @staticmethod
    def get_team_by_id(team_id: int) -> Optional[Team]:
        """根据ID获取团队"""
        with db_session() as session:
            return session.query(Team).filter(Team.id == team_id).first()
    
    @staticmethod
    def get_team_by_slug(slug: str) -> Optional[Team]:
        """根据slug获取团队"""
        with db_session() as session:
            return session.query(Team).filter(Team.slug == slug).first()
    
    @staticmethod
    def get_user_teams(user_id: int) -> List[Team]:
        """获取用户所在的团队"""
        with db_session() as session:
            # 查询用户的团队成员记录
            memberships = session.query(TeamMember).filter(
                and_(
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True
                )
            ).all()
            
            # 获取团队列表
            team_ids = [m.team_id for m in memberships]
            teams = session.query(Team).filter(
                and_(
                    Team.id.in_(team_ids),
                    Team.is_active == True
                )
            ).all()
            
            return teams
    
    @staticmethod
    def add_team_member(
        team_id: int,
        user_id: int,
        role: TeamRoleEnum,
        invited_by: int,
        permissions: Optional[Dict[str, bool]] = None
    ) -> TeamMember:
        """
        添加团队成员
        
        Args:
            team_id: 团队ID
            user_id: 用户ID
            role: 团队角色
            invited_by: 邀请人ID
            permissions: 自定义权限
            
        Returns:
            团队成员对象
        """
        with db_session() as session:
            # 检查团队是否存在
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError("团队不存在")
            
            # 检查是否可以添加成员
            if not team.can_add_member():
                raise ValueError("团队成员已达上限")
            
            # 检查用户是否已在团队中
            existing = session.query(TeamMember).filter(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id
                )
            ).first()
            
            if existing:
                if existing.is_active:
                    raise ValueError("用户已在团队中")
                else:
                    # 重新激活
                    existing.is_active = True
                    existing.role = role
                    existing.invited_by = invited_by
                    existing.joined_at = datetime.utcnow()
                    if permissions:
                        existing.set_permissions(permissions)
                    session.commit()
                    return existing
            
            # 创建新成员
            member = TeamMember(
                team_id=team_id,
                user_id=user_id,
                role=role,
                invited_by=invited_by
            )
            
            if permissions:
                member.set_permissions(permissions)
            
            session.add(member)
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=invited_by,
                action="team_member_added",
                resource_type="team",
                resource_id=str(team_id),
                description=f"添加成员: {user_id} ({role.value})"
            )
            session.add(audit_log)
            
            session.commit()
            session.refresh(member)
            
            return member
    
    @staticmethod
    def remove_team_member(team_id: int, user_id: int, removed_by: int) -> bool:
        """
        移除团队成员
        
        Args:
            team_id: 团队ID
            user_id: 用户ID
            removed_by: 操作人ID
            
        Returns:
            是否成功
        """
        with db_session() as session:
            member = session.query(TeamMember).filter(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True
                )
            ).first()
            
            if not member:
                return False
            
            # 不能移除所有者
            if member.role == TeamRoleEnum.OWNER:
                raise ValueError("不能移除团队所有者")
            
            member.is_active = False
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=removed_by,
                action="team_member_removed",
                resource_type="team",
                resource_id=str(team_id),
                description=f"移除成员: {user_id}"
            )
            session.add(audit_log)
            
            session.commit()
            
            return True
    
    @staticmethod
    def update_team_member_role(
        team_id: int,
        user_id: int,
        new_role: TeamRoleEnum,
        updated_by: int
    ) -> Optional[TeamMember]:
        """
        更新团队成员角色
        
        Args:
            team_id: 团队ID
            user_id: 用户ID
            new_role: 新角色
            updated_by: 操作人ID
            
        Returns:
            更新后的团队成员对象
        """
        with db_session() as session:
            member = session.query(TeamMember).filter(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True
                )
            ).first()
            
            if not member:
                return None
            
            # 不能修改所有者角色
            if member.role == TeamRoleEnum.OWNER:
                raise ValueError("不能修改团队所有者角色")
            
            old_role = member.role
            member.role = new_role
            
            # 记录审计日志
            audit_log = AuditLog.log_action(
                user_id=updated_by,
                action="team_member_role_updated",
                resource_type="team",
                resource_id=str(team_id),
                description=f"更新成员角色: {user_id} ({old_role.value} -> {new_role.value})"
            )
            session.add(audit_log)
            
            session.commit()
            session.refresh(member)
            
            return member
    
    @staticmethod
    def get_team_members(team_id: int, active_only: bool = True) -> List[TeamMember]:
        """
        获取团队成员列表
        
        Args:
            team_id: 团队ID
            active_only: 仅活跃成员
            
        Returns:
            团队成员列表
        """
        with db_session() as session:
            query = session.query(TeamMember).filter(TeamMember.team_id == team_id)
            
            if active_only:
                query = query.filter(TeamMember.is_active == True)
            
            return query.all()
    
    @staticmethod
    def check_team_permission(team_id: int, user_id: int, permission: str) -> bool:
        """
        检查团队权限
        
        Args:
            team_id: 团队ID
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        with db_session() as session:
            member = session.query(TeamMember).filter(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.is_active == True
                )
            ).first()
            
            if not member:
                return False
            
            return member.has_permission(permission)
    
    @staticmethod
    def update_team_info(
        team_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None,
        updated_by: int = None
    ) -> Optional[Team]:
        """
        更新团队信息
        
        Args:
            team_id: 团队ID
            name: 团队名称
            description: 团队描述
            avatar_url: 团队头像URL
            updated_by: 操作人ID
            
        Returns:
            更新后的团队对象
        """
        with db_session() as session:
            team = session.query(Team).filter(Team.id == team_id).first()
            
            if not team:
                return None
            
            if name:
                team.name = name
            if description is not None:
                team.description = description
            if avatar_url is not None:
                team.avatar_url = avatar_url
            
            team.updated_at = datetime.utcnow()
            
            # 记录审计日志
            if updated_by:
                audit_log = AuditLog.log_action(
                    user_id=updated_by,
                    action="team_info_updated",
                    resource_type="team",
                    resource_id=str(team_id),
                    description="更新团队信息"
                )
                session.add(audit_log)
            
            session.commit()
            session.refresh(team)
            
            return team
