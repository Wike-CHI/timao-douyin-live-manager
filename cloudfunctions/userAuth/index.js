const cloudbase = require('@cloudbase/node-sdk');
const bcrypt = require('bcryptjs');

const app = cloudbase.init({ env: process.env.TCB_ENV_ID });
const db = app.database();
const _ = db.command;

exports.main = async (event) => {
  try {
    const { path, body } = event || {};
    if (path === '/api/auth/register') {
      const { email, password, nickname } = JSON.parse(body || '{}');
      if (!email || !password || !nickname) return { success: false, message: '缺少必要参数' };
      const hashed = bcrypt.hashSync(password, 10);
      const now = new Date();
      const existing = await db.collection('users').where({ email }).get();
      if (existing.data && existing.data.length > 0) return { success: false, message: '邮箱已存在' };
      const addRes = await db.collection('users').add({ email, password: hashed, nickname, isPaid: false, balance: 0, firstFreeUsed: false, createdAt: now });
      return { success: true, message: '注册成功', userId: addRes.id };
    }

    if (path === '/api/auth/login') {
      const { email, password } = JSON.parse(body || '{}');
      if (!email || !password) return { success: false, message: '缺少必要参数' };
      const res = await db.collection('users').where({ email }).get();
      if (!res.data || res.data.length === 0) return { success: false, message: '用户不存在' };
      const user = res.data[0];
      const ok = bcrypt.compareSync(password, user.password);
      if (!ok) return { success: false, message: '密码错误' };
      // 简单 token（演示用，生产建议使用云开发鉴权或 JWT）
      const token = Buffer.from(`${user._id}:${Date.now()}`).toString('base64');
      return {
        success: true,
        message: '登录成功',
        user: { id: user._id, email: user.email, nickname: user.nickname },
        token,
        isPaid: !!user.isPaid,
        balance: typeof user.balance === 'number' ? user.balance : 0,
        firstFreeUsed: !!user.firstFreeUsed,
      };
    }

    return { success: false, message: '未匹配的路径' };
  } catch (err) {
    return { success: false, message: err && err.message ? err.message : '服务错误' };
  }
};