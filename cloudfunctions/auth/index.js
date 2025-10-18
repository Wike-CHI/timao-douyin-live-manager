const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const crypto = require('crypto');

function makeSalt(len = 16) {
  return crypto.randomBytes(len).toString('hex');
}
function hashPassword(password, salt) {
  const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512');
  return hash.toString('hex');
}
function makeToken() { return crypto.randomBytes(24).toString('hex'); }
function sanitizeUser(u) { if (!u) return null; const { password_hash, salt, _openid, ...rest } = u; return rest; }

async function register(data) {
  const { email, password, nickName } = data || {};
  if (!email || !password) return { code: 400, msg: '缺少 email 或 password' };
  const users = db.collection('users');
  const exists = await users.where({ email }).count();
  if (exists.total > 0) return { code: 409, msg: '邮箱已注册' };
  const salt = makeSalt();
  const password_hash = hashPassword(password, salt);
  const now = new Date();
  const doc = { email, nickName: nickName || email.split('@')[0], password_hash, salt, roles: ['user'], status: 'active', createdAt: now, updatedAt: now };
  const res = await users.add(doc);
  return { code: 0, data: { uid: res.id } };
}

async function login(data) {
  const { email, password } = data || {};
  if (!email || !password) return { code: 400, msg: '缺少 email 或 password' };
  const users = db.collection('users');
  const q = await users.where({ email }).get();
  if (!q.data || q.data.length === 0) return { code: 404, msg: '用户不存在' };
  const user = q.data[0];
  const hashed = hashPassword(password, user.salt);
  if (hashed !== user.password_hash) return { code: 401, msg: '密码错误' };
  const token = makeToken();
  const expiresAt = new Date(Date.now() + 2 * 60 * 60 * 1000);
  await db.collection('user_sessions').add({ uid: user._id, token, expiresAt, createdAt: new Date() });
  return { code: 0, data: { token, user: sanitizeUser(user) } };
}

async function profile(data) {
  const token = (data && data.token) || '';
  if (!token) return { code: 401, msg: '缺少 token' };
  const sessions = db.collection('user_sessions');
  const qs = await sessions.where({ token }).get();
  if (!qs.data || qs.data.length === 0) return { code: 401, msg: 'token 无效' };
  const sess = qs.data[0];
  if (new Date(sess.expiresAt) <= new Date()) return { code: 401, msg: 'token 过期' };
  const users = db.collection('users');
  const qu = await users.doc(sess.uid).get();
  const user = qu.data && qu.data[0];
  if (!user) return { code: 404, msg: '用户不存在' };
  return { code: 0, data: { user: sanitizeUser(user) } };
}

async function logout(data) {
  const token = (data && data.token) || '';
  if (!token) return { code: 400, msg: '缺少 token' };
  const sessions = db.collection('user_sessions');
  const qs = await sessions.where({ token }).get();
  if (!qs.data || qs.data.length === 0) return { code: 0, msg: '已注销' };
  const sess = qs.data[0];
  await sessions.doc(sess._id).remove();
  return { code: 0, msg: '已注销' };
}

exports.main = async (event, context) => {
  const action = event?.action;
  const data = event?.data || {};
  try {
    switch (action) {
      case 'register':
        return await register(data);
      case 'login':
        return await login(data);
      case 'profile':
        return await profile(data);
      case 'logout':
        return await logout(data);
      default:
        return { code: 400, msg: `未知动作: ${action}` };
    }
  } catch (err) {
    return { code: 500, msg: '服务器错误', error: String(err) };
  }
};