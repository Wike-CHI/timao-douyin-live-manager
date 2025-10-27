#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存缓存回退自测脚本
在 REDIS_ENABLED=false 下验证 RedisManager 的内存模式行为
"""

import sys
from pathlib import Path
import time

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from server.config import ConfigManager
from server.utils.redis_manager import RedisManager


def header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    header("🧪 内存缓存回退自测")

    cfg = ConfigManager().get_config()
    # 强制禁用 Redis，进入内存模式
    cfg.redis.enabled = False

    rm = RedisManager(cfg.redis)
    print(f"is_enabled: {rm.is_enabled()} (期望 False，表示未连接真实 Redis)")
    print(f"ping (内存模式应为 True): {rm.ping()}")

    # KV: set/get/expire/ttl/delete
    header("KV 测试")
    assert rm.set("kv:user", {"name": "张三"}, ttl=2)
    print("set ->", rm.get("kv:user"))
    print("ttl ->", rm.ttl("kv:user"))
    time.sleep(2.1)
    print("expired get ->", rm.get("kv:user"))
    assert rm.set("kv:num", 1)
    print("incr ->", rm.incr("kv:num"))
    print("decr ->", rm.decr("kv:num"))
    print("delete ->", rm.delete("kv:num"))

    # Hash: hset/hget/hgetall/hdel
    header("Hash 测试")
    assert rm.hset("h:user:1", "name", "李四")
    assert rm.hset("h:user:1", "role", "admin")
    print("hget(name) ->", rm.hget("h:user:1", "name"))
    print("hgetall ->", rm.hgetall("h:user:1"))
    print("hdel(role) ->", rm.hdel("h:user:1", "role"))
    print("hgetall ->", rm.hgetall("h:user:1"))

    # List: lpush/rpush/lrange/ltrim
    header("List 测试")
    assert rm.lpush("list:q", "m1")
    assert rm.rpush("list:q", "m2")
    assert rm.rpush("list:q", {"m": 3})
    print("lrange(0,-1) ->", rm.lrange("list:q", 0, -1))
    rm.ltrim("list:q", 0, 1)
    print("lrange(0,-1) after trim ->", rm.lrange("list:q", 0, -1))

    # Set: sadd/smembers/srem
    header("Set 测试")
    assert rm.sadd("set:online", "u1")
    assert rm.sadd("set:online", "u2")
    print("smembers ->", sorted(list(rm.smembers("set:online"))))
    print("srem(u1) ->", rm.srem("set:online", "u1"))
    print("smembers ->", sorted(list(rm.smembers("set:online"))))

    # exists/flush_db
    header("exists/flush 测试")
    print("exists ->", rm.exists("h:user:1", "list:q", "set:online"))
    print("flush_db ->", rm.flush_db())
    print("exists after flush ->", rm.exists("h:user:1", "list:q", "set:online"))

    print("\n✅ 内存缓存回退测试完成")


if __name__ == "__main__":
    main()