/**
 * 语音设置卡片 - 样式适配器
 *
 * 将 VoiceSettingsPanel 包装成 ToolsPage 样式
 */

import React from 'react';
import { Mic } from 'lucide-react';
import { VoiceSettingsPanel } from './VoiceSettingsPanel';

interface VoiceSettingsCardProps {
  onSettingsChange?: (settings: Record<string, unknown>) => void;
}

export function VoiceSettingsCard({ onSettingsChange }: VoiceSettingsCardProps) {
  return (
    <div
      className="timao-card bg-white/70 backdrop-blur-sm p-6 animate-fade-in-up"
      style={{ animationDelay: '0.6s', opacity: 0 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900 flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-300 hover:scale-110 hover:rotate-6"
            style={{ background: 'rgba(var(--accent-rgb), 0.1)' }}
          >
            <Mic size={16} style={{ color: 'var(--accent-main)' }} />
          </div>
          语音转写设置
        </h3>
      </div>

      {/* Voice Settings Panel with style overrides */}
      <div
        className="voice-settings-wrapper"
        style={{
          // Override VoiceSettingsPanel styles to match ToolsPage
          ['--voice-panel-bg' as string]: 'transparent',
          ['--voice-panel-border' as string]: 'none',
          ['--voice-panel-shadow' as string]: 'none',
        }}
      >
        <VoiceSettingsPanel
          className="border-0 shadow-none bg-transparent dark:bg-transparent"
          onSettingsChange={onSettingsChange}
        />
      </div>

      {/* Footer hint */}
      <p className="text-xs text-gray-400 mt-3 flex items-center gap-1">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
        实时配置语音识别模型和语言，更改后立即生效
      </p>

      {/* Style overrides for nested elements */}
      <style>{`
        .voice-settings-wrapper .bg-white,
        .voice-settings-wrapper .dark\\:bg-gray-800 {
          background-color: transparent !important;
        }
        .voice-settings-wrapper .rounded-lg {
          border-radius: var(--radius-lg, 0.75rem) !important;
        }
        .voice-settings-wrapper .shadow {
          box-shadow: none !important;
        }
        .voice-settings-wrapper select,
        .voice-settings-wrapper input {
          border-radius: 0.5rem !important;
        }
      `}</style>
    </div>
  );
}

export default VoiceSettingsCard;
