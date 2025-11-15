## 现状评估
1. 初始化：`server/utils/redis_manager.py` 使用 `redis.ConnectionPool` + `decode_responses=True`，应用在 `server/app/main.py` 启动时通过 `init_redis` 创建，关闭时 `close_redis` 释放；连接失败自动回退内存，逻辑健壮。
2. 配置：`server/config.py` 映射 `REDIS_ENABLED/REDIS_HOST/REDIS_PORT/REDIS_DB/REDIS_PASSWORD/REDIS_MAX_CONNECTIONS/REDIS_CACHE_TTL` 等环境变量；建议在 `server/.env` 补齐这些键。
3. 使用面：安全与会话、弹幕队列、性能监控等均通过 `RedisManager` 操作 `kv/hash/list/set`；`douyin_web_relay.py` 依赖 `zadd` 做热词统计，但 `RedisManager` 未实现 `sorted set` 方法，存在运行时风险。
4. 小问题：部分代码直接访问私有 `_client`（监控模块），以及对 `hgetall` 结果进行不必要的 bytes→str 转换。

## 计划目标
- 补齐 `sorted set` 能力，消除 `zadd` 相关报错风险。
- 统一通过 `RedisManager` 暴露方法，避免外部直接访问 `_client`。
- 简化冗余解码，保持与 `decode_responses=True` 一致。
- 补充环境配置与健康校验用例，验证真实 Redis 与内存回退两种路径。

## 实施步骤
1. 在 `RedisManager` 增加 `sorted set` 方法：`zadd/zincrby/zrem/zrange/zrevrange/zscore/zcard`，包含内存回退实现与 TTL 支持；沿用现有前缀与 JSON 序列化约定。
2. 调整使用点：
   - `server/app/services/douyin_web_relay.py` 改为使用新增的 `RedisManager` 方法进行热词统计；保留 `expire` 设置。
   - `server/utils/performance_monitor.py` 增加只读封装（如 `get_info(section)` 或 `info_memory/info_stats`），替换直接访问 `_client`。
   - `server/app/services/live_session_manager.py` 去除对 `hgetall` 的 bytes→str 冗余转换。
3. 环境与配置：在 `server/.env` 补齐 `REDIS_*` 变量；确认生产环境密码安全注入，不在仓库明文。
4. 测试与验证：
   - 单元测试覆盖 `kv/hash/list/set/sorted set`，分别在 `REDIS_ENABLED=true/false` 下跑通；包含前缀、TTL、序列化一致性。
   - 集成验证：启动应用，写入弹幕队列（`rpush`）与热词（`zadd`），读取并校验排序与过期；记录日志与指标。
5. 文档注记（代码内 docstring）：在 `RedisManager` 方法注释清晰标注回退行为与键前缀策略。

## 验收标准
- 所有 Redis 使用点不再直接访问 `_client`，统一通过管理器方法。
- `douyin_web_relay` 热词统计可用，`zadd/zrange` 行为在真实 Redis 与内存回退下一致。
- 单元与集成测试全部通过；启动与关闭日志显示 Redis 状态正常。
- `.env` 与配置项完整，生产环境不暴露敏感信息。