const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

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

            // If port 8090 is already in use (e.g., user started uvicorn manually),
            // do not spawn another process to avoid EADDRINUSE and noisy logs.
            const available = await isPortAvailable(8090);
            if (!available) {
                console.log('[electron] Port 8090 is already in use; assuming FastAPI is running.');
                return resolve({ success: true, message: 'FastAPI already running (external)' });
            }

            // Use uvicorn to run server.app.main:app on 127.0.0.1:8090 (default FastAPI port for Electron)
            // Spawn with project root as cwd so Python can import local packages
            apiProcess = spawn(
                process.platform === 'win32' ? 'python' : 'python3',
                ['-m', 'uvicorn', 'server.app.main:app', '--host', '127.0.0.1', '--port', '8090'],
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

// 简易启动引导：先启动后端并完成资源自检，再打开主窗口（类似 PS 启动器体验）
let splashWindow = null;

function createSplash() {
    const logoPath = path.join(__dirname, '..', 'assets', 'logo_cat_headset.jpg');
    const logoUrl = fs.existsSync(logoPath) ? 'file://' + logoPath.replace(/\\/g, '/') : '';
    const logoTag = logoUrl ? `<img class="logo" src="${logoUrl}" alt="logo"/>` : '<div class="logo fallback">🐱</div>';
    splashWindow = new BrowserWindow({
        width: 520,
        height: 320,
        frame: false,
        resizable: false,
        transparent: false,
        alwaysOnTop: false,
        show: true,
        webPreferences: { nodeIntegration: false, contextIsolation: true, preload: path.join(__dirname, 'preload.js') }
    });
    const html = `<!doctype html><meta charset="utf-8"/><title>启动中…</title>
    <style>
    body{font-family:system-ui,Segoe UI,Arial;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#faf7ff;color:#5b34b3}
    .box{background:#fff;border-radius:16px;box-shadow:0 18px 32px rgba(91,52,179,.18);padding:24px 28px;min-width:420px;position:relative}
    .drag-zone{position:absolute;top:0;left:0;right:0;height:36px;-webkit-app-region:drag}
    .toolbar{position:absolute;top:12px;right:16px;display:flex;gap:6px;-webkit-app-region:no-drag}
    .logo-wrap{display:flex;align-items:center;gap:12px;margin-bottom:12px;-webkit-app-region:no-drag}
    .logo{width:56px;height:56px;border-radius:16px;object-fit:cover;box-shadow:0 8px 20px rgba(91,52,179,.20);background:#f0eaff}
    .logo.fallback{display:flex;align-items:center;justify-content:center;font-size:28px}
    h1{font-size:18px;margin:0 0 10px}.msg{font-size:14px;color:#6b5a99;white-space:pre-wrap}
    .hint{margin-top:10px;color:#8c7bbf;font-size:12px}
    .bar{height:8px;background:#f0eaff;border-radius:999px;margin:10px 0;overflow:hidden}
    .bar>div{height:100%;width:0;background:linear-gradient(90deg,#a78bfa,#f472b6);transition:width .3s}
    .btns{display:flex;gap:8px;margin-top:10px}
    button{border:1px solid #e6d8ff;background:#fff;color:#5b34b3;border-radius:999px;padding:6px 10px;font-size:12px;cursor:pointer;-webkit-app-region:no-drag}
    button[disabled]{opacity:.4;cursor:not-allowed}
    </style>
    <div class="box">
      <div class="drag-zone"></div>
      <div class="toolbar">
        <button id="btn-pin">置顶</button>
      </div>
      <div class="logo-wrap">
        ${logoTag}
        <h1 style="margin:0">提猫直播助手 · 正在准备</h1>
      </div>
      <div id=msg class=msg>启动后端服务…</div>
      <div class=bar><div id=bar></div></div>
      <div id=hint class=hint></div>
      <div class=btns>
        <button id=btn-open-model disabled>打开模型目录</button>
        <button id=btn-open-vad disabled>打开VAD目录</button>
        <button id=btn-open-ff disabled>打开FFmpeg目录</button>
        <button id=btn-logs>打开日志</button>
        <button id=btn-retry>重试</button>
        <button id=btn-exit>退出</button>
      </div>
      <script>
        const E = (id)=>document.getElementById(id);
        const btnPin = E('btn-pin');
        const updatePinLabel = (pinned) => { if (btnPin) btnPin.textContent = pinned ? '取消置顶' : '置顶'; };
        const togglePin = async () => {
          try {
            const res = await window.electronAPI?.toggleSplashPin?.();
            if (res?.success) {
              updatePinLabel(res.pinned);
            }
          } catch (_) {}
        };
        updatePinLabel(false);
        const dragZone = document.querySelector('.drag-zone');
        if (dragZone) dragZone.addEventListener('dblclick', togglePin);
        if (btnPin) btnPin.onclick = togglePin;

        let paths = { model:'', vad:'', ff:'' };
        E('btn-exit').onclick = ()=>{ try{ window.electronAPI?.quitApp(); }catch(e){} };
        E('btn-open-model').onclick = ()=>{ if(paths.model) try{ window.electronAPI?.openPath(paths.model);}catch(e){} };
        E('btn-open-vad').onclick = ()=>{ if(paths.vad) try{ window.electronAPI?.openPath(paths.vad);}catch(e){} };
        E('btn-open-ff').onclick = ()=>{ if(paths.ff) try{ window.electronAPI?.openPath(paths.ff);}catch(e){} };
        E('btn-logs').onclick = ()=>{ try{ window.electronAPI?.openLogs(); }catch(e){} };
        E('btn-retry').onclick = async ()=>{ try{ E('hint').innerText=''; window._splashSet('重新检测中…','',10,null); const ok = await window.electronAPI?.bootstrapRetry(); if(ok?.success){ window._splashSet('检测通过，正在进入…','',100,null); } }catch(e){} };
        window._splashSet = (text,hint,percent,newPaths)=>{
          if(text!=null) E('msg').innerText = text;
          if(hint!=null) E('hint').innerText = hint;
          if(typeof percent==='number'){ E('bar').style.width = Math.max(0,Math.min(100,percent))+'%'; }
          if(newPaths){ paths = newPaths; E('btn-open-model').disabled = !paths.model; E('btn-open-vad').disabled = !paths.vad; E('btn-open-ff').disabled = !paths.ff; }
        };
      </script>
    </div>`;
    splashWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
}

async function httpJson(url, timeoutMs = 5000) {
    return new Promise((resolve) => {
        try {
            const lib = url.startsWith('https') ? require('https') : require('http');
            const req = lib.get(url, (res) => {
                let data = '';
                res.on('data', (chunk) => (data += chunk));
                res.on('end', () => {
                    try { resolve(JSON.parse(data || '{}')); } catch { resolve(null); }
                });
            });
            req.on('error', () => resolve(null));
            req.setTimeout(timeoutMs, () => { try { req.destroy(); } catch {} resolve(null); });
        } catch { resolve(null); }
    });
}

async function waitForBackendAndBootstrap() {
    const base = 'http://127.0.0.1:8090';
    // 1) 启动后端
    if (shouldStartApi) {
        try { await startFastAPI(); } catch (e) { console.error('Auto start FastAPI failed:', e); }
    }
    // 等待 /health 就绪
    const setMsg = async (text, hint, percent = null, paths = null) => {
        if (!splashWindow) return;
        try {
            const p = percent == null ? 'null' : String(percent);
            const js = `window._splashSet(${JSON.stringify(text)}, ${JSON.stringify(hint||'')}, ${p}, ${paths?JSON.stringify(paths):'null'})`;
            await splashWindow.webContents.executeJavaScript(js);
        } catch {}
    };
    let okHealth = false;
    for (let i = 0; i < 40; i++) {
        const h = await httpJson(base + '/health');
        if (h && h.status === 'healthy') { okHealth = true; break; }
        await new Promise(r => setTimeout(r, 500));
    }
    if (!okHealth) {
        await setMsg('后端启动超时', '请稍后重试，或检查端口 8090 是否被占用');
        return false;
    }

    // 2) 轮询资源自检（FFmpeg + 模型/VAD），允许 Python 端自动下载
    for (let i = 0; i < 600; i++) { // 最长等 10 分钟
        const st = await httpJson(base + '/api/bootstrap/status');
        const health = await httpJson(base + '/api/live_audio/health');
        const ffOk = (st && st.ffmpeg && st.ffmpeg.state === 'ok');
        const mvOk = (st && st.models && st.models.state === 'ok') || (health && health.success);
        const tips = Array.isArray(st?.suggestions) && st.suggestions.length ? st.suggestions.join('；') : '';
        const okHealth = true; // 到这里后端已就绪
        const percent = Math.round(((okHealth?1:0) + (ffOk?1:0) + (mvOk?1:0)) / 3 * 100);
        const paths = { model: st?.paths?.model_dir || '', vad: st?.paths?.vad_dir || '', ff: st?.paths?.ffmpeg_dir || '' };
        await setMsg(`准备资源…\nFFmpeg: ${ffOk ? 'OK' : '准备中'} · 模型/VAD: ${mvOk ? 'OK' : '准备中'}`, tips, percent, paths);
        if (ffOk && mvOk) return true;
        await new Promise(r => setTimeout(r, 1000));
    }
    await setMsg('资源准备失败', '可在提示目录手动放置模型/FFmpeg 后重启');
    return false;
}

// 当Electron完成初始化并准备创建浏览器窗口时调用此方法
app.on('ready', async () => {
    createSplash();
    const ok = await waitForBackendAndBootstrap();
    if (ok) {
        try { if (splashWindow) splashWindow.close(); } catch {}
        createWindow();
    } else {
        // 停留在引导界面，避免进入主界面；用户可手动处理资源后重启
        console.error('Bootstrap failed, keep splash open.');
    }
});

// Allow retry from splash

ipcMain.handle('bootstrap-retry', async () => {
    try {
        const ok = await waitForBackendAndBootstrap();
        if (ok) {
            try { if (splashWindow) splashWindow.close(); } catch {}
            createWindow();
            return { success: true };
        }
        return { success: false };
    } catch (e) {
        return { success: false, message: String(e) };
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


// IPC - Toggle splash pinning
ipcMain.handle('toggle-splash-pin', async () => {
    if (!splashWindow) return { success: false };
    try {
        const next = !splashWindow.isAlwaysOnTop();
        splashWindow.setAlwaysOnTop(next);
        return { success: true, pinned: next };
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
