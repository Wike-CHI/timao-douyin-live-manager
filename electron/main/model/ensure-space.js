/**
 * 磁盘空间与写入权限检查
 * 基于文档: docs/部分服务从服务器转移本地.md - 磁盘空间与写入权限检查
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');

const ERR_ENOSPC = 'ENOSPC';
const ERR_EACCES = 'EACCES';

/**
 * 获取磁盘可用空间（跨平台）
 * @param {string} targetPath 目标路径
 * @returns {Promise<number>} 可用字节数
 */
async function getDiskFreeSpace(targetPath) {
  // 使用 Node.js 内置方法（需要自定义实现或使用第三方库）
  // 这里使用简化实现：Windows用wmic，Linux用df
  const platform = os.platform();
  
  if (platform === 'win32') {
    // Windows: 获取盘符
    const driveLetter = path.parse(targetPath).root.replace(':\\', '');
    
    return new Promise((resolve, reject) => {
      const { exec } = require('child_process');
      exec(`wmic logicaldisk where "DeviceID='${driveLetter}:'" get FreeSpace /value`, 
        (error, stdout) => {
          if (error) {
            reject(error);
            return;
          }
          const match = stdout.match(/FreeSpace=(\d+)/);
          if (match) {
            resolve(parseInt(match[1], 10));
          } else {
            reject(new Error('无法解析磁盘空间'));
          }
        }
      );
    });
  } else {
    // Unix-like: 使用df命令
    return new Promise((resolve, reject) => {
      const { exec } = require('child_process');
      exec(`df -k "${path.dirname(targetPath)}" | tail -1 | awk '{print $4}'`, 
        (error, stdout) => {
          if (error) {
            reject(error);
            return;
          }
          const freeKB = parseInt(stdout.trim(), 10);
          resolve(freeKB * 1024); // 转换为字节
        }
      );
    });
  }
}

/**
 * 确保目标路径有足够空间并且可写
 * @param {string} targetPath 目标文件完整路径或目录
 * @param {number} modelSizeBytes 模型大小（字节）
 * @returns {Promise<{requiredSpace: number, free: number}>}
 * @throws {Error} 错误对象包含 .code (ENOSPC/EACCES)
 */
async function ensureEnoughSpaceAndWritable(targetPath, modelSizeBytes) {
  const dir = path.dirname(targetPath);
  const safetyMargin = Math.ceil(0.1 * modelSizeBytes);
  const requiredSpace = modelSizeBytes + safetyMargin;

  // 1) 检查可用空间
  let free;
  try {
    free = await getDiskFreeSpace(targetPath);
  } catch (error) {
    console.warn('无法获取磁盘空间，跳过检查:', error.message);
    // 降级：不检查空间，继续
    free = Number.MAX_SAFE_INTEGER;
  }

  if (free < requiredSpace) {
    const err = new Error(`磁盘空间不足: 可用 ${free} bytes, 需要 ${requiredSpace} bytes`);
    err.code = ERR_ENOSPC;
    err.free = free;
    err.required = requiredSpace;
    throw err;
  }

  // 2) 检查路径存在性与写权限（尝试创建临时文件）
  try {
    // 如果目录不存在，尝试创建
    await fs.mkdir(dir, { recursive: true });
  } catch (e) {
    const err = new Error(`无法创建目录 ${dir}: ${e.message}`);
    err.code = ERR_EACCES;
    throw err;
  }

  try {
    // 写测试
    const tmp = path.join(dir, `.timao_write_test_${Date.now()}.tmp`);
    await fs.writeFile(tmp, 'test');
    await fs.unlink(tmp);
  } catch (e) {
    const err = new Error(`写入权限检测失败: ${e.message}`);
    err.code = ERR_EACCES;
    throw err;
  }

  // 通过
  return { requiredSpace, free };
}

module.exports = { 
  ensureEnoughSpaceAndWritable, 
  getDiskFreeSpace,
  ERR_ENOSPC, 
  ERR_EACCES 
};
