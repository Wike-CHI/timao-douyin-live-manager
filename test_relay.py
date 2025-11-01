"""
测试直播数据采集功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.app.services.douyin_web_relay import get_douyin_web_relay
from server.utils.logger import logger

async def test_relay():
    """测试抖音弹幕采集"""
    
    # 测试房间ID（请替换为实际的直播间ID）
    live_id = "南栖77"  # 或者使用数字ID
    
    logger.info(f"🧪 开始测试弹幕采集，房间: {live_id}")
    
    # 获取 relay 实例
    relay = get_douyin_web_relay()
    
    # 启动弹幕采集
    try:
        result = await relay.start(live_id)
        logger.info(f"✅ Relay 启动结果: {result}")
    except Exception as e:
        logger.error(f"❌ Relay 启动失败: {e}")
        return
    
    # 注册客户端
    try:
        queue = await relay.register_client()
        logger.info(f"✅ 注册客户端成功，队列: {queue}")
    except Exception as e:
        logger.error(f"❌ 注册客户端失败: {e}")
        return
    
    # 接收弹幕事件
    event_count = 0
    try:
        logger.info("📡 开始接收弹幕事件（30秒）...")
        
        timeout_task = asyncio.create_task(asyncio.sleep(30))
        
        while not timeout_task.done():
            try:
                # 等待事件，最多等待1秒
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                event_count += 1
                
                event_type = event.get('type', 'unknown')
                payload = event.get('payload', {})
                
                if event_type == "follow":
                    logger.info(f"👤 关注: {payload.get('nickname', 'unknown')}")
                elif event_type == "member":
                    logger.info(f"🚪 进场: {payload.get('nickname', 'unknown')}")
                elif event_type == "chat":
                    logger.info(f"💬 弹幕: {payload.get('nickname', 'unknown')}: {payload.get('content', '')}")
                elif event_type == "like":
                    logger.info(f"❤️ 点赞: +{payload.get('count', 1)}")
                elif event_type == "gift":
                    logger.info(f"🎁 礼物: {payload.get('gift_name', 'unknown')} x{payload.get('count', 1)}")
                elif event_type == "room_user_stats":
                    logger.info(f"👥 在线人数: {payload.get('current', 0)}")
                else:
                    logger.debug(f"📨 事件: {event_type}")
                
            except asyncio.TimeoutError:
                # 1秒内没有事件，继续等待
                continue
        
        logger.info(f"✅ 测试完成，共接收 {event_count} 个事件")
        
    except KeyboardInterrupt:
        logger.info("⚠️ 用户中断测试")
    finally:
        # 清理
        await relay.unregister_client(queue)
        await relay.stop()
        logger.info("🧹 清理完成")

if __name__ == "__main__":
    asyncio.run(test_relay())
