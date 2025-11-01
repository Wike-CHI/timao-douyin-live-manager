#!/usr/bin/python
# coding:utf-8

# @FileName:    main.py
# @Time:        2024/1/2 22:27
# @Author:      bubu
# @Project:     douyinLiveWebFetcher

import argparse

from .liveMan import DouyinLiveWebFetcher

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Douyin 直播弹幕抓取工具")
    parser.add_argument("live_id", nargs="?", help="抖音直播间号或 room_id")
    return parser.parse_args()

def main():
    args = parse_args()
    live_id = args.live_id or input("请输入抖音直播间号: ").strip()
    if not live_id:
        print("【X】直播间号不能为空")
        return

    room = DouyinLiveWebFetcher(live_id)
    try:
        room.get_room_status()  # 获取房间状态,失败时重试即可，abogus不是100%有效
        room.start()
    except KeyboardInterrupt:
        print("已停止抓取")
    finally:
        room.stop()

if __name__ == '__main__':
    main()
