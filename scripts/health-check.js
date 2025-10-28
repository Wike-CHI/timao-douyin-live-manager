#!/usr/bin/env node

const http = require('http');

/**
 * 健康检查工具
 * 用于检查后端和前端服务是否正常运行
 */

const BACKEND_URL = 'http://127.0.0.1:9019/health';
const FRONTEND_URL = 'http://127.0.0.1:10030';

function checkService(url, serviceName) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (res) => {
      if (res.statusCode === 200) {
        console.log(`✅ ${serviceName} 服务正常运行 (${url})`);
        resolve(true);
      } else {
        console.log(`❌ ${serviceName} 服务异常 - 状态码: ${res.statusCode}`);
        resolve(false);
      }
    });

    request.on('error', (err) => {
      console.log(`❌ ${serviceName} 服务无法连接: ${err.message}`);
      resolve(false);
    });

    request.setTimeout(5000, () => {
      console.log(`❌ ${serviceName} 服务连接超时`);
      request.destroy();
      resolve(false);
    });
  });
}

async function healthCheck() {
  console.log('🔍 开始健康检查...\n');
  
  const backendStatus = await checkService(BACKEND_URL, '后端 FastAPI');
  const frontendStatus = await checkService(FRONTEND_URL, '前端 Vite');
  
  console.log('\n📊 健康检查结果:');
  console.log(`后端服务: ${backendStatus ? '✅ 正常' : '❌ 异常'}`);
  console.log(`前端服务: ${frontendStatus ? '✅ 正常' : '❌ 异常'}`);
  
  if (backendStatus && frontendStatus) {
    console.log('\n🎉 所有服务运行正常，可以启动 Electron 应用！');
    process.exit(0);
  } else {
    console.log('\n⚠️  部分服务异常，请检查服务状态');
    process.exit(1);
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  healthCheck();
}

module.exports = { checkService, healthCheck };