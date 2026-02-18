const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// 🆕 导入悬浮窗管理模块
const {
  createFloatingWindow,
  showFloatingWindow,
  hideFloatingWindow,
  closeFloatingWindow,
  sendDataToFloating,
  isFloatingWindowVisible,
  toggleAlwaysOnTop,      // 🆕 切换置顶状态
  getAlwaysOnTopState     // 🆕 获取置顶状态
} = require('./floatingWindow');

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
// 🔧 硬编码前端端口 10200（避开 Windows 保留端口范围 10017-10116）
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:10200';

// 保持对窗口对象的全局引用
let mainWindow;

// 日志目录
const logsDir = path.join(__dirname, '..', 'logs');
try { if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true }); } catch {}

// 后端服务配置
const BACKEND_PORT = 11111;
const BACKEND_HOST = '127.0.0.1';
let backendProcess = null;

// 获取后端可执行文件路径
function getBackendPath() {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, 'backend', 'timao_backend_service.exe');
    } else {
        // 开发环境使用 Python
        const venvPython = path.join(__dirname, '..', '..', '.venv', 'Scripts', 'python.exe');
        if (fs.existsSync(venvPython)) {
            return venvPython;
        }
        return 'python';
    }
}

// 等待服务健康检查
async function waitForHealthCheck(url, maxAttempts = 60, interval = 2000) {
    const http = require('http');
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const check = () => {
            attempts++;
            const req = http.get(url, (res) => {
                if (res.statusCode === 200) {
                    resolve(true);
                } else {
                    if (attempts < maxAttempts) {
                        setTimeout(check, interval);
                    } else {
                        resolve(false);
                    }
                }
            });
            req.on('error', () => {
                if (attempts < maxAttempts) {
                    setTimeout(check, interval);
                } else {
                    resolve(false);
                }
            });
            req.setTimeout(5000, () => {
                req.destroy();
                if (attempts < maxAttempts) {
                    setTimeout(check, interval);
                } else {
                    resolve(false);
                }
            });
        };
        check();
    });
}

// 启动后端服务
async function startBackend() {
    if (backendProcess) {
        console.log('[electron] 后端服务已在运行中');
        return true;
    }

    const backendPath = getBackendPath();
    console.log(`[electron] 后端服务路径: ${backendPath}`);

    // 检查可执行文件是否存在
    if (app.isPackaged && !fs.existsSync(backendPath)) {
        console.error('[electron] 后端可执行文件不存在:', backendPath);
        return false;
    }

    try {
        const backendDir = app.isPackaged
            ? path.dirname(backendPath)
            : path.join(__dirname, '..', '..');

        console.log('[electron] 启动后端服务...');

        const spawnOptions = {
            cwd: backendDir,
            stdio: ['ignore', 'pipe', 'pipe'],
            detached: false,
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
                BACKEND_PORT: BACKEND_PORT.toString()
            }
        };

        if (app.isPackaged) {
            // 生产环境：使用打包的可执行文件
            backendProcess = spawn(backendPath, [], spawnOptions);
        } else {
            // 开发环境：使用 Python 运行 uvicorn
            backendProcess = spawn(backendPath, [
                '-m', 'uvicorn', 'app.main:app',
                '--host', BACKEND_HOST,
                '--port', BACKEND_PORT.toString()
            ], spawnOptions);
        }

        // 监听输出
        if (backendProcess.stdout) {
            backendProcess.stdout.on('data', (data) => {
                console.log(`[backend] ${data.toString().trim()}`);
            });
        }

        if (backendProcess.stderr) {
            backendProcess.stderr.on('data', (data) => {
                console.error(`[backend] ${data.toString().trim()}`);
            });
        }

        // 监听退出
        backendProcess.on('exit', (code, signal) => {
            console.log(`[electron] 后端服务已退出 (code=${code}, signal=${signal})`);
            backendProcess = null;
        });

        backendProcess.on('error', (err) => {
            console.error('[electron] 后端服务启动失败:', err);
            backendProcess = null;
        });

        // 等待健康检查
        console.log('[electron] 等待后端服务启动...');
        const ready = await waitForHealthCheck(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`);

        if (ready) {
            console.log('[electron] 后端服务启动成功');
            return true;
        } else {
            console.warn('[electron] 后端服务健康检查未通过');
            return false;
        }

    } catch (error) {
        console.error('[electron] 启动后端服务失败:', error);
        return false;
    }
}

// 停止后端服务
function stopBackend() {
    if (backendProcess) {
        console.log('[electron] 正在停止后端服务...');

        try {
            if (process.platform === 'win32') {
                spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
            } else {
                backendProcess.kill('SIGTERM');
            }

            // 设置超时强制终止
            setTimeout(() => {
                if (backendProcess && !backendProcess.killed) {
                    console.warn('[electron] 强制终止后端服务');
                    backendProcess.kill('SIGKILL');
                }
            }, 5000);

        } catch (error) {
            console.error('[electron] 停止后端服务失败:', error);
        }

        backendProcess = null;
    }
}

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
    
    // 关闭悬浮窗
    closeFloatingWindow();
    
    // 停止后端服务
    stopBackend();
    
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
    // 启动后端服务（仅在生产环境，打包后）
    if (app.isPackaged) {
        console.log('[electron] 检测到打包环境，尝试启动后端服务...');
        const backendStarted = await startBackend();
        if (!backendStarted) {
            console.warn('[electron] 后端服务启动失败，应用将继续运行但部分功能可能不可用');
        }
    } else {
        console.log('[electron] 开发模式，跳过后端服务启动（请手动启动后端）');
    }
    
    // 启动 Python 转写服务（如果可用）
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
    
    // 后端服务状态
    ipcMain.handle('get-backend-status', async () => {
        return {
            running: backendProcess !== null && !backendProcess.killed,
            port: BACKEND_PORT,
            host: BACKEND_HOST,
            url: `http://${BACKEND_HOST}:${BACKEND_PORT}`
        };
    });
    
    // 启动后端服务
    ipcMain.handle('start-backend', async () => {
        const success = await startBackend();
        return { success };
    });
    
    // 停止后端服务
    ipcMain.handle('stop-backend', async () => {
        stopBackend();
        return { success: true };
    });
    
    // ========== 🆕 悬浮窗相关IPC处理器 ==========
    
    /**
     * 创建并显示独立悬浮窗
     * 主窗口点击"开始转写"时调用
     */
    ipcMain.handle('show-floating-window', async () => {
        try {
            console.log('📱 [IPC] 收到显示悬浮窗请求');
            const win = createFloatingWindow(rendererDevServerURL);
            return { success: true };
        } catch (error) {
            console.error('❌ [IPC] 显示悬浮窗失败:', error);
            return { success: false, error: error.message };
        }
    });
    
    /**
     * 隐藏悬浮窗
     */
    ipcMain.handle('hide-floating-window', async () => {
        try {
            console.log('🔴 [IPC] 收到隐藏悬浮窗请求');
            hideFloatingWindow();
            return { success: true };
        } catch (error) {
            console.error('❌ [IPC] 隐藏悬浮窗失败:', error);
            return { success: false, error: error.message };
        }
    });
    
    /**
     * 关闭悬浮窗
     */
    ipcMain.handle('close-floating-window', async () => {
        try {
            console.log('🔴 [IPC] 收到关闭悬浮窗请求');
            closeFloatingWindow();
            return { success: true };
        } catch (error) {
            console.error('❌ [IPC] 关闭悬浮窗失败:', error);
            return { success: false, error: error.message };
        }
    });
    
    /**
     * 推送数据到悬浮窗
     * 主窗口实时调用，将WebSocket/SSE数据推送到悬浮窗
     */
    ipcMain.on('floating-update-data', (event, data) => {
        // console.log('📡 [IPC] 推送数据到悬浮窗');
        sendDataToFloating('floating-data', data);
    });
    
    /**
     * 检查悬浮窗是否可见
     */
    ipcMain.handle('is-floating-window-visible', async () => {
        return isFloatingWindowVisible();
    });
    
    /**
     * 🆕 切换悬浮窗置顶状态
     */
    ipcMain.handle('toggle-floating-always-on-top', async () => {
        try {
            console.log('📌 [IPC] 收到切换置顶状态请求');
            const newState = toggleAlwaysOnTop();
            return { success: true, alwaysOnTop: newState };
        } catch (error) {
            console.error('❌ 切换置顶状态失败:', error);
            return { success: false, error: error.message };
        }
    });
    
    /**
     * 🆕 获取悬浮窗置顶状态
     */
    ipcMain.handle('get-floating-always-on-top', async () => {
        return getAlwaysOnTopState();
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
