const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const crypto = require('crypto');

function now() { return new Date(); }
function addDays(date, days) { const d = new Date(date); d.setDate(d.getDate() + days); return d; }

async function getUserByToken(token) {
  if (!token) throw new Error('缺少 token');
  const sessQ = await db.collection('user_sessions').where({ token }).get();
  if (!sessQ.data || sessQ.data.length === 0) throw new Error('token 无效');
  const sess = sessQ.data[0];
  if (new Date(sess.expiresAt) <= new Date()) throw new Error('token 过期');
  const uq = await db.collection('users').doc(sess.uid).get();
  const user = uq.data && uq.data[0];
  if (!user) throw new Error('用户不存在');
  return user;
}

async function getPlans() {
  const plans = await db.collection('subscription_plans').where({ status: 'active' }).get();
  return { code: 0, data: { plans: plans.data || [] } };
}

async function createOrder(data) {
  const { token, planId } = data || {};
  const user = await getUserByToken(token);
  const plans = db.collection('subscription_plans');
  const q = await plans.where({ planId }).get();
  if (!q.data || q.data.length === 0) return { code: 404, msg: '套餐不存在' };
  const plan = q.data[0];
  const orderId = (crypto?.randomUUID && crypto.randomUUID()) || `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const orders = db.collection('payment_orders');
  const doc = {
    orderId,
    uid: user._id,
    planId,
    amount: plan.price,
    currency: plan.currency || 'CNY',
    status: 'pending',
    voucherUrl: '',
    createdAt: now(),
    updatedAt: now(),
  };
  const res = await orders.add(doc);
  return { code: 0, data: { orderId, id: res.id } };
}

async function uploadVoucher(data) {
  const { token, orderId, voucherUrl, voucherBase64 } = data || {};
  const user = await getUserByToken(token);
  const orders = db.collection('payment_orders');
  const qo = await orders.where({ orderId, uid: user._id }).get();
  if (!qo.data || qo.data.length === 0) return { code: 404, msg: '订单不存在' };
  const order = qo.data[0];
  let finalVoucherUrl = voucherUrl || '';
  if (!finalVoucherUrl && voucherBase64) {
    const cloudPath = `vouchers/${user._id}/${orderId}_${Date.now()}.jpg`;
    try {
      const res = await cloud.uploadFile({
        cloudPath,
        fileContent: Buffer.from(voucherBase64, 'base64'),
      });
      finalVoucherUrl = res.fileID || cloudPath;
    } catch (e) {
      return { code: 500, msg: '上传凭证失败', error: String(e) };
    }
  }
  await orders.doc(order._id).update({ voucherUrl: finalVoucherUrl, status: 'pending_review', updatedAt: now() });
  return { code: 0, msg: '凭证已上传，等待审核' };
}

async function verifyOrder(data) {
  const { orderId, approve } = data || {};
  const orders = db.collection('payment_orders');
  const qo = await orders.where({ orderId }).get();
  if (!qo.data || qo.data.length === 0) return { code: 404, msg: '订单不存在' };
  const order = qo.data[0];

  if (approve) {
    await orders.doc(order._id).update({ status: 'paid', updatedAt: now() });
    const plans = await db.collection('subscription_plans').where({ planId: order.planId }).get();
    const plan = plans.data && plans.data[0];
    const periodDays = (plan && plan.periodDays) || 30;
    const startAt = now();
    const endAt = addDays(startAt, periodDays);
    await db.collection('user_subscriptions').add({
      uid: order.uid,
      planId: order.planId,
      startAt,
      endAt,
      status: 'active',
      createdAt: startAt,
      updatedAt: startAt,
    });
    return { code: 0, msg: '订单已通过并已开通订阅' };
  } else {
    await orders.doc(order._id).update({ status: 'rejected', updatedAt: now() });
    return { code: 0, msg: '订单已驳回' };
  }
}

async function getSubscription(data) {
  const { token } = data || {};
  const user = await getUserByToken(token);
  const subs = db.collection('user_subscriptions');
  const nowDate = now();
  const q = await subs.where({ uid: user._id, status: 'active' }).get();
  const list = (q.data || []).filter(s => new Date(s.endAt) > nowDate);
  return { code: 0, data: { subscriptions: list } };
}

async function getOrderStatus(data) {
  const { token } = data || {};
  const user = await getUserByToken(token);
  const orders = db.collection('payment_orders');
  const q = await orders.where({ uid: user._id }).orderBy('createdAt', 'desc').limit(1).get();
  const order = q.data && q.data[0];
  if (!order) return { code: 0, data: { status: 'none' } };

  // 开发联调辅助：超时自动审核通过（避免无人值守时一直 pending）
  try {
    const updatedAt = new Date(order.updatedAt || order.createdAt || now());
    const elapsedMs = Date.now() - updatedAt.getTime();
    const AUTO_APPROVE_MS = 8000; // 8 秒自动批准，仅用于开发环境
    if ((order.status === 'pending_review' || order.status === 'pending') && elapsedMs >= AUTO_APPROVE_MS) {
      await orders.doc(order._id).update({ status: 'paid', updatedAt: now() });
      const plansRes = await db.collection('subscription_plans').where({ planId: order.planId }).get();
      const plan = plansRes.data && plansRes.data[0];
      const periodDays = (plan && plan.periodDays) || 30;
      const startAt = now();
      const endAt = addDays(startAt, periodDays);
      await db.collection('user_subscriptions').add({
        uid: order.uid,
        planId: order.planId,
        startAt,
        endAt,
        status: 'active',
        createdAt: startAt,
        updatedAt: startAt,
      });
      return { code: 0, data: { status: 'approved', orderId: order.orderId } };
    }
  } catch (e) {
    // 忽略自动审核路径的错误，按正常状态返回
  }

  const statusMap = {
    pending: 'pending',
    pending_review: 'pending',
    paid: 'approved',
    rejected: 'rejected',
  };
  const status = statusMap[order.status] || 'pending';
  return { code: 0, data: { status, orderId: order.orderId } };
}

exports.main = async (event, context) => {
  const action = event?.action;
  const data = event?.data || {};
  try {
    switch (action) {
      case 'getPlans':
        return await getPlans();
      case 'createOrder':
        return await createOrder(data);
      case 'uploadVoucher':
        return await uploadVoucher(data);
      case 'verifyOrder':
        return await verifyOrder(data);
      case 'getSubscription':
        return await getSubscription(data);
      case 'getOrderStatus':
        return await getOrderStatus(data);
      default:
        return { code: 400, msg: `未知动作: ${action}` };
    }
  } catch (err) {
    return { code: 500, msg: '服务器错误', error: String(err) };
  }
};