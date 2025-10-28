import logoUrl from '../../assets/logo.jpg';

const AboutPage = () => {
  return (
    <div className="timao-card p-8 space-y-4">
      <div className="flex items-center gap-3">
        <img src={logoUrl} alt="TalkingCat" className="h-12 w-12 rounded-xl ring-2 ring-purple-300 shadow" />
        <div>
          <div className="text-xl font-semibold text-purple-600">提猫直播助手 · TalkingCat</div>
          <div className="text-sm timao-support-text">本地语音转写 + 抖音直播互动 · 隐私不出机</div>
        </div>
      </div>

      <div className="text-sm timao-support-text">
        - 桌面端
        <br />
        - 本地后端
        <br />
        - 语音识别
        <br />
        - 直播互动
      </div>

      <div className="text-xs text-slate-400">
        如需技术支持或商务合作，请联系产品团队。
      </div>
    </div>
  );
};

export default AboutPage;
