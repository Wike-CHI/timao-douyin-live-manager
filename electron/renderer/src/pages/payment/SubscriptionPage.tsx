import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  aiQuota: number;
  duration: number; // 天数
  features: string[];
  popular?: boolean;
}

interface UserSubscription {
  plan: string;
  aiQuotaUsed: number;
  aiQuotaRemaining: number;
  expiresAt: string;
  isActive: boolean;
}

const subscriptionPlans: SubscriptionPlan[] = [
  {
    id: 'basic',
    name: '基础版',
    price: 29,
    aiQuota: 1000,
    duration: 30,
    features: [
      '1000 次 AI 分析',
      '基础直播数据统计',
      '实时弹幕监控',
      '邮件客服支持'
    ]
  },
  {
    id: 'pro',
    name: '专业版',
    price: 59,
    aiQuota: 3000,
    duration: 30,
    features: [
      '3000 次 AI 分析',
      '高级数据分析报告',
      '智能话术推荐',
      '实时互动洞察',
      '优先客服支持'
    ],
    popular: true
  },
  {
    id: 'premium',
    name: '旗舰版',
    price: 99,
    aiQuota: 8000,
    duration: 30,
    features: [
      '8000 次 AI 分析',
      '全功能数据分析',
      'AI 冷场守护',
      '个性化推荐算法',
      '专属客服经理',
      '定制化功能开发'
    ]
  }
];

const SubscriptionPage = () => {
  const navigate = useNavigate();
  const { user, setFirstFreeUsed } = useAuthStore();
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  useEffect(() => {
    // 模拟获取用户当前订阅信息
    // 在实际应用中，这里应该调用 API 获取用户订阅状态
    const mockSubscription: UserSubscription = {
      plan: 'free',
      aiQuotaUsed: 50,
      aiQuotaRemaining: 0,
      expiresAt: new Date().toISOString(),
      isActive: false
    };
    setCurrentSubscription(mockSubscription);
  }, []);

  const handleSubscribe = (planId: string) => {
    setSelectedPlan(planId);
    setShowPaymentModal(true);
  };

  const handlePayment = async () => {
    setLoading(true);
    try {
      // 模拟支付处理
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 支付成功后更新用户状态
      setFirstFreeUsed(false); // 重置免费使用状态
      
      // 跳转到主应用
      navigate('/dashboard');
    } catch (error) {
      console.error('支付失败:', error);
    } finally {
      setLoading(false);
      setShowPaymentModal(false);
    }
  };

  const selectedPlanDetails = subscriptionPlans.find(plan => plan.id === selectedPlan);

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-purple-600 mb-4">选择订阅套餐</h1>
        <p className="text-lg timao-support-text">
          解锁全部 AI 功能，提升直播效率
        </p>
      </div>

      {/* 当前订阅状态 */}
      {currentSubscription && (
        <div className="timao-card p-6">
          <h2 className="text-xl font-semibold text-purple-600 mb-4 flex items-center gap-2">
            <span>📊</span>
            当前使用情况
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="timao-soft-card text-center">
              <div className="text-2xl font-bold text-purple-600">
                {currentSubscription.aiQuotaUsed}
              </div>
              <div className="text-sm timao-support-text">已使用 AI 次数</div>
            </div>
            <div className="timao-soft-card text-center">
              <div className="text-2xl font-bold text-orange-500">
                {currentSubscription.aiQuotaRemaining}
              </div>
              <div className="text-sm timao-support-text">剩余 AI 次数</div>
            </div>
            <div className="timao-soft-card text-center">
              <div className={`text-2xl font-bold ${currentSubscription.isActive ? 'text-green-500' : 'text-red-500'}`}>
                {currentSubscription.isActive ? '有效' : '已过期'}
              </div>
              <div className="text-sm timao-support-text">订阅状态</div>
            </div>
          </div>
          {!currentSubscription.isActive && (
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <div className="flex items-center gap-2 text-amber-800">
                <span>⚠️</span>
                <span className="font-medium">您的免费试用已结束，请选择合适的订阅套餐继续使用</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 订阅套餐 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {subscriptionPlans.map((plan) => (
          <div
            key={plan.id}
            className={`timao-card relative ${plan.popular ? 'ring-2 ring-purple-300' : ''}`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-purple-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  推荐
                </span>
              </div>
            )}
            
            <div className="text-center mb-6">
              <h3 className="text-xl font-bold text-purple-600 mb-2">{plan.name}</h3>
              <div className="text-3xl font-bold text-slate-800 mb-1">
                ¥{plan.price}
                <span className="text-lg font-normal text-slate-500">/月</span>
              </div>
              <div className="text-sm timao-support-text">
                {plan.aiQuota.toLocaleString()} 次 AI 分析
              </div>
            </div>

            <ul className="space-y-3 mb-8">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center gap-3 text-sm">
                  <span className="text-green-500">✓</span>
                  <span>{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSubscribe(plan.id)}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                plan.popular
                  ? 'timao-primary-btn'
                  : 'timao-outline-btn hover:bg-purple-50'
              }`}
            >
              选择套餐
            </button>
          </div>
        ))}
      </div>

      {/* 支付模态框 */}
      {showPaymentModal && selectedPlanDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="text-center mb-6">
              <h3 className="text-xl font-bold text-purple-600 mb-2">确认订阅</h3>
              <p className="timao-support-text">您选择了 {selectedPlanDetails.name}</p>
            </div>

            <div className="timao-soft-card mb-6">
              <div className="flex justify-between items-center mb-2">
                <span>套餐名称</span>
                <span className="font-medium">{selectedPlanDetails.name}</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span>AI 分析次数</span>
                <span className="font-medium">{selectedPlanDetails.aiQuota.toLocaleString()} 次</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span>有效期</span>
                <span className="font-medium">{selectedPlanDetails.duration} 天</span>
              </div>
              <div className="flex justify-between items-center text-lg font-bold text-purple-600 pt-2 border-t">
                <span>总计</span>
                <span>¥{selectedPlanDetails.price}</span>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={handlePayment}
                disabled={loading}
                className="w-full timao-primary-btn"
              >
                {loading ? '处理中...' : '确认支付'}
              </button>
              <button
                onClick={() => setShowPaymentModal(false)}
                disabled={loading}
                className="w-full timao-outline-btn"
              >
                取消
              </button>
            </div>

            <div className="mt-4 text-xs text-center timao-support-text">
              支付后立即生效，如有问题请联系客服
            </div>
          </div>
        </div>
      )}

      {/* 底部说明 */}
      <div className="text-center timao-support-text">
        <p className="mb-2">🔒 安全支付 · 7天无理由退款</p>
        <p className="text-xs">
          如有疑问，请联系客服：support@timao.com
        </p>
      </div>
    </div>
  );
};

export default SubscriptionPage;