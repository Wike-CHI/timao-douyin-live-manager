'use strict';
// 最小鉴权/支付后端（Node + Express），用于腾讯云云托管（CloudBase Run）
// 仅示例用途：请接入真实用户体系/数据库与安全校验

const express = require('express');
const cors = require('cors');
const multer = require('multer');

const app = express();
const upload = multer({ limits: { fileSize: 5 * 1024 * 1024 } }); // 5MB

// CORS：允许来源由环境变量控制，逗号分隔
const allowOrigins = (process.env.ALLOW_ORIGINS || 'http://127.0.0.1:5173').split(',').map(s => s.trim());
app.use(cors({ origin: (origin, cb) => cb(null, !origin || allowOrigins.includes(origin)), credentials: true }));
app.use(express.json());

// 演示用内存状态
let lastUploadAt = null;
let lastPaymentStatus = 'UNPAID'; // UNPAID -> PENDING_REVIEW -> APPROVED/REJECTED

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) return res.status(400).send('请输入邮箱和密码');
  // TODO: 验证密码（哈希）与数据库用户
  return res.json({
    success: true,
    token: 'jwt-token-placeholder',
    user: { id: 'user-1', email, nickname: '提猫主播' },
    isPaid: lastPaymentStatus === 'APPROVED',
  });
});

app.post('/api/auth/register', (req, res) => {
  const { email, password, nickname } = req.body || {};
  if (!email || !password || !nickname) return res.status(400).send('请填写完整信息');
  // TODO: 写入数据库
  return res.json({ success: true, user: { id: 'user-new', email, nickname } });
});

app.post('/api/payment/upload', upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).send('请上传收款截图');
  // TODO: 上传到 COS/对象存储 + 记录数据库 + 触发人工审核/自动审核
  lastUploadAt = Date.now();
  lastPaymentStatus = 'PENDING_REVIEW';
  return res.json({ success: true, status: 'PENDING_REVIEW', message: '已提交审核，预计稍后完成' });
});

app.get('/api/payment/status', (req, res) => {
  // Demo：上传 5 秒后自动通过；请替换为真实审核结果
  if (lastPaymentStatus === 'PENDING_REVIEW' && lastUploadAt && Date.now() - lastUploadAt > 5000) {
    lastPaymentStatus = 'APPROVED';
  }
  const success = lastPaymentStatus === 'APPROVED';
  return res.json({ success, status: lastPaymentStatus, message: success ? '支付已验证，感谢支持！' : '审核中或未通过' });
});

app.get('/health', (_req, res) => res.json({ ok: true }));

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`[auth-backend] listening on :${PORT}`));
