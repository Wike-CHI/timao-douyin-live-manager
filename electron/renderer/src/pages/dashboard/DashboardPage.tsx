const DashboardPage = () => {
  return (
    <div className="h-full timao-card p-8">
      <h1 className="text-2xl font-semibold text-purple-500 mb-4 flex items-center gap-2">
        <span>🚀</span>
        快速上线版本进度
      </h1>
      <p className="timao-support-text">
        登录与支付流程已就绪。接下来将接入实时弹幕、语音转写以及 AI 洞察功能。
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-100/80 to-white shadow">
          <h2 className="text-lg font-semibold text-purple-600">阶段 1 · 完成</h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>✅ 登录 / 注册界面与状态管理</li>
            <li>✅ 支付截图上传与审核流程（占位）</li>
            <li>✅ 主应用壳体与主题切换</li>
          </ul>
        </div>
        <div className="timao-soft-card">
          <h2 className="text-lg font-semibold text-purple-600">下一步</h2>
          <ul className="mt-3 space-y-2 text-sm timao-support-text">
            <li>🚧 集成 AST 语音转写控制面板</li>
            <li>🚧 Douyin 弹幕实时流 UI</li>
            <li>🚧 AI 洞察卡片与冷场提示</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
