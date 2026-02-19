import React, { useState, useEffect } from "react";
import {
  FloatingTabContent,
  AICard,
  ScriptCard,
  MetricCard,
  EmptyState,
  TranscriptDisplay,
} from "../components/floating";
import { Pin, X, Bot, MessageSquare, BarChart3, Users, Heart, Gift, AlertTriangle, Lightbulb, Copy, Check } from 'lucide-react';

/**
 * 悬浮窗数据类型
 */
interface FloatingData {
  latestTranscript?: string;
  aiAnalysis?: any;
  script?: any;
  stats?: {
    peak_viewers?: number; // 最高在线人数
    follows?: number; // 新增关注
    gifts?: Record<string, number>; // 礼物列表 {礼物名: 数量}
  };
  vibe?: any;
}

/**
 * Tab类型
 */
type TabType = "ai" | "script" | "stats";

/**
 * 独立悬浮窗页面
 *
 * 运行在独立的BrowserWindow中
 * 特点：
 * - 通过IPC接收主窗口推送的数据
 * - 使用Electron原生窗口拖拽
 * - 始终置顶，可覆盖OBS等全屏应用
 */
const FloatingWindowPage: React.FC = () => {
  const [data, setData] = useState<FloatingData>({});
  const [currentTab, setCurrentTab] = useState<TabType>("ai");
  const [alwaysOnTop, setAlwaysOnTop] = useState<boolean>(true); // 🆕 置顶状态

  // ========== 🆕 切换置顶状态 ==========

  const handleToggleAlwaysOnTop = async () => {
    if (window.electronAPI?.toggleFloatingAlwaysOnTop) {
      try {
        const result = await window.electronAPI.toggleFloatingAlwaysOnTop();
        if (result.success && result.alwaysOnTop !== undefined) {
          setAlwaysOnTop(result.alwaysOnTop);
          console.log("📌 置顶状态已切换:", result.alwaysOnTop);
        }
      } catch (error) {
        console.error("❌ 切换置顶状态失败:", error);
      }
    }
  };

  // ========== IPC数据接收 ==========

  useEffect(() => {
    console.log("🚀 悬浮窗页面加载完成");

    // 🆕 获取初始置顶状态
    if (window.electronAPI?.getFloatingAlwaysOnTop) {
      window.electronAPI.getFloatingAlwaysOnTop().then((state) => {
        setAlwaysOnTop(state);
        console.log("📌 初始置顶状态:", state);
      });
    }

    // 监听来自主窗口的数据推送
    if (window.electronAPI?.onFloatingData) {
      const cleanup = window.electronAPI.onFloatingData(
        (newData: FloatingData) => {
          console.log("📦 收到数据更新:", newData);
          setData((prev) => ({
            ...prev,
            ...newData,
          }));
        },
      );

      return cleanup;
    } else {
      console.warn("⚠️ electronAPI.onFloatingData 不可用");
    }
  }, []);

  // ========== 渲染 ==========

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background:
          "linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.80) 50%, rgba(190, 24, 93, 0.15) 100%)",
        backdropFilter: "blur(20px)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5), 0 0 60px rgba(244, 114, 182, 0.1)",
        borderRadius: "16px",
        border: "1px solid rgba(244, 114, 182, 0.2)",
      }}
    >
      {/* ========== 顶部拖拽区域 ========== */}
      <div
        style={{
          // @ts-ignore - Electron特有属性
          WebkitAppRegion: "drag", // 允许拖拽整个窗口
          height: 36,
          background: "rgba(0, 0, 0, 0.25)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 12px",
          borderTopLeftRadius: "16px",
          borderTopRightRadius: "16px",
        }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "#f472b6",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span>直播助手</span>
        </div>

        {/* 🆕 右侧按钮组 */}
        <div
          style={{
            display: "flex",
            gap: 8,
            // @ts-ignore - Electron特有属性
            WebkitAppRegion: "no-drag", // 按钮区域不拖拽
          }}
        >
          {/* 🆕 钉子按钮（切换置顶） */}
          <button
            onClick={handleToggleAlwaysOnTop}
            title={alwaysOnTop ? "取消置顶" : "窗口置顶"}
            style={{
              width: 24,
              height: 24,
              borderRadius: 8,
              border: "none",
              background: alwaysOnTop
                ? "rgba(244, 114, 182, 0.25)"
                : "transparent",
              color: alwaysOnTop ? "#f472b6" : "#94a3b8",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = alwaysOnTop
                ? "rgba(244, 114, 182, 0.4)"
                : "rgba(148, 163, 184, 0.2)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = alwaysOnTop
                ? "rgba(244, 114, 182, 0.25)"
                : "transparent";
            }}
          >
            <Pin size={14} />
          </button>

          {/* 关闭按钮 */}
          <button
            onClick={() => window.close()}
            style={{
              width: 24,
              height: 24,
              borderRadius: 8,
              border: "none",
              background: "transparent",
              color: "#94a3b8",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(239, 68, 68, 0.25)";
              e.currentTarget.style.color = "#ef4444";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#94a3b8";
            }}
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* ========== 最新转写（始终显示） ========== */}
      <div
        style={{
          padding: 12,
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <TranscriptDisplay
          text={data.latestTranscript || ""}
          timestamp={new Date().toLocaleTimeString()}
        />
      </div>

      {/* ========== 内容区域 ========== */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {currentTab === "ai" && (
          <AIAnalysisContent data={data.aiAnalysis} vibe={data.vibe} />
        )}
        {currentTab === "script" && <ScriptContent data={data.script} />}
        {currentTab === "stats" && <StatsContent data={data.stats} />}
      </div>

      {/* ========== 底部Tab栏 ========== */}
      <div
        style={{
          display: "flex",
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
          padding: 10,
          gap: 6,
          background: "rgba(0, 0, 0, 0.2)",
          borderBottomLeftRadius: "16px",
          borderBottomRightRadius: "16px",
          // @ts-ignore - Electron特有属性
          WebkitAppRegion: "no-drag", // Tab栏不拖拽
        }}
      >
        <TabButton
          active={currentTab === "ai"}
          onClick={() => setCurrentTab("ai")}
          icon={Bot}
          label="AI"
        />
        <TabButton
          active={currentTab === "script"}
          onClick={() => setCurrentTab("script")}
          icon={MessageSquare}
          label="话术"
        />
        <TabButton
          active={currentTab === "stats"}
          onClick={() => setCurrentTab("stats")}
          icon={BarChart3}
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
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
}

const TabButton: React.FC<TabButtonProps> = ({
  active,
  onClick,
  icon: Icon,
  label,
}) => (
  <button
    onClick={onClick}
    className={`
      flex-1 flex flex-col items-center gap-1 py-2 px-3
      rounded-xl border transition-all cursor-pointer
      ${
        active
          ? "bg-rose-500/25 border-rose-500/40 text-rose-400"
          : "bg-transparent border-transparent text-gray-400 hover:bg-white/5"
      }
    `}
  >
    <Icon size={16} className="text-base" />
    <span className="text-xs">{label}</span>
  </button>
);

/**
 * AI分析内容组件
 */
interface AIAnalysisContentProps {
  data: any;
  vibe: any;
}

const AIAnalysisContent: React.FC<AIAnalysisContentProps> = ({
  data,
  vibe,
}) => {
  if (!data && !vibe) {
    return <EmptyState icon={Bot} message="等待AI分析..." />;
  }

  return (
    <FloatingTabContent title="AI分析" icon={Bot}>
      {/* 氛围评估 */}
      {vibe && (
        <div className="bg-rose-500/15 border border-rose-500/30 rounded-xl p-3 mb-3">
          <div className="text-xs text-rose-400 mb-1">氛围评分</div>
          <div className="text-2xl font-bold text-white">
            {vibe.score || 0}{" "}
            <span className="text-sm text-gray-400">/100</span>
          </div>
          {vibe.description && (
            <div className="text-xs text-gray-300 mt-1">{vibe.description}</div>
          )}
        </div>
      )}

      {/* AI建议列表 */}
      {data?.suggestions?.map((suggestion: string, idx: number) => (
        <AICard
          key={idx}
          type="success"
          title={`建议 ${idx + 1}`}
          content={suggestion}
        />
      ))}

      {/* 风险提示 */}
      {data?.warnings?.map((warning: string, idx: number) => (
        <AICard
          key={`warning-${idx}`}
          type="warning"
          title="注意"
          content={warning}
        />
      ))}

      {/* 单个建议（兼容旧数据格式） */}
      {!data?.suggestions && data?.suggestion && (
        <AICard type="info" title="AI建议" content={data.suggestion} />
      )}
    </FloatingTabContent>
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
    return <EmptyState icon={MessageSquare} message="等待智能话术..." />;
  }

  const handleCopy = async () => {
    try {
      const textToCopy = data.text || data.line || "";
      await navigator.clipboard.writeText(textToCopy);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error("复制失败:", error);
    }
  };

  return (
    <FloatingTabContent title="智能话术" icon={MessageSquare}>
      {/* 话术卡片 */}
      <ScriptCard
        title={data.title || "推荐话术"}
        content={data.text || data.line || "暂无话术"}
        isActive={true}
      />

      {/* 话术类型标签 */}
      {data.type && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-400">类型:</span>
          <span className="text-xs px-2 py-1 bg-orange-500/20 text-orange-400 rounded">
            {data.type}
          </span>
        </div>
      )}

      {/* 复制按钮 */}
      <button
        onClick={handleCopy}
        className={`
          w-full py-2.5 px-4 rounded-lg border text-sm font-medium transition-all flex items-center justify-center gap-2
          ${
            copySuccess
              ? "bg-green-500/20 border-green-500/40 text-green-400"
              : "bg-orange-500/20 border-orange-500/40 text-orange-400 hover:bg-orange-500/30"
          }
        `}
      >
        {copySuccess ? <Check size={14} /> : <Copy size={14} />}
        {copySuccess ? "已复制" : "复制话术"}
      </button>
    </FloatingTabContent>
  );
};

/**
 * 数据统计内容组件
 */
interface StatsContentProps {
  data: FloatingData["stats"];
}

const StatsContent: React.FC<StatsContentProps> = ({ data }) => {
  // 计算礼物总价值（1钻石 ≈ ¥0.1）
  const calculateGiftValue = (): number => {
    if (!data?.gifts) return 0;
    // 这里简化处理，假设礼物名称或数量可以映射到钻石价值
    // 实际应该根据礼物价格表计算
    const totalCount = Object.values(data.gifts).reduce(
      (sum, count) => sum + count,
      0,
    );
    return totalCount * 0.1; // 简化：每个礼物按1钻石计算
  };

  const giftValue = calculateGiftValue();

  return (
    <FloatingTabContent title="实时数据" icon={BarChart3}>
      <MetricCard
        label="最高在线"
        value={data?.peak_viewers?.toLocaleString() || "0"}
        icon={Users}
      />

      <MetricCard
        label="新增关注"
        value={data?.follows?.toLocaleString() || "0"}
        icon={Heart}
      />

      <MetricCard
        label="礼物价值"
        value={`¥${giftValue.toFixed(2)}`}
        icon={Gift}
      />

      {/* 数据说明 */}
      <div className="mt-4 p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <p className="text-xs text-gray-400 leading-relaxed">
          数据实时更新，礼物价值按1钻石≈¥0.1估算
        </p>
      </div>
    </FloatingTabContent>
  );
};

export default FloatingWindowPage;
