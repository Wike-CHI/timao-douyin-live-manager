/**
 * Windows打包脚本自动测试
 * 审查人：叶维哲
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 颜色输出
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function success(message) {
    log(`✓ ${message}`, 'green');
}

function error(message) {
    log(`✗ ${message}`, 'red');
}

function info(message) {
    log(`ℹ ${message}`, 'cyan');
}

function warning(message) {
    log(`⚠ ${message}`, 'yellow');
}

// 测试结果统计
let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function test(name, fn) {
    totalTests++;
    try {
        fn();
        passedTests++;
        success(`测试通过: ${name}`);
        return true;
    } catch (err) {
        failedTests++;
        error(`测试失败: ${name}`);
        error(`  原因: ${err.message}`);
        return false;
    }
}

// 获取项目根目录
const projectRoot = path.join(__dirname, '..', '..');

log('\n========================================', 'cyan');
log('Windows打包脚本测试套件', 'cyan');
log('========================================\n', 'cyan');

// 测试1: 检查脚本文件是否存在
test('检查 package-windows.bat 文件存在', () => {
    const batPath = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows.bat');
    if (!fs.existsSync(batPath)) {
        throw new Error(`文件不存在: ${batPath}`);
    }
});

test('检查 package-windows.ps1 文件存在', () => {
    const ps1Path = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows.ps1');
    if (!fs.existsSync(ps1Path)) {
        throw new Error(`文件不存在: ${ps1Path}`);
    }
});

test('检查 package-windows-quick.bat 文件存在', () => {
    const quickPath = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows-quick.bat');
    if (!fs.existsSync(quickPath)) {
        throw new Error(`文件不存在: ${quickPath}`);
    }
});

// 测试2: 检查脚本内容
test('package-windows.bat 包含必要的构建步骤', () => {
    const batPath = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows.bat');
    const content = fs.readFileSync(batPath, 'utf-8');
    
    const requiredSteps = [
        'npm install',
        'npm run build',
        'electron-builder'
    ];
    
    for (const step of requiredSteps) {
        if (!content.includes(step)) {
            throw new Error(`缺少必要步骤: ${step}`);
        }
    }
});

test('package-windows.ps1 包含错误处理', () => {
    const ps1Path = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows.ps1');
    const content = fs.readFileSync(ps1Path, 'utf-8');
    
    if (!content.includes('ErrorActionPreference')) {
        throw new Error('缺少错误处理配置');
    }
    if (!content.includes('try') || !content.includes('catch')) {
        throw new Error('缺少try-catch错误处理');
    }
});

// 测试3: 检查package.json配置
test('package.json 包含新的打包命令', () => {
    const packagePath = path.join(projectRoot, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf-8'));
    
    const requiredScripts = [
        'package:windows',
        'package:windows:ps',
        'package:windows:quick'
    ];
    
    for (const script of requiredScripts) {
        if (!packageJson.scripts[script]) {
            throw new Error(`package.json缺少脚本: ${script}`);
        }
    }
});

// 测试4: 检查构建配置文件
test('build-config.json 存在且配置正确', () => {
    const configPath = path.join(projectRoot, 'build-config.json');
    if (!fs.existsSync(configPath)) {
        throw new Error('build-config.json 不存在');
    }
    
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    
    if (!config.win) {
        throw new Error('缺少Windows构建配置');
    }
    
    if (!config.win.target || !Array.isArray(config.win.target)) {
        throw new Error('Windows目标配置不正确');
    }
});

// 测试5: 检查必要的图标文件
test('检查Windows图标文件存在', () => {
    const iconPath = path.join(projectRoot, 'electron', 'renderer', 'src', 'assets', 'icon.ico');
    if (!fs.existsSync(iconPath)) {
        warning('图标文件不存在，打包可能会失败');
        throw new Error(`图标文件不存在: ${iconPath}`);
    }
});

// 测试6: 检查Node.js环境
test('检查Node.js环境', () => {
    try {
        const nodeVersion = execSync('node --version', { encoding: 'utf-8' }).trim();
        info(`  Node.js版本: ${nodeVersion}`);
        
        const versionMatch = nodeVersion.match(/v(\d+)/);
        if (versionMatch && parseInt(versionMatch[1]) < 16) {
            throw new Error('Node.js版本过低，需要16或更高版本');
        }
    } catch (err) {
        throw new Error('Node.js未安装或版本检查失败');
    }
});

test('检查npm环境', () => {
    try {
        const npmVersion = execSync('npm --version', { encoding: 'utf-8' }).trim();
        info(`  npm版本: ${npmVersion}`);
    } catch (err) {
        throw new Error('npm未安装');
    }
});

// 测试7: 检查electron-builder依赖
test('检查electron-builder依赖', () => {
    const packagePath = path.join(projectRoot, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf-8'));
    
    const hasElectronBuilder = 
        (packageJson.devDependencies && packageJson.devDependencies['electron-builder']) ||
        (packageJson.dependencies && packageJson.dependencies['electron-builder']);
    
    if (!hasElectronBuilder) {
        throw new Error('package.json中缺少electron-builder依赖');
    }
});

// 测试8: 检查输出目录配置
test('检查输出目录配置', () => {
    const configPath = path.join(projectRoot, 'build-config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    
    if (!config.directories || !config.directories.output) {
        throw new Error('缺少输出目录配置');
    }
    
    info(`  输出目录: ${config.directories.output}`);
});

// 测试9: 检查文件包含配置
test('检查文件包含配置', () => {
    const configPath = path.join(projectRoot, 'build-config.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    
    if (!config.files || !Array.isArray(config.files)) {
        throw new Error('缺少文件包含配置');
    }
    
    // 检查是否包含关键文件
    const hasMainJs = config.files.some(f => f.includes('main.js'));
    const hasRenderer = config.files.some(f => f.includes('renderer'));
    
    if (!hasMainJs) {
        warning('文件配置可能缺少main.js');
    }
    if (!hasRenderer) {
        warning('文件配置可能缺少renderer目录');
    }
});

// 测试10: 验证脚本可执行性
test('验证批处理脚本可执行', () => {
    const batPath = path.join(projectRoot, 'scripts', '构建与启动', 'package-windows.bat');
    const content = fs.readFileSync(batPath, 'utf-8');
    
    // 检查是否有UTF-8 BOM标记或正确的编码声明
    if (!content.includes('chcp 65001')) {
        warning('批处理脚本可能缺少UTF-8编码设置');
    }
    
    // 检查是否有错误处理
    if (!content.includes('errorlevel')) {
        warning('批处理脚本可能缺少错误处理');
    }
});

// 输出测试结果
log('\n========================================', 'cyan');
log('测试结果统计', 'cyan');
log('========================================', 'cyan');
log(`总测试数: ${totalTests}`);
log(`通过: ${passedTests}`, 'green');
log(`失败: ${failedTests}`, failedTests > 0 ? 'red' : 'reset');
log(`成功率: ${((passedTests / totalTests) * 100).toFixed(2)}%`, failedTests > 0 ? 'yellow' : 'green');
log('========================================\n', 'cyan');

// 提供使用建议
if (failedTests === 0) {
    success('所有测试通过！可以安全使用打包脚本。\n');
    info('使用方法:');
    info('  1. 完整打包: npm run package:windows');
    info('  2. PowerShell版本: npm run package:windows:ps');
    info('  3. 快速打包: npm run package:windows:quick\n');
} else {
    error('部分测试失败，请修复后再使用打包脚本。\n');
}

// 退出码
process.exit(failedTests > 0 ? 1 : 0);

