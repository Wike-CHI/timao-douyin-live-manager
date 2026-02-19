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
    <div className="h-full timao-card p-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-2">
        功能概览
      </h1>
      <p className="text-gray-500 mb-6">
        这里列出当前版本适合主播的全部能力，方便快速了解还能做什么、该去哪个页面操作。
      </p>

      {!isPaid && !isSuperAdmin && (
        <div className="mb-6 bg-orange-50 border border-orange-200 rounded-lg p-5">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <Sparkles size={20} className="text-orange-600" />
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-gray-900 mb-1">
                解锁全部功能，开启AI直播新体验
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                订阅套餐后即可使用实时字幕、AI分析、话术生成等强大功能
              </p>
              <button
                onClick={() => navigate('/pay/subscription')}
                className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-sm font-medium"
              >
                查看订阅套餐
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-3 md:grid-cols-2">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div key={index} className="timao-soft-card">
              <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <Icon size={18} className="text-gray-500" />
                {feature.title}
              </h2>
              <ul className="space-y-2 text-sm text-gray-600">
                {feature.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
              <div className="mt-4 text-xs text-gray-400">
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
