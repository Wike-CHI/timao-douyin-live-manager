#!/usr/bin/env node

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

/**
 * 杀死指定端口的进程
 * @param {number} port - 要杀死的端口号
 */
async function killPort(port) {
    try {
        console.log(`🔍 检查端口 ${port} 的占用情况...`);
        
        // 查找占用端口的进程
        const { stdout } = await execAsync(`netstat -ano | findstr :${port}`);
        
        if (!stdout.trim()) {
            console.log(`✅ 端口 ${port} 未被占用`);
            return;
        }
        
        // 解析进程ID
        const lines = stdout.trim().split('\n');
        const pids = new Set();
        
        for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 5) {
                const pid = parts[parts.length - 1];
                if (pid && pid !== '0') {
                    pids.add(pid);
                }
            }
        }
        
        if (pids.size === 0) {
            console.log(`✅ 端口 ${port} 未找到有效进程`);
            return;
        }
        
        // 杀死进程
        for (const pid of pids) {
            try {
                console.log(`🔪 正在杀死进程 PID: ${pid}...`);
                await execAsync(`taskkill /F /PID ${pid}`);
                console.log(`✅ 成功杀死进程 PID: ${pid}`);
            } catch (error) {
                console.log(`⚠️  无法杀死进程 PID: ${pid} (可能已经结束)`);
            }
        }
        
        // 等待一下确保端口释放
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 再次检查端口状态
        try {
            const { stdout: checkResult } = await execAsync(`netstat -ano | findstr :${port}`);
            if (checkResult.trim()) {
                console.log(`⚠️  端口 ${port} 仍被占用，可能需要手动处理`);
            } else {
                console.log(`✅ 端口 ${port} 已成功释放`);
            }
        } catch (error) {
            console.log(`✅ 端口 ${port} 已成功释放`);
        }
        
    } catch (error) {
        console.log(`✅ 端口 ${port} 未被占用或已释放`);
    }
}

// 从命令行参数获取端口号
const port = process.argv[2];

if (!port) {
    console.error('❌ 请提供端口号参数');
    console.log('用法: node kill-port.js <端口号>');
    process.exit(1);
}

if (isNaN(port) || port < 1 || port > 65535) {
    console.error('❌ 无效的端口号');
    process.exit(1);
}

// 执行杀死端口进程
killPort(parseInt(port))
    .then(() => {
        console.log(`🎉 端口 ${port} 处理完成`);
    })
    .catch((error) => {
        console.error(`❌ 处理端口 ${port} 时出错:`, error.message);
        process.exit(1);
    });