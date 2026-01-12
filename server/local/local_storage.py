# -*- coding: utf-8 -*-
"""
本地JSON文件存储服务

提供线程安全的JSON文件读写功能，替代数据库存储。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import threading
import shutil

logger = logging.getLogger(__name__)


class LocalStorage:
    """本地JSON文件存储服务（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 数据目录：项目根目录/data
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 会话数据目录
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件锁字典
        self._file_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()
        
        logger.info(f"✅ 本地存储服务初始化完成，数据目录: {self.data_dir}")
    
    def _get_file_lock(self, filename: str) -> threading.Lock:
        """获取文件专用锁"""
        with self._locks_lock:
            if filename not in self._file_locks:
                self._file_locks[filename] = threading.Lock()
            return self._file_locks[filename]
    
    def _resolve_path(self, filename: str) -> Path:
        """解析文件路径"""
        if os.path.isabs(filename):
            return Path(filename)
        return self.data_dir / filename
    
    def read(self, filename: str, default: Any = None) -> Any:
        """
        读取JSON文件
        
        Args:
            filename: 文件名（相对于data目录）或绝对路径
            default: 文件不存在时的默认值
            
        Returns:
            解析后的JSON数据
        """
        filepath = self._resolve_path(filename)
        
        if not filepath.exists():
            return default
        
        with self._get_file_lock(str(filepath)):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误 [{filepath}]: {e}")
                return default
            except IOError as e:
                logger.error(f"文件读取错误 [{filepath}]: {e}")
                return default
    
    def write(self, filename: str, data: Any) -> bool:
        """
        写入JSON文件
        
        Args:
            filename: 文件名（相对于data目录）或绝对路径
            data: 要写入的数据
            
        Returns:
            是否写入成功
        """
        filepath = self._resolve_path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_file_lock(str(filepath)):
            try:
                # 先写入临时文件，再原子性替换
                temp_path = filepath.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
                # 原子性替换
                shutil.move(str(temp_path), str(filepath))
                return True
            except IOError as e:
                logger.error(f"文件写入错误 [{filepath}]: {e}")
                return False
    
    def append_to_list(self, filename: str, item: Any) -> bool:
        """
        向JSON数组追加元素
        
        Args:
            filename: 文件名
            item: 要追加的元素
            
        Returns:
            是否追加成功
        """
        data = self.read(filename, [])
        if not isinstance(data, list):
            data = []
        data.append(item)
        return self.write(filename, data)
    
    def update_dict(self, filename: str, updates: Dict) -> bool:
        """
        更新JSON对象（合并更新）
        
        Args:
            filename: 文件名
            updates: 要更新的键值对
            
        Returns:
            是否更新成功
        """
        data = self.read(filename, {})
        if not isinstance(data, dict):
            data = {}
        data.update(updates)
        return self.write(filename, data)
    
    def delete(self, filename: str) -> bool:
        """
        删除JSON文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        filepath = self._resolve_path(filename)
        
        with self._get_file_lock(str(filepath)):
            try:
                if filepath.exists():
                    filepath.unlink()
                return True
            except IOError as e:
                logger.error(f"文件删除错误 [{filepath}]: {e}")
                return False
    
    def exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        filepath = self._resolve_path(filename)
        return filepath.exists()
    
    def list_files(self, directory: str = "", pattern: str = "*.json") -> List[str]:
        """
        列出目录下的JSON文件
        
        Args:
            directory: 相对目录
            pattern: 文件匹配模式
            
        Returns:
            文件名列表
        """
        dir_path = self.data_dir / directory if directory else self.data_dir
        if not dir_path.exists():
            return []
        return [f.name for f in dir_path.glob(pattern)]
    
    # ========== 会话数据专用方法 ==========
    
    def get_session_dir(self, session_id: Union[int, str]) -> Path:
        """获取会话数据目录"""
        session_dir = self.sessions_dir / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_session(self, session_id: Union[int, str], data: Dict) -> bool:
        """保存会话基本信息"""
        filename = f"sessions/{session_id}/info.json"
        return self.write(filename, data)
    
    def get_session(self, session_id: Union[int, str]) -> Optional[Dict]:
        """获取会话基本信息"""
        filename = f"sessions/{session_id}/info.json"
        return self.read(filename)
    
    def save_danmaku(self, session_id: Union[int, str], danmaku_list: List[Dict]) -> bool:
        """保存弹幕数据"""
        filename = f"sessions/{session_id}/danmaku.json"
        return self.write(filename, danmaku_list)
    
    def append_danmaku(self, session_id: Union[int, str], danmaku: Dict) -> bool:
        """追加单条弹幕"""
        filename = f"sessions/{session_id}/danmaku.json"
        return self.append_to_list(filename, danmaku)
    
    def get_danmaku(self, session_id: Union[int, str]) -> List[Dict]:
        """获取弹幕数据"""
        filename = f"sessions/{session_id}/danmaku.json"
        return self.read(filename, [])
    
    def save_transcript(self, session_id: Union[int, str], transcript_data: Dict) -> bool:
        """保存转写数据"""
        filename = f"sessions/{session_id}/transcript.json"
        return self.write(filename, transcript_data)
    
    def get_transcript(self, session_id: Union[int, str]) -> Optional[Dict]:
        """获取转写数据"""
        filename = f"sessions/{session_id}/transcript.json"
        return self.read(filename)
    
    def save_report(self, session_id: Union[int, str], report_data: Dict) -> bool:
        """保存报告数据"""
        filename = f"sessions/{session_id}/report.json"
        return self.write(filename, report_data)
    
    def get_report(self, session_id: Union[int, str]) -> Optional[Dict]:
        """获取报告数据"""
        filename = f"sessions/{session_id}/report.json"
        return self.read(filename)
    
    def list_sessions(self) -> List[str]:
        """列出所有会话ID"""
        if not self.sessions_dir.exists():
            return []
        return [d.name for d in self.sessions_dir.iterdir() if d.is_dir()]
    
    def delete_session(self, session_id: Union[int, str]) -> bool:
        """删除会话及其所有数据"""
        session_dir = self.sessions_dir / str(session_id)
        try:
            if session_dir.exists():
                shutil.rmtree(session_dir)
            return True
        except Exception as e:
            logger.error(f"删除会话失败 [{session_id}]: {e}")
            return False


# 全局单例实例
local_storage = LocalStorage()

