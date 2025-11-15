const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');

// 开发环境下跳过SSL证书验证，解决X509_V_FLAG_NOTIFY_POLICY错误
if (process.env.NODE_ENV !== 'production') {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
}

// Ensure packaged app ships with a working AI backend without manual env setup.
const defaultAiEnv = {
    AI_SERVICE: 'qwen',
    AI_BASE_URL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    AI_MODEL: 'qwen3-max',
    AI_API_KEY: 'sk-92045f0a33984350925ce3ccffb3489e',
    OPENAI_API_KEY: 'sk-92045f0a33984350925ce3ccffb3489e',
    OPENAI_BASE_URL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    OPENAI_MODEL: 'qwen3-max',
};
for (const [key, value] of Object.entries(defaultAiEnv)) {
    if (!process.env[key]) {
        process.env[key] = value;
    }
}

const isDev = !app.isPackaged;
// 🔧 硬编码前端端口 10065（演示测试）
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:10065';

// 保持对窗口对象的全局引用
let mainWindow;

// 日志目录
const logsDir = path.join(__dirname, '..', 'logs');
try { if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true }); } catch {}

/**
 * 解析生产环境的 index.html 路径
 */
function resolveProductionIndex() {
    const distIndex = path.join(__dirname, 'renderer', 'dist', 'index.html');
    const legacyIndex = path.join(__dirname, 'renderer', 'index.html');
    if (fs.existsSync(distIndex)) {
        return distIndex;
    }
    if (fs.existsSync(legacyIndex)) {
        return legacyIndex;
    }
    return path.join(__dirname, 'renderer', 'voice_transcription.html');
}

/**
 * 创建主窗口
 */
function createWindow() {
    // 查找应用图标
    const iconCandidates = [
        path.join(__dirname, 'renderer', 'src', 'assets', 'app.png'),
        path.join(__dirname, 'renderer', 'src', 'assets', 'app.ico'),
        path.join(__dirname, 'renderer', 'src', 'assets', 'logo.png'),
        path.join(__dirname, 'renderer', 'src', 'assets', 'talkingcat.png'),
        path.join(__dirname, 'renderer', 'src', 'assets', 'icon.png'),
        path.join(__dirname, 'renderer', 'src', 'assets', 'icon.ico'),
    ];
    const iconPath = iconCandidates.find(p => {
        try { return fs.existsSync(p); } catch { return false; }
    });

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        title: '提猫直播助手 • TalkingCat',
        ...(iconPath ? { icon: iconPath } : {}),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: false,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    // 加载页面
    if (isDev) {
        mainWindow.loadURL(rendererDevServerURL);
        mainWindow.webContents.openDevTools();
    } else {
        const indexPath = resolveProductionIndex();
        mainWindow.loadFile(indexPath);
    }

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

/**
 * 应用退出前清理资源
 */
app.on('before-quit', async (event) => {
    console.log('[electron] App is about to quit. Cleaning up resources...');
    
    // 通知所有渲染进程清理资源
    const allWindows = BrowserWindow.getAllWindows();
    if (allWindows.length > 0) {
        console.log(`[electron] Notifying ${allWindows.length} window(s) to cleanup...`);
        
        allWindows.forEach((win) => {
            if (!win.isDestroyed()) {
                try {
                    win.webContents.send('app-cleanup-request');
                    console.log('[electron] Cleanup signal sent to window');
                } catch (error) {
                    console.error('[electron] Failed to send cleanup signal:', error);
                }
            }
        });
        
        // 等待渲染进程完成清理
        console.log('[electron] Waiting for renderer cleanup (500ms)...');
        await new Promise(resolve => setTimeout(resolve, 500));
        console.log('[electron] Renderer cleanup wait completed');
    }
    
    console.log('[electron] Cleanup completed');
});

/**
 * 当所有窗口都关闭时退出
 */
app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

/**
 * 在 macOS 上激活时重新创建窗口
 */
app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

/**
 * 应用准备就绪时创建窗口
 */
app.whenReady().then(async () => {
    // 🆕 启动 Python 转写服务（如果可用）
    try {
        // 动态加载 Python 转写服务（TypeScript 编译后的 JS）
        const pythonTranscriberPath = path.join(__dirname, 'services', 'pythonTranscriber.js');
        if (fs.existsSync(pythonTranscriberPath)) {
            console.log('[electron] 加载 Python 转写服务...');
            const { pythonTranscriber } = require('./services/pythonTranscriber.js');
            
            // 启动 Python 转写服务
            console.log('[electron] 启动 Python 转写服务...');
            await pythonTranscriber.start();
            console.log('[electron] ✅ Python 转写服务已启动');
            
            // 注册退出时停止服务
            app.on('will-quit', () => {
                console.log('[electron] 停止 Python 转写服务...');
                pythonTranscriber.stop();
            });
        } else {
            console.log('[electron] ⚠️ Python 转写服务未找到，将使用服务器端转写');
        }
    } catch (error) {
        console.error('[electron] ❌ Python 转写服务启动失败:', error);
        console.log('[electron] 将回退到服务器端转写模式');
    }
    
    createWindow();
    
    // 注册 IPC 处理器
    ipcMain.handle('open-external-link', async (event, url) => {
        shell.openExternal(url);
    });
    
    ipcMain.handle('get-app-version', () => app.getVersion());
    
    ipcMain.handle('get-app-path', () => app.getAppPath());
    
    ipcMain.handle('get-user-data-path', () => app.getPath('userData'));
    
    ipcMain.handle('get-logs-path', () => logsDir);
    
    ipcMain.handle('get-is-dev', () => isDev);
    
    ipcMain.handle('app-quit', () => {
        app.quit();
    });
    
    ipcMain.handle('open-path', async (event, targetPath) => {
        try {
            shell.openPath(targetPath);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });
    
    ipcMain.handle('open-logs', async () => {
        try {
            shell.openPath(logsDir);
            return { success: true, path: logsDir };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });
    
    ipcMain.handle('get-app-info', async () => {
        return {
            version: app.getVersion(),
            name: app.getName(),
            path: app.getAppPath(),
            userDataPath: app.getPath('userData'),
            logsPath: logsDir,
            isDev: isDev,
            platform: process.platform
        };
    });
    
    console.log('[electron] Application initialized successfully');
    console.log(`[electron] Version: ${app.getVersion()}`);
    console.log(`[electron] Platform: ${process.platform}`);
    console.log(`[electron] Development mode: ${isDev}`);
});

// 防止证书错误
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    if (isDev) {
        event.preventDefault();
        callback(true);
    } else {
        callback(false);
    }
});

console.log('提猫直播助手 Electron 主进程已启动');
console.log(`Electron版本: ${process.versions.electron}`);
console.log(`Node版本: ${process.versions.node}`);
console.log(`Chrome版本: ${process.versions.chrome}`);
