import WebSocket from 'ws';
import { pythonTranscriber, TranscribeResult } from './pythonTranscriber';
import axios, { AxiosInstance } from 'axios';

/**
 * 音频流接收器
 * 
 * 从服务器接收音频流，本地转写后回传结果
 */
class AudioStreamReceiver {
  private ws: WebSocket | null = null;
  private audioBuffer: Buffer[] = [];
  private readonly CHUNK_SIZE = 16000 * 2 * 0.4; // 0.4秒音频块（16kHz * 2字节 * 0.4秒）
  private sessionId: string = '';
  private serverUrl: string = '';
  private httpClient: AxiosInstance | null = null;
  private isConnected = false;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private readonly RECONNECT_DELAY = 3000; // 3秒重连延迟

  /**
   * 连接到服务器音频流
   * 
   * @param serverUrl 服务器地址（如 http://localhost:8000）
   * @param sessionId 会话ID
   */
  connect(serverUrl: string, sessionId: string): void {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[AudioStreamReceiver] 已连接，无需重复连接');
      return;
    }

    this.serverUrl = serverUrl;
    this.sessionId = sessionId;

    // 初始化 HTTP 客户端
    this.httpClient = axios.create({
      baseURL: serverUrl,
      timeout: 10000,
    });

    // 清理旧连接
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    console.log(`[AudioStreamReceiver] 连接到音频流: ${serverUrl}`);

    // WebSocket URL
    const wsUrl = serverUrl.replace(/^http/, 'ws') + '/api/live_audio/ws/audio';

    try {
      this.ws = new WebSocket(wsUrl);

      // 连接成功
      this.ws.on('open', () => {
        console.log('[AudioStreamReceiver] ✅ WebSocket 连接成功');
        this.isConnected = true;
        this.audioBuffer = [];

        // 启动心跳
        this.startHeartbeat();
      });

      // 接收音频数据
      this.ws.on('message', async (data: Buffer) => {
        await this.handleAudioData(data);
      });

      // 连接关闭
      this.ws.on('close', (code, reason) => {
        console.log(`[AudioStreamReceiver] WebSocket 连接关闭 (code=${code}, reason=${reason})`);
        this.isConnected = false;
        this.scheduleReconnect();
      });

      // 连接错误
      this.ws.on('error', (error) => {
        console.error('[AudioStreamReceiver] WebSocket 错误:', error);
      });
    } catch (error) {
      console.error('[AudioStreamReceiver] 连接失败:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 处理接收到的音频数据
   */
  private async handleAudioData(data: Buffer): Promise<void> {
    try {
      // 累积音频数据
      this.audioBuffer.push(data);

      // 计算总大小
      const totalSize = this.audioBuffer.reduce((sum, buf) => sum + buf.length, 0);

      // 如果累积到指定大小，触发转写
      if (totalSize >= this.CHUNK_SIZE) {
        const audioChunk = Buffer.concat(this.audioBuffer);
        this.audioBuffer = [];

        // 本地转写
        try {
          const result = await pythonTranscriber.transcribe(audioChunk);

          // 如果有文本，回传服务器
          if (result.text && result.text.trim()) {
            await this.uploadTranscription(result);
          }
        } catch (error) {
          console.error('[AudioStreamReceiver] 转写失败:', error);
        }
      }
    } catch (error) {
      console.error('[AudioStreamReceiver] 处理音频数据失败:', error);
    }
  }

  /**
   * 上传转写结果到服务器
   */
  private async uploadTranscription(result: TranscribeResult): Promise<void> {
    if (!this.httpClient) {
      console.error('[AudioStreamReceiver] HTTP 客户端未初始化');
      return;
    }

    try {
      const payload = {
        session_id: this.sessionId,
        text: result.text,
        confidence: result.confidence || 0.0,
        timestamp: result.timestamp || Date.now(),
      };

      console.log('[AudioStreamReceiver] 上传转写结果:', payload.text);

      await this.httpClient.post('/api/live_audio/transcriptions', payload);
    } catch (error) {
      console.error('[AudioStreamReceiver] 上传转写结果失败:', error);
    }
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    if (!this.ws) return;

    const heartbeatInterval = setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        clearInterval(heartbeatInterval);
        return;
      }

      try {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      } catch (error) {
        console.error('[AudioStreamReceiver] 心跳发送失败:', error);
      }
    }, 30000); // 每30秒发送一次心跳
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    console.log(`[AudioStreamReceiver] ${this.RECONNECT_DELAY / 1000}秒后尝试重连...`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.serverUrl && this.sessionId) {
        this.connect(this.serverUrl, this.sessionId);
      }
    }, this.RECONNECT_DELAY);
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    console.log('[AudioStreamReceiver] 断开音频流连接');

    // 清理重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // 关闭 WebSocket
    if (this.ws) {
      this.isConnected = false;
      this.ws.close();
      this.ws = null;
    }

    // 清空缓冲区
    this.audioBuffer = [];
    this.httpClient = null;
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus(): {
    isConnected: boolean;
    sessionId: string;
    bufferSize: number;
  } {
    const bufferSize = this.audioBuffer.reduce((sum, buf) => sum + buf.length, 0);
    return {
      isConnected: this.isConnected,
      sessionId: this.sessionId,
      bufferSize,
    };
  }
}

// 导出单例
export const audioStreamReceiver = new AudioStreamReceiver();

