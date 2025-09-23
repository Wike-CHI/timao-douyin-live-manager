#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web API测试脚本
用于验证SenseVoice服务的Web API接口是否正常工作
"""

import sys
import os
import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_api():
    """测试Web API"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # 测试获取状态
        logger.info("测试获取服务状态...")
        response = requests.get(f"{base_url}/api/status")
        status_data = response.json()
        logger.info(f"✅ 状态接口响应: {status_data}")
        
        # 测试获取设备列表
        logger.info("测试获取音频设备列表...")
        response = requests.get(f"{base_url}/api/devices")
        devices_data = response.json()
        logger.info(f"✅ 设备列表接口响应: {devices_data}")
        
        # 测试初始化服务
        logger.info("测试初始化服务...")
        response = requests.post(f"{base_url}/api/init", json={})
        init_data = response.json()
        logger.info(f"✅ 初始化接口响应: {init_data}")
        
        # 再次测试获取状态
        logger.info("再次测试获取服务状态...")
        response = requests.get(f"{base_url}/api/status")
        status_data = response.json()
        logger.info(f"✅ 状态接口响应: {status_data}")
        
        # 测试清理服务
        logger.info("测试清理服务...")
        response = requests.post(f"{base_url}/api/cleanup")
        cleanup_data = response.json()
        logger.info(f"✅ 清理接口响应: {cleanup_data}")
        
        logger.info("✅ 所有Web API测试通过")
        return True
        
    except Exception as e:
        logger.error(f"Web API测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始Web API测试")
    result = test_web_api()
    if result:
        logger.info("✅ Web API测试通过")
    else:
        logger.error("❌ Web API测试失败")
    sys.exit(0 if result else 1)