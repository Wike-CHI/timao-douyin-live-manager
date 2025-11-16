/**
 * 测试 Python 服务启动
 */

const pythonService = require('./electron/main/python-service');

async function test() {
  console.log('🧪 开始测试 Python 服务...\n');
  
  try {
    // 启动服务
    console.log('1️⃣ 启动 Python 服务...');
    await pythonService.start();
    
    // 获取状态
    const status = pythonService.getStatus();
    console.log('\n✅ 服务启动成功！');
    console.log('📊 服务状态:', JSON.stringify(status, null, 2));
    
    // 等待5秒
    console.log('\n⏳ 等待 5 秒观察服务运行...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 健康检查
    console.log('\n2️⃣ 执行健康检查...');
    await pythonService.healthCheck();
    console.log('✅ 健康检查通过！');
    
    // 停止服务
    console.log('\n3️⃣ 停止服务...');
    await pythonService.stop();
    console.log('✅ 服务已停止');
    
    console.log('\n🎉 测试完成！');
    process.exit(0);
    
  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    console.error('错误堆栈:', error.stack);
    process.exit(1);
  }
}

test();
