#!/usr/bin/env node

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

/**
 * 端口管理器 - 支持批量端口检测和杀死
 */
class PortManager {
    constructor() {
        this.defaultPorts = [9019, 9020, 9021, 10030];
    }

    /**
     * 检查单个端口是否被占用
     * @param {number} port - 端口号
     * @returns {Promise<boolean>} 是否被占用
     */
    async isPortOccupied(port) {
        try {
            const { stdout } = await execAsync(`netstat -ano | findstr :${port}`);
            return stdout.trim().length > 0;
        } catch (error) {
            return false;
        }
    }

    /**
     * 获取占用端口的进程ID列表
     * @param {number} port - 端口号
     * @returns {Promise<Set<string>>} 进程ID集合
     */
    async getPortProcesses(port) {
        try {
            const { stdout } = await execAsync(`netstat -ano | findstr :${port}`);
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
            
            return pids;
        } catch (error) {
            return new Set();
        }
    }

    /**
     * 杀死指定进程
     * @param {string} pid - 进程ID
     * @returns {Promise<boolean>} 是否成功
     */
    async killProcess(pid) {
        try {
            await execAsync(`taskkill /F /PID ${pid}`);
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * 杀死占用指定端口的所有进程
     * @param {number} port - 端口号
     * @returns {Promise<{success: boolean, killedPids: string[]}>}
     */
    async killPort(port) {
        console.log(`🔍 检查端口 ${port} 的占用情况...`);
        
        const pids = await this.getPortProcesses(port);
        
        if (pids.size === 0) {
            console.log(`✅ 端口 ${port} 未被占用`);
            return { success: true, killedPids: [] };
        }

        const killedPids = [];
        
        for (const pid of pids) {
            console.log(`🔪 正在杀死进程 PID: ${pid}...`);
            const success = await this.killProcess(pid);
            
            if (success) {
                console.log(`✅ 成功杀死进程 PID: ${pid}`);
                killedPids.push(pid);
            } else {
                console.log(`⚠️  无法杀死进程 PID: ${pid} (可能已经结束)`);
            }
        }

        // 等待端口释放
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 验证端口状态
        const stillOccupied = await this.isPortOccupied(port);
        if (stillOccupied) {
            console.log(`⚠️  端口 ${port} 仍被占用，可能需要手动处理`);
            return { success: false, killedPids };
        } else {
            console.log(`✅ 端口 ${port} 已成功释放`);
            return { success: true, killedPids };
        }
    }

    /**
     * 批量杀死多个端口
     * @param {number[]} ports - 端口列表
     * @returns {Promise<{totalKilled: number, results: Object}>}
     */
    async killPorts(ports) {
        console.log(`🚀 开始批量清理端口: ${ports.join(', ')}`);
        console.log('=' * 50);
        
        const results = {};
        let totalKilled = 0;
        
        for (const port of ports) {
            const result = await this.killPort(port);
            results[port] = result;
            totalKilled += result.killedPids.length;
            console.log(''); // 空行分隔
        }
        
        console.log('=' * 50);
        console.log(`🎉 批量清理完成，共杀死 ${totalKilled} 个进程`);
        
        return { totalKilled, results };
    }

    /**
     * 检查所有默认端口状态
     * @returns {Promise<{occupied: number[], free: number[]}>}
     */
    async checkDefaultPorts() {
        const occupied = [];
        const free = [];
        
        console.log('🔍 检查默认端口状态...');
        
        for (const port of this.defaultPorts) {
            const isOccupied = await this.isPortOccupied(port);
            if (isOccupied) {
                occupied.push(port);
                console.log(`❌ 端口 ${port}: 已占用`);
            } else {
                free.push(port);
                console.log(`✅ 端口 ${port}: 可用`);
            }
        }
        
        return { occupied, free };
    }

    /**
     * 清理所有默认端口
     * @returns {Promise<{totalKilled: number, results: Object}>}
     */
    async cleanDefaultPorts() {
        const status = await this.checkDefaultPorts();
        
        if (status.occupied.length === 0) {
            console.log('✅ 所有默认端口都可用，无需清理');
            return { totalKilled: 0, results: {} };
        }
        
        console.log(`⚠️  发现 ${status.occupied.length} 个端口被占用，开始清理...`);
        return await this.killPorts(status.occupied);
    }
}

// 命令行接口
async function main() {
    const manager = new PortManager();
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('端口管理器 - 使用说明:');
        console.log('  node port-manager.js check          - 检查默认端口状态');
        console.log('  node port-manager.js clean          - 清理所有默认端口');
        console.log('  node port-manager.js kill <port>    - 杀死指定端口');
        console.log('  node port-manager.js kill <p1> <p2> - 杀死多个端口');
        console.log('');
        console.log('默认端口: 9019, 9020, 9021, 10030');
        return;
    }
    
    const command = args[0];
    
    try {
        switch (command) {
            case 'check':
                await manager.checkDefaultPorts();
                break;
                
            case 'clean':
                await manager.cleanDefaultPorts();
                break;
                
            case 'kill':
                if (args.length === 1) {
                    console.error('❌ 请提供要杀死的端口号');
                    process.exit(1);
                }
                
                const ports = args.slice(1).map(p => {
                    const port = parseInt(p);
                    if (isNaN(port) || port < 1 || port > 65535) {
                        console.error(`❌ 无效的端口号: ${p}`);
                        process.exit(1);
                    }
                    return port;
                });
                
                if (ports.length === 1) {
                    await manager.killPort(ports[0]);
                } else {
                    await manager.killPorts(ports);
                }
                break;
                
            default:
                console.error(`❌ 未知命令: ${command}`);
                process.exit(1);
        }
    } catch (error) {
        console.error(`❌ 执行失败: ${error.message}`);
        process.exit(1);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    main();
}

module.exports = PortManager;