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
    const { field, order } = params.sort || { field: 'id', order: 'ASC' };
    
    // 构建查询参数
    const query = new URLSearchParams({
      page: page.toString(),
      perPage: perPage.toString(),
    });

    // 添加排序
    if (field && order) {
      const sortField = order === 'ASC' ? field : `-${field}`;
      query.append('sort', sortField);
    }

    // 添加过滤
    if (params.filter) {
      Object.entries(params.filter).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (typeof value === 'object' && value !== null) {
            // 处理对象类型的过滤（如时间范围）
            query.append(`filter[${key}]`, JSON.stringify(value));
          } else {
            query.append(`filter[${key}]`, value.toString());
          }
        }
      });
    }

    const url = `${API_BASE}/api/admin/${resource}?${query.toString()}`;
    const { json } = await httpClient(url);
    
    return {
      data: json.data || json.items || [],
      total: json.total || json.data?.length || 0,
    };
  },

  getOne: async (resource, params) => {
    const url = `${API_BASE}/api/admin/${resource}/${params.id}`;
    const { json } = await httpClient(url);
    
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

