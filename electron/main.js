const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

// 全局变量
let mainWindow;
let flaskProcess;
const FLASK_URL = 'http://127.0.0.1:5001';

/**
 * 创建主窗口
 */
function createWindow() {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    title: '提猫直播助手',
    show: false, // 初始隐藏，等待加载完成
    titleBarStyle: 'default'
  });

  // 加载应用页面
  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // 开发模式下打开开发者工具
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });

  // 窗口关闭事件
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 设置菜单
  createMenu();
}

/**
 * 创建应用菜单
 */
function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: '重做', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { label: '重新加载', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: '强制重新加载', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { label: '开发者工具', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { label: '放大', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { type: 'separator' },
        { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click: () => {
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: '关于提猫直播助手',
              message: '提猫直播助手 v1.0.0',
              detail: '一个基于 Electron + Flask 的抖音直播评论实时分析与AI话术生成工具。'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * 启动Flask后端服务
 */
function startFlaskServer() {
  return new Promise((resolve, reject) => {
    console.log('正在启动Flask后端服务...');
    
    // 启动Python Flask服务
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const serverPath = path.join(__dirname, '../server/app.py');
    
    flaskProcess = spawn(pythonPath, [serverPath], {
      cwd: path.join(__dirname, '..'),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // 监听输出
    flaskProcess.stdout.on('data', (data) => {
      console.log(`Flask输出: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
      console.error(`Flask错误: ${data}`);
    });

    flaskProcess.on('close', (code) => {
      console.log(`Flask进程退出，代码: ${code}`);
    });

    flaskProcess.on('error', (error) => {
      console.error(`Flask启动失败: ${error}`);
      reject(error);
    });

    // 等待服务启动
    const checkServer = async () => {
      try {
        await axios.get(`${FLASK_URL}/api/health`, { timeout: 1000 });
        console.log('Flask服务启动成功');
        resolve();
      } catch (error) {
        setTimeout(checkServer, 1000);
      }
    };

    setTimeout(checkServer, 2000);
  });
}

/**
 * 停止Flask后端服务
 */
function stopFlaskServer() {
  if (flaskProcess) {
    console.log('正在停止Flask后端服务...');
    flaskProcess.kill();
    flaskProcess = null;
  }
}

/**
 * 检查Flask服务状态
 */
async function checkFlaskHealth() {
  try {
    const response = await axios.get(`${FLASK_URL}/api/health`, { timeout: 5000 });
    return response.data;
  } catch (error) {
    throw new Error(`Flask服务连接失败: ${error.message}`);
  }
}

// IPC 通信处理
ipcMain.handle('flask-health-check', async () => {
  try {
    const health = await checkFlaskHealth();
    return { success: true, data: health };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-flask-url', () => {
  return FLASK_URL;
});

// 应用事件处理
app.whenReady().then(async () => {
  try {
    // 启动Flask服务
    await startFlaskServer();
    
    // 创建主窗口
    createWindow();
    
    console.log('应用启动完成');
  } catch (error) {
    console.error('应用启动失败:', error);
    
    const { dialog } = require('electron');
    dialog.showErrorBox('启动失败', `应用启动失败: ${error.message}`);
    
    app.quit();
  }
});

// 所有窗口关闭时退出应用 (macOS除外)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// macOS 激活应用时重新创建窗口
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 应用退出前清理
app.on('before-quit', () => {
  console.log('应用即将退出，清理资源...');
  stopFlaskServer();
});

// 处理未捕获的异常
process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的Promise拒绝:', reason);
});

// 导出模块 (用于测试)
module.exports = {
  createWindow,
  startFlaskServer,
  stopFlaskServer,
  checkFlaskHealth
};