const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn, spawnSync } = require('child_process');
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
const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:10030';

// 保持对窗口对象的全局引用，如果不这样做，窗口会在JavaScript对象被垃圾回收时自动关闭
let mainWindow;

// Child process for backend API (FastAPI via uvicorn)
let fastAPIProcess = null;
const logsDir = path.join(__dirname, '..', 'logs');
try { if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true }); } catch {}
const uvicornLogPath = path.join(logsDir, 'uvicorn.log');

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
            webSecurity: false,  // 允许访问本地 API
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
            if (fastAPIProcess) {
                return resolve({ success: true, message: 'FastAPI already running' });
            }

            // If port 9019 is already in use, check if it's our FastAPI service
            const available = await isPortAvailable(9019);
            if (!available) {
                console.log('[electron] Port 9019 is already in use, checking if it\'s our FastAPI service...');
                
                // Try to connect to the health endpoint to verify it's our service
                // Add retry mechanism for health check as the service might be starting up
                const maxRetries = 5;
                const retryDelay = 1000; // 1 second
                
                for (let attempt = 1; attempt <= maxRetries; attempt++) {
                    try {
                        console.log(`[electron] Health check attempt ${attempt}/${maxRetries}...`);
                        
                        // Use a more reliable HTTP request method for Node.js
                        const http = require('http');
                        const healthCheckPromise = new Promise((resolveHealth, rejectHealth) => {
                            const req = http.get('http://127.0.0.1:9019/health', { timeout: 2000 }, (res) => {
                                let data = '';
                                res.on('data', chunk => data += chunk);
                                res.on('end', () => {
                                    try {
                                        const response = JSON.parse(data);
                                        if (res.statusCode === 200 && response.status === 'healthy') {
                                            resolveHealth(true);
                                        } else {
                                            rejectHealth(new Error('Service not healthy'));
                                        }
                                    } catch (e) {
                                        rejectHealth(e);
                                    }
                                });
                            });
                            
                            req.on('error', rejectHealth);
                            req.on('timeout', () => {
                                req.destroy();
                                rejectHealth(new Error('Health check timeout'));
                            });
                        });
                        
                        await healthCheckPromise;
                        console.log('[electron] FastAPI service is already running and healthy.');
                        return resolve({ success: true, message: 'FastAPI already running (external)' });
                        
                    } catch (error) {
                        console.log(`[electron] Health check attempt ${attempt} failed: ${error.message}`);
                        
                        if (attempt === maxRetries) {
                            console.log(`[electron] All health check attempts failed. Port 9019 occupied but service not responding, attempting to start anyway...`);
                            // If all health checks fail, the port might be occupied by a dead process
                            // We'll try to start anyway and let uvicorn handle the error
                            break;
                        } else {
                            // Wait before next retry
                            await new Promise(resolve => setTimeout(resolve, retryDelay));
                        }
                    }
                }
            }

            // Use uvicorn to run server.app.main:app on 127.0.0.1:9019 (default FastAPI port for Electron)
            // Spawn with project root as cwd so Python can import local packages
            // 准备后端运行环境变量：默认使用本地SQLite并禁用Redis，确保无外部依赖即可运行
            const userDataDir = app.getPath('userData');
            const sqliteDir = path.join(userDataDir, 'data');
            try { fs.mkdirSync(sqliteDir, { recursive: true }); } catch {}
            const sqlitePath = path.join(sqliteDir, 'app.db');

            const envForApi = {
                ...process.env,
                // 强制优先走SQLite，若外部已设置DB_TYPE/DATABASE_PATH则保留外部配置
                DB_TYPE: process.env.DB_TYPE || 'sqlite',
                DATABASE_PATH: process.env.DATABASE_PATH || sqlitePath,
                // 没有Redis服务的本地演示默认关闭Redis
                REDIS_ENABLED: process.env.REDIS_ENABLED || 'false',
                // Force UTF-8 so emojis/Chinese don't garble in Windows pipes
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
            };

            fastAPIProcess = spawn(
                process.platform === 'win32' ? 'python' : 'python3',
                ['-m', 'uvicorn', 'server.app.main:app', '--host', '127.0.0.1', '--port', '9019'],
                {
                    cwd: path.join(__dirname, '..'),
                    env: envForApi,
                }
            );

            fastAPIProcess.stdout.on('data', (data) => {
                const text = data.toString();
                console.log(`[uvicorn] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-log', text);
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
            });

            fastAPIProcess.stderr.on('data', (data) => {
                const text = data.toString();
                console.error(`[uvicorn] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-error', text);
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
            });

            fastAPIProcess.on('close', (code) => {
                console.log(`FastAPI process exited: ${code}`);
                if (mainWindow) mainWindow.webContents.send('service-stopped', code);
                fastAPIProcess = null;
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

// IPC处理程序 - 检查服务健康状态
ipcMain.handle('check-service-health', async () => {
    try {
        const response = await fetch('http://127.0.0.1:9019/health');
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

// IPC处理程序 - 获取服务URL
ipcMain.handle('get-service-url', async () => {
    return 'http://127.0.0.1:9019';
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
