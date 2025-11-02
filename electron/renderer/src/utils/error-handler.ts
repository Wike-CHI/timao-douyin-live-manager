/**
 * 统一的错误处理工具
 * 修复需求: MISC-003 (错误响应统一)
 */

import { ErrorResponse, ErrorDetail, ValidationError, isErrorDetail, isValidationErrorArray } from '../types/api-types';

/**
 * 统一的错误处理类
 */
export class ErrorHandler {
  /**
   * 从错误响应中提取用户友好的错误消息
   */
  static extractMessage(error: ErrorResponse | any): string {
    if (!error) return '未知错误';
    
    // 标准 ErrorResponse 格式
    if ('detail' in error) {
      const { detail } = error;
      
      // 字符串格式
      if (typeof detail === 'string') {
        return detail;
      }
      
      // ErrorDetail 对象格式
      if (isErrorDetail(detail)) {
        return detail.message;
      }
      
      // ValidationError 数组格式
      if (isValidationErrorArray(detail)) {
        return this.formatValidationErrors(detail);
      }
    }
    
    // 网络错误
    if (error.message) {
      return error.message;
    }
    
    return '操作失败，请稍后重试';
  }
  
  /**
   * 格式化验证错误为可读字符串
   */
  private static formatValidationErrors(errors: ValidationError[]): string {
    if (errors.length === 0) return '验证失败';
    if (errors.length === 1) {
      const error = errors[0];
      const field = error.loc.join('.');
      return `${field}: ${error.msg}`;
    }
    
    // 多个错误，返回第一个或总结
    return errors.map(e => e.msg).join('; ');
  }
  
  /**
   * 提取错误代码（如果有）
   */
  static extractCode(error: ErrorResponse | any): string | undefined {
    if ('detail' in error && isErrorDetail(error.detail)) {
      return error.detail.code;
    }
    return undefined;
  }
  
  /**
   * 判断是否是特定类型的错误
   */
  static isErrorType(error: any, errorCode: string): boolean {
    const code = this.extractCode(error);
    return code === errorCode;
  }
}

/**
 * API 调用包装器，统一错误处理
 */
export async function apiCall<T>(
  fetchFn: () => Promise<Response>,
  errorPrefix: string = '操作'
): Promise<T> {
  try {
    const response = await fetchFn();
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `${errorPrefix}失败: HTTP ${response.status}`
      }));
      
      throw new Error(ErrorHandler.extractMessage(error));
    }
    
    return await response.json();
  } catch (error: any) {
    // 网络错误
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('网络连接失败，请检查网络设置');
    }
    
    // 已处理的错误
    if (error.message) {
      throw error;
    }
    
    // 未知错误
    throw new Error(`${errorPrefix}失败，请稍后重试`);
  }
}

