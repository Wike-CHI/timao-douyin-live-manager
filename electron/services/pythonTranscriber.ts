import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import axios, { AxiosInstance } from 'axios';
import { app } from 'electron';

/**
 * Python 转写服务管理器
 * 
 * 负责启动、监控和停止 Python 转写子进程
 */
class PythonTranscriberService {
  private process: ChildProcess | null = null;
  private readonly port = 9527;
  private readonly host = '127.0.0.1';
  private httpClient: AxiosInstance;
  private isStarting = false;
  private isReady = false;

  constructor() {
    this.httpClient = axios.create({
      baseURL: `http://${this.host}:${this.port}`,
      timeout: 30000, // 30秒超时
    });
  }

  /**
   * 启动 Python 转写服务
   */
  async start(): Promise<void> {
    if (this.isStarting) {
      console.log('[PythonTranscriber] 服务正在启动中...');
      return;
    }

    if (this.process && !this.process.killed) {
      console.log('[PythonTranscriber] 服务已在运行中');
      return;
    }

    this.isStarting = true;
    this.isReady = false;

    try {
      console.log('[PythonTranscriber] 开始启动 Python 转写服务...');

      // 获取可执行文件路径
      const exePath = this.getExecutablePath();
      console.log(`[PythonTranscriber] Python 服务路径: ${exePath}`);

      // 启动子进程
      this.process = spawn(exePath, [], {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
      });

      // 监听标准输出
      if (this.process.stdout) {
        this.process.stdout.on('data', (data) => {
          console.log(`[PythonTranscriber stdout] ${data.toString()}`);
        });
      }

      // 监听标准错误
      if (this.process.stderr) {
        this.process.stderr.on('data', (data) => {
          console.error(`[PythonTranscriber stderr] ${data.toString()}`);
        });
      }

      // 监听进程退出
      this.process.on('exit', (code, signal) => {
        console.log(`[PythonTranscriber] 进程已退出 (code=${code}, signal=${signal})`);
        this.isReady = false;
        this.process = null;
      });

      // 监听进程错误
      this.process.on('error', (err) => {
        console.error(`[PythonTranscriber] 进程错误:`, err);
        this.isReady = false;
      });

      // 等待服务就绪
      await this.waitForReady(60000); // 60秒超时（模型加载需要时间）
      this.isReady = true;
      console.log('[PythonTranscriber] ✅ Python 转写服务启动成功');
    } catch (error) {
      console.error('[PythonTranscriber] ❌ 启动失败:', error);
      this.stop();
      throw error;
    } finally {
      this.isStarting = false;
    }
  }

  /**
   * 等待服务就绪
   */
  private async waitForReady(maxWait = 60000): Promise<void> {
    const startTime = Date.now();
    const checkInterval = 1000; // 每秒检查一次

    console.log('[PythonTranscriber] 等待服务就绪...');

    while (Date.now() - startTime < maxWait) {
      try {
        // 尝试调用健康检查端点
        const response = await this.httpClient.get('/health');
        if (response.data && response.data.status === 'ok') {
          console.log('[PythonTranscriber] 服务已就绪');
          return;
        }
      } catch (error) {
        // 忽略连接失败，继续重试
      }

      // 等待后重试
      await new Promise((resolve) => setTimeout(resolve, checkInterval));
    }

    throw new Error('Python 转写服务启动超时');
  }

  /**
   * 获取可执行文件路径
   */
  private getExecutablePath(): string {
    const isDev = !app.isPackaged;

    if (isDev) {
      // 开发环境：使用本地 Python 脚本
      const scriptPath = path.join(
        __dirname,
        '..',
        'python-transcriber',
        'transcriber_service.py'
      );
      return process.platform === 'win32' ? 'python' : 'python3';
      // 注意：开发环境需要手动运行 python transcriber_service.py
    } else {
      // 生产环境：使用打包后的可执行文件
      const resourcePath = process.resourcesPath;
      const exeName =
        process.platform === 'win32' ? 'transcriber_service.exe' : 'transcriber_service';
      return path.join(resourcePath, 'python-transcriber', exeName);
    }
  }

  /**
   * 转写音频数据
   * 
   * @param audioData PCM 16bit 16kHz mono 音频数据
   * @returns 转写结果
   */
  async transcribe(audioData: Buffer): Promise<TranscribeResult> {
    if (!this.isReady) {
      throw new Error('Python 转写服务未就绪');
    }

    try {
      const response = await this.httpClient.post('/transcribe', audioData, {
        headers: {
          'Content-Type': 'application/octet-stream',
        },
        timeout: 10000, // 10秒超时
      });

      return response.data as TranscribeResult;
    } catch (error) {
      console.error('[PythonTranscriber] 转写失败:', error);
      throw error;
    }
  }

  /**
   * 获取服务信息
   */
  async getInfo(): Promise<ServiceInfo> {
    if (!this.isReady) {
      throw new Error('Python 转写服务未就绪');
    }

    try {
      const response = await this.httpClient.get('/info');
      return response.data as ServiceInfo;
    } catch (error) {
      console.error('[PythonTranscriber] 获取服务信息失败:', error);
      throw error;
    }
  }

  /**
   * 停止 Python 转写服务
   */
  stop(): void {
    if (this.process) {
      console.log('[PythonTranscriber] 正在停止 Python 转写服务...');
      
      try {
        // 发送 SIGTERM 信号
        this.process.kill('SIGTERM');
        
        // 设置超时强制杀死进程
        setTimeout(() => {
          if (this.process && !this.process.killed) {
            console.warn('[PythonTranscriber] 强制终止进程');
            this.process.kill('SIGKILL');
          }
        }, 5000);
      } catch (error) {
        console.error('[PythonTranscriber] 停止进程失败:', error);
      }

      this.process = null;
      this.isReady = false;
    }
  }

  /**
   * 检查服务是否就绪
   */
  isServiceReady(): boolean {
    return this.isReady && this.process !== null && !this.process.killed;
  }
}

/**
 * 转写结果接口
 */
export interface TranscribeResult {
  text: string;
  confidence: number;
  duration?: number;
  inference_time?: number;
  timestamp?: number;
  error?: string;
}

/**
 * 服务信息接口
 */
export interface ServiceInfo {
  service: string;
  version: string;
  model: string;
  vad: string;
  device: string;
  sample_rate: number;
  initialized: boolean;
}

// 导出单例
export const pythonTranscriber = new PythonTranscriberService();

