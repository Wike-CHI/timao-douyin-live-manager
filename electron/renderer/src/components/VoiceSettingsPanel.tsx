/**
 * 语音设置面板组件
 * 支持前端实时配置语音转写模型和语言
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  settingsService,
  VoiceSettings,
  VoiceModel,
  LANGUAGE_OPTIONS,
} from '../services/settingsService';

interface VoiceSettingsPanelProps {
  className?: string;
  onSettingsChange?: (settings: VoiceSettings) => void;
}

export function VoiceSettingsPanel({
  className = '',
  onSettingsChange,
}: VoiceSettingsPanelProps) {
  const [settings, setSettings] = useState<VoiceSettings | null>(null);
  const [models] = useState<VoiceModel[]>(settingsService.getVoiceModels());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // 加载设置
  const loadSettings = useCallback(async () => {
    try {
      setError(null);
      const data = await settingsService.getVoiceSettings();
      setSettings(data);
    } catch (err) {
      console.error('加载语音设置失败:', err);
      setError('加载设置失败，请检查后端服务是否启动');
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  // 更新设置
  const updateSettings = async (updates: Partial<VoiceSettings>) => {
    if (!settings) return;

    setLoading(true);
    setError(null);
    setSaved(false);

    try {
      const updated = await settingsService.updateVoiceSettings(updates);
      setSettings(updated);
      setSaved(true);
      onSettingsChange?.(updated);

      // 3秒后隐藏保存成功提示
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('更新语音设置失败:', err);
      setError('保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 重置设置
  const resetSettings = async () => {
    setLoading(true);
    setError(null);

    try {
      const reset = await settingsService.resetVoiceSettings();
      setSettings(reset);
      onSettingsChange?.(reset);
    } catch (err) {
      console.error('重置语音设置失败:', err);
      setError('重置失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  if (!settings) {
    return (
      <div className={`p-4 bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          语音转写设置
        </h3>
        {saved && (
          <span className="text-sm text-green-600 dark:text-green-400 flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            已保存
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* 语音模型选择 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            语音模型
          </label>
          <select
            value={settings.model}
            onChange={(e) => updateSettings({ model: e.target.value as VoiceSettings['model'] })}
            disabled={loading}
            className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} {m.recommended ? '(推荐)' : ''}
              </option>
            ))}
          </select>
          {models.find((m) => m.id === settings.model)?.description && (
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {models.find((m) => m.id === settings.model)?.description}
            </p>
          )}
        </div>

        {/* 语言选择 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            识别语言
          </label>
          <select
            value={settings.language}
            onChange={(e) => updateSettings({ language: e.target.value as VoiceSettings['language'] })}
            disabled={loading}
            className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* VAD 开关 */}
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              语音活动检测 (VAD)
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              自动检测语音片段，过滤静音
            </p>
          </div>
          <button
            type="button"
            onClick={() => updateSettings({ enable_vad: !settings.enable_vad })}
            disabled={loading}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer
                        rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
                        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                        ${settings.enable_vad ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'}
                        ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full
                          bg-white shadow ring-0 transition duration-200 ease-in-out
                          ${settings.enable_vad ? 'translate-x-5' : 'translate-x-0'}`}
            />
          </button>
        </div>

        {/* 采样率显示 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            采样率
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {settings.sample_rate} Hz
          </p>
        </div>

        {/* 重置按钮 */}
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={resetSettings}
            disabled={loading}
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white
                       underline underline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            恢复默认设置
          </button>
        </div>
      </div>
    </div>
  );
}

export default VoiceSettingsPanel;
