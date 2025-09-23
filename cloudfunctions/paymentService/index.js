const cloudbase = require('@cloudbase/node-sdk');
const app = cloudbase.init({ env: process.env.TCB_ENV_ID });
const db = app.database();

exports.main = async (event) => {
  try {
    const { path, headers } = event || {};
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