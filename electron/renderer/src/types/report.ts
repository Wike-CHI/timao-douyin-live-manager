/**
 * 直播复盘相关的类型定义
 */

export interface AIMetadata {
  model: string;
  cost: number;
  tokens: number;
  duration: number;
}

export interface AISummary {
  summary?: string;
  highlight_points?: string[];
  risks?: string[];
  suggestions?: string[];
  overall_score?: number;
  performance_analysis?: any;
  key_highlights?: string[];  // Gemini 生成的亮点列表
  key_issues?: string[];  // Gemini 生成的问题列表
  improvement_suggestions?: any[];  // Gemini 生成的改进建议
  gemini_metadata?: AIMetadata;
  error?: string;
}

export interface ReviewData {
  session_id: string;
  room_id?: string;
  anchor_name?: string;
  started_at?: number;
  stopped_at?: number;
  ended_at?: number;  // 添加结束时间
  duration_seconds?: number;
  pause_count?: number;  // 🆕 暂停次数
  metrics?: Record<string, any>;
  transcript?: string;
  comments_count?: number;
  ai_summary?: AISummary;
  transcript_chars?: number;
  segments_count?: number;
  trend_charts?: Record<string, any>;  // 添加趋势图数据
  // 🆕 送礼大哥榜
  top_gift_users?: Array<{
    nickname: string;
    total_value: number;
    yuan_value: number;
    tier: string;
    label: string;
    color: string;
    icon: string;
  }>;
  // 🆕 在线人数快照
  viewer_snapshots?: Array<{
    timestamp: number;
    minute: number;
    count: number;
    elapsed_seconds: number;
  }>;
}

export interface ReportArtifacts {
  comments?: string;
  transcript?: string;
  report?: string;
  review_data?: ReviewData;
}
