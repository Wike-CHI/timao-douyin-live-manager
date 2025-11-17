/**
 * Python本地服务管理模块
 * 负责启动、停止、重启和监控Python FastAPI服务
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const dependencyInstaller = require('./install-deps');

// 安全获取 Electron app（兼容非 Electron 环境）
let app = null;
let isElectronEnv = false;
try {
  const electron = require('electron');
  if (electron && electron.app) {
    app = electron.app;
    isElectronEnv = true;
  }
} catch (e) {
  // 非 Electron 环境
}

class PythonService {
  constructor() {
    this.process = null;
    this.port = 8765; // 默认端口
    this.host = '127.0.0.1';
    this.healthCheckInterval = null;
    this.restartAttempts = 0;
    this.maxRestartAttempts = 3;
    this.isProduction = app ? app.isPackaged : false;
  }

  /**
   * 获取Python运行时路径
   */
  getPythonPath() {
    if (this.isProduction) {
      // 生产环境：从app.asar.unpacked/python-runtime读取
      return path.join(process.resourcesPath, 'python-runtime', 'python.exe');
    } else {
      // 开发环境：使用系统 Python（.venv 或系统全局）
      return 'python';  // 依赖 PATH 环境变量
    }
  }

  /**
   * 获取服务启动脚本路径
   */
  getServerPath() {
    if (this.isProduction) {
      return path.join(process.resourcesPath, 'python-runtime', 'server', 'local', 'main.py');
    } else {
      return path.join(__dirname, '..', '..', 'server', 'local', 'main.py');
    }
  }

  /**
   * 启动Python服务
   */
  async start() {
    if (this.process) {
      console.log('[PythonService] 服务已运行');
      return;
    }

    // 首次启动时确保依赖已安装（仅生产环境）
    if (this.isProduction) {
      console.log('[PythonService] 检查 AI 依赖...');
      try {
        await dependencyInstaller.ensureDependencies();
        console.log('[PythonService] AI 依赖检查完成');
      } catch (error) {
        console.error('[PythonService] AI 依赖安装失败:', error);
        throw error;
      }
    }

    const pythonPath = this.getPythonPath();
    const serverPath = this.getServerPath();

    console.log('[PythonService] 启动服务...');
    console.log(`  Python路径: ${pythonPath}`);
    console.log(`  服务脚本: ${serverPath}`);
    console.log(`  监听地址: http://${this.host}:${this.port}`);

    try {
      this.process = spawn(pythonPath, [
        '-m', 'uvicorn',
        'server.local.main:app',
        '--host', this.host,
        '--port', String(this.port),
        '--log-level', 'info'
      ], {
        cwd: this.isProduction ? path.join(process.resourcesPath, 'python-runtime') : path.join(__dirname, '..', '..'),
        env: {
          ...process.env,
          PYTHONPATH: this.isProduction ? path.join(process.resourcesPath, 'python-runtime') : path.join(__dirname, '..', '..'),
          PYTHONUNBUFFERED: '1'
        },
        windowsHide: true // Windows下隐藏控制台窗口
      });

      // 监听标准输出
      this.process.stdout.on('data', (data) => {
        console.log(`[Python] ${data.toString().trim()}`);
      });

      // 监听错误输出
      this.process.stderr.on('data', (data) => {
        const message = data.toString().trim();
        // 过滤正常的日志信息
        if (!message.includes('INFO') && !message.includes('Started server process')) {
          console.error(`[Python Error] ${message}`);
        } else {
          console.log(`[Python] ${message}`);
        }
      });

      // 监听进程退出
      this.process.on('exit', (code, signal) => {
        console.log(`[PythonService] 进程退出 code=${code}, signal=${signal}`);
        this.process = null;
        this.stopHealthCheck();

        // 自动重启（如果不是正常退出）
        if (code !== 0 && this.restartAttempts < this.maxRestartAttempts) {
          this.restartAttempts++;
          console.log(`[PythonService] 尝试自动重启 (${this.restartAttempts}/${this.maxRestartAttempts})...`);
          setTimeout(() => this.start(), 3000); // 3秒后重启
        } else if (this.restartAttempts >= this.maxRestartAttempts) {
          console.error('[PythonService] 达到最大重启次数，停止自动重启');
        }
      });

      // 监听进程错误
      this.process.on('error', (error) => {
        console.error('[PythonService] 进程启动失败:', error);
        this.process = null;
      });

      // 等待服务启动
      await this.waitForReady();

      // 启动健康检查
      this.startHealthCheck();

      // 重置重启计数
      this.restartAttempts = 0;

      console.log('[PythonService] ✅ 服务启动成功');
    } catch (error) {
      console.error('[PythonService] 启动失败:', error);
      throw error;
    }
  }

  /**
   * 等待服务就绪
   */
  waitForReady(timeout = 30000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const checkInterval = 500;

      const check = () => {
        this.healthCheck()
          .then(() => {
            console.log('[PythonService] 服务已就绪');
            resolve();
          })
          .catch(() => {
            if (Date.now() - startTime > timeout) {
              reject(new Error('服务启动超时'));
            } else {
              setTimeout(check, checkInterval);
            }
          });
      };

      setTimeout(check, 2000); // 首次检查延迟2秒
    });
  }

  /**
   * 健康检查
   */
  healthCheck() {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.host,
        port: this.port,
        path: '/health',
        method: 'GET',
        timeout: 3000
      };

      const req = http.request(options, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          reject(new Error(`Health check failed: ${res.statusCode}`));
        }
      });

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Health check timeout'));
      });

      req.end();
    });
  }

  /**
   * 启动健康检查定时器
   */
  startHealthCheck() {
    this.stopHealthCheck();
    this.healthCheckInterval = setInterval(() => {
      this.healthCheck().catch(() => {
        console.warn('[PythonService] 健康检查失败，尝试重启...');
        this.restart();
      });
    }, 30000); // 每30秒检查一次
  }

  /**
   * 停止健康检查
   */
  stopHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  /**
   * 停止Python服务
   */
  async stop() {
    if (!this.process) {
      console.log('[PythonService] 服务未运行');
      return;
    }

    console.log('[PythonService] 停止服务...');
    this.stopHealthCheck();

    return new Promise((resolve) => {
      this.process.on('exit', () => {
        console.log('[PythonService] ✅ 服务已停止');
        this.process = null;
        resolve();
      });

      // Windows下发送SIGTERM
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', this.process.pid, '/f', '/t']);
      } else {
        this.process.kill('SIGTERM');
      }

      // 超时强制终止
      setTimeout(() => {
        if (this.process) {
          console.warn('[PythonService] 强制终止进程');
          this.process.kill('SIGKILL');
        }
        resolve();
      }, 5000);
    });
  }

  /**
   * 重启Python服务
   */
  async restart() {
    console.log('[PythonService] 重启服务...');
    await this.stop();
    await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒
    await this.start();
  }

  /**
   * 获取服务状态
   */
  getStatus() {
    return {
      running: !!this.process,
      pid: this.process ? this.process.pid : null,
      port: this.port,
      host: this.host,
      url: `http://${this.host}:${this.port}`
    };
  }
}

// 导出单例
const pythonService = new PythonService();

// 应用退出时自动清理（仅在 Electron 环境）
if (app && app.on) {
  app.on('before-quit', async () => {
    console.log('[PythonService] 应用退出，清理Python服务...');
    await pythonService.stop();
  });
}

module.exports = pythonService;
