import os
import sys
import time
from typing import Any

os.environ.setdefault("REDIS_ENABLED", "false")

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.utils.redis_manager import get_redis
from server.app.core.security import LoginLimiter, SessionManager


def assert_true(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


def test_login_limiter() -> None:
    identifier = "test-user"

    # 清理可能残留的状态
    # 通过内部调用会使用 RedisManager 的内存模式，无需手动 flush

    # 先尝试未达到锁定阈值的失败次数
    for i in range(LoginLimiter.MAX_ATTEMPTS - 1):
        result = LoginLimiter.record_attempt(identifier, success=False)
        assert_true(result["locked"] is False, "应未锁定")
        assert_true(result["attempts"] == i + 1, "尝试计数不正确")

    # 成功一次应清零计数
    result = LoginLimiter.record_attempt(identifier, success=True)
    assert_true(result["locked"] is False, "成功登录不应锁定")
    assert_true(result["attempts"] == 0, "成功后计数应为0")

    status = LoginLimiter.get_status(identifier)
    assert_true(status["locked"] is False, "状态应未锁定")
    assert_true(status["attempts"] == 0, "状态尝试计数应为0")

    # 触发锁定
    for i in range(LoginLimiter.MAX_ATTEMPTS):
        result = LoginLimiter.record_attempt(identifier, success=False)
    assert_true(result["locked"] is True, "应被锁定")
    assert_true(LoginLimiter.is_locked(identifier) is True, "锁定检查应为True")


def test_session_manager() -> None:
    user_id = "u1"
    user_data = {"name": "tester"}

    # 创建会话
    session_id = SessionManager.create_session(user_id, user_data, expire_minutes=1)
    assert_true(isinstance(session_id, str) and len(session_id) > 0, "session_id 无效")

    # 获取会话
    sess = SessionManager.get_session(session_id)
    assert_true(sess is not None, "会话应存在")
    assert_true(sess["user_id"] == user_id, "user_id 不匹配")

    # 更新活动时间
    last = sess["last_activity"]
    time.sleep(0.01)
    ok = SessionManager.update_session_activity(session_id)
    assert_true(ok is True, "更新活动时间失败")
    sess2 = SessionManager.get_session(session_id)
    assert_true(sess2["last_activity"] >= last, "last_activity 未更新")

    # 删除会话
    ok = SessionManager.delete_session(session_id)
    assert_true(ok is True, "删除会话失败")
    assert_true(SessionManager.get_session(session_id) is None, "会话应已删除")

    # 多会话删除
    ids = [SessionManager.create_session(user_id, user_data, expire_minutes=1) for _ in range(3)]
    count = SessionManager.delete_user_sessions(user_id)
    assert_true(count == 3, f"删除会话数量不正确: {count}")


def main() -> None:
    rm = get_redis()
    print("Redis enabled:", (rm.is_enabled() if rm else False))
    test_login_limiter()
    test_session_manager()
    print("✅ security memory-mode smoke tests passed.")


if __name__ == "__main__":
    main()