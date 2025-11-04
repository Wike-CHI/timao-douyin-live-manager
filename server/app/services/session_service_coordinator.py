# -*- coding: utf-8 -*-
"""
统一会话服务协调器
确保所有服务在启动/停止时正确更新统一会话状态
"""

import logging
from typing import Optional

from .live_session_manager import get_session_manager

logger = logging.getLogger(__name__)


class SessionServiceCoordinator:
    """统一会话服务协调器"""
    
    @staticmethod
    async def get_or_create_session_id() -> Optional[str]:
        """获取或创建统一会话ID"""
        try:
            session_mgr = get_session_manager()
            current_session = await session_mgr.get_current_session()
            if current_session:
                return current_session.session_id
        except Exception as e:
            logger.warning(f"获取统一会话ID失败: {e}")
        return None
    
    @staticmethod
    async def update_service_status(
        service_name: str,
        active: bool,
        session_id: Optional[str] = None
    ):
        """更新服务状态到统一会话"""
        try:
            session_mgr = get_session_manager()
            if not session_mgr:
                return
            
            updates = {}
            
            if service_name == "recording":
                updates["recording_active"] = active
                if session_id:
                    updates["recording_session_id"] = session_id
            elif service_name == "audio_transcription":
                updates["audio_transcription_active"] = active
                if session_id:
                    updates["audio_session_id"] = session_id
            elif service_name == "ai_analysis":
                updates["ai_analysis_active"] = active
                if session_id:
                    updates["ai_session_id"] = session_id
            elif service_name == "douyin_relay":
                updates["douyin_relay_active"] = active
                if session_id:
                    updates["douyin_session_id"] = session_id
            
            if updates:
                await session_mgr.update_session(**updates)
                logger.debug(f"✅ 已更新服务状态: {service_name} = {active}")
        except Exception as e:
            logger.warning(f"更新服务状态失败 ({service_name}): {e}")

