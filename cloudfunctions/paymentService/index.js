const cloudbase = require('@cloudbase/node-sdk');
const app = cloudbase.init({ env: process.env.TCB_ENV_ID });
const db = app.database();

exports.main = async (event) => {
  try {
    const { path, headers, body } = event || {};
    // 简单鉴权：从 Authorization 解析用户ID（与 userAuth 返回的 token 对齐，仅演示用）
    let userId = null;
    const auth = headers && headers.Authorization ? headers.Authorization : headers.authorization;
    if (auth && auth.startsWith('Bearer ')) {
      const token = auth.slice(7);
      try {
        const decoded = Buffer.from(token, 'base64').toString('utf8');
        userId = decoded.split(':')[0];
      } catch (_) {}
    }

    if (!userId) return { success: false, message: '未登录或令牌无效' };

    // 钱包相关API
    if (path === '/api/wallet/balance') {
      const res = await db.collection('users').doc(userId).get();
      if (!res.data || res.data.length === 0) return { success: false, message: '用户不存在' };
      const user = res.data[0];
      return {
        success: true,
        balance: typeof user.balance === 'number' ? user.balance : 0,
        firstFreeUsed: !!user.firstFreeUsed,
      };
    }

    if (path === '/api/wallet/recharge') {
      const { amount } = JSON.parse(body || '{}');
      if (!amount || amount <= 0) return { success: false, message: '充值金额无效' };
      
      const res = await db.collection('users').doc(userId).get();
      if (!res.data || res.data.length === 0) return { success: false, message: '用户不存在' };
      const user = res.data[0];
      const newBalance = (typeof user.balance === 'number' ? user.balance : 0) + amount;
      
      await db.collection('users').doc(userId).update({ balance: newBalance });
      
      // 记录充值历史
      await db.collection('wallet_transactions').add({
        userId,
        type: 'recharge',
        amount,
        balanceAfter: newBalance,
        createdAt: new Date(),
      });
      
      return { success: true, balance: newBalance, message: `充值成功，当前余额 ${newBalance} 元` };
    }

    if (path === '/api/wallet/consume') {
      const { amount, reason } = JSON.parse(body || '{}');
      if (!amount || amount <= 0) return { success: false, message: '消费金额无效' };
      
      const res = await db.collection('users').doc(userId).get();
      if (!res.data || res.data.length === 0) return { success: false, message: '用户不存在' };
      const user = res.data[0];
      const currentBalance = typeof user.balance === 'number' ? user.balance : 0;
      
      if (currentBalance < amount) {
        return { success: false, message: '余额不足', balance: currentBalance };
      }
      
      const newBalance = currentBalance - amount;
      await db.collection('users').doc(userId).update({ balance: newBalance });
      
      // 记录消费历史
      await db.collection('wallet_transactions').add({
        userId,
        type: 'consume',
        amount,
        reason: reason || '直播服务消费',
        balanceAfter: newBalance,
        createdAt: new Date(),
      });
      
      return { success: true, balance: newBalance, message: `消费成功，当前余额 ${newBalance} 元` };
    }

    if (path === '/api/wallet/useFree') {
      const res = await db.collection('users').doc(userId).get();
      if (!res.data || res.data.length === 0) return { success: false, message: '用户不存在' };
      const user = res.data[0];
      
      if (user.firstFreeUsed) {
        return { success: false, message: '首次免费已使用' };
      }
      
      await db.collection('users').doc(userId).update({ firstFreeUsed: true });
      
      // 记录免费使用历史
      await db.collection('wallet_transactions').add({
        userId,
        type: 'free_use',
        amount: 0,
        reason: '首次免费使用',
        balanceAfter: typeof user.balance === 'number' ? user.balance : 0,
        createdAt: new Date(),
      });
      
      return { success: true, firstFreeUsed: true, message: '首次免费使用成功' };
    }

    // 原有支付相关API
    if (path === '/api/payment/upload') {
      // 简化：不处理真实文件，写入数据库一条待审核记录
      const now = new Date();
      await db.collection('payments').add({ userId, status: 'PENDING', createdAt: now });
      return { success: true, message: '已提交审核，预计1-3分钟完成' };
    }

    if (path === '/api/payment/status') {
      const res = await db.collection('payments').where({ userId }).orderBy('createdAt', 'desc').limit(1).get();
      const record = res.data && res.data[0];
      if (!record) return { success: false, message: '未找到支付记录' };
      // 演示：将最近一次记录标记为 APPROVED 并更新用户 isPaid
      if (record.status !== 'APPROVED') {
        await db.collection('payments').doc(record._id).update({ status: 'APPROVED' });
        await db.collection('users').doc(userId).update({ isPaid: true });
      }
      return { success: true, message: '审核通过，已解锁全部功能', status: 'APPROVED' };
    }

    return { success: false, message: '未匹配的路径' };
  } catch (err) {
    return { success: false, message: err && err.message ? err.message : '服务错误' };
  }
};