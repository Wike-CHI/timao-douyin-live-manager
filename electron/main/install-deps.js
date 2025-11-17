const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app, BrowserWindow } = require('electron');

/**
 * 首次启动时安装大型 AI 依赖（torch, funasr 等）
 * 避免打包进安装包，减小安装包体积
 */

class DependencyInstaller {
  constructor() {
    this.pythonPath = this.getPythonPath();
    this.depsMarkerFile = path.join(app.getPath('userData'), '.deps-installed');
    this.progressWindow = null;
  }

  /**
   * 获取 Python 可执行文件路径
   */
  getPythonPath() {
    if (app.isPackaged) {
      // 生产环境：从 resources 目录读取
      const resourcesPath = process.resourcesPath;
      return path.join(resourcesPath, 'python-runtime', 'python.exe');
    } else {
      // 开发环境：从项目根目录读取
      return path.join(process.cwd(), 'python-runtime', 'python.exe');
    }
  }

  /**
   * 检查依赖是否已安装
   */
  async checkDepsInstalled() {
    // 检查标记文件
    if (fs.existsSync(this.depsMarkerFile)) {
      return true;
    }

    // 检查 torch 是否可导入
    return new Promise((resolve) => {
      const proc = spawn(this.pythonPath, ['-c', 'import torch; import funasr']);
      proc.on('close', (code) => {
        resolve(code === 0);
      });
    });
  }

  /**
   * 创建进度窗口
   */
  createProgressWindow() {
    console.log('[DependencyInstaller] Creating progress window...');
    
    this.progressWindow = new BrowserWindow({
      width: 600,
      height: 400,
      frame: false,
      transparent: true,
      resizable: false,
      alwaysOnTop: true,  // 确保窗口始终在最前面
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    this.progressWindow.on('closed', () => {
      console.log('[DependencyInstaller] Progress window closed');
      this.progressWindow = null;
    });

    // 加载进度页面（简单 HTML）
    this.progressWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: white;
          }
          .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
          }
          h1 { font-size: 32px; margin-bottom: 20px; }
          .status { font-size: 18px; margin: 20px 0; opacity: 0.9; }
          .progress-bar {
            width: 400px;
            height: 8px;
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
            overflow: hidden;
            margin: 20px auto;
          }
          .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            width: 0%;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(0,255,136,0.5);
          }
          .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
          .eta { font-size: 14px; opacity: 0.7; margin-top: 10px; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🚀 提猫直播管理平台</h1>
          <div class="spinner"></div>
          <div class="status" id="status">正在准备 AI 依赖...</div>
          <div class="progress-bar">
            <div class="progress-fill" id="progress"></div>
          </div>
          <div class="eta" id="eta">预计需要 5-10 分钟</div>
        </div>
      </body>
      </html>
    `)}`);
  }

  /**
   * 更新进度
   */
  updateProgress(status, progress, eta) {
    console.log(`[DependencyInstaller] Progress: ${progress}% - ${status} - ${eta}`);
    
    if (this.progressWindow && !this.progressWindow.isDestroyed()) {
      // 直接执行 JS 更新界面
      this.progressWindow.webContents.executeJavaScript(`
        try {
          const statusEl = document.getElementById('status');
          const progressEl = document.getElementById('progress');
          const etaEl = document.getElementById('eta');
          
          if (statusEl) statusEl.textContent = ${JSON.stringify(status)};
          if (progressEl) progressEl.style.width = ${progress} + '%';
          if (etaEl) etaEl.textContent = ${JSON.stringify(eta)};
          
          console.log('Progress updated: ${progress}%');
        } catch (e) {
          console.error('Failed to update progress:', e);
        }
      `).catch(err => {
        console.error('[DependencyInstaller] Failed to execute JS:', err);
      });
    }
  }

  /**
   * 安装依赖包
   */
  async installPackage(packageName, index, total) {
    console.log(`[DependencyInstaller] Installing ${packageName} (${index}/${total})...`);
    
    return new Promise((resolve, reject) => {
      const progress = Math.round((index / total) * 100);
      this.updateProgress(
        `正在安装 ${packageName}... (${index}/${total})`,
        progress,
        `预计剩余 ${Math.max(1, total - index)} 分钟`
      );

      const args = [
        '-m', 'pip', 'install',
        packageName,
        '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
        '--no-warn-script-location',
        '--disable-pip-version-check'  // 禁用版本检查，加快速度
      ];

      console.log(`[DependencyInstaller] Running: ${this.pythonPath} ${args.join(' ')}`);
      const proc = spawn(this.pythonPath, args);

      let output = '';
      let errorOutput = '';
      let installTimeout = null;
      
      // 设置超时（每个包最多 5 分钟）
      installTimeout = setTimeout(() => {
        console.error(`[DependencyInstaller] Installation timeout for ${packageName}`);
        proc.kill();
        reject(new Error(`安装 ${packageName} 超时（5分钟）`));
      }, 5 * 60 * 1000);
      
      proc.stdout.on('data', (data) => {
        const text = data.toString();
        output += text;
        // 只输出关键信息，避免刷屏
        if (text.includes('Collecting') || text.includes('Installing') || text.includes('Successfully')) {
          console.log(`[pip] ${text.trim()}`);
        }
      });

      proc.stderr.on('data', (data) => {
        const text = data.toString();
        errorOutput += text;
        // stderr 可能包含警告而非错误
        console.log(`[pip stderr] ${text.trim()}`);
      });

      proc.on('close', (code) => {
        if (installTimeout) {
          clearTimeout(installTimeout);
          installTimeout = null;
        }
        
        if (code === 0) {
          console.log(`[DependencyInstaller] ✅ ${packageName} installed successfully`);
          console.log(`[DependencyInstaller] Output: ${output.substring(0, 200)}...`);
          resolve();
        } else {
          const errorMsg = errorOutput || output || '未知错误';
          console.error(`[DependencyInstaller] ❌ Failed to install ${packageName}`);
          console.error(`[DependencyInstaller] Exit code: ${code}`);
          console.error(`[DependencyInstaller] Output: ${output}`);
          console.error(`[DependencyInstaller] Error: ${errorOutput}`);
          reject(new Error(`安装 ${packageName} 失败 (exit code ${code}): ${errorMsg.substring(0, 200)}`));
        }
      });

      proc.on('error', (err) => {
        console.error(`[DependencyInstaller] ❌ Process error for ${packageName}:`, err);
        reject(err);
      });
    });
  }

  /**
   * 安装所有大型依赖
   */
  async installDependencies() {
    console.log('[DependencyInstaller] Starting dependency installation...');
    
    this.createProgressWindow();
    
    // 等待窗口加载完成
    await new Promise((resolve) => {
      if (this.progressWindow) {
        this.progressWindow.webContents.once('did-finish-load', () => {
          console.log('[DependencyInstaller] Progress window loaded');
          setTimeout(resolve, 500);  // 额外等待 500ms 确保 DOM 完全就绪
        });
      } else {
        resolve();
      }
    });

    const packages = [
      // 核心 AI 框架（~1GB）
      'torch',
      'torchaudio',
      
      // 科学计算库
      'numpy',
      'scipy',
      'librosa',
      'soundfile',
      
      // FunASR 及依赖
      'funasr',
      'modelscope',
      'pyaudio',
      'websockets',
      'pydub',
      'keyboard',
      
      // NLP & LLM
      'transformers',
      'sentence-transformers',
      'langchain',
      'langchain-openai',
      'langchain-community',
      
      // 其他工具
      'tiktoken',
      'openai',
      'redis',
      'sqlalchemy',
      'pillow',
      'pytest'
    ];

    try {
      console.log(`[DependencyInstaller] Installing ${packages.length} packages...`);
      
      for (let i = 0; i < packages.length; i++) {
        await this.installPackage(packages[i], i + 1, packages.length);
      }

      // 创建标记文件
      console.log('[DependencyInstaller] Creating marker file...');
      fs.writeFileSync(this.depsMarkerFile, new Date().toISOString());

      this.updateProgress('✅ 依赖安装完成！', 100, '准备启动...');
      
      // 等待 2 秒后关闭窗口
      console.log('[DependencyInstaller] Installation complete, closing window in 2s...');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      if (this.progressWindow && !this.progressWindow.isDestroyed()) {
        this.progressWindow.close();
      }

      console.log('[DependencyInstaller] ✅ All dependencies installed successfully');
      return true;
    } catch (error) {
      console.error('[DependencyInstaller] ❌ Failed to install dependencies:', error);
      console.error('[DependencyInstaller] Full error:', error.stack || error);
      
      this.updateProgress(
        '❌ 依赖安装失败，请检查网络连接',
        0,
        error.message || '未知错误'
      );

      // 显示错误 15 秒后关闭
      await new Promise(resolve => setTimeout(resolve, 15000));
      
      if (this.progressWindow && !this.progressWindow.isDestroyed()) {
        this.progressWindow.close();
      }

      throw error;
    }
  }

  /**
   * 确保依赖已安装（主入口）
   */
  async ensureDependencies() {
    console.log('[DependencyInstaller] Checking dependencies...');
    
    const installed = await this.checkDepsInstalled();
    
    if (!installed) {
      console.log('[DependencyInstaller] Dependencies not found, starting installation...');
      await this.installDependencies();
    } else {
      console.log('[DependencyInstaller] ✅ Dependencies already installed, skipping...');
    }
  }
}

module.exports = new DependencyInstaller();
