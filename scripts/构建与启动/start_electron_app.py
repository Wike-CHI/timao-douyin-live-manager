#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Electron应用启动脚本
用于检查并安装Electron依赖，然后启动语音转录服务的桌面应用
"""

import os
import sys
import subprocess
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_node_installed():
    """检查Node.js是否已安装"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Node.js版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Node.js检查失败: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("未找到Node.js，请先安装Node.js")
        return False
    except Exception as e:
        logger.error(f"检查Node.js时发生错误: {e}")
        return False

def check_npm_installed():
    """检查npm是否已安装"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"npm版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"npm检查失败: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("未找到npm，请先安装Node.js (包含npm)")
        return False
    except Exception as e:
        logger.error(f"检查npm时发生错误: {e}")
        return False

def install_electron_dependencies():
    """安装Electron依赖"""
    electron_dir = os.path.join(os.path.dirname(__file__), 'electron')
    
    if not os.path.exists(electron_dir):
        logger.error(f"Electron目录不存在: {electron_dir}")
        return False
    
    try:
        logger.info("正在安装Electron依赖...")
        # 切换到electron目录
        original_cwd = os.getcwd()
        os.chdir(electron_dir)
        
        # 安装依赖
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True, timeout=300)
        
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            logger.info("Electron依赖安装成功")
            return True
        else:
            logger.error(f"Electron依赖安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"安装Electron依赖时发生错误: {e}")
        return False

def start_electron_app():
    """启动Electron应用"""
    electron_dir = os.path.join(os.path.dirname(__file__), 'electron')
    
    if not os.path.exists(electron_dir):
        logger.error(f"Electron目录不存在: {electron_dir}")
        return False
    
    try:
        logger.info("正在启动Electron应用...")
        # 切换到electron目录
        original_cwd = os.getcwd()
        os.chdir(electron_dir)
        
        # 启动Electron应用
        result = subprocess.run(['npx', 'electron', '.'], capture_output=False, text=True)
        
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            logger.info("Electron应用启动成功")
            return True
        else:
            logger.error(f"Electron应用启动失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"启动Electron应用时发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始启动语音转录服务桌面应用")
    
    # 检查Node.js和npm
    if not check_node_installed():
        logger.error("请先安装Node.js: https://nodejs.org/")
        return False
    
    if not check_npm_installed():
        logger.error("请确保npm已正确安装")
        return False
    
    # 安装Electron依赖（如果需要）
    electron_dir = os.path.join(os.path.dirname(__file__), 'electron')
    node_modules_dir = os.path.join(electron_dir, 'node_modules')
    
    if not os.path.exists(node_modules_dir):
        logger.info("检测到未安装Electron依赖，正在安装...")
        if not install_electron_dependencies():
            logger.error("Electron依赖安装失败")
            return False
    
    # 启动Electron应用
    return start_electron_app()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)