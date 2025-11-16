/**
 * 模型管理器 - Electron 主进程
 * 管理模型下载、状态、IPC通信
 * 基于文档: docs/部分服务从服务器转移本地.md
 */

const { ipcMain, app } = require('electron');
const ModelDownloader = require('./model-downloader');
const { ensureEnoughSpaceAndWritable, ERR_ENOSPC, ERR_EACCES } = require('./ensure-space');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const https = require('https');

// 模型下载状态
const ModelDownloadState = {
  IDLE: 'idle',
  CHECKING: 'checking',
  AVAILABLE: 'available',
  MISSING: 'missing',
  DOWNLOADING: 'downloading',
  PAUSED: 'paused',
  VERIFYING: 'verifying',
  VERIFY_FAILED: 'verify_failed',
  ERROR: 'error',
  CANCELLED: 'cancelled',
};

class ModelManager {
  constructor() {
    this.downloaders = new Map();  // modelId -> ModelDownloader
    this.downloadStates = new Map(); // modelId -> state
    this.modelBasePath = path.join(app.getPath('userData'), 'models');
    this.cachePath = path.join(app.getPath('userData'), 'cache');
    this.registryPath = path.join(this.cachePath, 'model_registry.json');
  }

  /**
   * 初始化 IPC 监听
   */
  setupIPC() {
    ipcMain.handle('model:check', async (event, { modelId }) => {
      return await this.checkModel(modelId);
    });

    ipcMain.handle('model:start-download', async (event, { modelId }) => {
      return await this.startDownload(modelId, (progress) => {
        event.sender.send('model:download-progress', { modelId, ...progress });
      });
    });

    ipcMain.handle('model:cancel-download', async (event, { modelId }) => {
      return this.cancelDownload(modelId);
    });

    console.log('✅ ModelManager IPC handlers registered');
  }

  /**
   * 检查模型是否存在且有效
   */
  async checkModel(modelId) {
    try {
      const modelPath = this.getModelPath(modelId);
      const manifest = await this.fetchManifest();
      const modelInfo = manifest.models.find(m => m.id === modelId);
      
      if (!modelInfo) {
        return { state: ModelDownloadState.ERROR, error: `模型 ${modelId} 不存在于清单` };
      }

      // 检查主文件
      const mainFile = modelInfo.files[0];
      const mainFilePath = path.join(modelPath, mainFile.name);

      if (!fsSync.existsSync(mainFilePath)) {
        return { state: ModelDownloadState.MISSING };
      }

      // 检查文件大小
      const stat = await fs.stat(mainFilePath);
      if (stat.size !== mainFile.size) {
        return { state: ModelDownloadState.MISSING };
      }

      // TODO: 可选：SHA256 校验（首次启动或怀疑损坏时）
      
      return { state: ModelDownloadState.AVAILABLE, path: mainFilePath };
    } catch (error) {
      console.error('检查模型失败:', error);
      return { state: ModelDownloadState.ERROR, error: error.message };
    }
  }

  /**
   * 开始下载模型
   */
  async startDownload(modelId, onProgress) {
    try {
      // 1. 获取 manifest
      const manifest = await this.fetchManifest();
      const modelInfo = manifest.models.find(m => m.id === modelId);
      
      if (!modelInfo) {
        throw new Error(`模型 ${modelId} 不存在`);
      }

      const mainFile = modelInfo.files[0]; // 主文件
      const modelPath = this.getModelPath(modelId);
      const targetPath = path.join(modelPath, mainFile.name);

      // 2. 检查磁盘空间与权限
      onProgress({ state: ModelDownloadState.CHECKING });
      
      try {
        await ensureEnoughSpaceAndWritable(targetPath, mainFile.size);
      } catch (error) {
        if (error.code === ERR_ENOSPC) {
          onProgress({ 
            state: ModelDownloadState.ERROR, 
            error: `磁盘空间不足: 需要 ${(error.required / 1024 / 1024 / 1024).toFixed(2)}GB, 可用 ${(error.free / 1024 / 1024 / 1024).toFixed(2)}GB` 
          });
          return { success: false, reason: 'ENOSPC', ...error };
        }
        if (error.code === ERR_EACCES) {
          onProgress({ 
            state: ModelDownloadState.ERROR, 
            error: '写入权限不足，请以管理员权限运行或选择其他目录' 
          });
          return { success: false, reason: 'EACCES', message: error.message };
        }
        throw error;
      }

      // 3. 准备下载路径
      await fs.mkdir(modelPath, { recursive: true });

      // 4. 创建下载器
      const downloader = new ModelDownloader(mainFile, targetPath);
      this.downloaders.set(modelId, downloader);

      // 5. 开始下载
      onProgress({ state: ModelDownloadState.DOWNLOADING, progress: 0 });
      
      await downloader.download((progress) => {
        onProgress({
          state: ModelDownloadState.DOWNLOADING,
          ...progress,
          total: mainFile.size,
        });
      });

      // 6. 下载完成
      onProgress({ state: ModelDownloadState.AVAILABLE, progress: 100 });
      
      // 7. 更新注册表
      await this.updateRegistry(modelId, {
        version: modelInfo.version,
        downloadedAt: Date.now(),
        path: targetPath,
      });

      return { success: true };

    } catch (error) {
      console.error('下载失败:', error);
      onProgress({
        state: error.message === 'CANCELLED' ? ModelDownloadState.CANCELLED : ModelDownloadState.ERROR,
        error: error.message,
      });
      return { success: false, error: error.message };
    }
  }

  /**
   * 取消下载
   */
  cancelDownload(modelId) {
    const downloader = this.downloaders.get(modelId);
    if (downloader) {
      downloader.cancel();
      this.downloaders.delete(modelId);
      return { success: true };
    }
    return { success: false, error: '下载器不存在' };
  }

  /**
   * 获取模型存储路径
   */
  getModelPath(modelId) {
    return path.join(this.modelBasePath, modelId);
  }

  /**
   * 获取 CDN manifest（支持降级）
   */
  async fetchManifest() {
    const manifestUrl = process.env.MODEL_MANIFEST_URL || 'https://cdn.example.com/models/manifest.json';
    
    try {
      const data = await this.httpsGet(manifestUrl);
      return JSON.parse(data);
    } catch (error) {
      console.warn('获取 CDN manifest 失败，使用内置降级:', error.message);
      return require('./manifest-fallback.json');
    }
  }

  /**
   * 简单的 HTTPS GET 请求
   */
  httpsGet(url) {
    return new Promise((resolve, reject) => {
      https.get(url, (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }
        
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve(data));
        res.on('error', reject);
      }).on('error', reject);
    });
  }

  /**
   * 更新模型注册表
   */
  async updateRegistry(modelId, info) {
    try {
      await fs.mkdir(this.cachePath, { recursive: true });
      
      let registry = {};
      if (fsSync.existsSync(this.registryPath)) {
        const data = await fs.readFile(this.registryPath, 'utf8');
        registry = JSON.parse(data);
      }
      
      registry[modelId] = {
        ...registry[modelId],
        ...info,
      };
      
      await fs.writeFile(this.registryPath, JSON.stringify(registry, null, 2));
    } catch (error) {
      console.error('更新注册表失败:', error);
    }
  }
}

// 单例
const modelManager = new ModelManager();

module.exports = modelManager;
