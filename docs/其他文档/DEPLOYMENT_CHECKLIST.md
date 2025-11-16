# Redis优化部署检查清单

**审查人**: 叶维哲  
**部署日期**: ______

---

## 📋 部署前检查

- [ ] 备份数据库
- [ ] 备份当前代码
- [ ] 记录当前性能基线
- [ ] 准备回滚方案

---

## 🚀 部署步骤

### 1. Redis部署

- [ ] 运行部署脚本: `sudo ./scripts/deploy_redis.sh`
- [ ] 验证Redis运行: `redis-cli ping`
- [ ] 检查Redis配置: `cat /etc/redis/redis.conf`

### 2. 环境配置

- [ ] 编辑 `.env` 文件，添加Redis配置
- [ ] 验证环境变量: `cat .env | grep REDIS`
- [ ] 检查批量写入配置
- [ ] 检查监控配置

### 3. 代码部署

- [ ] 拉取最新代码: `git pull`
- [ ] 检查文件完整性
- [ ] 验证Python依赖: `pip install -r requirements.txt`

### 4. 服务重启

- [ ] 停止旧服务
- [ ] 启动新服务
- [ ] 检查服务状态
- [ ] 查看启动日志

### 5. 功能验证

- [ ] 测试Redis连接: `redis-cli ping`
- [ ] 测试API健康检查: `curl http://localhost:8000/health`
- [ ] 检查批量写入日志
- [ ] 验证性能监控运行

---

## ✅ 部署后验证

### 功能测试

- [ ] 创建测试直播会话
- [ ] 发送测试转写数据
- [ ] 发送测试弹幕数据
- [ ] 检查Redis键创建: `redis-cli KEYS *`
- [ ] 验证批量写入日志

### 性能测试

- [ ] 运行基础压力测试: `python scripts/stress_test.py`
- [ ] 检查MySQL连接数
- [ ] 检查Redis内存使用
- [ ] 检查进程内存使用

### 监控验证

- [ ] 查看性能监控日志
- [ ] 检查告警是否正常
- [ ] 验证指标写入Redis

---

## 📊 性能基准

### 优化前（记录实际值）

- MySQL连接数: ______
- 进程内存: ______
- 转写延迟: ______
- 支持直播数: ______

### 优化后（记录实际值）

- MySQL连接数: ______
- 进程内存: ______
- 转写延迟: ______
- 支持直播数: ______

---

## 🔧 故障处理

### 如遇问题，立即执行：

1. [ ] 查看服务日志: `tail -f logs/server.log`
2. [ ] 查看Redis日志: `sudo tail -f /var/log/redis/redis-server.log`
3. [ ] 检查Redis状态: `redis-cli info`
4. [ ] 检查MySQL连接: `mysql -h <host> -u <user> -p`

### 如需回滚：

1. [ ] 禁用Redis批量写入: `REDIS_BATCH_ENABLED=0`
2. [ ] 恢复连接池配置: `pool_size=20, max_overflow=10`
3. [ ] 重启服务
4. [ ] 验证回滚成功

---

## 📝 签字确认

部署人员: ________________  日期: ______

审查人员: 叶维哲  日期: ______

---

## 📚 相关文档

- Redis配置: `docs/REDIS_CONFIG.md`
- 压力测试: `docs/STRESS_TEST.md`
- 实施总结: `docs/IMPLEMENTATION_SUMMARY.md`
- 优化方案: `redis.plan.md`

---

**部署完成 ✅**

