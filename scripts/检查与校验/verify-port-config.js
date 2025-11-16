#!/usr/bin/env node

/**
 * 端口配置验证脚本
 * 
 * 功能：
 * 1. 检查所有配置文件中的端口设置是否一致
 * 2. 验证端口是否在 Windows 保留范围内
 * 3. 检查端口是否被占用
 * 
 * 使用：
 *   node scripts/检查与校验/verify-port-config.js
 * 
 * 审查人：叶维哲
 * 日期：2025-11-16
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 期望的端口配置
const EXPECTED_PORTS = {
    backend: 11111,
    frontend: 10200,  // 已从 10065 更新为 10200
};

// Windows 已知保留端口范围
const WINDOWS_RESERVED_RANGES = [
    { start: 10017, end: 10116, name: 'Hyper-V 动态端口' },
    { start: 49152, end: 65535, name: 'IANA 动态端口' },
];

console.log('🔍 开始验证端口配置...\n');

/**
 * 检查端口是否在保留范围内
 */
function isPortReserved(port) {
    for (const range of WINDOWS_RESERVED_RANGES) {
        if (port >= range.start && port <= range.end) {
            return { reserved: true, range };
        }
    }
    return { reserved: false };
}

/**
 * 检查端口是否被占用
 */
function isPortInUse(port) {
    try {
        // Windows: 使用 netstat
        const output = execSync(`netstat -ano | findstr ":${port} "`, { encoding: 'utf-8' });
        return output.trim().length > 0;
    } catch (error) {
        // findstr 没有找到匹配项会返回错误代码
        return false;
    }
}

/**
 * 检查 Windows 保留端口范围
 */
function checkWindowsReservedPorts() {
    try {
        const output = execSync('netsh interface ipv4 show excludedportrange protocol=tcp', { encoding: 'utf-8' });
        console.log('📋 Windows TCP 保留端口范围：');
        console.log(output);
        return output;
    } catch (error) {
        console.error('❌ 无法获取 Windows 保留端口范围');
        return null;
    }
}

/**
 * 验证配置文件
 */
function verifyConfigFile(filePath, expectedPort, searchPattern) {
    const fullPath = path.resolve(__dirname, '../../', filePath);
    
    if (!fs.existsSync(fullPath)) {
        console.log(`⚠️  文件不存在: ${filePath}`);
        return false;
    }
    
    const content = fs.readFileSync(fullPath, 'utf-8');
    const regex = new RegExp(searchPattern.replace('PORT', '\\d+'));
    const matches = content.match(regex);
    
    if (!matches) {
        console.log(`⚠️  未找到端口配置: ${filePath}`);
        return false;
    }
    
    const portMatch = matches[0].match(/\d+/);
    const actualPort = portMatch ? parseInt(portMatch[0]) : null;
    
    if (actualPort === expectedPort) {
        console.log(`✅ ${filePath}: ${actualPort}`);
        return true;
    } else {
        console.log(`❌ ${filePath}: 期望 ${expectedPort}, 实际 ${actualPort}`);
        return false;
    }
}

/**
 * 主验证流程
 */
function main() {
    let allPassed = true;
    
    // 1. 检查前端端口配置
    console.log('1️⃣  检查前端端口配置（期望: 10200）\n');
    
    const frontendConfigs = [
        {
            file: 'electron/renderer/vite.config.ts',
            pattern: 'port:\\s*PORT'
        },
        {
            file: 'electron/renderer/package.json',
            pattern: '--port\\s+PORT'
        },
        {
            file: 'electron/main.js',
            pattern: '127\\.0\\.0\\.1:PORT'
        },
        {
            file: 'package.json',
            pattern: '127\\.0\\.0\\.1:PORT'
        }
    ];
    
    for (const config of frontendConfigs) {
        const passed = verifyConfigFile(config.file, EXPECTED_PORTS.frontend, config.pattern);
        if (!passed) allPassed = false;
    }
    
    // 2. 检查端口是否在保留范围
    console.log('\n2️⃣  检查端口是否在 Windows 保留范围\n');
    
    for (const [name, port] of Object.entries(EXPECTED_PORTS)) {
        const result = isPortReserved(port);
        if (result.reserved) {
            console.log(`❌ ${name} 端口 ${port} 在保留范围内: ${result.range.name} (${result.range.start}-${result.range.end})`);
            allPassed = false;
        } else {
            console.log(`✅ ${name} 端口 ${port} 不在保留范围内`);
        }
    }
    
    // 3. 检查端口是否被占用
    console.log('\n3️⃣  检查端口是否被占用\n');
    
    for (const [name, port] of Object.entries(EXPECTED_PORTS)) {
        const inUse = isPortInUse(port);
        if (inUse) {
            console.log(`⚠️  ${name} 端口 ${port} 正在使用中`);
        } else {
            console.log(`✅ ${name} 端口 ${port} 未被占用`);
        }
    }
    
    // 4. 显示 Windows 保留端口范围
    console.log('\n4️⃣  Windows 保留端口范围\n');
    checkWindowsReservedPorts();
    
    // 5. 总结
    console.log('\n' + '='.repeat(60));
    if (allPassed) {
        console.log('✅ 所有端口配置验证通过！');
        console.log('\n可以使用以下命令启动服务：');
        console.log('  npm run start:integrated');
    } else {
        console.log('❌ 端口配置验证失败！');
        console.log('\n请检查上述错误并修复后再试。');
        process.exit(1);
    }
    console.log('='.repeat(60));
}

// 运行验证
try {
    main();
} catch (error) {
    console.error('❌ 验证过程中出错:', error.message);
    process.exit(1);
}
