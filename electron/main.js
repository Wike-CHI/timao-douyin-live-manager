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

// 统一后端服务管理
let backendServiceProcess = null;
let serviceManager = null;
const logsDir = path.join(__dirname, '..', 'logs');
try { if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir, { recursive: true }); } catch {}
const uvicornLogPath = path.join(logsDir, 'uvicorn.log');

// 服务配置
const serviceConfig = {
    main: {
        name: 'FastAPI',
        port: process.env.BACKEND_PORT || '9019',
        healthPath: '/health'
    },
    streamcap: {
        name: 'StreamCap',
        port: process.env.STREAMCAP_PORT || '9020',
        healthPath: '/health'
    },
    douyin: {
        name: 'DouyinLive',
        port: process.env.DOUYIN_PORT || '9021',
        healthPath: '/health'
    }
};

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
// 启动统一后端服务
function startBackendServices() {
    return new Promise(async (resolve, reject) => {
        try {
            if (backendServiceProcess) {
                console.log('[electron] Backend services are already running.');
                return resolve({ success: true, message: 'Backend services already running' });
            }

            // 准备后端运行环境变量：默认使用本地SQLite并禁用Redis，确保无外部依赖即可运行
            const userDataDir = app.getPath('userData');
            const sqliteDir = path.join(userDataDir, 'data');
            try { fs.mkdirSync(sqliteDir, { recursive: true }); } catch {}
            const sqlitePath = path.join(sqliteDir, 'app.db');

            // 检查是否有服务已在运行
            const runningServices = await checkExistingServices();
            if (runningServices.length > 0) {
                console.log(`[electron] Found running services: ${runningServices.join(', ')}`);
                return resolve({ success: true, message: 'Services already running externally' });
            }

            console.log('[electron] Starting unified backend services...');
            
            const envForServices = {
                ...process.env,
                // 数据库配置
                DB_TYPE: process.env.DB_TYPE || 'sqlite',
                DATABASE_PATH: process.env.DATABASE_PATH || sqlitePath,
                REDIS_ENABLED: process.env.REDIS_ENABLED || 'false',
                // 编码配置
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
                // 服务端口配置
                BACKEND_PORT: serviceConfig.main.port,
                STREAMCAP_PORT: serviceConfig.streamcap.port,
                DOUYIN_PORT: serviceConfig.douyin.port,
                // 前端环境变量
                VITE_FASTAPI_URL: `http://127.0.0.1:${serviceConfig.main.port}`,
                VITE_STREAMCAP_URL: `http://127.0.0.1:${serviceConfig.streamcap.port}`,
                VITE_DOUYIN_URL: `http://127.0.0.1:${serviceConfig.douyin.port}`
            };

            // 启动统一服务启动器
            backendServiceProcess = spawn(
                process.platform === 'win32' ? 'python' : 'python3',
                ['service_launcher.py'],
                {
                    cwd: path.join(__dirname, '..'),
                    env: envForServices,
                }
            );

            backendServiceProcess.stdout.on('data', (data) => {
                const text = data.toString();
                console.log(`[service-manager] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-log', text);
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
            });

            backendServiceProcess.stderr.on('data', (data) => {
                const text = data.toString();
                console.error(`[service-manager] ${text}`.trim());
                if (mainWindow) mainWindow.webContents.send('service-error', text);
                try { fs.appendFileSync(uvicornLogPath, text); } catch {}
            });

            backendServiceProcess.on('close', (code) => {
                console.log(`Backend services process exited: ${code}`);
                if (mainWindow) mainWindow.webContents.send('service-stopped', code);
                backendServiceProcess = null;
            });

            // 等待服务启动并进行健康检查
            await waitForServicesReady();
            resolve({ success: true, message: 'Backend services started' });
            
        } catch (err) {
            console.error('Failed to start backend services:', err);
            reject(err);
        }
    });
}

// 检查现有服务
async function checkExistingServices() {
    const runningServices = [];
    
    for (const [key, config] of Object.entries(serviceConfig)) {
        try {
            const response = await fetch(`http://127.0.0.1:${config.port}${config.healthPath}`, {
                method: 'GET',
                timeout: 2000
            });
            
            if (response.ok) {
                runningServices.push(config.name);
                console.log(`[electron] ${config.name} service is already running on port ${config.port}`);
            }
        } catch (error) {
            // 服务未运行，继续检查其他服务
        }
    }
    
    return runningServices;
}

// 等待服务就绪
async function waitForServicesReady() {
    const maxRetries = 30;
    const retryDelay = 1000;
    
    console.log('[electron] Waiting for services to be ready...');
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            // 检查主服务（FastAPI）
            const response = await fetch(`http://127.0.0.1:${serviceConfig.main.port}/health`, {
                method: 'GET',
                timeout: 3000
            });
            
            if (response.ok) {
                console.log('[electron] Main service is ready!');
                return true;
            }
        } catch (error) {
            if (attempt === maxRetries) {
                throw new Error(`Services failed to start after ${maxRetries} attempts`);
            }
            
            console.log(`[electron] Waiting for services... attempt ${attempt}/${maxRetries}`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }
}

// 停止后端服务
async function stopBackendServices() {
    if (!backendServiceProcess) {
        return { success: true, message: 'Backend services not running' };
    }
    
    try {
        console.log('[electron] Stopping backend services...');
        
        // 发送终止信号
        if (process.platform === 'win32') {
            // Windows下使用taskkill强制终止
            spawn('taskkill', ['/pid', backendServiceProcess.pid, '/f', '/t']);
        } else {
            // Unix系统使用SIGTERM
            backendServiceProcess.kill('SIGTERM');
        }
        
        // 等待进程结束
        await new Promise((resolve) => {
            const timeout = setTimeout(() => {
                if (backendServiceProcess) {
                    backendServiceProcess.kill('SIGKILL');
                }
                resolve();
            }, 5000);
            
            if (backendServiceProcess) {
                backendServiceProcess.on('close', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            } else {
                clearTimeout(timeout);
                resolve();
            }
        });
        
        backendServiceProcess = null;
        return { success: true, message: 'Backend services stopped' };
        
    } catch (err) {
        console.error('Failed to stop backend services:', err);
        return { success: false, message: String(err) };
    }
}

// 控制是否由 Electron 自启本地 FastAPI（云端部署时可关闭）
const shouldStartApi = (process.env.ELECTRON_START_API || 'true') !== 'false';

async function ensureBackendReady() {
    if (!shouldStartApi) return;
    try {
        await startBackendServices();
    } catch (e) {
        console.error('Failed to auto start backend services:', e);
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
        try { await stopBackendServices(); } catch (e) {}
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

// IPC处理程序 - 启动后端服务（提供给渲染端按需调用）
ipcMain.handle('start-service', async () => {
    return startBackendServices();
});

// IPC处理程序 - 停止后端服务
ipcMain.handle('stop-service', async () => {
    return stopBackendServices();
});

// IPC处理程序 - 检查服务健康状态
ipcMain.handle('check-service-health', async (event, serviceName = 'main') => {
    try {
        const config = serviceConfig[serviceName];
        if (!config) {
            return { success: false, error: `Unknown service: ${serviceName}` };
        }
        
        const response = await fetch(`http://127.0.0.1:${config.port}${config.healthPath}`, {
            method: 'GET',
            timeout: 3000
        });
        
        const data = await response.json();
        return { success: true, data, service: serviceName };
    } catch (error) {
        return { success: false, error: error.message, service: serviceName };
    }
});

// IPC处理程序 - 检查所有服务健康状态
ipcMain.handle('check-all-services-health', async () => {
    const results = {};
    
    for (const [serviceName, config] of Object.entries(serviceConfig)) {
        try {
            const response = await fetch(`http://127.0.0.1:${config.port}${config.healthPath}`, {
                method: 'GET',
                timeout: 2000
            });
            
            if (response.ok) {
                const data = await response.json();
                results[serviceName] = { 
                    status: 'healthy', 
                    data, 
                    url: `http://127.0.0.1:${config.port}` 
                };
            } else {
                results[serviceName] = { 
                    status: 'unhealthy', 
                    error: `HTTP ${response.status}`,
                    url: `http://127.0.0.1:${config.port}` 
                };
            }
        } catch (error) {
            results[serviceName] = { 
                status: 'offline', 
                error: error.message,
                url: `http://127.0.0.1:${config.port}` 
            };
        }
    }
    
    return { success: true, services: results };
});

// IPC处理程序 - 获取服务URL
ipcMain.handle('get-service-url', async (event, serviceName = 'main') => {
    const config = serviceConfig[serviceName];
    if (!config) {
        return { success: false, error: `Unknown service: ${serviceName}` };
    }
    
    return { 
        success: true, 
        url: `http://127.0.0.1:${config.port}`,
        service: serviceName 
    };
});

// IPC处理程序 - 获取所有服务配置
ipcMain.handle('get-services-config', async () => {
    const services = {};
    
    for (const [serviceName, config] of Object.entries(serviceConfig)) {
        services[serviceName] = {
            name: config.name,
            url: `http://127.0.0.1:${config.port}`,
            port: config.port,
            healthPath: config.healthPath
        };
    }
    
    return { success: true, services };
});

// IPC处理程序 - 检查服务状态
ipcMain.handle('check-service-status', async () => {
    return {
        running: backendServiceProcess !== null,
        pid: backendServiceProcess ? backendServiceProcess.pid : null,
        services: Object.keys(serviceConfig)
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
