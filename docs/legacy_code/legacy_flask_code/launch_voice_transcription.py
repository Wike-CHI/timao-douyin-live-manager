#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转录服务启动器
提供多种方式启动语音转录服务
"""

import os
import sys
import subprocess
import webbrowser
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_electron_installed():
    """检查Electron是否已安装"""
    try:
        result = subprocess.run(['npx', 'electron', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Electron版本: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"Electron检查失败: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.warning("未找到Electron")
        return False
    except Exception as e:
        logger.error(f"检查Electron时发生错误: {e}")
        return False

def start_electron_app():
    """启动Electron桌面应用"""
    electron_dir = os.path.join(os.path.dirname(__file__), 'electron')
    
    if not os.path.exists(electron_dir):
        logger.error(f"Electron目录不存在: {electron_dir}")
        return False
    
    try:
        logger.info("正在启动Electron桌面应用...")
        # 切换到electron目录
        original_cwd = os.getcwd()
        os.chdir(electron_dir)
        
        # 启动Electron应用
        result = subprocess.Popen(['npx', 'electron', '.'])
        
        os.chdir(original_cwd)
        
        if result.poll() is None:
            logger.info("Electron桌面应用启动成功")
            return True
        else:
            logger.error("Electron桌面应用启动失败")
            return False
            
    except Exception as e:
        logger.error(f"启动Electron应用时发生错误: {e}")
        return False

def start_flask_server():
    """启动Flask服务器"""
    ast_module_dir = os.path.join(os.path.dirname(__file__), 'AST_module')
    server_script = os.path.join(ast_module_dir, 'test_server.py')
    
    if not os.path.exists(server_script):
        logger.error(f"服务器脚本不存在: {server_script}")
        return None
    
    try:
        logger.info("正在启动Flask服务器...")
        # 启动Flask服务器
        process = subprocess.Popen([sys.executable, server_script], 
                                 cwd=ast_module_dir,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        
        # 等待服务器启动
        time.sleep(3)
        
        if process.poll() is None:
            logger.info("Flask服务器启动成功")
            return process
        else:
            logger.error("Flask服务器启动失败")
            return None
            
    except Exception as e:
        logger.error(f"启动Flask服务器时发生错误: {e}")
        return None

def open_web_interface():
    """打开Web界面"""
    try:
        logger.info("正在打开Web界面...")
        webbrowser.open('http://127.0.0.1:5000')
        logger.info("Web界面已打开")
        return True
    except Exception as e:
        logger.error(f"打开Web界面时发生错误: {e}")
        return False

def show_instructions():
    """显示启动说明"""
    instructions = """
========================================
语音转录服务启动说明
========================================

方法1: 使用Electron桌面应用 (推荐)
1. 确保已安装Node.js和npm
2. 安装Electron依赖:
   cd electron
   npm install
3. 启动应用:
   npx electron .

方法2: 使用Flask服务器
1. 直接运行:
   python AST_module/test_server.py
2. 在浏览器中访问:
   http://127.0.0.1:5000

方法3: 使用启动脚本
1. 运行此脚本并选择相应选项

方法4: 自动启动服务 (新增)
1. 双击运行项目根目录下的 auto_launch_service.bat 文件
2. 或者直接运行 auto_launch_service.py Python脚本

========================================
"""
    print(instructions)

def main():
    """主函数"""
    logger.info("语音转录服务启动器")
    
    while True:
        print("\n请选择启动方式:")
        print("1. 启动Electron桌面应用")
        print("2. 启动Flask服务器")
        print("3. 打开Web界面 (需先启动服务器)")
        print("4. 自动启动服务 (新增功能)")
        print("5. 显示详细说明")
        print("6. 退出")
        
        choice = input("\n请输入选项 (1-6): ").strip()
        
        if choice == '1':
            if check_electron_installed():
                if start_electron_app():
                    print("Electron桌面应用已启动")
                else:
                    print("启动Electron桌面应用失败")
            else:
                print("未找到Electron，请先安装Node.js和Electron")
                
        elif choice == '2':
            server_process = start_flask_server()
            if server_process:
                print("Flask服务器已启动")
                print("请在浏览器中访问: http://127.0.0.1:5000")
            else:
                print("启动Flask服务器失败")
                
        elif choice == '3':
            if open_web_interface():
                print("Web界面已打开")
            else:
                print("打开Web界面失败")
                
        elif choice == '4':
            # 自动启动服务
            print("正在启动自动服务...")
            try:
                # 导入自动启动脚本并运行
                import auto_launch_service
                # 在新进程中运行自动启动脚本
                auto_process = subprocess.Popen([sys.executable, 'auto_launch_service.py'])
                print("自动服务已启动，请在浏览器中查看应用界面")
            except Exception as e:
                print(f"启动自动服务失败: {e}")
            
        elif choice == '5':
            show_instructions()
            
        elif choice == '6':
            print("退出启动器")
            break
            
        else:
            print("无效选项，请重新选择")

if __name__ == "__main__":
    main()