import React from 'react';

/**
 * Tab内容属性
 */
interface TabContentProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

/**
 * 悬浮窗Tab内容组件
 * 
 * 设计原则：
 * - 简洁明了，主播快速理解
 * - 高对比度，方便在直播中查看
 * - 大字体，不需要凑近屏幕
 */
export const FloatingTabContent: React.FC<TabContentProps> = ({ title, icon, children }) => {
  return (
    <div className="flex flex-col h-full">
      {/* 标题栏 */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-purple-500/20">
        <div className="text-purple-400">{icon}</div>
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      
      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {children}
      </div>
    </div>
  );
};

/**
 * AI建议卡片
 */
interface AICardProps {
  type: 'warning' | 'info' | 'success';
  title: string;
  content: string;
}

export const AICard: React.FC<AICardProps> = ({ type, title, content }) => {
  const bgColors = {
    warning: 'bg-yellow-500/10 border-yellow-500/30',
    info: 'bg-blue-500/10 border-blue-500/30',
    success: 'bg-green-500/10 border-green-500/30'
  };
  
  const textColors = {
    warning: 'text-yellow-400',
    info: 'text-blue-400',
    success: 'text-green-400'
  };
  
  return (
    <div className={`rounded-lg border ${bgColors[type]} p-3 mb-3`}>
      <div className={`text-xs font-medium ${textColors[type]} mb-1`}>{title}</div>
      <div className="text-sm text-white/90 leading-relaxed">{content}</div>
    </div>
  );
};

/**
 * 话术卡片
 */
interface ScriptCardProps {
  title: string;
  content: string;
  isActive?: boolean;
}

export const ScriptCard: React.FC<ScriptCardProps> = ({ title, content, isActive = false }) => {
  return (
    <div 
      className={`
        rounded-lg border p-3 mb-3 transition-all
        ${isActive 
          ? 'bg-purple-500/20 border-purple-500/50' 
          : 'bg-gray-800/50 border-gray-700/50 hover:border-purple-500/30'
        }
      `}
    >
      <div className="text-xs font-medium text-purple-400 mb-1">{title}</div>
      <div className="text-sm text-white/90 leading-relaxed">{content}</div>
    </div>
  );
};

/**
 * 数据指标卡片
 */
interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number; // 变化百分比
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, change, icon }) => {
  const isPositive = change !== undefined && change > 0;
  
  return (
    <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-400">{label}</span>
        {icon && <div className="text-purple-400">{icon}</div>}
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold text-white">{value}</span>
        {change !== undefined && (
          <span className={`text-xs ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '↑' : '↓'} {Math.abs(change)}%
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * 空状态组件
 */
interface EmptyStateProps {
  icon?: React.ReactNode;
  message: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, message }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-500">
      {icon && <div className="text-4xl mb-2">{icon}</div>}
      <p className="text-sm">{message}</p>
    </div>
  );
};

/**
 * 最新转写文本显示
 */
interface TranscriptDisplayProps {
  text: string;
  timestamp?: string;
}

export const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({ text, timestamp }) => {
  if (!text) {
    return <EmptyState icon="🎤" message="等待转写数据..." />;
  }
  
  return (
    <div className="bg-gray-800/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-purple-400 font-medium">最新转写</span>
        {timestamp && <span className="text-xs text-gray-500">{timestamp}</span>}
      </div>
      <div className="text-sm text-white/90 leading-relaxed">
        {text}
      </div>
    </div>
  );
};

