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
            <span>🎤</span>实时字幕与音量监控
          </h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>输入抖音直播间链接，一键拉起语音转写</li>
            <li>字幕内容本地保存，可随时回看或复制</li>
            <li>音量指示条提醒你是否声音过小</li>
            <li>支持暂停/继续，换场不丢历史记录</li>
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
            <li>AI 实时分析直播状态，给出风格/氛围建议</li>
            <li>遇到冷场可快速生成一句话术</li>
            <li>复盘报告会结合弹幕与转写自动总结亮点</li>
            <li>未来将接入更多互动脚本模板</li>
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
