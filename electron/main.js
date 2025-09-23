const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isDev = !app.isPackaged;
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:5173';

// 保持对窗口对象的全局引用，如果不这样做，窗口会在JavaScript对象被垃圾回收时自动关闭
let mainWindow;

// Child process for backend API (FastAPI via uvicorn)
let apiProcess = null;

// Legacy: test flask server (kept for voice_transcription.html fallback)
let legacyFlaskProcess = null;

function resolveProductionIndex() {
    const distIndex = path.join(__dirname, 'renderer', 'dist', 'index.html');
    const legacyIndex = path.join(__dirname, 'renderer', 'index.html');
    if (fs.existsSync(distIndex)) {
        return distIndex;
    }
    if (fs.existsSync(legacyIndex)) {
        return legacyIndex;
    }
    // 回退到旧页面，避免打包失败
    return path.join(__dirname, 'renderer', 'voice_transcription.html');
}

function createWindow() {
    // 创建浏览器窗口
    // Prefer a branded window icon when available
    const iconCandidates = [
        path.join(__dirname, '..', 'icons', 'app.png'),
        path.join(__dirname, '..', 'icons', 'app.ico'),
        path.join(__dirname, '..', 'icons', 'logo.png'),
        path.join(__dirname, '..', 'icons', 'logo.jpg'),
        path.join(__dirname, '..', 'icons', 'talkingcat.png'),
        path.join(__dirname, '..', 'icons', 'talkingcat.jpg'),
        // also allow using packaged build icons
        path.join(__dirname, '..', 'assets', 'icon.png'),
        path.join(__dirname, '..', 'assets', 'icon.ico'),
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
            preload: path.join(__dirname, 'preload.js')
        }
    });

    if (isDev) {
        mainWindow.loadURL(rendererDevServerURL);
    } else {
        mainWindow.loadFile(resolveProductionIndex());
    }
    // Ensure title reflects brand even if page overrides
    mainWindow.setTitle('提猫直播助手 • TalkingCat');

    // 当窗口关闭时触发
    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

// -------------------------------
// Backend API (FastAPI) launcher
// -------------------------------
function startFastAPI() {
    return new Promise(async (resolve, reject) => {
        try {
            if (apiProcess) {
                return resolve({ success: true, message: 'FastAPI already running' });
            }

            // If port 8007 is already in use (e.g., user started uvicorn manually),
            // do not spawn another process to avoid EADDRINUSE and noisy logs.
            const available = await isPortAvailable(8007);
            if (!available) {
                console.log('[electron] Port 8007 is already in use; assuming FastAPI is running.');
                return resolve({ success: true, message: 'FastAPI already running (external)' });
            }

            // Use uvicorn to run server.app.main:app on 127.0.0.1:8007 (changed from 8006)
            // Spawn with project root as cwd so Python can import local packages
            apiProcess = spawn(
                process.platform === 'win32' ? 'python' : 'python3',
                ['-m', 'uvicorn', 'server.app.main:app', '--host', '127.0.0.1', '--port', '8007'],
                {
                    cwd: path.join(__dirname, '..'),
                    env: {
                        ...process.env,
                        // Force UTF-8 so emojis/Chinese don't garble in Windows pipes
                        PYTHONIOENCODING: 'utf-8',
                        PYTHONUTF8: '1',
                    },
                }
            );

            apiProcess.stdout.on('data', (data) => {
                const text = data.toString();
                console.log(`[uvicorn] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-log', text);
            });

            apiProcess.stderr.on('data', (data) => {
                const text = data.toString();
                console.error(`[uvicorn] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-error', text);
            });

            apiProcess.on('close', (code) => {
                console.log(`FastAPI process exited: ${code}`);
                if (mainWindow) mainWindow.webContents.send('service-stopped', code);
                apiProcess = null;
            });

            // Give uvicorn a brief moment to boot
            setTimeout(() => resolve({ success: true, message: 'FastAPI started' }), 1500);
        } catch (err) {
            console.error('Failed to start FastAPI:', err);
            reject(err);
        }
    });
}

async function stopFastAPI() {
    if (!apiProcess) return { success: true, message: 'FastAPI not running' };
    try {
        apiProcess.kill();
        apiProcess = null;
        return { success: true, message: 'FastAPI stopped' };
    } catch (err) {
        console.error('Failed to stop FastAPI:', err);
        return { success: false, message: String(err) };
    }
}

// 控制是否由 Electron 自启本地 FastAPI（云端部署时可关闭）
const shouldStartApi = (process.env.ELECTRON_START_API || 'true') !== 'false';

// 当Electron完成初始化并准备创建浏览器窗口时调用此方法
app.on('ready', async () => {
    // Create window first so logs can be delivered
    createWindow();
    // Auto-start FastAPI so renderer can call /api/* endpoints (incl. Douyin)
    if (shouldStartApi) {
        try {
            await startFastAPI();
        } catch (e) {
            console.error('Auto start FastAPI failed:', e);
        }
    } else {
        console.log('[electron] Skip starting local FastAPI due to ELECTRON_START_API=false');
    }
});

// 当所有窗口都关闭时退出
app.on('window-all-closed', async function () {
    if (process.platform !== 'darwin') {
        // Stop backends
        try { await stopFastAPI(); } catch (e) {}
        if (legacyFlaskProcess) {
            try { legacyFlaskProcess.kill(); } catch (e) {}
            legacyFlaskProcess = null;
        }
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

// IPC处理程序 - 启动FastAPI服务（提供给渲染端按需调用）
ipcMain.handle('start-service', async () => {
    return startFastAPI();
});

// IPC处理程序 - 停止FastAPI服务
ipcMain.handle('stop-service', async () => {
    return stopFastAPI();
});

// IPC处理程序 - 检查服务状态
ipcMain.handle('check-service-status', async () => {
    return {
        running: apiProcess !== null,
        pid: apiProcess ? apiProcess.pid : null
    };
});

// -------------------------------
// Helpers
// -------------------------------
function isPortAvailable(port) {
    return new Promise((resolve) => {
        const net = require('net');
        const tester = net.createServer()
            .once('error', (err) => {
                if (err.code === 'EADDRINUSE') resolve(false);
                else resolve(false);
            })
            .once('listening', () => {
                tester.close(() => resolve(true));
            })
            .listen(port, '127.0.0.1');
    });
}
