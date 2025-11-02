# 管理员后台Token认证机制验证

## 当前实现状态

### ✅ 已实现的功能

#### 1. 登录流程
- **端点**：`POST /api/auth/login`
- **认证方式**：JWT (JSON Web Token)
- **Token类型**：
  - `access_token`：访问令牌（8小时 或 1小时）
  - `refresh_token`：刷新令牌（10年 或 1天）

#### 2. Token存储
- 位置：`localStorage`
- 字段：
  ```javascript
  localStorage.setItem('token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  ```

#### 3. Token使用
- 在API请求中携带：`Authorization: Bearer <token>`
- 格式：HTTP Bearer Authentication

#### 4. Token验证
- 使用 `JWTManager.verify_token()` 验证token
- 从token payload中提取用户ID (`sub` 字段)
- 从数据库加载用户信息

#### 5. 权限控制
- 通过 `get_current_user` 依赖注入验证用户身份
- 管理员角色检查：`role in ['admin', 'super_admin']`

### 🔍 需要验证的部分

#### 1. DataProvider中的Token传递
```typescript
// admin-dashboard/src/dataProvider.ts
const httpClient = (url: string, options: any = {}) => {
  const token = localStorage.getItem('token');
  const headers = new Headers({
    'Content-Type': 'application/json',
    ...options.headers,
  });
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  return fetch(url, { ...options, headers });
};
```

#### 2. 用户信息端点
- **端点**：`GET /api/auth/me`
- **认证**：需要Bearer token
- **返回**：用户详细信息

#### 3. 权限检查
```typescript
// authProvider.ts
getPermissions: async () => {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const user = await response.json();
  
  // 只允许管理员访问
  if (user.role === 'admin' || user.role === 'super_admin') {
    return Promise.resolve(user.role);
  }
  return Promise.reject({ message: '权限不足' });
}
```

## 与主应用的一致性

### ✅ 相同点
1. **认证端点**：都使用 `/api/auth/login`
2. **Token格式**：都使用JWT
3. **Token传递**：都使用 `Authorization: Bearer` 头
4. **Token验证**：都使用 `JWTManager.verify_token()`
5. **用户加载**：都从数据库加载用户信息

### ⚠️ 需要注意的差异
1. **用户角色要求**：
   - 主应用：所有注册用户
   - 管理后台：仅管理员 (`admin`/`super_admin`)

2. **Token有效期**：
   - 勾选"记住我"：access_token 8小时，refresh_token 10年
   - 未勾选：access_token 1小时，refresh_token 1天

## 测试清单

### 1. 登录测试
- [ ] 使用管理员账号登录
- [ ] 验证token是否保存到localStorage
- [ ] 验证token格式是否正确

### 2. API请求测试
- [ ] 验证请求头是否包含 `Authorization: Bearer <token>`
- [ ] 验证token是否被正确验证
- [ ] 验证403/401错误时是否跳转到登录页

### 3. 权限测试
- [ ] 普通用户无法访问管理后台
- [ ] 管理员可以访问所有管理功能
- [ ] Super Admin拥有最高权限

### 4. Token刷新测试
- [ ] Token过期后是否正确处理
- [ ] Refresh token是否可以刷新access token

## 管理员账号
- **用户名**：`tc1102Admin`
- **密码**：`xjystimao1115`
- **角色**：`super_admin`

