#!/usr/bin/env node
/**
 * 后端端口诊断工具
 * 检查 8080 端口状态和 FastAPI 服务
 */

const { execSync } = require('child_process');
const http = require('http');

console.log('🔍 开始诊断后端服务...\n');

// 1. 检查端口占用
console.log('📌 步骤 1: 检查端口 8080 占用情况');
try {
  if (process.platform === 'win32') {
    const output = execSync('netstat -ano | findstr ":8080"', { encoding: 'utf-8' });
    if (output.trim()) {
      console.log('✅ 端口 8080 被占用:');
      console.log(output);
      
      // 提取 PID
      const lines = output.trim().split('\n');
      const pids = new Set();
      lines.forEach(line => {
        const match = line.match(/\s+(\d+)\s*$/);
        if (match) {
          pids.add(match[1]);
        }
      });
      
      if (pids.size > 0) {
        console.log('\n📋 占用端口的进程:');
        pids.forEach(pid => {
          try {
            const taskOutput = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, { encoding: 'utf-8' });
            console.log(`  PID ${pid}: ${taskOutput.trim()}`);
          } catch (e) {
            console.log(`  PID ${pid}: 进程已结束或无法访问`);
          }
        });
      }
    } else {
      console.log('❌ 端口 8080 未被占用（这是问题所在！）');
    }
  } else {
    const output = execSync('lsof -i :8080', { encoding: 'utf-8' });
    console.log('端口 8080 占用情况:');
    console.log(output);
  }
} catch (error) {
  console.log('❌ 端口 8080 未被占用或检查失败');
  console.log('   错误信息:', error.message);
}

// 2. 检查 Python 进程
console.log('\n📌 步骤 2: 检查 Python 进程');
try {
  if (process.platform === 'win32') {
    const output = execSync('tasklist | findstr python', { encoding: 'utf-8' });
    console.log('Python 进程列表:');
    console.log(output);
  } else {
    const output = execSync('ps aux | grep python', { encoding: 'utf-8' });
    console.log('Python 进程列表:');
    console.log(output);
  }
} catch (error) {
  console.log('❌ 未找到 Python 进程');
}

// 3. 尝试连接健康检查端点
console.log('\n📌 步骤 3: 测试健康检查端点');
const testHealth = () => {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:8080/health', { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        console.log('✅ 健康检查端点响应:');
        console.log(`   状态码: ${res.statusCode}`);
        console.log(`   响应数据: ${data}`);
        resolve(true);
      });
    });

    req.on('error', (error) => {
      console.log('❌ 健康检查端点无法访问:');
      console.log(`   错误: ${error.message}`);
      console.log(`   错误代码: ${error.code}`);
      if (error.code === 'ECONNREFUSED') {
        console.log('   → 服务未启动或未监听 8080 端口');
      }
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.log('❌ 健康检查端点响应超时');
      resolve(false);
    });
  });
};

testHealth().then((success) => {
  console.log('\n' + '='.repeat(60));
  if (success) {
    console.log('✅ 诊断结果: FastAPI 服务运行正常');
  } else {
    console.log('❌ 诊断结果: FastAPI 服务未正常启动');
    console.log('\n建议检查:');
    console.log('1. 查看日志文件: logs/service_manager.log');
    console.log('2. 检查 .env 文件中的 BACKEND_PORT 配置');
    console.log('3. 尝试手动启动: python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8080');
    console.log('4. 检查防火墙是否阻止 8080 端口');
    console.log('5. 检查数据库连接是否正常（可能导致启动失败）');
  }
  console.log('='.repeat(60));
});

