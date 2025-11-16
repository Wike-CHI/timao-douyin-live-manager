#!/usr/bin/env node

const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

/**
 * 端口管理器 - 用于检查和清理端口占用
 */
class PortManager {
    constructor() {
        // 默认端口配置
        this.defaultPorts = {
            backend: 8000,      // FastAPI 后端
            electron: 8081,     // Electron 渲染进程
            frontend: 8081,     // 前端开发服务器
            vite: 5173          // Vite 开发服务器
        };
    }

    /**
     * 检查默认端口是否被占用
     */
    async checkDefaultPorts() {
        console.log('🔍 检查默认端口状态...\n');
        
        const portStatus = {};
        
        for (const [name, port] of Object.entries(this.defaultPorts)) {
            const pid = await this.getPortPid(port);
            portStatus[name] = {
                port,
                occupied: pid !== null,
                pid
            };
            
            if (pid) {
                console.log(`⚠️  ${name} 端口 ${port} 被占用（PID: ${pid}）`);
            } else {
                console.log(`✅ ${name} 端口 ${port} 可用`);
            }
        }
        
        console.log('');
        return portStatus;
    }

    /**
     * 清理默认端口（杀死占用进程）
     */
    async cleanDefaultPorts() {
        console.log('🧹 清理默认端口...\n');
        
        let cleaned = 0;
        let failed = 0;
        
        for (const [name, port] of Object.entries(this.defaultPorts)) {
            const pid = await this.getPortPid(port);
            
            if (pid) {
                try {
                    await this.killProcess(pid);
                    console.log(`✅ 已清理 ${name} 端口 ${port}（PID: ${pid}）`);
                    cleaned++;
                } catch (error) {
                    console.error(`❌ 清理 ${name} 端口 ${port} 失败:`, error.message);
                    failed++;
                }
            }
        }
        
        console.log('');
        console.log(`📊 清理结果: 成功 ${cleaned}, 失败 ${failed}`);
        console.log('');
        
        return { cleaned, failed };
    }

    /**
     * 获取占用指定端口的进程 PID
     * @param {number} port 端口号
     * @returns {Promise<number|null>} 进程 PID 或 null
     */
    async getPortPid(port) {
        try {
            const platform = process.platform;
            
            if (platform === 'win32') {
                // Windows: 使用 netstat
                const { stdout } = await execAsync(
                    `netstat -ano | findstr :${port}`,
                    { encoding: 'utf8' }
                );
                
                // 解析输出，查找 LISTENING 状态
                const lines = stdout.split('\n');
                for (const line of lines) {
                    if (line.includes('LISTENING')) {
                        const parts = line.trim().split(/\s+/);
                        const pid = parseInt(parts[parts.length - 1]);
                        if (!isNaN(pid)) {
                            return pid;
                        }
                    }
                }
            } else {
                // Unix/Linux/Mac: 使用 lsof
                const { stdout } = await execAsync(
                    `lsof -ti :${port}`,
                    { encoding: 'utf8' }
                );
                
                const pid = parseInt(stdout.trim());
                if (!isNaN(pid)) {
                    return pid;
                }
            }
            
            return null;
        } catch (error) {
            // 端口未被占用会抛出错误，返回 null
            return null;
        }
    }

    /**
     * 杀死指定进程
     * @param {number} pid 进程 PID
     */
    async killProcess(pid) {
        const platform = process.platform;
        
        try {
            if (platform === 'win32') {
                // Windows: 使用 taskkill
                await execAsync(`taskkill /F /PID ${pid}`, { encoding: 'utf8' });
            } else {
                // Unix/Linux/Mac: 使用 kill
                await execAsync(`kill -9 ${pid}`, { encoding: 'utf8' });
            }
            
            // 等待进程终止
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            throw new Error(`杀死进程 ${pid} 失败: ${error.message}`);
        }
    }

    /**
     * 检查单个端口是否可用
     * @param {number} port 端口号
     * @returns {Promise<boolean>} 端口是否可用
     */
    async isPortAvailable(port) {
        const pid = await this.getPortPid(port);
        return pid === null;
    }

    /**
     * 查找可用端口（从指定端口开始递增查找）
     * @param {number} startPort 起始端口
     * @param {number} maxAttempts 最大尝试次数
     * @returns {Promise<number|null>} 可用端口或 null
     */
    async findAvailablePort(startPort, maxAttempts = 10) {
        for (let i = 0; i < maxAttempts; i++) {
            const port = startPort + i;
            const available = await this.isPortAvailable(port);
            
            if (available) {
                return port;
            }
        }
        
        return null;
    }
}

module.exports = PortManager;

// 如果直接运行此文件，执行测试
if (require.main === module) {
    const manager = new PortManager();
    
    (async () => {
        console.log('=== 端口管理器测试 ===\n');
        
        // 检查端口
        await manager.checkDefaultPorts();
        
        // 询问是否清理
        console.log('是否清理占用的端口？(y/n)');
        
        process.stdin.once('data', async (data) => {
            const answer = data.toString().trim().toLowerCase();
            
            if (answer === 'y') {
                await manager.cleanDefaultPorts();
            }
            
            process.exit(0);
        });
    })();
}

