/**
 * 模型下载器组件
 * 提供模型下载状态检测、进度显示、下载控制（暂停/继续/取消）
 */
import React, { useState, useEffect, useCallback } from 'react';

interface IpcRenderer {
  invoke(channel: string, ...args: unknown[]): Promise<unknown>;
  on(channel: string, listener: (event: unknown, ...args: unknown[]) => void): void;
  removeAllListeners(channel: string): void;
}

declare global {
  interface Window {
    electron?: {
      ipcRenderer: IpcRenderer;
    };
  }
}

interface ModelInfo {
  id: string;
  name: string;
  size: number;
  description?: string;
}

interface ModelStatus {
  status: 'AVAILABLE' | 'MISSING' | 'DOWNLOADING' | 'PAUSED' | 'VERIFYING' | 'ERROR';
  progress?: number;
  downloadedBytes?: number;
  totalBytes?: number;
  speed?: number;        // 下载速度 (bytes/s)
  eta?: number;          // 预计剩余时间 (秒)
  error?: string;
}

interface ProgressPayload {
  modelId: string;
  state?: string;
  progress: number;
  downloaded?: number;
  downloadedBytes: number;
  totalBytes: number;
  speed?: number;
  eta?: number;
}

/**
 * 格式化字节数为可读格式
 */
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * 格式化速度
 */
const formatSpeed = (bytesPerSecond: number): string => {
  return `${formatBytes(bytesPerSecond)}/s`;
};

/**
 * 格式化剩余时间
 */
const formatETA = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}秒`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`;
  return `${Math.round(seconds / 3600)}小时`;
};

/**
 * 模型下载器组件
 */
export const ModelDownloader: React.FC = () => {
  const [models] = useState<ModelInfo[]>([
    { id: 'sensevoice-small', name: 'SenseVoice Small', size: 2.3 * 1024 * 1024 * 1024, description: '语音识别模型' },
    { id: 'vad-silero', name: 'VAD Silero', size: 1.8 * 1024 * 1024, description: '语音活动检测' },
  ]);

  const [modelStatuses, setModelStatuses] = useState<Record<string, ModelStatus>>({});
  const [checking, setChecking] = useState(false);

  const ipcRenderer = window.electron?.ipcRenderer;

  /**
   * 检查所有模型状态
   */
  const checkModels = useCallback(async () => {
    if (!ipcRenderer) {
      console.warn('[ModelDownloader] Electron IPC 不可用');
      return;
    }

    setChecking(true);
    const newStatuses: Record<string, ModelStatus> = {};

    for (const model of models) {
      try {
        const result = (await ipcRenderer.invoke('model:check', model.id)) as ModelStatus;
        newStatuses[model.id] = result;
      } catch (error) {
        console.error(`[ModelDownloader] 检查模型 ${model.id} 失败:`, error);
        newStatuses[model.id] = {
          status: 'ERROR',
          error: error instanceof Error ? error.message : String(error),
        };
      }
    }

    setModelStatuses(newStatuses);
    setChecking(false);
  }, [models, ipcRenderer]);

  /**
   * 开始下载模型
   */
  const startDownload = useCallback(
    async (modelId: string) => {
      if (!ipcRenderer) return;

      try {
        await ipcRenderer.invoke('model:start-download', modelId);
        setModelStatuses((prev) => ({
          ...prev,
          [modelId]: { status: 'DOWNLOADING', progress: 0, downloadedBytes: 0, totalBytes: 0 },
        }));
      } catch (error) {
        console.error(`[ModelDownloader] 启动下载失败:`, error);
        setModelStatuses((prev) => ({
          ...prev,
          [modelId]: {
            status: 'ERROR',
            error: error instanceof Error ? error.message : String(error),
          },
        }));
      }
    },
    [ipcRenderer]
  );

  /**
   * 暂停下载
   */
  const pauseDownload = useCallback(
    async (modelId: string) => {
      if (!ipcRenderer) return;

      try {
        await ipcRenderer.invoke('model:pause-download', modelId);
        setModelStatuses((prev) => ({
          ...prev,
          [modelId]: { ...prev[modelId], status: 'PAUSED' },
        }));
      } catch (error) {
        console.error(`[ModelDownloader] 暂停下载失败:`, error);
      }
    },
    [ipcRenderer]
  );

  /**
   * 继续下载
   */
  const resumeDownload = useCallback(
    async (modelId: string) => {
      if (!ipcRenderer) return;

      try {
        await ipcRenderer.invoke('model:resume-download', modelId);
        setModelStatuses((prev) => ({
          ...prev,
          [modelId]: { ...prev[modelId], status: 'DOWNLOADING' },
        }));
      } catch (error) {
        console.error(`[ModelDownloader] 继续下载失败:`, error);
      }
    },
    [ipcRenderer]
  );

  /**
   * 取消下载
   */
  const cancelDownload = useCallback(
    async (modelId: string) => {
      if (!ipcRenderer) return;

      try {
        await ipcRenderer.invoke('model:cancel-download', modelId);
        // 重新检查状态
        await checkModels();
      } catch (error) {
        console.error(`[ModelDownloader] 取消下载失败:`, error);
      }
    },
    [ipcRenderer, checkModels]
  );

  /**
   * 监听下载进度
   */
  useEffect(() => {
    if (!ipcRenderer) return;

    const handleProgress = (_event: unknown, ...args: unknown[]) => {
      const payload = args[0] as ProgressPayload;
      const { modelId, state, progress, downloaded, downloadedBytes, totalBytes, speed, eta } = payload;
      setModelStatuses((prev) => ({
        ...prev,
        [modelId]: {
          status: (state as ModelStatus['status']) || 'DOWNLOADING',
          progress,
          downloadedBytes: downloaded || downloadedBytes,
          totalBytes,
          speed,
          eta,
        },
      }));
    };

    ipcRenderer.on('model:download-progress', handleProgress);

    return () => {
      ipcRenderer.removeAllListeners('model:download-progress');
    };
  }, [ipcRenderer]);

  /**
   * 组件挂载时检查模型状态
   */
  useEffect(() => {
    checkModels();
  }, [checkModels]);

  if (!ipcRenderer) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800">⚠️ Electron 环境不可用,模型下载功能需要在桌面端运行</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">模型管理</h2>
        <button
          onClick={checkModels}
          disabled={checking}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {checking ? '检查中...' : '刷新状态'}
        </button>
      </div>

      <div className="space-y-3">
        {models.map((model) => {
          const status = modelStatuses[model.id];
          const isDownloading = status?.status === 'DOWNLOADING';
          const isPaused = status?.status === 'PAUSED';
          const isAvailable = status?.status === 'AVAILABLE';
          const isMissing = status?.status === 'MISSING';
          const isVerifying = status?.status === 'VERIFYING';
          const hasError = status?.status === 'ERROR';

          return (
            <div key={model.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{model.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {model.description} · {formatBytes(model.size)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {isAvailable && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full text-sm font-medium">
                      ✓ 已安装
                    </span>
                  )}
                  {isMissing && (
                    <button
                      onClick={() => startDownload(model.id)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
                    >
                      下载模型
                    </button>
                  )}
                  {isDownloading && (
                    <>
                      <button
                        onClick={() => pauseDownload(model.id)}
                        className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition"
                      >
                        暂停
                      </button>
                      <button
                        onClick={() => cancelDownload(model.id)}
                        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
                      >
                        取消
                      </button>
                    </>
                  )}
                  {isPaused && (
                    <>
                      <button
                        onClick={() => resumeDownload(model.id)}
                        className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                      >
                        继续
                      </button>
                      <button
                        onClick={() => cancelDownload(model.id)}
                        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
                      >
                        取消
                      </button>
                    </>
                  )}
                  {isVerifying && (
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full text-sm font-medium animate-pulse">
                      🔍 校验中...
                    </span>
                  )}
                  {hasError && (
                    <span className="px-3 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full text-sm font-medium">
                      ✗ 错误
                    </span>
                  )}
                </div>
              </div>

              {(isDownloading || isPaused) && status && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                    <span className="font-medium">
                      {isPaused ? '已暂停' : '下载进度'}
                    </span>
                    <span>
                      {formatBytes(status.downloadedBytes || 0)} / {formatBytes(status.totalBytes || 0)} (
                      {(status.progress || 0).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-300 ${
                        isPaused ? 'bg-yellow-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${status.progress || 0}%` }}
                    />
                  </div>
                  {isDownloading && status.speed !== undefined && status.eta !== undefined && (
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <span>速度: {formatSpeed(status.speed)}</span>
                      <span>剩余时间: {formatETA(status.eta)}</span>
                    </div>
                  )}
                </div>
              )}

              {hasError && status?.error && (
                <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                  <p className="text-sm text-red-800 dark:text-red-300">错误: {status.error}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ModelDownloader;
