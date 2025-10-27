"""
提猫直播助手 - WebSocket处理器
负责WebSocket连接管理和实时数据推送
"""

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

try:
    from flask_socketio import SocketIO, disconnect, emit

    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("Warning: flask-socketio not available, WebSocket功能将被禁用")

from .models import AIScript, Comment, data_manager
from .utils.helpers import format_time


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self, socketio: Optional[object] = None):
        self.socketio = socketio
        self.clients = {}  # 客户端连接信息
        self.rooms = defaultdict(set)  # 房间管理
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        # 事件处理器
        self.event_handlers = {}
        self.middleware = []

        # 配置
        self.config = {
            "max_connections": 100,
            "heartbeat_interval": 30,
            "message_rate_limit": 100,  # 每分钟最大消息数
            "auto_disconnect_timeout": 300,  # 自动断开超时（秒）
            "enable_compression": True,
            "enable_heartbeat": True,
        }

        # 消息队列
        self.message_queue = asyncio.Queue() if asyncio else None
        self.is_running = False
        self.worker_thread = None

        if socketio and SOCKETIO_AVAILABLE:
            self._setup_socketio_handlers()

    def setup_socketio(self, socketio):
        """设置SocketIO实例"""
        self.socketio = socketio
        if SOCKETIO_AVAILABLE:
            self._setup_socketio_handlers()

    def _setup_socketio_handlers(self):
        """设置SocketIO事件处理器"""
        if not self.socketio:
            return

        @self.socketio.on("connect")
        def handle_connect(auth=None):
            return self._handle_connect(auth)

        @self.socketio.on("disconnect")
        def handle_disconnect():
            return self._handle_disconnect()

        @self.socketio.on("join_room")
        def handle_join_room(data):
            return self._handle_join_room(data)

        @self.socketio.on("leave_room")
        def handle_leave_room(data):
            return self._handle_leave_room(data)

        @self.socketio.on("ping")
        def handle_ping():
            return self._handle_ping()

        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            return self._handle_subscribe(data)

        @self.socketio.on("unsubscribe")
        def handle_unsubscribe(data):
            return self._handle_unsubscribe(data)

    def start(self):
        """启动WebSocket管理器"""
        if self.is_running:
            return

        self.is_running = True
        if self.config["enable_heartbeat"]:
            self.worker_thread = threading.Thread(
                target=self._heartbeat_loop, daemon=True
            )
            self.worker_thread.start()

        print(f"[{format_time()}] WebSocket管理器已启动")

    def stop(self):
        """停止WebSocket管理器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        # 断开所有连接
        self._disconnect_all_clients()
        print(f"[{format_time()}] WebSocket管理器已停止")

    def _handle_connect(self, auth=None):
        """处理客户端连接"""
        try:
            from flask import request

            client_id = request.sid

            # 检查连接数限制
            if len(self.clients) >= self.config["max_connections"]:
                print(f"[{format_time()}] 连接数已达上限，拒绝连接: {client_id}")
                return False

            # 记录客户端信息
            self.clients[client_id] = {
                "id": client_id,
                "connected_at": datetime.now(),
                "last_ping": datetime.now(),
                "subscriptions": set(),
                "message_count": 0,
                "auth": auth,
                "ip": (
                    request.remote_addr
                    if hasattr(request, "remote_addr")
                    else "unknown"
                ),
            }

            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.clients)

            # 发送欢迎消息
            self.emit_to_client(
                client_id,
                "welcome",
                {
                    "message": "连接成功",
                    "client_id": client_id,
                    "server_time": datetime.now().isoformat(),
                    "config": {
                        "heartbeat_interval": self.config["heartbeat_interval"],
                        "message_rate_limit": self.config["message_rate_limit"],
                    },
                },
            )

            print(f"[{format_time()}] 客户端连接: {client_id}")
            return True

        except Exception as e:
            print(f"[{format_time()}] 处理连接失败: {e}")
            self.stats["errors"] += 1
            return False

    def _handle_disconnect(self):
        """处理客户端断开"""
        try:
            from flask import request

            client_id = request.sid

            if client_id in self.clients:
                # 从所有房间移除
                for room_name, room_clients in self.rooms.items():
                    room_clients.discard(client_id)

                # 移除客户端记录
                del self.clients[client_id]
                self.stats["active_connections"] = len(self.clients)

                print(f"[{format_time()}] 客户端断开: {client_id}")

        except Exception as e:
            print(f"[{format_time()}] 处理断开失败: {e}")
            self.stats["errors"] += 1

    def _handle_join_room(self, data):
        """处理加入房间"""
        try:
            from flask import request
            from flask_socketio import join_room

            client_id = request.sid
            room_name = data.get("room")

            if not room_name:
                return {"success": False, "error": "房间名不能为空"}

            # 加入房间
            join_room(room_name)
            self.rooms[room_name].add(client_id)

            # 更新客户端信息
            if client_id in self.clients:
                self.clients[client_id]["subscriptions"].add(room_name)

            print(f"[{format_time()}] 客户端 {client_id} 加入房间: {room_name}")
            return {"success": True, "room": room_name}

        except Exception as e:
            print(f"[{format_time()}] 加入房间失败: {e}")
            return {"success": False, "error": str(e)}

    def _handle_leave_room(self, data):
        """处理离开房间"""
        try:
            from flask import request
            from flask_socketio import leave_room

            client_id = request.sid
            room_name = data.get("room")

            if not room_name:
                return {"success": False, "error": "房间名不能为空"}

            # 离开房间
            leave_room(room_name)
            self.rooms[room_name].discard(client_id)

            # 更新客户端信息
            if client_id in self.clients:
                self.clients[client_id]["subscriptions"].discard(room_name)

            print(f"[{format_time()}] 客户端 {client_id} 离开房间: {room_name}")
            return {"success": True, "room": room_name}

        except Exception as e:
            print(f"[{format_time()}] 离开房间失败: {e}")
            return {"success": False, "error": str(e)}

    def _handle_ping(self):
        """处理心跳"""
        try:
            from flask import request

            client_id = request.sid

            if client_id in self.clients:
                self.clients[client_id]["last_ping"] = datetime.now()

            return {"pong": True, "server_time": datetime.now().isoformat()}

        except Exception as e:
            print(f"[{format_time()}] 处理心跳失败: {e}")
            return {"pong": False, "error": str(e)}

    def _handle_subscribe(self, data):
        """处理订阅事件"""
        try:
            from flask import request

            client_id = request.sid
            event_types = data.get("events", [])

            if client_id in self.clients:
                for event_type in event_types:
                    self.clients[client_id]["subscriptions"].add(f"event:{event_type}")

            return {"success": True, "subscribed": event_types}

        except Exception as e:
            print(f"[{format_time()}] 处理订阅失败: {e}")
            return {"success": False, "error": str(e)}

    def _handle_unsubscribe(self, data):
        """处理取消订阅"""
        try:
            from flask import request

            client_id = request.sid
            event_types = data.get("events", [])

            if client_id in self.clients:
                for event_type in event_types:
                    self.clients[client_id]["subscriptions"].discard(
                        f"event:{event_type}"
                    )

            return {"success": True, "unsubscribed": event_types}

        except Exception as e:
            print(f"[{format_time()}] 处理取消订阅失败: {e}")
            return {"success": False, "error": str(e)}

    def emit_to_client(self, client_id: str, event: str, data: Any):
        """向特定客户端发送消息"""
        if not self.socketio or not SOCKETIO_AVAILABLE:
            return False

        try:
            self.socketio.emit(event, data, room=client_id)
            self._update_message_stats(client_id)
            return True

        except Exception as e:
            print(f"[{format_time()}] 发送消息失败: {e}")
            self.stats["errors"] += 1
            return False

    def emit_to_room(self, room: str, event: str, data: Any):
        """向房间发送消息"""
        if not self.socketio or not SOCKETIO_AVAILABLE:
            return False

        try:
            self.socketio.emit(event, data, room=room)

            # 更新统计
            room_size = len(self.rooms.get(room, set()))
            self.stats["messages_sent"] += room_size

            return True

        except Exception as e:
            print(f"[{format_time()}] 发送房间消息失败: {e}")
            self.stats["errors"] += 1
            return False

    def broadcast(self, event: str, data: Any, exclude_client: str = None):
        """广播消息"""
        if not self.socketio or not SOCKETIO_AVAILABLE:
            return False

        try:
            if exclude_client:
                self.socketio.emit(event, data, skip_sid=exclude_client)
            else:
                self.socketio.emit(event, data)

            # 更新统计
            client_count = len(self.clients) - (1 if exclude_client else 0)
            self.stats["messages_sent"] += client_count

            return True

        except Exception as e:
            print(f"[{format_time()}] 广播消息失败: {e}")
            self.stats["errors"] += 1
            return False

    def emit_to_subscribers(self, event_type: str, event: str, data: Any):
        """向订阅者发送消息"""
        if not self.socketio or not SOCKETIO_AVAILABLE:
            return False

        subscription_key = f"event:{event_type}"
        sent_count = 0

        for client_id, client_info in self.clients.items():
            if subscription_key in client_info["subscriptions"]:
                if self.emit_to_client(client_id, event, data):
                    sent_count += 1

        return sent_count > 0

    def _update_message_stats(self, client_id: str):
        """更新消息统计"""
        if client_id in self.clients:
            self.clients[client_id]["message_count"] += 1
        self.stats["messages_sent"] += 1

    def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                current_time = datetime.now()
                timeout_threshold = (
                    current_time.timestamp() - self.config["auto_disconnect_timeout"]
                )

                # 检查超时连接
                timeout_clients = []
                for client_id, client_info in self.clients.items():
                    last_ping = client_info["last_ping"].timestamp()
                    if last_ping < timeout_threshold:
                        timeout_clients.append(client_id)

                # 断开超时连接
                for client_id in timeout_clients:
                    self._disconnect_client(client_id, "timeout")

                # 发送心跳
                if self.clients:
                    self.broadcast(
                        "heartbeat",
                        {
                            "server_time": current_time.isoformat(),
                            "active_connections": len(self.clients),
                        },
                    )

                time.sleep(self.config["heartbeat_interval"])

            except Exception as e:
                print(f"[{format_time()}] 心跳循环错误: {e}")
                time.sleep(5)

    def _disconnect_client(self, client_id: str, reason: str = "unknown"):
        """断开特定客户端"""
        if not self.socketio or not SOCKETIO_AVAILABLE:
            return

        try:
            # 发送断开通知
            self.emit_to_client(
                client_id,
                "disconnect_notice",
                {"reason": reason, "message": f"连接因 {reason} 被断开"},
            )

            # 强制断开
            self.socketio.disconnect(client_id)
            print(f"[{format_time()}] 强制断开客户端: {client_id}, 原因: {reason}")

        except Exception as e:
            print(f"[{format_time()}] 断开客户端失败: {e}")

    def _disconnect_all_clients(self):
        """断开所有客户端"""
        for client_id in list(self.clients.keys()):
            self._disconnect_client(client_id, "server_shutdown")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["active_connections"] = len(self.clients)
        stats["rooms_count"] = len(self.rooms)
        stats["is_running"] = self.is_running

        if stats["start_time"]:
            runtime = datetime.now() - stats["start_time"]
            stats["runtime_seconds"] = runtime.total_seconds()
            stats["messages_per_minute"] = stats["messages_sent"] / max(
                runtime.total_seconds() / 60, 1
            )

        return stats

    def get_clients_info(self) -> List[Dict[str, Any]]:
        """获取客户端信息"""
        clients_info = []
        for client_id, client_info in self.clients.items():
            info = client_info.copy()
            info["connected_duration"] = (
                datetime.now() - info["connected_at"]
            ).total_seconds()
            info["subscriptions"] = list(info["subscriptions"])
            clients_info.append(info)

        return clients_info

    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)

    def remove_middleware(self, middleware: Callable):
        """移除中间件"""
        if middleware in self.middleware:
            self.middleware.remove(middleware)


class LiveDataBroadcaster:
    """直播数据广播器"""

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.is_running = False
        self.broadcast_thread = None

        # 配置
        self.config = {
            "comment_broadcast_interval": 0.5,  # 评论广播间隔
            "hotword_broadcast_interval": 5.0,  # 热词广播间隔
            "script_broadcast_interval": 10.0,  # 话术广播间隔
            "stats_broadcast_interval": 30.0,  # 统计广播间隔
        }

        # 数据缓存
        self.last_broadcast_times = {
            "comments": 0,
            "hotwords": 0,
            "scripts": 0,
            "stats": 0,
        }

    def start(self):
        """启动广播器"""
        if self.is_running:
            return

        self.is_running = True
        self.broadcast_thread = threading.Thread(
            target=self._broadcast_loop, daemon=True
        )
        self.broadcast_thread.start()
        print(f"[{format_time()}] 数据广播器已启动")

    def stop(self):
        """停止广播器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=5)
        print(f"[{format_time()}] 数据广播器已停止")

    def _broadcast_loop(self):
        """广播循环"""
        while self.is_running:
            try:
                current_time = time.time()

                # 广播评论
                if (
                    current_time - self.last_broadcast_times["comments"]
                    >= self.config["comment_broadcast_interval"]
                ):
                    self._broadcast_comments()
                    self.last_broadcast_times["comments"] = current_time

                # 广播热词
                if (
                    current_time - self.last_broadcast_times["hotwords"]
                    >= self.config["hotword_broadcast_interval"]
                ):
                    self._broadcast_hotwords()
                    self.last_broadcast_times["hotwords"] = current_time

                # 广播话术
                if (
                    current_time - self.last_broadcast_times["scripts"]
                    >= self.config["script_broadcast_interval"]
                ):
                    self._broadcast_scripts()
                    self.last_broadcast_times["scripts"] = current_time

                # 广播统计
                if (
                    current_time - self.last_broadcast_times["stats"]
                    >= self.config["stats_broadcast_interval"]
                ):
                    self._broadcast_stats()
                    self.last_broadcast_times["stats"] = current_time

                time.sleep(0.1)

            except Exception as e:
                print(f"[{format_time()}] 广播循环错误: {e}")
                time.sleep(1)

    def _broadcast_comments(self):
        """广播最新评论"""
        try:
            try:
                recent_comments = data_manager.get_recent_comments(limit=10)
            except TypeError:
                recent_comments = data_manager.get_recent_comments()
            if recent_comments:
                comment_data = [asdict(comment) for comment in recent_comments]
                self.ws_manager.emit_to_subscribers(
                    "comments",
                    "new_comments",
                    {"comments": comment_data, "timestamp": datetime.now().isoformat()},
                )
        except Exception as e:
            print(f"[{format_time()}] 广播评论失败: {e}")

    def _broadcast_hotwords(self):
        """广播热词"""
        try:
            from .comment_processor import comment_processor

            try:
                hot_words = comment_processor.get_hot_words(limit=20)
            except TypeError:
                hot_words = comment_processor.get_hot_words()
            if hot_words:
                self.ws_manager.emit_to_subscribers(
                    "hotwords",
                    "hot_words_update",
                    {"hot_words": hot_words, "timestamp": datetime.now().isoformat()},
                )
        except Exception as e:
            print(f"[{format_time()}] 广播热词失败: {e}")

    def _broadcast_scripts(self):
        """广播AI话术"""
        try:
            try:
                latest_scripts = data_manager.get_latest_scripts(limit=5)
            except TypeError:
                latest_scripts = data_manager.get_latest_scripts()
            if latest_scripts:
                script_data = [asdict(script) for script in latest_scripts]
                self.ws_manager.emit_to_subscribers(
                    "scripts",
                    "new_scripts",
                    {"scripts": script_data, "timestamp": datetime.now().isoformat()},
                )
        except Exception as e:
            print(f"[{format_time()}] 广播话术失败: {e}")

    def _broadcast_stats(self):
        """广播统计信息"""
        try:
            from .comment_processor import comment_processor

            stats = {
                "comment_stats": comment_processor.get_stats(),
                "websocket_stats": self.ws_manager.get_stats(),
                "data_stats": data_manager.get_stats(),
                "timestamp": datetime.now().isoformat(),
            }

            self.ws_manager.emit_to_subscribers("stats", "stats_update", stats)
        except Exception as e:
            print(f"[{format_time()}] 广播统计失败: {e}")

    def broadcast_comment(self, comment: Comment):
        """广播单个评论"""
        try:
            self.ws_manager.emit_to_subscribers(
                "comments",
                "new_comment",
                {"comment": asdict(comment), "timestamp": datetime.now().isoformat()},
            )
        except Exception as e:
            print(f"[{format_time()}] 广播单个评论失败: {e}")

    def broadcast_script(self, script: AIScript):
        """广播单个话术"""
        try:
            self.ws_manager.emit_to_subscribers(
                "scripts",
                "new_script",
                {"script": asdict(script), "timestamp": datetime.now().isoformat()},
            )
        except Exception as e:
            print(f"[{format_time()}] 广播单个话术失败: {e}")


# 全局WebSocket管理器实例
ws_manager = WebSocketManager()
data_broadcaster = LiveDataBroadcaster(ws_manager)
_data_broadcaster_enabled = False


def setup_websocket(socketio):
    """设置WebSocket"""
    ws_manager.setup_socketio(socketio)


def start_websocket_services():
    """启动WebSocket服务"""
    global _data_broadcaster_enabled
    ws_manager.start()

    required_methods = [
        "get_recent_comments",
        "get_hot_words",
        "get_latest_scripts",
        "get_stats",
    ]
    if all(hasattr(data_manager, method) for method in required_methods):
        data_broadcaster.start()
        _data_broadcaster_enabled = True
    else:  # pragma: no cover - 运行时环境不满足时降级
        missing = [m for m in required_methods if not hasattr(data_manager, m)]
        print(
            f"[{format_time()}] 数据广播器未启动：data_manager 缺少 {', '.join(missing)}，已降级为仅 WebSocket 管理"
        )
        _data_broadcaster_enabled = False


def stop_websocket_services():
    """停止WebSocket服务"""
    global _data_broadcaster_enabled
    if _data_broadcaster_enabled:
        data_broadcaster.stop()
    _data_broadcaster_enabled = False
    ws_manager.stop()


def broadcast_comment(comment: Comment):
    """广播评论"""
    data_broadcaster.broadcast_comment(comment)


def broadcast_script(script: AIScript):
    """广播话术"""
    data_broadcaster.broadcast_script(script)
