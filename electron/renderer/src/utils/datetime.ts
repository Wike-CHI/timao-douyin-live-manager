/**
 * 日期时间工具类
 * 统一处理 ISO 8601 格式的日期时间字符串
 * 修复需求: MISC-002 (日期时间类型统一)
 */

/**
 * 日期时间工具类
 */
export class DateTimeUtils {
  /**
   * 解析 ISO 8601 字符串为 Date 对象
   * 
   * @param iso ISO 8601 格式的日期时间字符串
   * @returns Date 对象
   * @throws Error 如果字符串格式无效
   * 
   * @example
   * ```typescript
   * const date = DateTimeUtils.parse('2025-11-02T19:38:10.123Z');
   * ```
   */
  static parse(iso: string): Date {
    const date = new Date(iso);
    if (isNaN(date.getTime())) {
      throw new Error(`Invalid ISO 8601 date string: ${iso}`);
    }
    return date;
  }
  
  /**
   * 格式化 Date 对象为显示字符串
   * 
   * @param date Date 对象
   * @param format 格式选项
   * @returns 格式化后的字符串
   * 
   * @example
   * ```typescript
   * const date = new Date();
   * DateTimeUtils.format(date, 'date');      // "2025/11/2"
   * DateTimeUtils.format(date, 'time');      // "19:38:10"
   * DateTimeUtils.format(date, 'datetime');  // "2025/11/2 19:38:10"
   * DateTimeUtils.format(date, 'relative');  // "5分钟前"
   * ```
   */
  static format(
    date: Date, 
    format: 'date' | 'time' | 'datetime' | 'relative' = 'datetime'
  ): string {
    switch (format) {
      case 'date':
        return date.toLocaleDateString('zh-CN');
      case 'time':
        return date.toLocaleTimeString('zh-CN');
      case 'datetime':
        return date.toLocaleString('zh-CN');
      case 'relative':
        return this.formatRelative(date);
      default:
        return date.toISOString();
    }
  }
  
  /**
   * 格式化为相对时间（如"5分钟前"）
   * 
   * @param date Date 对象
   * @returns 相对时间字符串
   * 
   * @example
   * ```typescript
   * const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
   * DateTimeUtils.formatRelative(fiveMinutesAgo);  // "5分钟前"
   * ```
   */
  static formatRelative(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 0) return '未来时间';
    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时前`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}天前`;
    
    return this.format(date, 'date');
  }
  
  /**
   * 验证 ISO 8601 字符串格式
   * 
   * @param iso ISO 8601 字符串
   * @returns 是否有效
   * 
   * @example
   * ```typescript
   * DateTimeUtils.isValid('2025-11-02T19:38:10.123Z');  // true
   * DateTimeUtils.isValid('invalid-date');               // false
   * ```
   */
  static isValid(iso: string): boolean {
    try {
      const date = new Date(iso);
      return !isNaN(date.getTime());
    } catch {
      return false;
    }
  }
  
  /**
   * 比较两个日期
   * 
   * @param a 日期1（字符串或Date对象）
   * @param b 日期2（字符串或Date对象）
   * @returns 差值（毫秒），a > b 为正数，a < b 为负数，a = b 为0
   * 
   * @example
   * ```typescript
   * DateTimeUtils.compare('2025-11-02', '2025-11-01');  // > 0
   * ```
   */
  static compare(a: string | Date, b: string | Date): number {
    const dateA = typeof a === 'string' ? this.parse(a) : a;
    const dateB = typeof b === 'string' ? this.parse(b) : b;
    return dateA.getTime() - dateB.getTime();
  }
  
  /**
   * 计算日期差值（天数）
   * 
   * @param a 日期1
   * @param b 日期2
   * @returns 相差的天数
   * 
   * @example
   * ```typescript
   * DateTimeUtils.diffDays('2025-12-31', '2025-11-02');  // 59
   * ```
   */
  static diffDays(a: string | Date, b: string | Date): number {
    const dateA = typeof a === 'string' ? this.parse(a) : a;
    const dateB = typeof b === 'string' ? this.parse(b) : b;
    const diffMs = Math.abs(dateA.getTime() - dateB.getTime());
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  }
  
  /**
   * 判断日期是否在未来
   * 
   * @param date 日期
   * @returns 是否在未来
   */
  static isFuture(date: string | Date): boolean {
    const targetDate = typeof date === 'string' ? this.parse(date) : date;
    return targetDate.getTime() > Date.now();
  }
  
  /**
   * 判断日期是否在过去
   * 
   * @param date 日期
   * @returns 是否在过去
   */
  static isPast(date: string | Date): boolean {
    const targetDate = typeof date === 'string' ? this.parse(date) : date;
    return targetDate.getTime() < Date.now();
  }
}

