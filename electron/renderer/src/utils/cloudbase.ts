import cloudbase from '@cloudbase/js-sdk';

// 统一初始化与轻量封装，避免误用不存在的 API（如 app.functions / signInWithUsernameAndPassword 等）
// 当前项目鉴权/支付已走云函数 HTTP 网关（见 src/services/auth.ts），本文件仅用于：
// - 可选的 CloudBase 匿名登录（如后续直接从前端调用数据库/模型等）
// - 可选的云函数直调（callFunction），默认不使用

let cachedApp: any;
let cachedAuth: any;

export function getApp() {
  if (cachedApp) return cachedApp;
  const envId = (import.meta as any)?.env?.VITE_TCB_ENV_ID as string | undefined;
  cachedApp = cloudbase.init({ env: envId || undefined });
  return cachedApp;
}

export function getAuth() {
  if (cachedAuth) return cachedAuth;
  const app = getApp();
  cachedAuth = app.auth({ persistence: 'local' });
  return cachedAuth;
}

// 确保匿名登录（仅在需要直连 CloudBase 能力时使用；当前登录注册走 HTTP，不强制调用）
export async function ensureAnonymousLogin() {
  const auth = getAuth();
  const state = await auth.getLoginState();
  if (!state || !state.isLoggedIn) {
    await auth.signInAnonymously();
  }
}

// 可选：调用云函数（v2 SDK 使用 app.callFunction，而非 app.functions()）
export async function callFunction(name: string, data?: any) {
  const app = getApp();
  const fn = (app as any).callFunction;
  if (typeof fn !== 'function') {
    throw new Error('当前 SDK 不支持 callFunction，请升级 @cloudbase/js-sdk 或改用 HTTP 网关');
  }
  return fn({ name, data });
}