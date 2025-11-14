/**
 * 数据清理工具
 * 用于在重新登录、登出时清理直播相关的旧数据，防止数据残留
 */

/**
 * 清理所有直播相关的存储数据
 * 包括 sessionStorage 和 localStorage 中的临时数据
 */
export const cleanupLiveData = () => {
  console.log('🧹 开始清理直播相关数据...');
  
  const itemsToClean = [
    // SessionStorage 中的数据
    'timao-live-console',      // 直播控制台数据
    'timao-live-status',       // 直播状态
    'timao-websocket-state',   // WebSocket 状态
    
    // LocalStorage 中的临时数据（如果有）
    'timao-temp-transcript',   // 临时转写数据
    'timao-temp-comments',     // 临时弹幕数据
  ];
  
  let cleanedCount = 0;
  
  // 清理 sessionStorage
  itemsToClean.forEach(key => {
    try {
      if (sessionStorage.getItem(key)) {
        sessionStorage.removeItem(key);
        cleanedCount++;
        console.log(`  ✅ 已清理 sessionStorage: ${key}`);
      }
    } catch (error) {
      console.error(`  ❌ 清理 sessionStorage 失败 [${key}]:`, error);
    }
  });
  
  // 清理 localStorage 中的临时数据（保留用户设置和账号信息）
  itemsToClean.forEach(key => {
    try {
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key);
        cleanedCount++;
        console.log(`  ✅ 已清理 localStorage: ${key}`);
      }
    } catch (error) {
      console.error(`  ❌ 清理 localStorage 失败 [${key}]:`, error);
    }
  });
  
  console.log(`✅ 数据清理完成，共清理 ${cleanedCount} 项数据`);
  
  return cleanedCount;
};

/**
 * 清理所有用户数据（包括认证信息）
 * ⚠️ 警告：这会清除所有数据，包括登录状态
 * 通常在登出时使用
 */
export const cleanupAllUserData = () => {
  console.log('🧹 开始清理所有用户数据（登出）...');
  
  // 先清理直播数据
  cleanupLiveData();
  
  // 清理认证数据（由 useAuthStore 管理，这里只记录日志）
  console.log('  ℹ️  认证数据将由 useAuthStore 清理');
  
  console.log('✅ 所有用户数据清理完成');
};

/**
 * 检查并报告当前存储的数据量
 * 用于调试和监控
 */
export const reportStorageUsage = () => {
  console.log('📊 存储数据使用情况：');
  
  // SessionStorage
  console.log('\nSessionStorage:');
  let sessionCount = 0;
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key) {
      const value = sessionStorage.getItem(key);
      const size = value ? new Blob([value]).size : 0;
      console.log(`  - ${key}: ${(size / 1024).toFixed(2)} KB`);
      sessionCount++;
    }
  }
  console.log(`  总计: ${sessionCount} 项`);
  
  // LocalStorage
  console.log('\nLocalStorage:');
  let localCount = 0;
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key) {
      const value = localStorage.getItem(key);
      const size = value ? new Blob([value]).size : 0;
      console.log(`  - ${key}: ${(size / 1024).toFixed(2)} KB`);
      localCount++;
    }
  }
  console.log(`  总计: ${localCount} 项`);
};

