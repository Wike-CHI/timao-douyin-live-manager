import React from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { isPaid, user } = useAuthStore();
  const isSuperAdmin = user?.role === 'super_admin';

  return (
    <div className="h-full timao-card p-8">
      <h1 className="text-2xl font-semibold text-purple-500 mb-4 flex items-center gap-2">
        <span>🎯</span>
        提猫直播助手 · 功能概览
      </h1>
      <p className="timao-support-text">
        这里列出当前版本适合主播的全部能力，方便快速了解还能做什么、该去哪个页面操作。
      </p>

      {/* 未付费用户提示 */}
      {!isPaid && !isSuperAdmin && (
        <div className="mt-6 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🎁</span>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">
                解锁全部功能，开启AI直播新体验
              </h3>
              <p className="text-sm text-purple-700 mb-4">
                订阅套餐后即可使用实时字幕、AI分析、话术生成等强大功能，让您的直播更加出色！
              </p>
              <button
                onClick={() => navigate('/pay/subscription')}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-sm"
              >
                查看订阅套餐 →
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 grid gap-4 xl:grid-cols-3 md:grid-cols-2">
        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🎤</span>实时字幕与音频增强
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>输入抖音直播间链接，自动拉取音频流并实时转写</li>
            <li>自动增益（AGC）+ VAD 保持声音稳定，字幕可本地落盘</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：侧边栏「直播控制台」</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>💬</span>弹幕采集与整场复盘
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>弹幕自动拉取并保存，方便统计热词</li>
            <li>整场直播分段录制，生成文字稿</li>
            <li>支持一键导出弹幕、转写和视频目录</li>
            <li>结束后可生成 AI 撰写的复盘报告(待开发)</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：「直播控制台」&nbsp;/&nbsp;「直播报告」</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🤖</span>AI 助手与话术灵感
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>AI agent分析亮点、风险、节奏，结合话者统计提示“对手抢话”风险</li>
            <li>知识库检索直播运营话术与高情商素材，融合到分析卡片与答疑口播</li>
            <li>弹幕卡片一键生成主播口吻话术，支持暖心 / 直接 / 调侃多种风格</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：「直播控制台」底部 AI 区域</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🧾</span>账号管理
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>登录后自动保存身份，随时查看账号状态</li>
            <li>支持多种功能模式，满足不同使用需求</li>
            <li>基于功能权限的灵活管理模式</li>
            <li>账号内所有功能已与鉴权打通</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：侧边栏「设置」</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🔧</span>工具与设置
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>快速自检：检查模型/音频服务是否就绪</li>
            <li>主题、浅色/深色模式自由切换</li>
            <li>更多拓展工具正在集成中</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：侧边栏「工具」「设置」</div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
