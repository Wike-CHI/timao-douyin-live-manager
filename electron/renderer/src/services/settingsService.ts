/**
 * 设置服务 - 调用 V2 Settings API
 * 支持前端实时配置语音和 AI 设置
 */

import { requestWithRetry } from './apiConfig';

export interface VoiceSettings {
  model: 'sensevoice' | 'whisper' | 'funasr';
  language: 'auto' | 'zh' | 'en' | 'ja' | 'ko' | 'yue';
  enable_vad: boolean;
  sample_rate: number;
}

export interface AISettings {
  service: 'qwen' | 'openai' | 'deepseek' | 'doubao' | 'chatglm';
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface VoiceModel {
  id: string;
  name: string;
  description: string;
  languages: string[];
  recommended: boolean;
}

export const VOICE_MODELS: VoiceModel[] = [
  {
    id: 'sensevoice',
    name: 'SenseVoice',
    description: '阿里达摩院语音识别模型，中文效果好',
    languages: ['auto', 'zh', 'en', 'ja', 'ko', 'yue'],
    recommended: true,
  },
  {
    id: 'whisper',
    name: 'Whisper',
    description: 'OpenAI 通用语音识别模型',
    languages: ['auto', 'zh', 'en', 'ja', 'ko', 'yue'],
    recommended: false,
  },
  {
    id: 'funasr',
    name: 'FunASR',
    description: '阿里达摩院 FunASR 模型',
    languages: ['auto', 'zh', 'en'],
    recommended: false,
  },
];

export const LANGUAGE_OPTIONS = [
  { value: 'auto', label: '自动检测' },
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英语' },
  { value: 'ja', label: '日语' },
  { value: 'ko', label: '韩语' },
  { value: 'yue', label: '粤语' },
];

export const settingsService = {
  /**
   * 获取语音设置
   */
  async getVoiceSettings(): Promise<VoiceSettings> {
    return requestWithRetry<VoiceSettings>('main', '/api/v2/settings/voice');
  },

  /**
   * 更新语音设置
   */
  async updateVoiceSettings(settings: Partial<VoiceSettings>): Promise<VoiceSettings> {
    return requestWithRetry<VoiceSettings>('main', '/api/v2/settings/voice', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  /**
   * 重置语音设置
   */
  async resetVoiceSettings(): Promise<VoiceSettings> {
    return requestWithRetry<VoiceSettings>('main', '/api/v2/settings/voice/reset', {
      method: 'POST',
    });
  },

  /**
   * 获取 AI 设置
   */
  async getAISettings(): Promise<AISettings> {
    return requestWithRetry<AISettings>('main', '/api/v2/settings/ai');
  },

  /**
   * 更新 AI 设置
   */
  async updateAISettings(settings: Partial<AISettings>): Promise<AISettings> {
    return requestWithRetry<AISettings>('main', '/api/v2/settings/ai', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  /**
   * 重置 AI 设置
   */
  async resetAISettings(): Promise<AISettings> {
    return requestWithRetry<AISettings>('main', '/api/v2/settings/ai/reset', {
      method: 'POST',
    });
  },

  /**
   * 获取所有设置
   */
  async getAllSettings(): Promise<{ voice: VoiceSettings; ai: AISettings }> {
    return requestWithRetry<{ voice: VoiceSettings; ai: AISettings }>('main', '/api/v2/settings/all');
  },

  /**
   * 重置所有设置
   */
  async resetAllSettings(): Promise<{ voice: VoiceSettings; ai: AISettings }> {
    return requestWithRetry<{ voice: VoiceSettings; ai: AISettings }>('main', '/api/v2/settings/reset', {
      method: 'POST',
    });
  },

  /**
   * 获取可用语音模型列表
   */
  getVoiceModels(): VoiceModel[] {
    return VOICE_MODELS;
  },

  /**
   * 获取语言选项列表
   */
  getLanguageOptions() {
    return LANGUAGE_OPTIONS;
  },
};

export default settingsService;
