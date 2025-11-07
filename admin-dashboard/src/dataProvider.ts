import { DataProvider, fetchUtils } from 'react-admin';

const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9019';

// 刷新token的标志，防止多个请求同时刷新
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

// 刷新token的函数
const refreshAccessToken = async (): Promise<string> => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  
  if (!response.ok) {
    // 刷新失败，清除所有token并跳转到登录页
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/#/login';
    throw new Error('Token refresh failed');
  }
  
  const data = await response.json();
  const newToken = data.access_token || data.token;
  const newRefreshToken = data.refresh_token || data.refreshToken;
  
  if (newToken) {
    localStorage.setItem('token', newToken);
  }
  
  if (newRefreshToken) {
    localStorage.setItem('refresh_token', newRefreshToken);
  }
  
  return newToken;
};

const httpClient = async (url: string, options: any = {}) => {
  const token = localStorage.getItem('token');
  
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' });
  }
  
  if (token) {
    options.headers.set('Authorization', `Bearer ${token}`);
  }
  
  try {
    return await fetchUtils.fetchJson(url, options);
  } catch (error: any) {
    // 如果是401错误，尝试刷新token
    if (error.status === 401) {
      try {
        // 如果正在刷新，等待刷新完成
        if (isRefreshing && refreshPromise) {
          const newToken = await refreshPromise;
          options.headers.set('Authorization', `Bearer ${newToken}`);
          return await fetchUtils.fetchJson(url, options);
        }
        
        // 开始刷新token
        isRefreshing = true;
        refreshPromise = refreshAccessToken();
        
        const newToken = await refreshPromise;
        isRefreshing = false;
        refreshPromise = null;
        
        // 使用新token重试请求
        options.headers.set('Authorization', `Bearer ${newToken}`);
        return await fetchUtils.fetchJson(url, options);
      } catch (refreshError) {
        isRefreshing = false;
        refreshPromise = null;
        // 刷新失败，重新抛出原始错误
        throw error;
      }
    }
    
    // 其他错误直接抛出
    throw error;
  }
};

export const dataProvider: DataProvider = {
    getList: async (resource, params) => {
        const { page, perPage } = params.pagination || { page: 1, perPage: 25 };
        
        // 构建查询参数
        const query = new URLSearchParams({
            page: page.toString(),
            size: perPage.toString(),
        });

        // 添加排序（后端使用不同的排序格式）
        // 后端目前不支持排序参数，可以在后续添加

        // 添加过滤
        if (params.filter) {
            // 搜索关键词 (支持 q 和 search 两种参数名)
            if (params.filter.q || params.filter.search) {
                query.append('search', params.filter.q || params.filter.search);
            }
            // 角色过滤
            if (params.filter.role) {
                query.append('role', params.filter.role);
            }
            // 状态过滤
            if (params.filter.status) {
                query.append('status', params.filter.status);
            }
            // 支付方式过滤
            if (params.filter.payment_method) {
                query.append('payment_method', params.filter.payment_method);
            }
            // 激活状态过滤
            if (params.filter.is_active !== undefined && params.filter.is_active !== null && params.filter.is_active !== '') {
                query.append('is_active', params.filter.is_active.toString());
            }
            // 验证状态过滤
            if (params.filter.is_verified !== undefined && params.filter.is_verified !== null && params.filter.is_verified !== '') {
                query.append('is_verified', params.filter.is_verified.toString());
            }
            // 套餐类型过滤
            if (params.filter.plan_type) {
                query.append('plan_type', params.filter.plan_type);
            }
        }

        const url = `${API_BASE}/api/admin/${resource}?${query.toString()}`;
        const { json } = await httpClient(url);
        
        return {
            data: json.data || json.items || [],
            total: json.total || (json.data ? json.data.length : 0),
        };
    },

    getOne: async (resource, params) => {
        const url = `${API_BASE}/api/admin/${resource}/${params.id}`;
        const { json } = await httpClient(url);
        
        // 如果返回的是详情格式，提取user字段
        if (json.data && json.data.user) {
            return {
                data: json.data,
            };
        }
        
        return {
            data: json.data || json,
        };
    },

  getMany: async (resource, params) => {
    const promises = params.ids.map((id) =>
      httpClient(`${API_BASE}/api/admin/${resource}/${id}`)
    );
    const responses = await Promise.all(promises);
    
    return {
      data: responses.map(({ json }) => json.data || json),
    };
  },

  getManyReference: async (resource, params) => {
    const { page, perPage } = params.pagination || { page: 1, perPage: 25 };
    
    const query = new URLSearchParams({
      page: page.toString(),
      size: perPage.toString(),
    });
    
    // 添加目标字段过滤
    query.append(params.target, params.id.toString());

    const url = `${API_BASE}/api/admin/${resource}?${query.toString()}`;
    const { json } = await httpClient(url);
    
    return {
      data: json.data || json.items || [],
      total: json.total || 0,
    };
  },

  create: async (resource, params) => {
    const url = `${API_BASE}/api/admin/${resource}`;
    const { json } = await httpClient(url, {
      method: 'POST',
      body: JSON.stringify(params.data),
    });
    
    return {
      data: json.data || json,
    };
  },

  update: async (resource, params) => {
    const url = `${API_BASE}/api/admin/${resource}/${params.id}`;
    const { json } = await httpClient(url, {
      method: 'PUT',
      body: JSON.stringify(params.data),
    });
    
    return {
      data: json.data || json,
    };
  },

  updateMany: async (resource, params) => {
    const promises = params.ids.map((id) =>
      httpClient(`${API_BASE}/api/admin/${resource}/${id}`, {
        method: 'PUT',
        body: JSON.stringify(params.data),
      })
    );
    const responses = await Promise.all(promises);
    
    return {
      data: responses.map(({ json }) => json.data || json),
    };
  },

  delete: async (resource, params) => {
    const url = `${API_BASE}/api/admin/${resource}/${params.id}`;
    const { json } = await httpClient(url, {
      method: 'DELETE',
    });
    
    return {
      data: json.data || { id: params.id },
    };
  },

  deleteMany: async (resource, params) => {
    const promises = params.ids.map((id) =>
      httpClient(`${API_BASE}/api/admin/${resource}/${id}`, {
        method: 'DELETE',
      })
    );
    await Promise.all(promises);
    
    return {
      data: params.ids,
    };
  },
};

