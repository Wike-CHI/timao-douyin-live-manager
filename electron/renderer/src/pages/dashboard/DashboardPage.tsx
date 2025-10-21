import React from 'react';

const DashboardPage: React.FC = () => {
  return (
    <div className="h-full timao-card p-8">
      <h1 className="text-2xl font-semibold text-purple-500 mb-4 flex items-center gap-2">
        <span>🎯</span>
        提猫直播助手 · 功能概览
      </h1>
      <p className="timao-support-text">
        这里列出当前版本适合主播的全部能力，方便快速了解还能做什么、该去哪个页面操作。
      </p>

      <div className="mt-6 grid gap-4 xl:grid-cols-3 md:grid-cols-2">
        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🎤</span>实时字幕与音频增强
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>输入抖音直播间链接，即刻拉起 SenseVoice 实时转写</li>
            <li>自动增益（AGC）+ VAD 保持声音稳定，字幕可本地落盘</li>
            <li>内置说话人分离，字幕自动标注【主播 / 嘉宾】身份</li>
            <li>音量指示条与最近发言者提示，及时把握麦克风状态</li>
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
            <li>结束后可生成 AI 撰写的复盘报告</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：「直播控制台」&nbsp;/&nbsp;「直播报告」</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🤖</span>AI 助手与话术灵感
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>LangGraph Workflow 滚动分析亮点、风险、节奏，结合话者统计提示“对手抢话”风险</li>
            <li>知识库检索直播运营话术与高情商素材，融合到分析卡片与答疑口播</li>
            <li>弹幕卡片一键生成主播口吻话术，支持暖心 / 直接 / 调侃多种风格</li>
            <li>复盘报告自动汇总弹幕、转写与 AI 观察，沉淀可复用笔记</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：「直播控制台」底部 AI 区域</div>
        </div>

        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600 flex items-center gap-2">
            <span>🧾</span>钱包与账号管理
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>登录后自动保存身份，随时查看余额</li>
            <li>首次可领取一次免费使用额度</li>
            <li>钱包页支持上传转账凭证，提醒补充套餐</li>
            <li>账号内所有功能已与鉴权打通</li>
          </ul>
          <div className="mt-4 text-xs text-purple-500">入口：侧边栏「支付」&nbsp;/&nbsp;右上角余额卡片</div>
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
