import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useLiveModeStore } from '../../store/useLiveModeStore';
import { useLiveConsoleStore } from '../../store/useLiveConsoleStore';

/**
 * Tab类型定义
 */
type TabType = 'ai' | 'script' | 'stats';

/**
 * 悬浮窗组件Props
 */
interface FloatingWindowProps {
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 直播模式悬浮窗组件
 * 
 * 功能：
 * - 可拖拽移动
 * - 显示三种类型信息（AI分析、话术、数据统计）
 * - Tab切换
 * - 位置持久化
 */
export const FloatingWindow: React.FC<FloatingWindowProps> = ({ onClose }) => {
  // ========== Store状态 ==========
  const { floatingPosition, updatePosition, switchToFullMode } = useLiveModeStore();
  const { aiEvents, answerScripts, vibe, latest } = useLiveConsoleStore();
  
  // ========== 本地状态 ==========
  const [position, setPosition] = useState(floatingPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [currentTab, setCurrentTab] = useState<TabType>('ai');
  
  const windowRef = useRef<HTMLDivElement>(null);
  
  // ========== 数据提取 ==========
  
  /** 最新的AI分析数据 */
  const latestAIAnalysis = useMemo(() => {
    if (!aiEvents || aiEvents.length === 0) return null;
    return aiEvents[aiEvents.length - 1];
  }, [aiEvents]);
  
  /** 最新的话术 */
  const latestScript = useMemo(() => {
    if (!answerScripts || answerScripts.length === 0) return null;
    return answerScripts[answerScripts.length - 1];
  }, [answerScripts]);
  
  /** 统计数据 */
  const statsData = useMemo(() => ({
    viewerCount: 0, // 从latest或其他数据源提取
    giftValue: 0,
    engagementRate: 0,
  }), [latest]);
  
  // ========== 拖拽逻辑 ==========
  
  /** 鼠标按下 - 开始拖拽 */
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };
  
  /** 拖拽中和释放的处理 */
  useEffect(() => {
    if (!isDragging) return;
    
    const handleMouseMove = (e: MouseEvent) => {
      let newX = e.clientX - dragStart.x;
      let newY = e.clientY - dragStart.y;
      
      // 限制在屏幕边界内
      const maxX = window.innerWidth - (windowRef.current?.offsetWidth || 320);
      const maxY = window.innerHeight - (windowRef.current?.offsetHeight || 240);
      
      newX = Math.max(0, Math.min(newX, maxX));
      newY = Math.max(0, Math.min(newY, maxY));
      
      setPosition({ x: newX, y: newY });
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      // 保存位置到store（会自动持久化到LocalStorage）
      updatePosition(position.x, position.y);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragStart, position, updatePosition]);
  
  // ========== 渲染 ==========
  
  return (
    <div
      ref={windowRef}
      className="floating-window"
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: 320,
        minHeight: 240,
        background: 'rgba(26, 32, 44, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: 16,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        zIndex: 9999,
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: isDragging ? 'none' : 'left 0.2s, top 0.2s',
      }}
    >
      {/* ========== 标题栏 ========== */}
      <div
        className="title-bar"
        onMouseDown={handleMouseDown}
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          cursor: isDragging ? 'grabbing' : 'move',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          userSelect: 'none',
        }}
      >
        <span style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>
          📊 提猫直播助手
        </span>
        
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={switchToFullMode}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: 16,
              padding: '4px 8px',
              borderRadius: 4,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            title="切换到全功能模式"
          >
            ⇄
          </button>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: 18,
              padding: '4px 8px',
              borderRadius: 4,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            title="关闭悬浮窗"
          >
            ×
          </button>
        </div>
      </div>
      
      {/* ========== 内容区 ========== */}
      <div style={{ padding: 16, height: 'calc(100% - 100px)', overflow: 'auto' }}>
        {currentTab === 'ai' && <AIAnalysisContent data={latestAIAnalysis} vibe={vibe} />}
        {currentTab === 'script' && <ScriptContent data={latestScript} />}
        {currentTab === 'stats' && <StatsContent data={statsData} />}
      </div>
      
      {/* ========== 底部Tab栏 ========== */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          display: 'flex',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          padding: 8,
          gap: 4,
        }}
      >
        <TabButton
          active={currentTab === 'ai'}
          onClick={() => setCurrentTab('ai')}
          icon="🤖"
          label="AI"
        />
        <TabButton
          active={currentTab === 'script'}
          onClick={() => setCurrentTab('script')}
          icon="💬"
          label="话术"
        />
        <TabButton
          active={currentTab === 'stats'}
          onClick={() => setCurrentTab('script')}
          icon="📈"
          label="数据"
        />
      </div>
    </div>
  );
};

// ========== 子组件 ==========

/**
 * Tab按钮组件
 */
interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    style={{
      flex: 1,
      padding: '8px 12px',
      background: active ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
      border: active ? '1px solid rgba(168, 85, 247, 0.4)' : '1px solid transparent',
      borderRadius: 8,
      color: active ? '#a855f7' : '#94a3b8',
      fontSize: 12,
      cursor: 'pointer',
      transition: 'all 0.2s',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 4,
    }}
    onMouseEnter={(e) => {
      if (!active) {
        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
      }
    }}
    onMouseLeave={(e) => {
      if (!active) {
        e.currentTarget.style.background = 'transparent';
      }
    }}
  >
    <span style={{ fontSize: 16 }}>{icon}</span>
    <span>{label}</span>
  </button>
);

/**
 * AI分析内容组件
 */
interface AIAnalysisContentProps {
  data: any;
  vibe: any;
}

const AIAnalysisContent: React.FC<AIAnalysisContentProps> = ({ data, vibe }) => {
  if (!data && !vibe) {
    return <EmptyState message="暂无AI分析数据" icon="🤖" />;
  }
  
  const vibeScore = vibe?.score || 0;
  const suggestion = data?.analysis?.suggestion || data?.suggestion || '暂无建议';
  
  return (
    <div style={{ color: 'white', fontSize: 13, lineHeight: 1.6 }}>
      {/* 氛围评分 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 8 }}>氛围评分</div>
        <div style={{ 
          fontSize: 32, 
          fontWeight: 700,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          {vibeScore}
          <span style={{ fontSize: 14, color: '#94a3b8', marginLeft: 4 }}>/100</span>
        </div>
      </div>
      
      {/* AI建议 */}
      <div>
        <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 8 }}>💡 AI建议</div>
        <div style={{
          background: 'rgba(168, 85, 247, 0.1)',
          padding: 12,
          borderRadius: 8,
          fontSize: 12,
          lineHeight: 1.5,
        }}>
          {suggestion}
        </div>
      </div>
    </div>
  );
};

/**
 * 话术内容组件
 */
interface ScriptContentProps {
  data: any;
}

const ScriptContent: React.FC<ScriptContentProps> = ({ data }) => {
  const [copySuccess, setCopySuccess] = useState(false);
  
  if (!data) {
    return <EmptyState message="暂无话术建议" icon="💬" />;
  }
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data.text || data.line || '');
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('复制失败:', error);
    }
  };
  
  return (
    <div style={{ color: 'white', fontSize: 13 }}>
      {/* 话术文本 */}
      <div style={{
        background: 'rgba(168, 85, 247, 0.1)',
        padding: 12,
        borderRadius: 8,
        marginBottom: 12,
        fontSize: 13,
        lineHeight: 1.6,
      }}>
        {data.text || data.line || '暂无话术'}
      </div>
      
      {/* 复制按钮 */}
      <button
        onClick={handleCopy}
        style={{
          width: '100%',
          padding: '10px 16px',
          background: copySuccess 
            ? 'rgba(16, 185, 129, 0.2)' 
            : 'rgba(168, 85, 247, 0.2)',
          border: copySuccess
            ? '1px solid rgba(16, 185, 129, 0.4)'
            : '1px solid rgba(168, 85, 247, 0.3)',
          borderRadius: 8,
          color: copySuccess ? '#10b981' : 'white',
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 500,
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          if (!copySuccess) {
            e.currentTarget.style.background = 'rgba(168, 85, 247, 0.3)';
          }
        }}
        onMouseLeave={(e) => {
          if (!copySuccess) {
            e.currentTarget.style.background = 'rgba(168, 85, 247, 0.2)';
          }
        }}
      >
        {copySuccess ? '✓ 已复制' : '📋 复制话术'}
      </button>
    </div>
  );
};

/**
 * 数据统计内容组件
 */
interface StatsContentProps {
  data: {
    viewerCount: number;
    giftValue: number;
    engagementRate: number;
  };
}

const StatsContent: React.FC<StatsContentProps> = ({ data }) => {
  return (
    <div style={{ color: 'white', fontSize: 13 }}>
      {/* 在线人数 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 6 }}>在线人数</div>
        <div style={{ fontSize: 24, fontWeight: 600 }}>
          {data.viewerCount.toLocaleString()}
        </div>
      </div>
      
      {/* 礼物价值 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 6 }}>礼物价值</div>
        <div style={{ fontSize: 20, fontWeight: 600 }}>
          ¥{data.giftValue.toLocaleString()}
        </div>
      </div>
      
      {/* 互动率 */}
      <div>
        <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 6 }}>互动率</div>
        <div style={{ fontSize: 20, fontWeight: 600 }}>
          {data.engagementRate.toFixed(1)}%
        </div>
      </div>
    </div>
  );
};

/**
 * 空状态组件
 */
interface EmptyStateProps {
  message: string;
  icon: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({ message, icon }) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      color: '#94a3b8',
      fontSize: 13,
    }}
  >
    <span style={{ fontSize: 32, marginBottom: 12 }}>{icon}</span>
    <p>{message}</p>
  </div>
);

