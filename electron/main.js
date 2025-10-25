const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

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
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:30013';

// 保持对窗口对象的全局引用，如果不这样做，窗口会在JavaScript对象被垃圾回收时自动关闭
let mainWindow;

// Child process for backend API (FastAPI via uvicorn)
let apiProcess = null;
const logsDir = path.join(__dirname, '..', 'logs');
try { if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true }); } catch {}
const uvicornLogPath = path.join(logsDir, 'uvicorn.log');

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
            webSecurity: true,
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

            // If port 10090 is already in use (e.g., user started uvicorn manually),
            // do not spawn another process to avoid EADDRINUSE and noisy logs.
            const available = await isPortAvailable(10090);
            if (!available) {
                console.log('[electron] Port 10090 is already in use; assuming FastAPI is running.');
                return resolve({ success: true, message: 'FastAPI already running (external)' });
            }

            // Use uvicorn to run server.app.main:app on 127.0.0.1:10090 (default FastAPI port for Electron)
            // Spawn with project root as cwd so Python can import local packages
            apiProcess = spawn(
                process.platform === 'win32' ? 'python' : 'python3',
                ['-m', 'uvicorn', 'server.app.main:app', '--host', '127.0.0.1', '--port', '10090'],
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
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
            });

            apiProcess.stderr.on('data', (data) => {
                const text = data.toString();
                console.error(`[uvicorn] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-error', text);
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
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

async function ensureBackendReady() {
    if (!shouldStartApi) return;
    try {
        await startFastAPI();
    } catch (e) {
        console.error('Failed to auto start FastAPI:', e);
    }
}

// 当Electron完成初始化并准备创建浏览器窗口时调用此方法
app.on('ready', async () => {
    await ensureBackendReady();
    createWindow();
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

// IPC - Open a path in OS file manager
ipcMain.handle('open-path', async (_event, targetPath) => {
    try {
        if (!targetPath) return { success: false, message: 'path required' };
        const res = await shell.openPath(String(targetPath));
        if (res) return { success: false, message: res };
        return { success: true };
    } catch (e) {
        return { success: false, message: String(e) };
    }
});

// IPC - Runtime info
ipcMain.handle('runtime-info', async () => {
    try {
        const info = {
            node: process.versions.node,
            chrome: process.versions.chrome,
            electron: process.versions.electron,
            platform: process.platform,
            arch: process.arch,
            env: {
                LIVE_FORCE_DEVICE: process.env.LIVE_FORCE_DEVICE || null,
                FORCE_TORCH_MODE: process.env.FORCE_TORCH_MODE || null,
            }
        };
        try {
            const pyCmd = 'import torch, json;print(json.dumps({"version": getattr(torch, "__version__", "unknown"), "cuda": torch.cuda.is_available() if hasattr(torch, "cuda") else False}))';
            const result = spawnSync(process.platform === 'win32' ? 'python' : 'python3', ['-c', pyCmd], { timeout: 5000 });
            if (result.status === 0) {
                const parsed = JSON.parse(result.stdout.toString() || '{}');
                info.torch = parsed;
            } else {
                info.torch = { error: result.stderr?.toString() || 'unknown error' };
            }
        } catch (err) {
            info.torch = { error: String(err) };
        }
        return { success: true, info };
    } catch (e) {
        return { success: false, message: String(e) };
    }
});

ipcMain.handle('run-prepare-torch', async () => {
    return new Promise((resolve) => {
        const proc = spawn(process.platform === 'win32' ? 'python' : 'python3', ['tools/prepare_torch.py'], {
            cwd: path.join(__dirname, '..'),
            env: { ...process.env, PYTHONENSUREPIP: '1' },
        });
        let output = '';
        proc.stdout.on('data', (data) => { output += data.toString(); });
        proc.stderr.on('data', (data) => { output += data.toString(); });
        proc.on('close', (code) => {
            resolve({ success: code === 0, code, output });
        });
    });
});

ipcMain.handle('set-runtime-device', async (_event, device) => {
    try {
        const value = (device || '').trim();
        if (value) process.env.LIVE_FORCE_DEVICE = value;
        else delete process.env.LIVE_FORCE_DEVICE;
        return { success: true, device: value || null };
    } catch (e) {
        return { success: false, message: String(e) };
    }
});

// IPC - Quit app
ipcMain.handle('app-quit', async () => {
    try { app.quit(); return { success: true }; }
    catch (e) { return { success: false, message: String(e) }; }
});

// IPC - Open logs directory
ipcMain.handle('open-logs', async () => {
    try {
        const res = await shell.openPath(logsDir);
        if (res) return { success: false, message: res };
        return { success: true };
    } catch (e) {
        return { success: false, message: String(e) };
    }
});

// -------------------------------
// Helpers
// -------------------------------
// IPC handler for app info
ipcMain.handle('get-app-info', async () => {
    const packagePath = path.join(__dirname, 'package.json');
    try {
        const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
        return {
            name: packageData.name,
            version: packageData.version,
            description: packageData.description
        };
    } catch (error) {
        console.error('Failed to read package.json:', error);
        return {
            name: 'ast-voice-transcription-app',
            version: '1.0.0',
            description: '语音转录服务桌面应用'
        };
    }
});

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
