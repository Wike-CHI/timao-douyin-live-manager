#!/usr/bin/env node
/**
 * 测试 deltaModeRef 生命周期
 * 验证 WebSocket 重连和会话切换场景
 * 
 * 运行方式：node tests/test_deltamode_lifecycle.js
 */

const WebSocket = require('ws');

const FASTAPI_BASE_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8007';
const WS_URL = FASTAPI_BASE_URL.replace(/^http/i, 'ws') + '/api/live_audio/ws';

let testResults = [];

function log(msg) {
  const time = new Date().toLocaleTimeString();
  console.log(`[${time}] ${msg}`);
}

function addResult(testName, passed, details = '') {
  testResults.push({ testName, passed, details });
  console.log(`${passed ? '✅ PASS' : '❌ FAIL'}: ${testName}${details ? ' - ' + details : ''}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function apiCall(endpoint, method = 'GET', body = null) {
  const url = `${FASTAPI_BASE_URL}${endpoint}`;
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    throw new Error(`API call failed: ${err.message}`);
  }
}

async function test1_normalStartStop() {
  log('测试一：正常启动与停止');
  
  try {
    // 1. 启动转写
    log('1.1 启动转写服务');
    const startRes = await apiCall('/api/live_audio/start', 'POST', {
      live_url: 'test_room_deltamode_1'
    });
    log(`启动成功: session_id=${startRes.data?.session_id}`);
    
    // 2. 连接 WebSocket
    log('1.2 连接 WebSocket');
    let receivedMessages = [];
    let ws = new WebSocket(WS_URL);
    
    ws.on('open', () => log('WebSocket 连接成功'));
    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        receivedMessages.push(msg);
        log(`收到消息: ${msg.type}`);
      } catch (err) {
        log(`解析消息失败: ${err.message}`);
      }
    });
    ws.on('error', (err) => log(`WebSocket 错误: ${err.message}`));
    
    // 等待接收消息
    await sleep(3000);
    
    // 3. 停止转写
    log('1.3 停止转写服务');
    await apiCall('/api/live_audio/stop', 'POST');
    log('停止成功');
    ws.close();
    
    // 4. 验证
    const hasStatusMsg = receivedMessages.some(m => m.type === 'status' || m.type === 'connected');
    addResult('正常启动与停止', hasStatusMsg, `收到 ${receivedMessages.length} 条消息`);
    
  } catch (err) {
    addResult('正常启动与停止', false, err.message);
  }
  
  await sleep(1000);
}

async function test2_restartSession() {
  log('测试二：连续启动多次（验证 deltaModeRef 重置）');
  
  try {
    // 第一次启动
    log('2.1 第一次启动');
    await apiCall('/api/live_audio/start', 'POST', {
      live_url: 'test_room_deltamode_2a'
    });
    await sleep(2000);
    
    // 停止
    log('2.2 第一次停止');
    await apiCall('/api/live_audio/stop', 'POST');
    await sleep(1000);
    
    // 第二次启动
    log('2.3 第二次启动');
    await apiCall('/api/live_audio/start', 'POST', {
      live_url: 'test_room_deltamode_2b'
    });
    
    // 连接 WebSocket 验证能否接收消息
    let ws = new WebSocket(WS_URL);
    let receivedMessages = [];
    
    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        receivedMessages.push(msg);
      } catch {}
    });
    
    await sleep(3000);
    
    // 停止
    await apiCall('/api/live_audio/stop', 'POST');
    ws.close();
    
    // 验证第二次启动能正常接收消息
    const passed = receivedMessages.length > 0;
    addResult('连续启动多次', passed, `第二次启动收到 ${receivedMessages.length} 条消息`);
    
  } catch (err) {
    addResult('连续启动多次', false, err.message);
  }
  
  await sleep(1000);
}

async function test3_websocketReconnect() {
  log('测试三：WebSocket 重连');
  
  try {
    // 启动转写
    log('3.1 启动转写服务');
    await apiCall('/api/live_audio/start', 'POST', {
      live_url: 'test_room_deltamode_3'
    });
    
    // 第一次连接
    log('3.2 建立第一次 WebSocket 连接');
    let ws1 = new WebSocket(WS_URL);
    let messages1 = [];
    
    ws1.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        messages1.push(msg);
      } catch {}
    });
    
    await sleep(2000);
    
    // 断开并重连
    log('3.3 断开并重连');
    ws1.close();
    await sleep(500);
    
    let ws2 = new WebSocket(WS_URL);
    let messages2 = [];
    
    ws2.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        messages2.push(msg);
      } catch {}
    });
    
    await sleep(2000);
    
    // 停止
    await apiCall('/api/live_audio/stop', 'POST');
    ws2.close();
    
    // 验证重连后能正常接收消息
    const passed = messages2.length > 0;
    addResult('WebSocket 重连', passed, `重连后收到 ${messages2.length} 条消息`);
    
  } catch (err) {
    addResult('WebSocket 重连', false, err.message);
  }
  
  await sleep(1000);
}

async function test4_statusQuery() {
  log('测试四：状态查询');
  
  try {
    // 查询状态（应该是停止状态）
    const status = await apiCall('/api/live_audio/status');
    
    const passed = status.hasOwnProperty('is_running');
    addResult('状态查询', passed, `is_running=${status.is_running}`);
    
  } catch (err) {
    addResult('状态查询', false, err.message);
  }
}

async function runAllTests() {
  console.log('========================================');
  console.log('deltaModeRef 生命周期测试');
  console.log('========================================\n');
  
  log(`测试目标: ${FASTAPI_BASE_URL}`);
  log(`WebSocket: ${WS_URL}\n`);
  
  // 检查后端是否可用
  try {
    await apiCall('/health');
    log('后端服务可用\n');
  } catch (err) {
    console.error('❌ 后端服务不可用，请先启动 FastAPI 服务');
    console.error(`   错误: ${err.message}`);
    process.exit(1);
  }
  
  // 运行测试
  await test1_normalStartStop();
  await test2_restartSession();
  await test3_websocketReconnect();
  await test4_statusQuery();
  
  // 输出结果
  console.log('\n========================================');
  console.log('测试结果汇总');
  console.log('========================================');
  
  const passed = testResults.filter(r => r.passed).length;
  const failed = testResults.filter(r => !r.passed).length;
  
  testResults.forEach(result => {
    console.log(`${result.passed ? '✅' : '❌'} ${result.testName}`);
    if (result.details) {
      console.log(`   ${result.details}`);
    }
  });
  
  console.log(`\n总计: ${testResults.length} 个测试`);
  console.log(`通过: ${passed} 个`);
  console.log(`失败: ${failed} 个`);
  
  const exitCode = failed > 0 ? 1 : 0;
  console.log(`\n${exitCode === 0 ? '✅ 所有测试通过' : '❌ 部分测试失败'}`);
  
  process.exit(exitCode);
}

// 运行测试
runAllTests().catch(err => {
  console.error('测试执行失败:', err);
  process.exit(1);
});

