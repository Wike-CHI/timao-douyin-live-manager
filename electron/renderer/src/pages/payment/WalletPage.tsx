import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWallet, recharge } from '../../services/auth';
import useAuthStore from '../../store/useAuthStore';

const WalletPage = () => {
  const navigate = useNavigate();
  const { balance, setBalance } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [amount, setAmount] = useState<number>(10);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const res = await getWallet();
        if (mounted) {
          setBalance(res.balance ?? 0);
        }
      } catch (e: any) {
        setError(e?.message || '获取钱包信息失败');
      } finally {
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [setBalance]);

  const handleRecharge = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await recharge(amount);
      setBalance(res.balance ?? 0);
    } catch (e: any) {
      setError(e?.message || '充值失败');
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => navigate('/dashboard');

  return (
    <div className="bg-white/5 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">钱包</h2>
        <button onClick={goBack} className="text-sm text-purple-400 hover:text-purple-300">返回控制台</button>
      </div>

      <div className="mb-4">
        <div className="text-sm text-gray-400">当前余额</div>
        <div className="text-3xl font-bold text-green-400">{loading ? '加载中...' : (balance ?? 0).toFixed(2)}</div>
      </div>

      <div className="mt-6">
        <label className="block text-sm mb-2">充值金额</label>
        <div className="flex gap-2">
          <input
            type="number"
            min={1}
            step={1}
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value || 0))}
            className="flex-1 px-3 py-2 rounded bg-white/10 outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleRecharge}
            disabled={loading || amount <= 0}
            className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-50"
          >
            {loading ? '处理中...' : '充值'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 text-sm text-red-400">{error}</div>
      )}

      <div className="mt-8 text-sm text-gray-400">
        说明：余额可用于启动一次实时转写；若余额不足且未使用过首次免费，将在启动时自动使用首次免费额度。
      </div>
    </div>
  );
};

export default WalletPage;