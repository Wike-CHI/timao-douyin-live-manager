#!/usr/bin/env node

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const PortManager = require('./port-manager');

/**
 * 一体化启动器
 */
class IntegratedLauncher {
    constructor() {
        this.portManager = new PortManager();
        this.processes = new Map();
        this.projectRoot = path.resolve(__dirname, '..');
        this.isShuttingDown = false;
        
        // 绑定信号处理
        this.setupSignalHandlers();
    }

    /**
     * 设置信号处理器
     */
    setupSignalHandlers() {
        const signals = ['SIGINT', 'SIGTERM', 'SIGQUIT'];
        
        signals.forEach(signal => {
            process.on(signal, async () => {
                if (!this.isShuttingDown) {
                    console.log(`\n🛑 接收到 ${signal} 信号，正在关闭所有服务...`);
                    await this.shutdown();
                }
            });
        });
        
        process.on('exit', () => {
            console.log('👋 启动器已退出');
        });
    }

    /**
     * 检查必要文件是否存在
     */
    checkPrerequisites() {
        const requiredFiles = [
            'package.json',
            'server/app/main.py',
            'electron/renderer/package.json',
            'service_launcher.py'
        ];
        
        console.log('🔍 检查必要文件...');
        
        for (const file of requiredFiles) {
            const filePath = path.join(this.projectRoot, file);
            if (!fs.existsSync(filePath)) {
                throw new Error(`必要文件不存在: ${file}`);
            }
        }
        
        console.log('✅ 所有必要文件检查通过');
    }

    /**
     * 启动单个服务
     * @param {string} name - 服务名称
     * @param {string} command - 命令
     * @param {string[]} args - 参数
     * @param {string} cwd - 工作目录
     * @param {Object} options - 额外选项
     */
    async startService(name, command, args = [], cwd = this.projectRoot, options = {}) {
        return new Promise((resolve, reject) => {
            console.log(`🚀 启动服务: ${name}`);
            console.log(`   命令: ${command} ${args.join(' ')}`);
            console.log(`   目录: ${cwd}`);
            
            const process = spawn(command, args, {
                cwd,
                stdio: ['ignore', 'pipe', 'pipe'],
                shell: true,
                ...options
            });
            
            this.processes.set(name, process);
            
            // 输出处理
            process.stdout.on('data', (data) => {
                const output = data.toString().trim();
                if (output) {
                    console.log(`[${name}] ${output}`);
                }
            });
            
            process.stderr.on('data', (data) => {
                const output = data.toString().trim();
                if (output) {
                    console.log(`[${name}] ${output}`);
                }
            });
            
            process.on('close', (code) => {
                this.processes.delete(name);
                if (code === 0) {
                    console.log(`✅ 服务 ${name} 正常退出`);
                } else {
                    console.log(`❌ 服务 ${name} 异常退出 (代码: ${code})`);
                }
            });
            
            process.on('error', (error) => {
                this.processes.delete(name);
                console.error(`❌ 服务 ${name} 启动失败: ${error.message}`);
                reject(error);
            });
            
            // 给进程一些时间启动
            setTimeout(() => {
                if (this.processes.has(name)) {
                    console.log(`✅ 服务 ${name} 启动成功 (PID: ${process.pid})`);
                    resolve(process);
                }
            }, 2000);
        });
    }

    /**
     * 等待服务健康检查
     * @param {string} url - 健康检查URL
     * @param {number} maxAttempts - 最大尝试次数
     * @param {number} interval - 检查间隔(ms)
     */
    async waitForHealthCheck(url, maxAttempts = 30, interval = 2000) {
        console.log(`🔍 等待服务健康检查: ${url}`);
        
        for (let i = 0; i < maxAttempts; i++) {
            try {
                const { exec } = require('child_process');
                const { promisify } = require('util');
                const execAsync = promisify(exec);
                
                await execAsync(`curl -f ${url}`, { timeout: 5000 });
                console.log(`✅ 服务健康检查通过: ${url}`);
                return true;
            } catch (error) {
                if (i === maxAttempts - 1) {
                    console.log(`❌ 服务健康检查失败: ${url}`);
                    return false;
                }
                
                console.log(`⏳ 等待服务启动... (${i + 1}/${maxAttempts})`);
                await new Promise(resolve => setTimeout(resolve, interval));
            }
        }
        
        return false;
    }

    /**
     * 启动后端服务
     */
    async startBackend() {
        const serverPath = path.join(this.projectRoot, 'server');
        await this.startService(
            'Backend',
            'python',
            ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '9019', '--reload'],
            serverPath
        );
        
        // 等待后端服务启动
        const backendReady = await this.waitForHealthCheck('http://127.0.0.1:9019/health');
        if (!backendReady) {
            throw new Error('后端服务启动失败');
        }
    }

    /**
     * 启动前端开发服务器
     */
    async startFrontend() {
        const rendererPath = path.join(this.projectRoot, 'electron', 'renderer');
        await this.startService(
            'Frontend',
            'npm',
            ['run', 'dev'],
            rendererPath
        );
        
        // 等待前端服务启动
        const frontendReady = await this.waitForHealthCheck('http://127.0.0.1:10030');
        if (!frontendReady) {
            throw new Error('前端服务启动失败');
        }
    }

    /**
     * 启动Electron应用
     */
    async startElectron() {
        await this.startService(
            'Electron',
            'npm',
            ['run', 'dev:electron'],
            this.projectRoot
        );
    }

    /**
     * 启动所有服务
     */
    async startAll() {
        try {
            console.log('🎯 开始一体化启动流程');
            console.log('=' * 60);
            
            // 1. 检查必要文件
            this.checkPrerequisites();
            
            // 2. 清理端口
            console.log('\n📋 第一步: 清理端口占用');
            await this.portManager.cleanDefaultPorts();
            
            // 3. 启动后端服务
            console.log('\n📋 第二步: 启动后端服务');
            await this.startBackend();
            
            // 4. 启动前端开发服务器
            console.log('\n📋 第三步: 启动前端开发服务器');
            await this.startFrontend();
            
            // 5. 启动Electron应用
            console.log('\n📋 第四步: 启动Electron应用');
            await this.startElectron();
            
            console.log('\n' + '=' * 60);
            console.log('🎉 所有服务启动完成！');
            console.log('');
            console.log('📍 服务地址:');
            console.log('   - 后端API: http://127.0.0.1:9019');
            console.log('   - 前端开发: http://127.0.0.1:10030');
            console.log('   - 健康检查: http://127.0.0.1:9019/health');
            console.log('');
            console.log('💡 按 Ctrl+C 停止所有服务');
            console.log('=' * 60);
            
            // 保持运行
            await this.keepAlive();
            
        } catch (error) {
            console.error(`❌ 启动失败: ${error.message}`);
            await this.shutdown();
            process.exit(1);
        }
    }

    /**
     * 保持进程运行
     */
    async keepAlive() {
        return new Promise((resolve) => {
            // 监听进程退出
            const checkInterval = setInterval(() => {
                if (this.processes.size === 0) {
                    console.log('⚠️  所有服务都已退出');
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 5000);
        });
    }

    /**
     * 关闭所有服务
     */
    async shutdown() {
        if (this.isShuttingDown) return;
        this.isShuttingDown = true;
        
        console.log('\n🛑 正在关闭所有服务...');
        
        const shutdownPromises = [];
        
        for (const [name, process] of this.processes) {
            shutdownPromises.push(
                new Promise((resolve) => {
                    console.log(`🔄 关闭服务: ${name}`);
                    
                    const timeout = setTimeout(() => {
                        console.log(`⚠️  强制杀死服务: ${name}`);
                        process.kill('SIGKILL');
                        resolve();
                    }, 5000);
                    
                    process.on('close', () => {
                        clearTimeout(timeout);
                        console.log(`✅ 服务 ${name} 已关闭`);
                        resolve();
                    });
                    
                    // 发送终止信号
                    if (process.platform === 'win32') {
                        exec(`taskkill /pid ${process.pid} /f /t`);
                    } else {
                        process.kill('SIGTERM');
                    }
                })
            );
        }
        
        await Promise.all(shutdownPromises);
        console.log('✅ 所有服务已关闭');
    }
}

// 命令行接口
async function main() {
    const launcher = new IntegratedLauncher();
    
    const args = process.argv.slice(2);
    const command = args[0] || 'start';
    
    switch (command) {
        case 'start':
            await launcher.startAll();
            break;
            
        case 'check':
            launcher.checkPrerequisites();
            await launcher.portManager.checkDefaultPorts();
            break;
            
        case 'clean':
            await launcher.portManager.cleanDefaultPorts();
            break;
            
        case 'help':
            console.log('一体化启动器 - 使用说明:');
            console.log('  node integrated-launcher.js start  - 启动所有服务 (默认)');
            console.log('  node integrated-launcher.js check  - 检查环境和端口');
            console.log('  node integrated-launcher.js clean  - 清理端口占用');
            console.log('  node integrated-launcher.js help   - 显示帮助');
            break;
            
        default:
            console.error(`❌ 未知命令: ${command}`);
            console.log('使用 "node integrated-launcher.js help" 查看帮助');
            process.exit(1);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(error => {
        console.error(`❌ 启动器错误: ${error.message}`);
        process.exit(1);
    });
}

module.exports = IntegratedLauncher;