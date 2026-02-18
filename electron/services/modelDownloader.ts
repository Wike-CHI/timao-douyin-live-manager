import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import https from 'https';
import { app } from 'electron';
import axios, { AxiosInstance } from 'axios';

/**
 * 模型下载服务
 * 首次启动时检测并下载 SenseVoice 模型
 */
class ModelDownloaderService {
  private httpClient: AxiosInstance;
  private downloadProgress: number = 0;
  private isDownloading: boolean = false;
  private cancelToken: any = null;

  // 模型配置
  private readonly MODEL_URL = 'https://modelscope.oss-cn-beijing.aliyuncs.com/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch';
  private readonly MODEL_SIZE_GB = 1.5;
  private readonly MODEL_DIR = 'models';
  private readonly MODEL_CHECKPOINT = 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch';
  private readonly TRANSCRIBER_MODEL_FILE = 'transcriber_service.exe';

  constructor() {
    this.httpClient = axios.create({
      timeout: 600000, // 10分钟超时
    });
  }

  /**
   * 获取模型目录路径
   */
  getModelDir(): string {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-transcriber', this.MODEL_DIR);
    } else {
      return path.join(__dirname, '..', 'python-transcriber', this.MODEL_DIR);
    }
  }

  /**
   * 获取模型检查点路径
   */
  getModelCheckpointPath(): string {
    return path.join(this.getModelDir(), this.MODEL_CHECKPOINT);
  }

  /**
   * 获取转写服务可执行文件路径
   */
  getTranscriberPath(): string {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, 'python-transcriber', this.TRANSCRIBER_MODEL_FILE);
    } else {
      return path.join(__dirname, '..', 'python-transcriber', 'dist', this.TRANSCRIBER_MODEL_FILE);
    }
  }

  /**
   * 检查模型是否已存在
   */
  async checkModelExists(): Promise<boolean> {
    const modelPath = this.getModelCheckpointPath();
    const exists = fs.existsSync(modelPath);
    console.log(`[ModelDownloader] 模型检查: ${exists ? '已存在' : '不存在'} - ${modelPath}`);
    return exists;
  }

  /**
   * 检查转写服务是否可用
   */
  async checkTranscriberAvailable(): Promise<boolean> {
    const transcriberPath = this.getTranscriberPath();
    const exists = fs.existsSync(transcriberPath);
    console.log(`[ModelDownloader] 转写服务检查: ${exists ? '可用' : '不可用'} - ${transcriberPath}`);
    return exists;
  }

  /**
   * 获取模型状态
   */
  async getModelStatus(): Promise<{
    modelExists: boolean;
    transcriberAvailable: boolean;
    needsDownload: boolean;
    modelPath: string;
  }> {
    const modelExists = await this.checkModelExists();
    const transcriberAvailable = await this.checkTranscriberAvailable();

    return {
      modelExists,
      transcriberAvailable,
      needsDownload: !modelExists && transcriberAvailable,
      modelPath: this.getModelCheckpointPath()
    };
  }

  /**
   * 下载模型文件
   * 使用 modelscope CLI 或手动下载
   */
  async downloadModel(
    onProgress?: (progress: number, downloaded: number, total: number) => void
  ): Promise<boolean> {
    if (this.isDownloading) {
      console.log('[ModelDownloader] 下载已在进行中');
      return false;
    }

    const modelDir = this.getModelDir();
    const modelPath = this.getModelCheckpointPath();

    // 确保目录存在
    if (!fs.existsSync(modelDir)) {
      fs.mkdirSync(modelDir, { recursive: true });
    }

    this.isDownloading = true;
    this.downloadProgress = 0;

    console.log(`[ModelDownloader] 开始下载模型到: ${modelPath}`);
    console.log(`[ModelDownloader] 预计大小: ${this.MODEL_SIZE_GB} GB`);

    try {
      // 使用 modelscope download 命令
      const downloadSuccess = await this.downloadWithModelScope(modelDir, onProgress);

      if (downloadSuccess) {
        console.log('[ModelDownloader] 模型下载完成');
        this.downloadProgress = 100;
        return true;
      } else {
        console.error('[ModelDownloader] 模型下载失败');
        return false;
      }
    } catch (error) {
      console.error('[ModelDownloader] 下载错误:', error);
      return false;
    } finally {
      this.isDownloading = false;
    }
  }

  /**
   * 使用 ModelScope CLI 下载模型
   */
  private async downloadWithModelScope(
    targetDir: string,
    onProgress?: (progress: number, downloaded: number, total: number) => void
  ): Promise<boolean> {
    return new Promise((resolve) => {
      // 检查 modelscope 是否可用
      const pythonPath = this.getPythonPath();
      const checkCmd = spawn(pythonPath, ['-c', 'import modelscope; print("ok")'], {
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let checked = false;
      const checkTimeout = setTimeout(() => {
        if (!checked) {
          checked = true;
          checkCmd.kill();
          console.log('[ModelDownloader] modelscope 检查超时，尝试备用方案');
          resolve(this.downloadFallback(targetDir, onProgress));
        }
      }, 10000);

      checkCmd.stdout.on('data', (data) => {
        if (!checked && data.toString().includes('ok')) {
          checked = true;
          clearTimeout(checkTimeout);
          checkCmd.kill();

          // 使用 modelscope download
          console.log('[ModelDownloader] 使用 modelscope download');
          const downloadCmd = spawn(pythonPath, [
            '-m', 'modelscope', 'download',
            '--model', 'iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
            '--local_dir', targetDir
          ], {
            stdio: ['ignore', 'pipe', 'pipe']
          });

          let output = '';
          downloadCmd.stdout.on('data', (data) => {
            output += data.toString();
            console.log(`[ModelScope] ${data.toString().trim()}`);

            // 解析进度（如果有）
            const progressMatch = output.match(/(\d+)%/);
            if (progressMatch) {
              const progress = parseInt(progressMatch[1]);
              this.downloadProgress = progress;
              if (onProgress) {
                onProgress(progress, progress * this.MODEL_SIZE_GB * 1024, this.MODEL_SIZE_GB * 1024 * 1024);
              }
            }
          });

          downloadCmd.stderr.on('data', (data) => {
            console.log(`[ModelScope stderr] ${data.toString().trim()}`);
          });

          downloadCmd.on('close', (code) => {
            if (code === 0) {
              // 重命名目录（如果需要）
              this.renameModelDir(targetDir);
              resolve(true);
            } else {
              console.log('[ModelScope] 下载失败，尝试备用方案');
              resolve(this.downloadFallback(targetDir, onProgress));
            }
          });
        }
      });

      checkCmd.stderr.on('data', (data) => {
        console.log(`[Check stderr] ${data.toString().trim()}`);
      });
    });
  }

  /**
   * 备用下载方案：手动下载
   */
  private async downloadFallback(
    targetDir: string,
    onProgress?: (progress: number, downloaded: number, total: number) => void
  ): Promise<boolean> {
    console.log('[ModelDownloader] 使用备用下载方案');
    console.log('[ModelDownloader] 请手动下载模型并放置到以下目录:');
    console.log(`[ModelDownloader] ${targetDir}`);

    // 返回 false，提示用户手动下载
    return false;
  }

  /**
   * 重命名模型目录（如果 modelscope 下载的目录名不同）
   */
  private renameModelDir(targetDir: string): void {
    // 检查是否有子目录需要重命名
    const items = fs.readdirSync(targetDir);
    for (const item of items) {
      const itemPath = path.join(targetDir, item);
      if (fs.statSync(itemPath).isDirectory()) {
        // 如果有以 iic 开头的目录，可能是 modelscope 下载的
        if (item.startsWith('iic.')) {
          const newPath = path.join(targetDir, this.MODEL_CHECKPOINT);
          if (!fs.existsSync(newPath)) {
            try {
              fs.renameSync(itemPath, newPath);
              console.log(`[ModelDownloader] 重命名目录: ${item} -> ${this.MODEL_CHECKPOINT}`);
            } catch (e) {
              console.warn('[ModelDownloader] 重命名失败:', e);
            }
          }
        }
      }
    }
  }

  /**
   * 获取 Python 路径
   */
  private getPythonPath(): string {
    if (app.isPackaged) {
      // 打包环境：使用后端目录的 Python（如果有）
      const backendPython = path.join(process.resourcesPath, 'backend', 'python.exe');
      if (fs.existsSync(backendPython)) {
        return backendPython;
      }
      return 'python'; // 假设在 PATH 中
    } else {
      // 开发环境
      const venvPython = path.join(__dirname, '..', '..', '..', '.venv', 'Scripts', 'python.exe');
      if (fs.existsSync(venvPython)) {
        return venvPython;
      }
      return 'python';
    }
  }

  /**
   * 取消下载
   */
  cancelDownload(): void {
    if (this.cancelToken) {
      this.cancelToken.cancel('用户取消下载');
    }
    this.isDownloading = false;
    console.log('[ModelDownloader] 下载已取消');
  }

  /**
   * 获取下载进度
   */
  getDownloadProgress(): number {
    return this.downloadProgress;
  }

  /**
   * 是否正在下载
   */
  isCurrentlyDownloading(): boolean {
    return this.isDownloading;
  }

  /**
   * 获取模型大小信息
   */
  getModelSizeInfo(): string {
    return `${this.MODEL_SIZE_GB} GB`;
  }
}

// 导出单例
export const modelDownloader = new ModelDownloaderService();
