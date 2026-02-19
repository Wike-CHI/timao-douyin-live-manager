import logoUrl from '../../assets/logo.jpg';

const AboutPage = () => {
  return (
    <div className="timao-card p-8 space-y-4">
      <div className="flex items-center gap-3">
        <img src={logoUrl} alt="TalkingCat" className="h-12 w-12 rounded-lg" />
        <div>
          <div className="text-xl font-semibold text-gray-900">提猫直播助手</div>
          <div className="text-sm text-gray-500">本地语音转写 + 抖音直播互动</div>
        </div>
      </div>

      <div className="text-sm text-gray-600 space-y-1">
        <div>桌面端应用</div>
        <div>本地后端服务</div>
        <div>语音识别引擎</div>
        <div>直播互动功能</div>
      </div>

      <div className="text-xs text-gray-400">
        如需技术支持或商务合作，请联系产品团队。
      </div>
    </div>
  );
};

export default AboutPage;
