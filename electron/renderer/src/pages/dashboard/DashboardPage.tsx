import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mic,
  MessageSquare,
  Bot,
  User,
  Settings,
  Sparkles
} from 'lucide-react';
import useAuthStore from '../../store/useAuthStore';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { isPaid, user } = useAuthStore();
  const isSuperAdmin = user?.role === 'super_admin';

  const features = [
    {
      icon: Mic,
      title: '实时字幕与音频增强',
      items: [
        '输入抖音直播间链接，自动拉取音频流并实时转写',
        '自动增益（AGC）+ VAD 保持声音稳定，字幕可本地落盘'
      ],
      entry: '侧边栏「直播控制台」'
    },
    {
      icon: MessageSquare,
      title: '弹幕采集与整场复盘',
      items: [
        '弹幕自动拉取并保存，方便统计热词',
        '整场直播分段录制，生成文字稿',
        '支持一键导出弹幕、转写和视频目录',
        '结束后可生成 AI 撰写的复盘报告(待开发)'
      ],
      entry: '「直播控制台」 / 「直播报告」'
    },
    {
      icon: Bot,
      title: 'AI 助手与话术灵感',
      items: [
        'AI agent分析亮点、风险、节奏，结合话者统计提示风险',
        '知识库检索直播运营话术与高情商素材',
        '弹幕卡片一键生成主播口吻话术，支持多种风格'
      ],
      entry: '「直播控制台」底部 AI 区域'
    },
    {
      icon: User,
      title: '账号管理',
      items: [
        '登录后自动保存身份，随时查看账号状态',
        '支持多种功能模式，满足不同使用需求',
        '基于功能权限的灵活管理模式'
      ],
      entry: '侧边栏「设置」'
    },
    {
      icon: Settings,
      title: '工具与设置',
      items: [
        '快速自检：检查模型/音频服务是否就绪',
        '主题、浅色/深色模式自由切换',
        '更多拓展工具正在集成中'
      ],
      entry: '侧边栏「工具」「设置」'
    }
  ];

  return (
    <div className="h-full bg-white/60 backdrop-blur-sm rounded-2xl p-8 border border-gray-100 animate-fade-in">
      <h1 className="text-2xl font-semibold text-gray-900 mb-2">
        功能概览
      </h1>
      <p className="text-gray-500 mb-8">
        这里列出当前版本适合主播的全部能力，方便快速了解还能做什么、该去哪个页面操作。
      </p>

      {/* 订阅提示 */}
      {!isPaid && !isSuperAdmin && (
        <div
          className="mb-8 border rounded-2xl p-6 animate-fade-in-up"
          style={{
            background: 'var(--accent-light)',
            borderColor: 'rgba(var(--accent-rgb), 0.2)',
            animationDelay: '0.1s',
            opacity: 0
          }}
        >
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300 hover:scale-110"
                style={{ background: 'rgba(var(--accent-rgb), 0.1)' }}
              >
                <Sparkles size={22} style={{ color: 'var(--accent-main)' }} />
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-gray-900 mb-1.5">
                解锁全部功能，开启 AI 直播新体验
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                订阅套餐后即可使用实时字幕、AI 分析、话术生成等强大功能
              </p>
              <button
                onClick={() => navigate('/pay/subscription')}
                className="timao-primary-btn text-sm font-medium"
              >
                查看订阅套餐
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 功能卡片 */}
      <div className="grid gap-5 xl:grid-cols-3 md:grid-cols-2">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          const staggerClass = `stagger-${Math.min(index + 1, 5)}` as const;
          return (
            <div
              key={index}
              className={`bg-white rounded-2xl p-6 border border-gray-100 transition-all duration-300 group cursor-default hover:scale-[1.02] timao-card-interactive animate-fade-in-up ${staggerClass}`}
              style={{ opacity: 0 }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(var(--accent-rgb), 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '';
              }}
            >
              <h2 className="text-base font-semibold text-gray-900 flex items-center gap-3 mb-4">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
                  style={{ background: 'rgba(var(--accent-rgb), 0.1)' }}
                >
                  <Icon size={18} style={{ color: 'var(--accent-main)' }} />
                </div>
                {feature.title}
              </h2>
              <ul className="space-y-2.5 text-sm text-gray-600 leading-relaxed">
                {feature.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 transition-all duration-200 hover:translate-x-1">
                    <span
                      className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0"
                      style={{ background: 'var(--accent-main)' }}
                    />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-5 pt-4 border-t border-gray-50 text-xs text-gray-400 group-hover:text-gray-500 transition-colors">
                入口：{feature.entry}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DashboardPage;
