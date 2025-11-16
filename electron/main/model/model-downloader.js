/**
 * 模型下载器 - 支持断点续传、SHA256校验
 * 基于文档: docs/部分服务从服务器转移本地.md
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');
const http = require('http');

class ModelDownloader {
  constructor(modelInfo, targetPath) {
    this.modelInfo = modelInfo;      // manifest 中的模型信息 {url, size, sha256, name}
    this.targetPath = targetPath;    // 最终保存路径
    this.tempPath = `${targetPath}.part`;  // 临时文件
    this.chunkSize = 10 * 1024 * 1024;     // 10MB 分片
    this.maxRetries = 3;                    // 最大重试次数
    this.cancelled = false;
  }

  /**
   * 开始下载
   * @param {Function} onProgress 进度回调 { downloaded, progress, speed, eta }
   */
  async download(onProgress) {
    const { url, size, sha256 } = this.modelInfo;
    
    try {
      // 1. 检查是否有未完成的下载
      let downloaded = 0;
      if (fsSync.existsSync(this.tempPath)) {
        const stat = await fs.stat(this.tempPath);
        downloaded = stat.size;
        console.log(`📦 发现未完成的下载，已下载: ${downloaded}/${size}`);
      }

      // 2. 分片下载
      const chunks = this.calculateChunks(downloaded, size);
      console.log(`🔗 分片数量: ${chunks.length}`);

      const startTime = Date.now();
      for (const chunk of chunks) {
        if (this.cancelled) {
          throw new Error('CANCELLED');
        }
        
        await this.downloadChunk(url, chunk, onProgress, startTime);
      }

      // 3. 校验文件
      console.log('🔍 校验文件完整性...');
      const isValid = await this.verifySHA256(this.tempPath, sha256);
      if (!isValid) {
        throw new Error('文件校验失败，SHA256 不匹配');
      }

      // 4. 移动到正式目录
      await fs.rename(this.tempPath, this.targetPath);
      console.log('✅ 模型下载完成');
      
      return true;
    } catch (error) {
      if (error.message !== 'CANCELLED') {
        console.error('下载失败:', error);
      }
      throw error;
    }
  }

  /**
   * 计算分片
   */
  calculateChunks(downloaded, total) {
    const chunks = [];
    let start = downloaded;
    
    while (start < total) {
      const end = Math.min(start + this.chunkSize - 1, total - 1);
      chunks.push({ start, end });
      start = end + 1;
    }
    
    return chunks;
  }

  /**
   * 下载单个分片（支持重试）
   */
  async downloadChunk(url, { start, end }, onProgress, startTime) {
    let retries = 0;
    
    while (retries < this.maxRetries) {
      try {
        const buffer = await this.fetchRange(url, start, end);
        
        // 追加写入临时文件
        await fs.appendFile(this.tempPath, buffer);
        
        // 更新进度
        if (onProgress) {
          const stat = await fs.stat(this.tempPath);
          const downloaded = stat.size;
          const progress = (downloaded / this.modelInfo.size) * 100;
          
          // 计算速度与ETA
          const elapsed = (Date.now() - startTime) / 1000; // 秒
          const speed = elapsed > 0 ? downloaded / elapsed : 0;
          const remaining = this.modelInfo.size - downloaded;
          const eta = speed > 0 ? remaining / speed : 0;
          
          onProgress({ 
            downloaded, 
            progress,
            speed,
            eta
          });
        }

        return; // 成功
      } catch (error) {
        retries++;
        console.error(`❌ 下载分片失败 (${retries}/${this.maxRetries}):`, error.message);
        
        if (retries >= this.maxRetries) {
          throw error;
        }
        
        // 指数退避重试
        await this.sleep(Math.pow(2, retries) * 1000);
      }
    }
  }

  /**
   * 使用 HTTP Range 请求获取分片
   */
  fetchRange(url, start, end) {
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const client = urlObj.protocol === 'https:' ? https : http;
      
      const options = {
        hostname: urlObj.hostname,
        port: urlObj.port,
        path: urlObj.pathname + urlObj.search,
        method: 'GET',
        headers: {
          'Range': `bytes=${start}-${end}`,
        },
      };

      const req = client.request(options, (res) => {
        if (res.statusCode !== 206 && res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }

        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => resolve(Buffer.concat(chunks)));
        res.on('error', reject);
      });

      req.on('error', reject);
      req.setTimeout(30000, () => {
        req.abort();
        reject(new Error('ETIMEDOUT'));
      });
      
      req.end();
    });
  }

  /**
   * SHA256 完整性校验
   */
  async verifySHA256(filePath, expectedHash) {
    return new Promise((resolve, reject) => {
      const hash = crypto.createHash('sha256');
      const stream = fsSync.createReadStream(filePath);
      
      stream.on('data', (chunk) => hash.update(chunk));
      stream.on('end', () => {
        const actualHash = hash.digest('hex');
        resolve(actualHash.toLowerCase() === expectedHash.toLowerCase());
      });
      stream.on('error', reject);
    });
  }

  /**
   * 取消下载
   */
  cancel() {
    this.cancelled = true;
  }

  /**
   * 延迟函数
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = ModelDownloader;
