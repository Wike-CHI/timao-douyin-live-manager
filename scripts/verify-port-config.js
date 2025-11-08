#!/usr/bin/env node
/**
 * 端口配置验证脚本
 * 检查所有配置文件中的端口设置是否正确
 */

const fs = require('fs');
const path = require('path');

const projectRoot = path.join(__dirname, '..');

// 预期配置
const EXPECTED_PORTS = {
    frontend: '10050',
    backend: '11111'
};

const checks = [];

console.log('🔍 开始验证端口配置...\n');

// 1. 检查 electron/main.js
try {
    const mainJsPath = path.join(projectRoot, 'electron', 'main.js');
    const content = fs.readFileSync(mainJsPath, 'utf8');
    
    // 检查前端端口
    if (content.includes(`http://127.0.0.1:${EXPECTED_PORTS.frontend}`)) {
        checks.push({ file: 'electron/main.js', item: '前端端口', status: '✅', value: EXPECTED_PORTS.frontend });
    } else {
        checks.push({ file: 'electron/main.js', item: '前端端口', status: '❌', value: '未找到' });
    }
    
    // 检查后端端口
    if (content.includes(`port: '${EXPECTED_PORTS.backend}'`)) {
        checks.push({ file: 'electron/main.js', item: '后端端口', status: '✅', value: EXPECTED_PORTS.backend });
    } else {
        checks.push({ file: 'electron/main.js', item: '后端端口', status: '❌', value: '未找到' });
    }
} catch (error) {
    checks.push({ file: 'electron/main.js', item: '文件读取', status: '❌', value: error.message });
}

// 2. 检查 electron/renderer/vite.config.ts
try {
    const viteConfigPath = path.join(projectRoot, 'electron', 'renderer', 'vite.config.ts');
    const content = fs.readFileSync(viteConfigPath, 'utf8');
    
    if (content.includes(`port: ${EXPECTED_PORTS.frontend}`)) {
        checks.push({ file: 'electron/renderer/vite.config.ts', item: '前端端口', status: '✅', value: EXPECTED_PORTS.frontend });
    } else {
        checks.push({ file: 'electron/renderer/vite.config.ts', item: '前端端口', status: '❌', value: '未找到' });
    }
    
    if (content.includes('strictPort: true')) {
        checks.push({ file: 'electron/renderer/vite.config.ts', item: 'strictPort', status: '✅', value: 'true' });
    } else {
        checks.push({ file: 'electron/renderer/vite.config.ts', item: 'strictPort', status: '⚠️', value: 'false或未设置' });
    }
} catch (error) {
    checks.push({ file: 'electron/renderer/vite.config.ts', item: '文件读取', status: '❌', value: error.message });
}

// 3. 检查 electron/renderer/package.json
try {
    const packageJsonPath = path.join(projectRoot, 'electron', 'renderer', 'package.json');
    const content = fs.readFileSync(packageJsonPath, 'utf8');
    
    if (content.includes(`--port ${EXPECTED_PORTS.frontend}`) && content.includes('--strictPort')) {
        checks.push({ file: 'electron/renderer/package.json', item: 'dev脚本', status: '✅', value: `端口${EXPECTED_PORTS.frontend}+strictPort` });
    } else {
        checks.push({ file: 'electron/renderer/package.json', item: 'dev脚本', status: '❌', value: '配置不完整' });
    }
} catch (error) {
    checks.push({ file: 'electron/renderer/package.json', item: '文件读取', status: '❌', value: error.message });
}

// 4. 检查 scripts/integrated-launcher.js
try {
    const launcherPath = path.join(projectRoot, 'scripts', 'integrated-launcher.js');
    const content = fs.readFileSync(launcherPath, 'utf8');
    
    const backendMatches = content.match(/const backendPort = '(\d+)'/g);
    const frontendMatches = content.match(/const frontendPort = '(\d+)'/g);
    
    if (backendMatches && backendMatches.some(m => m.includes(EXPECTED_PORTS.backend))) {
        checks.push({ file: 'scripts/integrated-launcher.js', item: '后端端口', status: '✅', value: EXPECTED_PORTS.backend });
    } else {
        checks.push({ file: 'scripts/integrated-launcher.js', item: '后端端口', status: '❌', value: '未找到或不正确' });
    }
    
    if (frontendMatches && frontendMatches.some(m => m.includes(EXPECTED_PORTS.frontend))) {
        checks.push({ file: 'scripts/integrated-launcher.js', item: '前端端口', status: '✅', value: EXPECTED_PORTS.frontend });
    } else {
        checks.push({ file: 'scripts/integrated-launcher.js', item: '前端端口', status: '❌', value: '未找到或不正确' });
    }
} catch (error) {
    checks.push({ file: 'scripts/integrated-launcher.js', item: '文件读取', status: '❌', value: error.message });
}

// 5. 检查 server/config.py
try {
    const configPyPath = path.join(projectRoot, 'server', 'config.py');
    const content = fs.readFileSync(configPyPath, 'utf8');
    
    if (content.includes(`port: int = ${EXPECTED_PORTS.backend}`)) {
        checks.push({ file: 'server/config.py', item: '后端端口', status: '✅', value: EXPECTED_PORTS.backend });
    } else {
        checks.push({ file: 'server/config.py', item: '后端端口', status: '❌', value: '未找到或不正确' });
    }
} catch (error) {
    checks.push({ file: 'server/config.py', item: '文件读取', status: '❌', value: error.message });
}

// 输出结果
console.log('📊 验证结果:\n');
console.log('┌─────────────────────────────────────┬──────────────┬────────┬─────────────┐');
console.log('│ 文件                                │ 检查项       │ 状态   │ 值          │');
console.log('├─────────────────────────────────────┼──────────────┼────────┼─────────────┤');

checks.forEach(check => {
    const file = check.file.padEnd(36);
    const item = check.item.padEnd(12);
    const status = check.status.padEnd(6);
    const value = check.value.padEnd(12);
    console.log(`│ ${file}│ ${item}│ ${status}│ ${value}│`);
});

console.log('└─────────────────────────────────────┴──────────────┴────────┴─────────────┘\n');

// 统计结果
const passed = checks.filter(c => c.status === '✅').length;
const failed = checks.filter(c => c.status === '❌').length;
const warning = checks.filter(c => c.status === '⚠️').length;

console.log(`✅ 通过: ${passed}/${checks.length}`);
if (warning > 0) console.log(`⚠️  警告: ${warning}/${checks.length}`);
if (failed > 0) console.log(`❌ 失败: ${failed}/${checks.length}`);

if (failed > 0) {
    console.log('\n❌ 端口配置验证失败！请检查上述失败项。');
    process.exit(1);
} else if (warning > 0) {
    console.log('\n⚠️  端口配置有警告项，建议检查。');
    process.exit(0);
} else {
    console.log('\n✅ 所有端口配置正确！');
    console.log(`\n📌 配置摘要:`);
    console.log(`   - 前端端口: ${EXPECTED_PORTS.frontend}`);
    console.log(`   - 后端端口: ${EXPECTED_PORTS.backend}`);
    process.exit(0);
}

