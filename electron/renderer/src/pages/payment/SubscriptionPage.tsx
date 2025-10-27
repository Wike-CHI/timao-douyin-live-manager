import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../../store/useAuthStore';
import {
  getPlans,
  getCurrentSubscription,
  createAndConfirmPayment,
  validateCoupon,
  type Plan,
  type Subscription,
  type Coupon
} from '../../services/payment';
import type { UserInfo } from '../../services/auth'; // 导入UserInfo类型

const SubscriptionPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [availablePlans, setAvailablePlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [couponCode, setCouponCode] = useState('');
  const [couponValidation, setCouponValidation] = useState<{
    valid: boolean;
    discount_amount?: number;
    final_amount?: number;
    message?: string;
  } | null>(null);
  const [error, setError] = useState<string>('');

  // 加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // 并行加载套餐和当前订阅
      const [plans, subscription] = await Promise.all([
        getPlans(),
        getCurrentSubscription()
      ]);
      
      setAvailablePlans(plans);
      setCurrentSubscription(subscription);
    } catch (error) {
      console.error('加载数据失败:', error);
      setError('加载数据失败，请刷新页面重试');
    } finally {
      setLoading(false);
    }
  };

  // 验证优惠券
  const handleValidateCoupon = async (planId: string) => {
    if (!couponCode.trim()) {
      setCouponValidation(null);
      return;
    }

    const plan = availablePlans.find(p => p.id === planId);
    if (!plan) return;

    try {
      const result = await validateCoupon(couponCode.trim(), plan.price);
      setCouponValidation(result);
    } catch (error) {
      setCouponValidation({
        valid: false,
        message: '优惠券验证失败'
      });
    }
  };

  const handleSubscribe = (planId: string) => {
    setSelectedPlan(planId);
    setShowPaymentModal(true);
    setCouponCode('');
    setCouponValidation(null);
  };

  const handlePayment = async (method: 'alipay' | 'wechat' | 'bank_transfer') => {
    if (!selectedPlan) return;

    setLoading(true);
    setError('');
    
    try {
      const result = await createAndConfirmPayment(selectedPlan, method);
      
      if (result.success) {
        // 支付成功，更新状态
        setCurrentSubscription(result.subscription || null);
        
        // 跳转到主应用
        navigate('/dashboard');
      } else {
        setError(result.message || '支付失败，请重试');
      }
    } catch (error) {
      console.error('支付失败:', error);
      setError((error as Error).message || '支付失败，请重试');
    } finally {
      setLoading(false);
      setShowPaymentModal(false);
    }
  };

  const selectedPlanDetails = availablePlans.find(plan => plan.id === selectedPlan);
  const finalAmount = couponValidation?.valid ? couponValidation.final_amount : selectedPlanDetails?.price;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">选择您的订阅套餐</h1>
          <p className="text-xl text-gray-600">解锁更多 AI 分析功能，提升直播效果</p>
        </div>

        {/* 超级管理员提示 */}
        {user?.role === 'super_admin' && (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-800">
                  您是超级管理员，已自动获得所有功能权限，无需订阅即可使用所有功能。
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 当前订阅状态 */}
        {currentSubscription && (
          <div className="mb-12 bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">当前订阅状态</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-blue-900">套餐类型</h3>
                <p className="text-2xl font-bold text-blue-600">{currentSubscription.plan_name}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-green-900">订阅状态</h3>
                <p className="text-2xl font-bold text-green-600">
                  {currentSubscription.is_active ? '活跃' : '已过期'}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-purple-900">到期时间</h3>
                <p className="text-lg font-semibold text-purple-600">
                  {currentSubscription.end_date ? new Date(currentSubscription.end_date).toLocaleDateString() : '永久'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 加载状态 */}
        {loading && availablePlans.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="mt-4 text-gray-600">加载中...</p>
          </div>
        ) : (
          /* 套餐列表 */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {availablePlans.map((plan) => (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl shadow-xl overflow-hidden transform transition-all duration-300 hover:scale-105 ${
                  plan.is_popular ? 'ring-2 ring-indigo-500' : ''
                }`}
              >
                {plan.is_popular && (
                  <div className="absolute top-0 right-0 bg-indigo-500 text-white px-4 py-1 text-sm font-medium rounded-bl-lg">
                    推荐
                  </div>
                )}
                
                <div className="p-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-indigo-600">¥{plan.price}</span>
                    <span className="text-gray-500 ml-2">/{plan.duration}天</span>
                  </div>
                  
                  <div className="mb-6">
                    <div className="flex items-center mb-2">
                      <span className="text-lg font-semibold text-gray-900">套餐时长</span>
                    </div>
                    <span className="text-2xl font-bold text-green-600">{plan.duration}</span>
                    <span className="text-gray-500 ml-1">天</span>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature: string, index: number) => (
                      <li key={index} className="flex items-start">
                        <svg className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleSubscribe(plan.id)}
                    disabled={loading}
                    className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-colors duration-200 ${
                      plan.is_popular
                        ? 'bg-indigo-600 hover:bg-indigo-700'
                        : 'bg-gray-600 hover:bg-gray-700'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {loading ? '处理中...' : '立即订阅'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 支付模态框 */}
        {showPaymentModal && selectedPlanDetails && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">确认订阅</h3>
                <button
                  onClick={() => setShowPaymentModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold text-lg">{selectedPlanDetails.name}</h4>
                <p className="text-gray-600">{selectedPlanDetails.description} / {selectedPlanDetails.duration} 天</p>
                
                {/* 优惠券输入 */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    优惠券代码（可选）
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value)}
                      placeholder="输入优惠券代码"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <button
                      onClick={() => handleValidateCoupon(selectedPlan)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                    >
                      验证
                    </button>
                  </div>
                  
                  {couponValidation && (
                    <div className={`mt-2 text-sm ${couponValidation.valid ? 'text-green-600' : 'text-red-600'}`}>
                      {couponValidation.message || (couponValidation.valid ? '优惠券有效' : '优惠券无效')}
                    </div>
                  )}
                </div>

                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span>原价:</span>
                    <span>¥{selectedPlanDetails.price}</span>
                  </div>
                  {couponValidation?.valid && (
                    <div className="flex justify-between items-center text-green-600">
                      <span>优惠:</span>
                      <span>-¥{couponValidation.discount_amount}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center font-semibold text-lg border-t pt-2 mt-2">
                    <span>实付:</span>
                    <span>¥{finalAmount}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => handlePayment('alipay')}
                  disabled={loading}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  <span className="mr-2">💰</span>
                  支付宝支付
                </button>
                
                <button
                  onClick={() => handlePayment('wechat')}
                  disabled={loading}
                  className="w-full py-3 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  <span className="mr-2">💚</span>
                  微信支付
                </button>
                
                <button
                  onClick={() => handlePayment('bank_transfer')}
                  disabled={loading}
                  className="w-full py-3 px-4 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  <span className="mr-2">🏦</span>
                  银行转账
                </button>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionPage;