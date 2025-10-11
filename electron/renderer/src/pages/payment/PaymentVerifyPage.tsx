import React, { ChangeEvent, FormEvent, useEffect, useRef, useState } from 'react';
import useAuthStore from '../../store/useAuthStore';
import { pollPayment, uploadPayment } from '../../services/auth';

type PaymentStatus = 'UNPAID' | 'PENDING' | 'APPROVED' | 'REJECTED';

interface PollConfig {
  interval: number; // 轮询间隔（毫秒）
  maxAttempts: number; // 最大轮询次数
  timeout: number; // 总超时时间（毫秒）
}

const DEFAULT_POLL_CONFIG: PollConfig = {
  interval: 3000, // 每3秒轮询一次
  maxAttempts: 100, // 最多轮询100次
  timeout: 5 * 60 * 1000, // 总超时5分钟
};

const PaymentVerifyPage = () => {
  const { setPaid } = useAuthStore();
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('请上传微信/支付宝收款截图，审核通过后即可使用全部功能。');
  const [status, setStatus] = useState<PaymentStatus>('UNPAID');
  const [loading, setLoading] = useState(false);
  const [pollAttempts, setPollAttempts] = useState(0);
  const [pollProgress, setPollProgress] = useState(0); // 轮询进度（0-100）
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  // 清理轮询定时器
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const targetFile = event.target.files?.[0] ?? null;
    setFile(targetFile);
  };

  /**
   * 启动轮询审核状态
   */
  const startPolling = (config: PollConfig = DEFAULT_POLL_CONFIG) => {
    // 清理之前的轮询
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    startTimeRef.current = Date.now();
    let attempts = 0;

    const poll = async () => {
      try {
        attempts += 1;
        setPollAttempts(attempts);

        // 计算进度（基于时间和次数）
        const elapsed = Date.now() - startTimeRef.current;
        const timeProgress = Math.min((elapsed / config.timeout) * 100, 100);
        const attemptProgress = Math.min((attempts / config.maxAttempts) * 100, 100);
        setPollProgress(Math.max(timeProgress, attemptProgress));

        // 检查超时
        if (elapsed >= config.timeout) {
          stopPolling();
          setStatus('PENDING');
          setMessage(`审核超时（已轮询 ${attempts} 次）。审核可能需要更长时间，请稍后刷新页面查看结果，或联系客服。`);
          return;
        }

        // 检查最大次数
        if (attempts >= config.maxAttempts) {
          stopPolling();
          setStatus('PENDING');
          setMessage(`已达最大轮询次数（${attempts} 次）。审核可能需要更长时间，请稍后刷新页面查看结果。`);
          return;
        }

        // 调用后端查询审核状态
        const pollResult = await pollPayment();
        
        if (pollResult.success) {
          // 解析审核状态
          const paymentStatus = (pollResult.status || 'pending').toLowerCase();
          
          if (paymentStatus === 'approved' || paymentStatus === 'paid') {
            // 审核通过
            stopPolling();
            setStatus('APPROVED');
            setMessage('审核通过！您现在可以使用全部功能了。');
            setPaid(true);
            setPollProgress(100);
          } else if (paymentStatus === 'rejected' || paymentStatus === 'failed') {
            // 审核拒绝
            stopPolling();
            setStatus('REJECTED');
            setMessage(pollResult.message || '审核未通过，请重新上传符合要求的支付凭证。');
            setPollProgress(0);
          } else {
            // 仍在审核中，继续轮询
            setStatus('PENDING');
            setMessage(`审核中...（已等待 ${Math.floor(elapsed / 1000)} 秒，第 ${attempts} 次查询）`);
          }
        } else {
          // 查询失败，可能是网络问题，继续轮询
          console.warn('轮询失败:', pollResult.message);
          setMessage(`审核中...（查询状态失败，将继续尝试）`);
        }
      } catch (err) {
        console.error('轮询错误:', err);
        // 发生错误时继续轮询，除非达到限制
      }
    };

    // 立即执行第一次轮询
    poll();

    // 启动定时轮询
    pollingRef.current = setInterval(poll, config.interval);
  };

  /**
   * 停止轮询
   */
  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setMessage('请先选择截图文件');
      return;
    }
    try {
      setLoading(true);
      setPollAttempts(0);
      setPollProgress(0);
      setMessage('正在上传审核材料...');
      
      // 上传支付凭证
      const uploadResult = await uploadPayment(file);
      
      if (uploadResult.success) {
        setStatus('PENDING');
        setMessage('上传成功，正在等待人工审核...');
        setLoading(false);
        
        // 启动轮询
        startPolling();
      } else {
        throw new Error(uploadResult.message || '上传失败');
      }
    } catch (err) {
      setMessage((err as Error).message || '提交审核失败');
      setStatus('REJECTED');
      setLoading(false);
    }
  };

  /**
   * 重新提交
   */
  const handleRetry = () => {
    setFile(null);
    setStatus('UNPAID');
    setMessage('请重新选择支付凭证并提交。');
    setPollAttempts(0);
    setPollProgress(0);
    stopPolling();
  };

  const statusConfig = {
    UNPAID: {
      color: 'text-slate-500',
      icon: '📄',
      title: '等待提交',
    },
    PENDING: {
      color: 'text-purple-500',
      icon: '⏳',
      title: '审核中',
    },
    APPROVED: {
      color: 'text-green-500',
      icon: '✅',
      title: '审核通过',
    },
    REJECTED: {
      color: 'text-red-500',
      icon: '❌',
      title: '审核未通过',
    },
  }[status];

  return (
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-purple-500 mb-2 flex items-center gap-2">
        <span>💳</span>
        上传收款截图
      </h2>
      
      {/* 状态指示器 */}
      <div className={`flex items-center gap-3 mb-4 p-4 rounded-2xl ${
        status === 'APPROVED' ? 'bg-green-50 border border-green-200' :
        status === 'REJECTED' ? 'bg-red-50 border border-red-200' :
        status === 'PENDING' ? 'bg-purple-50 border border-purple-200' :
        'bg-slate-50 border border-slate-200'
      }`}>
        <span className="text-2xl">{statusConfig.icon}</span>
        <div className="flex-1">
          <div className={`font-semibold ${statusConfig.color}`}>{statusConfig.title}</div>
          <p className={`text-sm ${statusConfig.color}`}>{message}</p>
        </div>
      </div>

      {/* 轮询进度条（仅在 PENDING 状态显示） */}
      {status === 'PENDING' && pollProgress > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>审核进度</span>
            <span>{pollAttempts} 次查询 · {Math.round(pollProgress)}%</span>
          </div>
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-purple-500 transition-all duration-300"
              style={{ width: `${Math.min(pollProgress, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* 表单（仅在 UNPAID 或 REJECTED 状态显示） */}
      {(status === 'UNPAID' || status === 'REJECTED') && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="border-2 border-dashed border-purple-200/70 rounded-3xl p-6 text-center bg-white/70">
            <label htmlFor="payment-proof" className="block text-sm font-medium text-purple-500 mb-3">
              上传支付凭证
            </label>
            <input
              id="payment-proof"
              type="file"
              accept="image/png,image/jpeg"
              onChange={handleFileChange}
              className="w-full text-sm text-slate-500"
              aria-describedby="payment-proof-help"
              required
            />
            <p id="payment-proof-help" className="text-xs timao-support-text mt-2">
              支持 PNG/JPG，大小 &lt; 5MB
            </p>
            {file && (
              <p className="text-xs text-purple-600 mt-2">
                已选择：{file.name}
              </p>
            )}
          </div>
          <button type="submit" className="timao-primary-btn w-full" disabled={loading}>
            {loading ? '提交中...' : status === 'REJECTED' ? '重新提交审核' : '提交审核'}
          </button>
        </form>
      )}

      {/* PENDING 状态：显示等待提示 */}
      {status === 'PENDING' && (
        <div className="space-y-3">
          <div className="rounded-2xl bg-purple-50/80 border border-purple-100 p-4 text-sm text-slate-600">
            <div className="font-semibold mb-2">审核说明：</div>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>人工审核通常需要 1-5 分钟</li>
              <li>系统会自动轮询审核结果，无需手动刷新</li>
              <li>如果长时间未通过，可能需要联系客服</li>
            </ul>
          </div>
          <button 
            className="timao-outline-btn w-full"
            onClick={() => {
              stopPolling();
              handleRetry();
            }}
          >
            取消审核并重新提交
          </button>
        </div>
      )}

      {/* APPROVED 状态：显示成功提示 */}
      {status === 'APPROVED' && (
        <div className="rounded-2xl bg-green-50/80 border border-green-100 p-4 text-sm text-green-700">
          <div className="font-semibold mb-2">🎉 审核通过！</div>
          <p>您现在可以使用所有功能了。感谢您的支持！</p>
        </div>
      )}

      {/* REJECTED 状态：显示重试提示 */}
      {status === 'REJECTED' && (
        <div className="rounded-2xl bg-red-50/80 border border-red-100 p-4 text-sm text-red-700 mt-4">
          <div className="font-semibold mb-2">审核未通过原因：</div>
          <p className="mb-3">{message}</p>
          <div className="text-xs">
            <div className="font-semibold mb-1">请确保：</div>
            <ul className="list-disc list-inside space-y-1">
              <li>截图清晰完整，能看清金额和时间</li>
              <li>支付凭证为微信/支付宝官方截图</li>
              <li>金额与套餐价格一致</li>
            </ul>
          </div>
        </div>
      )}

      <div className="text-xs timao-support-text mt-4">
        审核通过前，核心功能将保持锁定。如有问题，请联系客服。
      </div>
    </div>
  );
};

export default PaymentVerifyPage;
