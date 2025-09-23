import { ChangeEvent, FormEvent, useState } from 'react';
import useAuthStore from '../../store/useAuthStore';
import { pollPayment, uploadPayment } from '../../services/auth';

const PaymentVerifyPage = () => {
  const { setPaid } = useAuthStore();
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('请上传微信/支付宝收款截图，审核通过后即可使用全部功能。');
  const [status, setStatus] = useState<'UNPAID' | 'PENDING' | 'APPROVED' | 'REJECTED'>('UNPAID');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const targetFile = event.target.files?.[0] ?? null;
    setFile(targetFile);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setMessage('请先选择截图文件');
      return;
    }
    try {
      setLoading(true);
      setMessage('正在提交审核...');
      const uploadResult = await uploadPayment(file);
      if (uploadResult.success) {
        setStatus('PENDING');
        setMessage(uploadResult.message);
        const pollResult = await pollPayment();
        if (pollResult.success) {
          setStatus('APPROVED');
          setMessage(pollResult.message);
          setPaid(true);
        } else {
          setStatus('REJECTED');
          setMessage(pollResult.message);
        }
      }
    } catch (err) {
      setMessage((err as Error).message);
      setStatus('REJECTED');
    } finally {
      setLoading(false);
    }
  };

  const statusColor = {
    UNPAID: 'text-slate-500',
    PENDING: 'text-purple-500',
    APPROVED: 'text-green-500',
    REJECTED: 'text-red-500',
  }[status];

  return (
    <div className="timao-card p-10">
      <h2 className="text-2xl font-semibold text-purple-500 mb-2 flex items-center gap-2">
        <span>💳</span>
        上传收款截图
      </h2>
      <p className={`text-sm mb-4 ${statusColor}`}>{message}</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="border-2 border-dashed border-purple-200/70 rounded-3xl p-6 text-center bg-white/70">
          <input
            type="file"
            accept="image/png,image/jpeg"
            onChange={handleFileChange}
            className="w-full text-sm text-slate-500"
          />
          <p className="text-xs timao-support-text mt-2">支持 PNG/JPG，大小 &lt; 5MB</p>
        </div>
        <button type="submit" className="timao-primary-btn w-full" disabled={loading}>
          {loading ? '审核中...' : '提交审核'}
        </button>
      </form>
      <div className="text-xs timao-support-text mt-4">
        审核通过前，核心功能将保持锁定。后续可上传微信/支付宝官方收款截图，以确保使用安全。
      </div>
    </div>
  );
};

export default PaymentVerifyPage;
