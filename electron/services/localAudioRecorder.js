/**
 * 本地音频录制服务（Electron客户端）
 * 
 * 功能：
 * - 从服务器获取直播流地址
 * - 使用本地ffmpeg录制音频
 * - 保存到用户电脑（Documents/TalkingCat/audio/）
 * - 不占用服务器空间
 * 
 * 符合KISS原则：简单、直接、本地化
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');
const axios = require('axios');

class LocalAudioRecorder {
  constructor() {
    this.ffmpegProcess = null;
    this.isRecording = false;
    this.currentSessionId = null;
    this.currentStreamUrl = null;
    this.audioSavePath = null;
    
    // 获取用户文档目录
    this.audioDir = path.join(app.getPath('documents'), 'TalkingCat', 'audio');
    
    // 确保目录存在
    this._ensureDirectory();
  }
  
  /**
   * 确保音频目录存在
   */
  _ensureDirectory() {
    try {
      if (!fs.existsSync(this.audioDir)) {
        fs.mkdirSync(this.audioDir, { recursive: true });
        console.log(`📁 音频目录已创建: ${this.audioDir}`);
      }
    } catch (error) {
      console.error('创建音频目录失败:', error);
    }
  }
  
  /**
   * 获取ffmpeg路径
   */
  _getFfmpegPath() {
    // Electron打包后的ffmpeg路径
    const isPackaged = app.isPackaged;
    
    if (isPackaged) {
      // 生产环境：从resources目录
      const platform = process.platform;
      let ffmpegName = 'ffmpeg';
      if (platform === 'win32') {
        ffmpegName = 'ffmpeg.exe';
      }
      return path.join(process.resourcesPath, 'tools', 'ffmpeg', ffmpegName);
    } else {
      // 开发环境：从项目目录
      const platform = process.platform;
      let platformDir = 'linux';
      let ffmpegName = 'ffmpeg';
      
      if (platform === 'win32') {
        platformDir = 'win64';
        ffmpegName = 'ffmpeg.exe';
      } else if (platform === 'darwin') {
        platformDir = 'mac';
      }
      
      return path.join(__dirname, '../../tools/ffmpeg', platformDir, 'bin', ffmpegName);
    }
  }
  
  /**
   * 从服务器获取直播流地址
   */
  async getStreamUrl(liveUrlOrId, apiUrl) {
    try {
      console.log(`🔍 获取直播流地址: ${liveUrlOrId}`);
      const response = await axios.get(`${apiUrl}/api/live_audio/stream-url/${encodeURIComponent(liveUrlOrId)}`);
      
      if (response.data && response.data.success && response.data.data) {
        const { stream_url, anchor_name, live_id } = response.data.data;
        console.log(`✅ 获取到流地址: ${anchor_name} (${live_id})`);
        return response.data.data;
      } else {
        throw new Error('服务器返回数据格式错误');
      }
    } catch (error) {
      console.error('获取流地址失败:', error.message);
      throw new Error(`获取直播流地址失败: ${error.response?.data?.message || error.message}`);
    }
  }
  
  /**
   * 开始录制音频
   */
  async startRecording(liveUrlOrId, apiUrl, options = {}) {
    if (this.isRecording) {
      throw new Error('录制已在进行中');
    }
    
    try {
      // 1. 获取流地址
      const streamInfo = await this.getStreamUrl(liveUrlOrId, apiUrl);
      this.currentStreamUrl = streamInfo.stream_url;
      this.currentSessionId = options.sessionId || `live_${streamInfo.live_id}_${Date.now()}`;
      
      // 2. 生成保存路径
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `${streamInfo.anchor_name || streamInfo.live_id}_${timestamp}.wav`;
      this.audioSavePath = path.join(this.audioDir, filename);
      
      // 3. 获取ffmpeg路径
      const ffmpegPath = this._getFfmpegPath();
      
      // 检查ffmpeg是否存在
      if (!fs.existsSync(ffmpegPath)) {
        throw new Error(`ffmpeg未找到: ${ffmpegPath}`);
      }
      
      // 4. 构建ffmpeg命令
      const args = [
        '-loglevel', 'warning',
        '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '-headers', 'referer:https://live.douyin.com',
        '-i', this.currentStreamUrl,
        '-vn',           // 不要视频
        '-ac', '1',      // 单声道
        '-ar', '16000',  // 16kHz
        '-f', 'wav',     // WAV格式
        this.audioSavePath
      ];
      
      console.log(`🎬 启动本地录制: ${ffmpegPath}`);
      console.log(`📁 保存路径: ${this.audioSavePath}`);
      
      // 5. 启动ffmpeg进程
      this.ffmpegProcess = spawn(ffmpegPath, args);
      this.isRecording = true;
      
      // 监听stderr（ffmpeg输出日志到stderr）
      this.ffmpegProcess.stderr.on('data', (data) => {
        const message = data.toString();
        // 只记录警告和错误
        if (message.includes('error') || message.includes('warning')) {
          console.log(`[ffmpeg] ${message.trim()}`);
        }
      });
      
      // 监听进程退出
      this.ffmpegProcess.on('close', (code) => {
        this.isRecording = false;
        this.ffmpegProcess = null;
        
        if (code === 0) {
          // 检查文件大小
          const stats = fs.statSync(this.audioSavePath);
          const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
          console.log(`✅ 录制完成: ${this.audioSavePath} (${sizeMB} MB)`);
        } else {
          console.error(`❌ ffmpeg异常退出: code=${code}`);
        }
      });
      
      // 监听进程错误
      this.ffmpegProcess.on('error', (error) => {
        console.error('ffmpeg进程错误:', error);
        this.isRecording = false;
        this.ffmpegProcess = null;
      });
      
      return {
        success: true,
        sessionId: this.currentSessionId,
        savePath: this.audioSavePath,
        streamInfo: streamInfo
      };
      
    } catch (error) {
      this.isRecording = false;
      this.ffmpegProcess = null;
      throw error;
    }
  }
  
  /**
   * 停止录制
   */
  stopRecording() {
    if (!this.isRecording || !this.ffmpegProcess) {
      return {
        success: false,
        message: '没有正在录制的任务'
      };
    }
    
    try {
      console.log('🛑 停止录制...');
      
      // 发送'q'命令优雅停止ffmpeg
      if (this.ffmpegProcess.stdin) {
        this.ffmpegProcess.stdin.write('q');
      }
      
      // 如果5秒后还没停止，强制杀死
      setTimeout(() => {
        if (this.ffmpegProcess && !this.ffmpegProcess.killed) {
          this.ffmpegProcess.kill('SIGKILL');
        }
      }, 5000);
      
      const savePath = this.audioSavePath;
      this.isRecording = false;
      
      return {
        success: true,
        savePath: savePath,
        message: '录制已停止'
      };
      
    } catch (error) {
      console.error('停止录制失败:', error);
      return {
        success: false,
        message: error.message
      };
    }
  }
  
  /**
   * 获取录制状态
   */
  getStatus() {
    return {
      isRecording: this.isRecording,
      sessionId: this.currentSessionId,
      savePath: this.audioSavePath,
      audioDir: this.audioDir
    };
  }
  
  /**
   * 获取已录制的音频列表
   */
  getAudioFiles() {
    try {
      const files = fs.readdirSync(this.audioDir);
      const audioFiles = files
        .filter(file => file.endsWith('.wav'))
        .map(file => {
          const filePath = path.join(this.audioDir, file);
          const stats = fs.statSync(filePath);
          return {
            name: file,
            path: filePath,
            size: stats.size,
            sizeMB: (stats.size / (1024 * 1024)).toFixed(2),
            modifiedTime: stats.mtime,
            createdTime: stats.birthtime
          };
        })
        .sort((a, b) => b.modifiedTime - a.modifiedTime); // 按修改时间倒序
      
      return audioFiles;
    } catch (error) {
      console.error('获取音频文件列表失败:', error);
      return [];
    }
  }
  
  /**
   * 删除音频文件
   */
  deleteAudioFile(filePath) {
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`🗑️ 已删除: ${filePath}`);
        return { success: true };
      } else {
        return { success: false, message: '文件不存在' };
      }
    } catch (error) {
      console.error('删除文件失败:', error);
      return { success: false, message: error.message };
    }
  }
  
  /**
   * 打开音频目录
   */
  openAudioDirectory() {
    const { shell } = require('electron');
    shell.openPath(this.audioDir);
  }
}

// 单例模式
let recorderInstance = null;

function getLocalAudioRecorder() {
  if (!recorderInstance) {
    recorderInstance = new LocalAudioRecorder();
  }
  return recorderInstance;
}

module.exports = {
  LocalAudioRecorder,
  getLocalAudioRecorder
};

