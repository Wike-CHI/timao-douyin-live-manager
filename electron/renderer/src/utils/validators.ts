/**
 * 用户输入验证工具类
 * 与后端 Pydantic 验证器保持一致（修复 AUTH-004）
 */

export class UserValidator {
  /**
   * 验证用户名
   * 规则：3-50字符，仅支持字母、数字、下划线和连字符
   * 对应后端: server/app/api/auth.py:40-61
   */
  static validateUsername(username: string): { valid: boolean; message?: string } {
    if (!username || username.length < 3) {
      return { valid: false, message: '用户名长度至少3个字符' };
    }
    
    if (username.length > 50) {
      return { valid: false, message: '用户名长度不能超过50个字符' };
    }
    
    const pattern = /^[A-Za-z0-9_-]+$/;
    if (!pattern.test(username)) {
      return { valid: false, message: '用户名只能包含字母、数字、下划线和连字符' };
    }
    
    return { valid: true };
  }

  /**
   * 生成合法的用户名
   * 与后端逻辑保持一致
   * 对应后端: server/app/api/auth.py:40-61
   */
  static generateUsername(nickname: string, email: string): string {
    let candidate = nickname?.trim() || email.split('@')[0];
    
    // 移除非法字符
    candidate = candidate.replace(/[^A-Za-z0-9_-]/g, '');
    
    // 确保长度符合要求
    if (candidate.length < 3) {
      candidate = `user_${Date.now().toString().slice(-6)}`;
    }
    
    if (candidate.length > 50) {
      candidate = candidate.slice(0, 50);
    }
    
    return candidate;
  }

  /**
   * 验证密码
   * 规则：至少6个字符
   * 对应后端: server/app/api/auth.py:63-67
   */
  static validatePassword(password: string): { valid: boolean; message?: string } {
    if (!password || password.length < 6) {
      return { valid: false, message: '密码长度至少6个字符' };
    }
    
    return { valid: true };
  }

  /**
   * 验证邮箱
   * 基础邮箱格式验证
   */
  static validateEmail(email: string): { valid: boolean; message?: string } {
    if (!email) {
      return { valid: false, message: '邮箱不能为空' };
    }

    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!pattern.test(email)) {
      return { valid: false, message: '邮箱格式不正确' };
    }

    return { valid: true };
  }

  /**
   * 验证手机号（中国大陆）
   * 规则：11位数字，1开头
   */
  static validatePhone(phone: string): { valid: boolean; message?: string } {
    if (!phone) {
      return { valid: true };  // 手机号是可选的
    }

    const pattern = /^1[3-9]\d{9}$/;
    if (!pattern.test(phone)) {
      return { valid: false, message: '手机号格式不正确' };
    }

    return { valid: true };
  }

  /**
   * 验证昵称
   * 规则：1-50个字符
   */
  static validateNickname(nickname: string): { valid: boolean; message?: string } {
    if (!nickname) {
      return { valid: true };  // 昵称是可选的
    }

    if (nickname.length < 1 || nickname.length > 50) {
      return { valid: false, message: '昵称长度必须在1-50个字符之间' };
    }

    return { valid: true };
  }
}

/**
 * 金额格式化工具
 * 处理字符串格式的金额（修复 PAY-001）
 */
export class MoneyFormatter {
  /**
   * 格式化金额显示
   * @param amount 金额字符串（如 "99.00"）
   * @param currency 货币符号（默认 "¥"）
   * @returns 格式化后的字符串（如 "¥99.00"）
   */
  static format(amount: string, currency: string = '¥'): string {
    const num = parseFloat(amount);
    if (isNaN(num)) {
      return `${currency}0.00`;
    }
    return `${currency}${num.toFixed(2)}`;
  }

  /**
   * 解析金额字符串为数字（仅用于显示）
   * @param amount 金额字符串
   * @returns 数字
   */
  static parse(amount: string): number {
    const num = parseFloat(amount);
    return isNaN(num) ? 0 : num;
  }

  /**
   * 验证金额格式
   * @param amount 金额字符串
   * @returns 验证结果
   */
  static validate(amount: string): { valid: boolean; message?: string } {
    if (!amount) {
      return { valid: false, message: '金额不能为空' };
    }

    const num = parseFloat(amount);
    if (isNaN(num)) {
      return { valid: false, message: '金额格式不正确' };
    }

    if (num <= 0) {
      return { valid: false, message: '金额必须大于0' };
    }

    // 检查小数位数不超过2位
    const parts = amount.split('.');
    if (parts.length > 1 && parts[1].length > 2) {
      return { valid: false, message: '金额最多保留2位小数' };
    }

    return { valid: true };
  }

  /**
   * 金额字符串运算（加法）
   * @param amount1 金额1
   * @param amount2 金额2
   * @returns 结果金额字符串
   */
  static add(amount1: string, amount2: string): string {
    const num1 = parseFloat(amount1) || 0;
    const num2 = parseFloat(amount2) || 0;
    return (num1 + num2).toFixed(2);
  }

  /**
   * 金额字符串运算（减法）
   * @param amount1 金额1
   * @param amount2 金额2
   * @returns 结果金额字符串
   */
  static subtract(amount1: string, amount2: string): string {
    const num1 = parseFloat(amount1) || 0;
    const num2 = parseFloat(amount2) || 0;
    return (num1 - num2).toFixed(2);
  }

  /**
   * 金额字符串运算（乘法）
   * @param amount 金额
   * @param multiplier 乘数
   * @returns 结果金额字符串
   */
  static multiply(amount: string, multiplier: number): string {
    const num = parseFloat(amount) || 0;
    return (num * multiplier).toFixed(2);
  }
}

