/**
 * 独立悬浮窗管理模块
 * 
 * 功能：
 * - 创建系统级独立悬浮窗（BrowserWindow）
 * - 始终置顶，可覆盖OBS等全屏应用
 * - 管理悬浮窗生命周期
 * - 位置持久化
 */

const { BrowserWindow, screen } = require('electron');
const path = require('path');
const fs = require('fs');

// 悬浮窗实例
let floatingWindow = null;

// 配置文件路径
const CONFIG_DIR = path.join(__dirname, '..', 'config');
const POSITION_FILE = path.join(CONFIG_DIR, 'floating-position.json');

/**
 * 确保配置目录存在
 */
function ensureConfigDir() {
  try {
    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
  } catch (error) {
    console.error('创建配置目录失败:', error);
  }
}

/**
 * 加载上次保存的悬浮窗位置
 * @returns {{x: number, y: number} | null}
 */
function loadFloatingPosition() {
  try {
    if (fs.existsSync(POSITION_FILE)) {
      const data = fs.readFileSync(POSITION_FILE, 'utf8');
      const position = JSON.parse(data);
      
      // 验证位置是否在屏幕内
      const display = screen.getPrimaryDisplay();
      const { width, height } = display.workAreaSize;
      
      if (
        position.x >= 0 && 
        position.x < width - 320 &&
        position.y >= 0 && 
        position.y < height - 280
      ) {
        console.log('加载保存的悬浮窗位置:', position);
        return position;
      }
    }
  } catch (error) {
    console.error('加载悬浮窗位置失败:', error);
  }
  return null;
}

/**
 * 保存悬浮窗位置
 * @param {{x: number, y: number}} position
 */
function saveFloatingPosition(position) {
  try {
    ensureConfigDir();
    fs.writeFileSync(POSITION_FILE, JSON.stringify(position, null, 2));
    console.log('保存悬浮窗位置:', position);
  } catch (error) {
    console.error('保存悬浮窗位置失败:', error);
  }
}

/**
 * 获取默认悬浮窗位置（右下角）
 * @returns {{x: number, y: number}}
 */
function getDefaultPosition() {
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.workAreaSize;
  
  const WINDOW_WIDTH = 320;
  const WINDOW_HEIGHT = 280;
  const MARGIN = 20;
  
  return {
    x: width - WINDOW_WIDTH - MARGIN,
    y: height - WINDOW_HEIGHT - MARGIN,
  };
}

/**
 * 边缘吸附检测
 * @param {number} x - X坐标
 * @param {number} y - Y坐标  
 * @returns {{x: number, y: number, snapped: boolean}}
 */
function checkEdgeSnap(x, y) {
  const SNAP_THRESHOLD = 30;
  
  // 🆕 获取窗口当前所在的显示器（支持多显示器）
  const display = screen.getDisplayNearestPoint({ x, y });
  const { x: displayX, y: displayY, width, height } = display.workArea;
  
  const WINDOW_WIDTH = 320;
  const WINDOW_HEIGHT = 280;
  
  let newX = x;
  let newY = y;
  let snapped = false;
  
  // 🆕 相对于当前显示器的坐标
  const relativeX = x - displayX;
  const relativeY = y - displayY;
  
  // 左边缘吸附（相对于当前显示器）
  if (relativeX < SNAP_THRESHOLD) {
    newX = displayX;
    snapped = true;
  }
  // 右边缘吸附（相对于当前显示器）
  else if (width - (relativeX + WINDOW_WIDTH) < SNAP_THRESHOLD) {
    newX = displayX + width - WINDOW_WIDTH;
    snapped = true;
  }
  
  // 上边缘吸附（相对于当前显示器）
  if (relativeY < SNAP_THRESHOLD) {
    newY = displayY;
    snapped = true;
  }
  // 下边缘吸附（相对于当前显示器）
  else if (height - (relativeY + WINDOW_HEIGHT) < SNAP_THRESHOLD) {
    newY = displayY + height - WINDOW_HEIGHT;
    snapped = true;
  }
  
  return { x: newX, y: newY, snapped };
}

/**
 * 创建独立悬浮窗
 * @param {string} rendererURL - 渲染器开发服务器URL
 * @returns {BrowserWindow}
 */
function createFloatingWindow(rendererURL) {
  // 如果已存在，直接显示
  if (floatingWindow) {
    floatingWindow.show();
    floatingWindow.focus();
    return floatingWindow;
  }
  
  console.log('🚀 创建独立悬浮窗...');
  
  // 获取位置（优先使用保存的位置）
  const savedPosition = loadFloatingPosition();
  const position = savedPosition || getDefaultPosition();
  
  // 创建独立窗口
  floatingWindow = new BrowserWindow({
    width: 320,
    height: 280,
    x: position.x,
    y: position.y,
    
    // 窗口样式
    frame: false,              // 无边框
    transparent: true,         // 透明背景
    alwaysOnTop: true,        // 始终置顶（关键！）
    skipTaskbar: true,        // 不显示在任务栏
    resizable: false,         // 不可调整大小
    minimizable: false,       // 不可最小化
    maximizable: false,       // 不可最大化
    hasShadow: true,          // 显示阴影
    
    // 窗口行为
    show: false,              // 创建时不显示（准备好后显示）
    focusable: true,          // 可获得焦点
    
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      // 允许悬浮窗访问后端API
      webSecurity: true,
    }
  });
  
  // 判断是否开发环境
  const isDev = !require('electron').app.isPackaged;
  
  // 加载悬浮窗页面
  if (isDev) {
    // 开发环境：加载开发服务器
    floatingWindow.loadURL(`${rendererURL}/#/floating`);
    // 打开DevTools方便调试
    // floatingWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    // 生产环境：加载打包后的文件
    floatingWindow.loadFile(
      path.join(__dirname, 'renderer', 'dist', 'index.html'),
      { hash: '/floating' }
    );
  }
  
  // 窗口准备好后显示
  floatingWindow.once('ready-to-show', () => {
    console.log('✅ 悬浮窗准备完成，显示窗口');
    floatingWindow.show();
    floatingWindow.focus();
  });
  
  // 监听窗口移动，实现边缘吸附
  let moveTimer = null;
  floatingWindow.on('move', () => {
    if (moveTimer) clearTimeout(moveTimer);
    
    // 防抖：100ms后检查是否需要吸附
    moveTimer = setTimeout(() => {
      if (!floatingWindow || floatingWindow.isDestroyed()) return;
      
      const bounds = floatingWindow.getBounds();
      const result = checkEdgeSnap(bounds.x, bounds.y);
      
      if (result.snapped) {
        console.log('🧲 边缘吸附:', { from: { x: bounds.x, y: bounds.y }, to: { x: result.x, y: result.y } });
        floatingWindow.setBounds({
          x: result.x,
          y: result.y,
          width: 320,
          height: 280,
        });
      }
      
      // 保存位置
      saveFloatingPosition({ x: result.x, y: result.y });
    }, 100);
  });
  
  // 窗口关闭时清理
  floatingWindow.on('closed', () => {
    console.log('🔴 悬浮窗已关闭');
    if (moveTimer) clearTimeout(moveTimer);
    floatingWindow = null;
  });
  
  // 防止窗口失去焦点时隐藏（确保始终可见）
  floatingWindow.setAlwaysOnTop(true, 'screen-saver', 1);
  
  console.log('✅ 悬浮窗创建完成');
  return floatingWindow;
}

/**
 * 显示悬浮窗
 */
function showFloatingWindow() {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.show();
    floatingWindow.focus();
    console.log('✅ 显示悬浮窗');
  } else {
    console.warn('⚠️ 悬浮窗不存在，请先创建');
  }
}

/**
 * 隐藏悬浮窗
 */
function hideFloatingWindow() {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.hide();
    console.log('🔴 隐藏悬浮窗');
  }
}

/**
 * 关闭悬浮窗
 */
function closeFloatingWindow() {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.close();
    floatingWindow = null;
    console.log('🔴 关闭悬浮窗');
  }
}

/**
 * 发送数据到悬浮窗
 * @param {string} channel - IPC通道名
 * @param {any} data - 数据
 */
function sendDataToFloating(channel, data) {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.webContents.send(channel, data);
  }
}

/**
 * 获取悬浮窗实例
 * @returns {BrowserWindow | null}
 */
function getFloatingWindow() {
  return floatingWindow;
}

/**
 * 检查悬浮窗是否存在且可见
 * @returns {boolean}
 */
function isFloatingWindowVisible() {
  return floatingWindow && !floatingWindow.isDestroyed() && floatingWindow.isVisible();
}

module.exports = {
  createFloatingWindow,
  showFloatingWindow,
  hideFloatingWindow,
  closeFloatingWindow,
  sendDataToFloating,
  getFloatingWindow,
  isFloatingWindowVisible,
};

