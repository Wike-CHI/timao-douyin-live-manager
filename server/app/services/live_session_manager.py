# -*- coding: utf-8 -*-
"""
统一直播会话管理器
管理整场直播的所有服务（录制、转写、AI、弹幕）的统一会话
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class LiveSessionState:
    """统一会话状态"""
    session_id: str
    live_url: str
    live_id: Optional[str] = None
    room_id: Optional[str] = None
    anchor_name: Optional[str] = None
    platform_key: str = "douyin"
    
    # 时间信息（用于防止连接旧session）
    session_date: str = ""  # YYYY-MM-DD
    started_at: int = field(default_factory=lambda: int(time.time() * 1000))
    last_updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    # 服务状态
    status: str = "recording"  # recording / paused / stopped / error
    recording_active: bool = False
    audio_transcription_active: bool = False
    ai_analysis_active: bool = False
    douyin_relay_active: bool = False
    
    # 服务特定的session_id（如果有）
    recording_session_id: Optional[str] = None
    audio_session_id: Optional[str] = None
    ai_session_id: Optional[str] = None
    douyin_session_id: Optional[str] = None
    
    # 错误信息
    last_error: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class LiveSessionManager:
    """统一直播会话管理器"""
    
    def __init__(self, records_root: Optional[str] = None):
        self.records_root = Path(records_root or os.getenv("RECORDS_ROOT", "records")).resolve()
        self.records_root.mkdir(parents=True, exist_ok=True)
        
        # 当前活跃会话
        self._current_session: Optional[LiveSessionState] = None
        self._lock = asyncio.Lock()
        
        # 会话状态文件路径
        self._state_file = self.records_root / ".live_session_state.json"
        
        # 会话目录（按session_id组织）
        self._sessions_dir = self.records_root / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_dir(self, session_id: str) -> Path:
        """获取会话目录"""
        return self._sessions_dir / session_id
    
    def _generate_session_id(self, live_url: str, anchor_name: Optional[str] = None) -> str:
        """生成会话ID"""
        # 格式：live_{platform}_{anchor}_{date}_{timestamp}
        platform = "douyin"
        anchor = anchor_name or "unknown"
        date = datetime.now().strftime("%Y%m%d")
        timestamp = int(time.time())
        return f"live_{platform}_{anchor}_{date}_{timestamp}"
    
    def _is_session_valid(self, session: LiveSessionState) -> bool:
        """检查会话是否有效（防止连接旧session）"""
        try:
            # 检查会话日期是否为今天
            today = datetime.now().strftime("%Y-%m-%d")
            if session.session_date and session.session_date != today:
                logger.warning(
                    f"会话 {session.session_id} 的日期 {session.session_date} 不是今天 ({today})，拒绝恢复"
                )
                return False
            
            # 检查会话是否超过24小时未更新（可能已过期）
            now_ms = int(time.time() * 1000)
            hours_since_update = (now_ms - session.last_updated_at) / (1000 * 60 * 60)
            if hours_since_update > 24:
                logger.warning(
                    f"会话 {session.session_id} 超过24小时未更新，拒绝恢复"
                )
                return False
            
            # 检查会话状态是否可恢复
            if session.status not in ["recording", "paused"]:
                logger.info(f"会话 {session.session_id} 状态为 {session.status}，不可恢复")
                return False
            
            # 🆕 验证room_id一致性（如果提供了room_id）
            # 注意：这个检查在恢复时可能需要重新验证，因为room_id可能已变化
            # 这里只做基本检查，实际恢复时应该重新验证
            
            return True
        except Exception as e:
            logger.error(f"检查会话有效性失败: {e}")
            return False
    
    async def create_session(
        self,
        live_url: str,
        live_id: Optional[str] = None,
        room_id: Optional[str] = None,
        anchor_name: Optional[str] = None,
        platform_key: str = "douyin"
    ) -> LiveSessionState:
        """创建新会话"""
        async with self._lock:
            # 如果已有活跃会话，先停止
            if self._current_session and self._current_session.status in ["recording", "paused"]:
                logger.warning(f"已有活跃会话 {self._current_session.session_id}，将创建新会话")
                await self.stop_session()
            
            # 生成会话ID
            session_id = self._generate_session_id(live_url, anchor_name)
            
            # 创建会话目录
            session_dir = self._get_session_dir(session_id)
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建会话状态
            session = LiveSessionState(
                session_id=session_id,
                live_url=live_url,
                live_id=live_id,
                room_id=room_id,
                anchor_name=anchor_name,
                platform_key=platform_key,
                session_date=datetime.now().strftime("%Y-%m-%d"),
                status="recording"
            )
            
            self._current_session = session
            await self._save_session_state()
            
            logger.info(f"✅ 创建新会话: {session_id}")
            return session
    
    async def get_current_session(self) -> Optional[LiveSessionState]:
        """获取当前活跃会话"""
        async with self._lock:
            return self._current_session
    
    async def resume_session(self) -> Optional[LiveSessionState]:
        """恢复之前的会话（如果有效）"""
        async with self._lock:
            # 从文件加载会话状态
            session = await self._load_session_state()
            
            if not session:
                logger.info("没有可恢复的会话")
                return None
            
            # 检查会话有效性
            if not self._is_session_valid(session):
                logger.info(f"会话 {session.session_id} 无效，无法恢复")
                await self._clear_session_state()
                return None
            
            # 恢复会话
            self._current_session = session
            session.last_updated_at = int(time.time() * 1000)
            await self._save_session_state()
            
            logger.info(f"✅ 恢复会话: {session.session_id}")
            return session
    
    async def update_session(
        self,
        session_id: Optional[str] = None,
        **updates: Any
    ) -> Optional[LiveSessionState]:
        """更新会话状态"""
        async with self._lock:
            session = self._current_session
            
            # 如果指定了session_id，验证是否匹配
            if session_id and session and session.session_id != session_id:
                logger.warning(f"会话ID不匹配: 期望 {session_id}, 实际 {session.session_id}")
                return None
            
            if not session:
                logger.warning("没有活跃会话可更新")
                return None
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            session.last_updated_at = int(time.time() * 1000)
            await self._save_session_state()
            
            return session
    
    async def stop_session(self) -> Optional[LiveSessionState]:
        """停止当前会话"""
        async with self._lock:
            if not self._current_session:
                return None
            
            session = self._current_session
            session.status = "stopped"
            session.recording_active = False
            session.audio_transcription_active = False
            session.ai_analysis_active = False
            session.douyin_relay_active = False
            session.last_updated_at = int(time.time() * 1000)
            
            await self._save_session_state()
            
            # 保留会话数据，但标记为已停止
            logger.info(f"✅ 会话已停止: {session.session_id}")
            
            return session
    
    async def pause_session(self) -> Optional[LiveSessionState]:
        """暂停当前会话"""
        async with self._lock:
            if not self._current_session:
                return None
            
            session = self._current_session
            session.status = "paused"
            session.last_updated_at = int(time.time() * 1000)
            
            await self._save_session_state()
            logger.info(f"⏸️ 会话已暂停: {session.session_id}")
            
            return session
    
    async def resume_paused_session(self) -> Optional[LiveSessionState]:
        """恢复暂停的会话"""
        async with self._lock:
            if not self._current_session:
                return None
            
            session = self._current_session
            if session.status != "paused":
                logger.warning(f"会话 {session.session_id} 状态为 {session.status}，不是 paused")
                return None
            
            session.status = "recording"
            session.last_updated_at = int(time.time() * 1000)
            
            await self._save_session_state()
            logger.info(f"▶️ 会话已恢复: {session.session_id}")
            
            return session
    
    async def _save_session_state(self):
        """保存会话状态到文件和Redis"""
        if not self._current_session:
            return
        
        try:
            state_data = asdict(self._current_session)
            
            # 1. 保存到文件（保持原有功能）
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            # 2. 🆕 同步到Redis（优先读取，定期同步到MySQL）
            try:
                from server.utils.redis_manager import get_redis
                redis_mgr = get_redis()
                if redis_mgr:
                    session_id = self._current_session.session_id
                    redis_key = f"session:{session_id}:state"
                    
                    # 使用Hash存储会话详情（方便部分更新）
                    redis_mgr.hset(redis_key, mapping=state_data)
                    
                    # 设置过期时间（48小时，超过会话可能的生命周期）
                    redis_mgr.expire(redis_key, 172800)
                    
                    # 添加到活跃会话集合
                    if self._current_session.status in ["recording", "paused"]:
                        redis_mgr.sadd("active_sessions", session_id)
                    else:
                        redis_mgr.srem("active_sessions", session_id)
                    
                    logger.debug(f"✅ 会话状态已保存到Redis: {session_id}")
            except Exception as e:
                logger.warning(f"保存会话状态到Redis失败（将继续使用文件）: {e}")
            
            logger.debug(f"✅ 会话状态已保存: {self._current_session.session_id}")
        except Exception as e:
            logger.error(f"保存会话状态失败: {e}", exc_info=True)
    
    async def _load_session_state(self) -> Optional[LiveSessionState]:
        """从Redis或文件加载会话状态（优先Redis）"""
        # 1. 🆕 尝试从Redis加载
        try:
            from server.utils.redis_manager import get_redis
            redis_mgr = get_redis()
            if redis_mgr:
                # 从活跃会话集合中获取最近的会话
                active_sessions = redis_mgr.smembers("active_sessions")
                if active_sessions:
                    # 取第一个活跃会话（实际可能需要更复杂的逻辑）
                    for session_id_bytes in active_sessions:
                        session_id = session_id_bytes if isinstance(session_id_bytes, str) else session_id_bytes.decode('utf-8')
                        redis_key = f"session:{session_id}:state"
                        state_data = redis_mgr.hgetall(redis_key)
                        
                        if state_data:
                            # 转换字节类型的键值
                            if state_data and any(isinstance(k, bytes) for k in state_data.keys()):
                                state_data = {
                                    k.decode('utf-8') if isinstance(k, bytes) else k: 
                                    v.decode('utf-8') if isinstance(v, bytes) else v
                                    for k, v in state_data.items()
                                }
                            
                            # 类型转换（Redis存储的都是字符串）
                            for int_field in ['started_at', 'last_updated_at']:
                                if int_field in state_data:
                                    state_data[int_field] = int(state_data[int_field])
                            for bool_field in ['recording_active', 'audio_transcription_active', 
                                             'ai_analysis_active', 'douyin_relay_active']:
                                if bool_field in state_data:
                                    state_data[bool_field] = state_data[bool_field] in ['True', 'true', '1', True]
                            
                            # 恢复metadata（如果是JSON字符串）
                            if 'metadata' in state_data and isinstance(state_data['metadata'], str):
                                try:
                                    state_data['metadata'] = json.loads(state_data['metadata'])
                                except:
                                    state_data['metadata'] = {}
                            
                            session = LiveSessionState(**state_data)
                            logger.debug(f"✅ 从Redis加载会话状态: {session.session_id}")
                            return session
        except Exception as e:
            logger.warning(f"从Redis加载会话状态失败（将尝试从文件加载）: {e}")
        
        # 2. 回退到文件加载
        if not self._state_file.exists():
            return None
        
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = LiveSessionState(**data)
            logger.debug(f"✅ 从文件加载会话状态: {session.session_id}")
            return session
        except Exception as e:
            logger.error(f"加载会话状态失败: {e}", exc_info=True)
            return None
    
    async def _clear_session_state(self):
        """清除会话状态文件和Redis"""
        try:
            # 1. 清除文件
            if self._state_file.exists():
                self._state_file.unlink()
                logger.debug("✅ 会话状态文件已清除")
            
            # 2. 🆕 清除Redis中的会话数据
            try:
                from server.utils.redis_manager import get_redis
                redis_mgr = get_redis()
                if redis_mgr and self._current_session:
                    session_id = self._current_session.session_id
                    redis_key = f"session:{session_id}:state"
                    
                    # 删除会话状态Hash
                    redis_mgr.delete(redis_key)
                    
                    # 从活跃会话集合中移除
                    redis_mgr.srem("active_sessions", session_id)
                    
                    logger.debug(f"✅ Redis会话状态已清除: {session_id}")
            except Exception as e:
                logger.warning(f"清除Redis会话状态失败: {e}")
        except Exception as e:
            logger.error(f"清除会话状态失败: {e}")
    
    def get_session_data_dir(self, session_id: Optional[str] = None) -> Optional[Path]:
        """获取会话数据目录"""
        session_id = session_id or (self._current_session.session_id if self._current_session else None)
        if not session_id:
            return None
        return self._get_session_dir(session_id)
    
    async def cleanup_old_sessions(self, days: int = 7):
        """清理旧会话（超过指定天数的已停止会话）"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_date.timestamp() * 1000)
            
            cleaned = 0
            for session_dir in self._sessions_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                
                # 检查会话状态文件
                state_file = self._sessions_dir / f"{session_dir.name}.json"
                if state_file.exists():
                    try:
                        with open(state_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        session_date = data.get('session_date', '')
                        last_updated = data.get('last_updated_at', 0)
                        status = data.get('status', 'stopped')
                        
                        # 只清理已停止且超过指定天数的会话
                        if status == 'stopped' and last_updated < cutoff_timestamp:
                            import shutil
                            shutil.rmtree(session_dir)
                            state_file.unlink()
                            cleaned += 1
                            logger.info(f"🗑️ 清理旧会话: {session_dir.name}")
                    except Exception as e:
                        logger.warning(f"清理会话 {session_dir.name} 失败: {e}")
            
            if cleaned > 0:
                logger.info(f"✅ 清理了 {cleaned} 个旧会话")
        except Exception as e:
            logger.error(f"清理旧会话失败: {e}", exc_info=True)


# 全局单例
_session_manager: Optional[LiveSessionManager] = None


def get_session_manager() -> LiveSessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = LiveSessionManager()
    return _session_manager


def reset_session_manager():
    """重置会话管理器（用于测试）"""
    global _session_manager
    _session_manager = None

