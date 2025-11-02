import { DataProvider, fetchUtils } from 'react-admin';

const API_BASE = import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:9019';

const httpClient = (url: string, options: any = {}) => {
  const token = localStorage.getItem('token');
  
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' });
  }
  
  if (token) {
    options.headers.set('Authorization', `Bearer ${token}`);
  }
  
  return fetchUtils.fetchJson(url, options);
};

export const dataProvider: DataProvider = {
    getList: async (resource, params) => {
        const { page, perPage } = params.pagination || { page: 1, perPage: 25 };
        const { field, order } = params.sort || { field: 'id', order: 'DESC' };
        
        // 构建查询参数
        const query = new URLSearchParams({
            page: page.toString(),
            size: perPage.toString(),
        });

        // 添加排序（后端使用不同的排序格式）
        // 后端目前不支持排序参数，可以在后续添加

        // 添加过滤
        if (params.filter) {
            // 搜索关键词
            if (params.filter.search) {
                query.append('search', params.filter.search);
            }
            // 角色过滤
            if (params.filter.role) {
                query.append('role', params.filter.role);
            }
            // 状态过滤
            if (params.filter.is_active !== undefined) {
                query.append('is_active', params.filter.is_active.toString());
            }
            // 验证状态过滤
            if (params.filter.is_verified !== undefined) {
                query.append('is_verified', params.filter.is_verified.toString());
            }
            // 处理嵌套的filter对象
            if (params.filter.filter) {
                Object.entries(params.filter.filter).forEach(([key, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        query.append(key, value.toString());
                    }
                });
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
    const { field, order } = params.sort || { field: 'id', order: 'ASC' };
    
    const query = new URLSearchParams({
      page: page.toString(),
      perPage: perPage.toString(),
      [`filter[${params.target}]`]: params.id,
    });

    if (field && order) {
      const sortField = order === 'ASC' ? field : `-${field}`;
      query.append('sort', sortField);
    }

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
      data: params.ids.map((id) => ({ id })),
    };
  },
};

