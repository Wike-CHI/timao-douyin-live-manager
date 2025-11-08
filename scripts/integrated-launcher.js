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
            'scripts/service_launcher.py'
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
            
            // 准备环境变量（在 spawn 之前，避免变量作用域冲突）
            const spawnEnv = {
                ...process.env,
                // 设置 UTF-8 编码，解决 Windows 中文乱码问题
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
            };
            
            // 合并传入的环境变量选项
            const finalEnv = { ...spawnEnv, ...(options.env || {}) };
            const childProcess = spawn(command, args, {
                cwd,
                stdio: ['ignore', 'pipe', 'pipe'],
                shell: true,
                env: finalEnv,
                ...options
            });
            
            this.processes.set(name, childProcess);
            
            // 输出处理（使用 UTF-8 解码）
            childProcess.stdout.on('data', (data) => {
                const output = data.toString('utf-8').trim();
                if (output) {
                    console.log(`[${name}] ${output}`);
                }
            });
            
            childProcess.stderr.on('data', (data) => {
                const output = data.toString('utf-8').trim();
                if (output) {
                    console.log(`[${name}] ${output}`);
                }
            });
            
            childProcess.on('close', (code) => {
                this.processes.delete(name);
                if (code === 0) {
                    console.log(`✅ 服务 ${name} 正常退出`);
                } else {
                    console.log(`❌ 服务 ${name} 异常退出 (代码: ${code})`);
                }
            });
            
            childProcess.on('error', (error) => {
                this.processes.delete(name);
                console.error(`❌ 服务 ${name} 启动失败: ${error.message}`);
                reject(error);
            });
            
            // 给进程一些时间启动
            setTimeout(() => {
                if (this.processes.has(name)) {
                    console.log(`✅ 服务 ${name} 启动成功 (PID: ${childProcess.pid})`);
                    resolve(childProcess);
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
        // 使用环境变量 BACKEND_PORT，默认 11111（按需与前端配置保持一致）
        const backendPort = process.env.BACKEND_PORT || '11111';
        const serverPath = path.join(this.projectRoot, 'server');
        
        // 检测虚拟环境中的Python路径
        const venvPython = process.platform === 'win32'
            ? path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe')
            : path.join(this.projectRoot, '.venv', 'bin', 'python');
        
        // 如果虚拟环境存在，使用虚拟环境的Python，否则使用全局Python
        const pythonCommand = fs.existsSync(venvPython) ? venvPython : 'python';
        
        console.log(`📍 使用Python: ${pythonCommand}`);
        
        // 将端口号传递给子进程
        const spawnEnv = {
            ...process.env,
            BACKEND_PORT: backendPort,
            PYTHONIOENCODING: 'utf-8',
            PYTHONUTF8: '1',
        };
        
        await this.startService(
            'Backend',
            pythonCommand,
            ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', backendPort, '--reload'],
            serverPath,
            { env: spawnEnv }
        );
        
        // 等待后端服务启动
        const backendReady = await this.waitForHealthCheck(`http://127.0.0.1:${backendPort}/health`);
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
        
        // 等待前端服务启动（默认端口 10089，可通过 FRONTEND_PORT 覆盖）
        const frontendPort = process.env.FRONTEND_PORT || '10089';
        const frontendReady = await this.waitForHealthCheck(`http://127.0.0.1:${frontendPort}`);
        if (!frontendReady) {
            // 如果默认端口失败，尝试旧版本使用的 10109 端口（向后兼容）
            const fallbackReady = await this.waitForHealthCheck('http://127.0.0.1:10109');
            if (!fallbackReady) {
                throw new Error('前端服务启动失败');
            }
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
            console.log('='.repeat(60));
            
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
            
            const backendPort = process.env.BACKEND_PORT || '11111';
            const frontendPort = process.env.FRONTEND_PORT || '10089';
            console.log('\n' + '='.repeat(60));
            console.log('🎉 所有服务启动完成！');
            console.log('');
            console.log('📍 服务地址:');
            console.log(`   - 后端API: http://127.0.0.1:${backendPort}`);
            console.log(`   - 前端开发: http://127.0.0.1:${frontendPort}`);
            console.log(`   - 健康检查: http://127.0.0.1:${backendPort}/health`);
            console.log('');
            console.log('💡 按 Ctrl+C 停止所有服务');
            console.log('='.repeat(60));
            
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