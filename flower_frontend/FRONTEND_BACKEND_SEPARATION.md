# 前后端分离架构文档

## 架构概述

本项目已完全采用**前后端分离 + JWT统一认证**的架构模式。

### 核心原则

1. **JWT作为唯一主认证机制** - 所有API认证统一使用JWT
2. **Session仅保留给极少数服务端页面场景** - 不再用于API认证
3. **前端完全控制Token生命周期** - Token存储在localStorage
4. **后端无状态** - 所有认证信息通过JWT传递

## 技术栈

### 后端
- **Flask** - Web框架
- **JWT** - 无状态认证
- **MySQL** - 数据库
- **YOLOv5** - 花卉识别模型

### 前端
- **jQuery** - DOM操作
- **localStorage** - Token存储
- **AJAX** - API调用

## 认证流程

### 1. 登录流程

```
用户输入用户名密码
    ↓
前端发送POST /api/login
    ↓
后端验证用户名密码
    ↓
后端生成JWT Token (Access Token + Refresh Token)
    ↓
后端返回Token给前端
    ↓
前端保存Token到localStorage
```

**请求示例**:
```javascript
$.ajax({
    url: '/api/login',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ 
        username: 'user',
        password: 'pass',
        captcha_id: 'abc123',
        captcha_text: 'ABCD'
    }),
    success: function(response) {
        if (response.success) {
            // 保存JWT Token
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('refresh_token', response.refresh_token);
            localStorage.setItem('token_expires', Date.now() + response.expires_in * 1000);
            
            currentUser = response.user;
            currentToken = response.access_token;
        }
    }
});
```

**响应示例**:
```json
{
    "success": true,
    "message": "登录成功",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "role": "user"
    }
}
```

### 2. API认证流程

```
前端发送请求
    ↓
前端在Header中添加Authorization: Bearer <token>
    ↓
后端验证Token
    ↓
后端返回数据或401错误
```

**请求示例**:
```javascript
const accessToken = localStorage.getItem('access_token');

$.ajax({
    url: '/api/results',
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + accessToken
    },
    success: function(response) {
        console.log(response);
    },
    error: function(xhr) {
        if (xhr.status === 401) {
            // Token无效或过期，清除Token
            localStorage.removeItem('access_token');
            currentUser = null;
            currentToken = null;
            updateNavbar();
        }
    }
});
```

### 3. Token刷新流程

```
Token即将过期
    ↓
前端发送POST /api/refresh_token
    ↓
后端验证Refresh Token
    ↓
后端生成新的Access Token
    ↓
后端返回新的Access Token
    ↓
前端更新Token
```

**请求示例**:
```javascript
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    const response = await fetch('/api/refresh_token', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    const data = await response.json();
    
    if (data.success) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('token_expires', Date.now() + data.expires_in * 1000);
    } else {
        // Refresh Token也失效了，需要重新登录
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        currentUser = null;
        currentToken = null;
        updateNavbar();
    }
}
```

### 4. 登出流程

```
用户点击登出
    ↓
前端发送POST /api/logout
    ↓
后端将Token加入黑名单
    ↓
后端返回成功
    ↓
前端清除Token
```

**请求示例**:
```javascript
function logout() {
    const accessToken = localStorage.getItem('access_token');
    
    $.ajax({
        url: '/api/logout',
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + accessToken
        },
        success: function(response) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            currentUser = null;
            currentToken = null;
            updateNavbar();
            showNotification('已退出登录', 'success');
            showPage('homePage');
        }
    });
}
```

## API接口规范

### 认证相关API

#### 1. 登录
```
POST /api/login
```

**请求**:
```json
{
    "username": "user",
    "password": "pass",
    "captcha_id": "abc123",
    "captcha_text": "ABCD"
}
```

**响应**:
```json
{
    "success": true,
    "message": "登录成功",
    "access_token": "xxx",
    "refresh_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {...}
}
```

#### 2. 刷新Token
```
POST /api/refresh_token
```

**请求**:
```json
{
    "refresh_token": "xxx"
}
```

**响应**:
```json
{
    "success": true,
    "access_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 900
}
```

#### 3. 登出
```
POST /api/logout
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "message": "已成功登出"
}
```

#### 4. 获取用户信息
```
GET /api/user_info
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "role": "user",
        "created_at": "2024-01-01T00:00:00"
    }
}
```

#### 5. 检查认证状态
```
GET /api/check_auth
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "authenticated": true,
    "user": {
        "username": "user"
    }
}
```

### 业务相关API

#### 1. 上传图片识别
```
POST /api/upload
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "result": "rose (0.95), tulip (0.05)",
    "predictions": [...]
}
```

#### 2. 获取识别结果
```
GET /api/results
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "results": [...]
}
```

#### 3. 删除识别结果
```
DELETE /api/results/:result_id
```

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "message": "删除成功"
}
```

#### 4. 图片识别（JSON方式）
```
POST /api/recognize
```

**请求头**:
```
Authorization: Bearer <token>
```

**请求**:
```json
{
    "image_path": "/path/to/image.jpg"
}
```

**响应**:
```json
{
    "success": true,
    "result": "rose (0.95)",
    "predictions": [...]
}
```

## JWT Token结构

### Access Token
```json
{
    "user_id": 1,
    "username": "user",
    "role": "user",
    "type": "access",
    "exp": 1234567890,
    "iat": 1234567290,
    "jti": "abc123"
}
```

**有效期**: 15分钟

### Refresh Token
```json
{
    "user_id": 1,
    "username": "user",
    "role": "user",
    "type": "refresh",
    "exp": 1234567890,
    "iat": 1234567290,
    "jti": "def456"
}
```

**有效期**: 7天

## 安全机制

### 1. Token黑名单
- 退出登录时将Token加入黑名单
- 黑名单存储在数据库
- 过期后自动清理

### 2. 登录失败限制
- 连续5次失败后锁定账号5分钟
- IP地址级别的限制
- 记录到数据库

### 3. 图形验证码
- 防止自动化攻击
- 5分钟有效期
- 一次性使用

### 4. 防邮箱轰炸
- 同一邮箱60秒内只能发送一次邮件
- 记录到数据库

## 前端存储策略

### localStorage
- `access_token` - Access Token
- `refresh_token` - Refresh Token
- `token_expires` - Token过期时间戳
- `current_user` - 当前用户信息（可选）

### Cookie
- 不使用Cookie存储Token
- Cookie仅用于必要的会话场景（如需要）

## 迁移指南

### 从Session迁移到JWT

#### 1. 移除Session依赖
```python
# ❌ 旧代码
session['user_id'] = user['id']
session['username'] = user['username']

# ✅ 新代码
# 使用JWT Token传递用户信息
```

#### 2. 更新API认证
```javascript
// ❌ 旧代码
$.ajax({
    url: '/api/data',
    method: 'GET',
    success: function(response) {
        // 使用Session认证
    }
});

// ✅ 新代码
const accessToken = localStorage.getItem('access_token');

$.ajax({
    url: '/api/data',
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + accessToken
    },
    success: function(response) {
        // 使用JWT认证
    },
    error: function(xhr) {
        if (xhr.status === 401) {
            // Token无效或过期
            localStorage.removeItem('access_token');
        }
    }
});
```

#### 3. 更新登出逻辑
```javascript
// ❌ 旧代码
function logout() {
    // 后端清除Session
    $.post('/api/logout', function() {
        // 前端清除状态
        currentUser = null;
    });
}

// ✅ 新代码
function logout() {
    const accessToken = localStorage.getItem('access_token');
    
    $.ajax({
        url: '/api/logout',
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + accessToken
        },
        success: function() {
            // 清除前端存储的Token
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            currentUser = null;
        }
    });
}
```

## 最佳实践

### 1. Token管理
- ✅ 使用Access Token + Refresh Token机制
- ✅ Access Token短期有效（15分钟）
- ✅ Refresh Token长期有效（7天）
- ✅ Token过期后自动刷新
- ✅ 登出时清除Token

### 2. 错误处理
- ✅ 401错误时清除Token
- ✅ 403错误时提示权限不足
- ✅ 500错误时提示服务器错误

### 3. 安全性
- ✅ 使用HTTPS
- ✅ Token存储在localStorage（非HttpOnly）
- ✅ 定期刷新Token
- ✅ 登出时清除Token
- ✅ 使用Token黑名单

### 4. 性能优化
- ✅ 使用Refresh Token避免频繁登录
- ✅ Token过期前自动刷新
- ✅ 使用CDN加速静态资源

## 监控和日志

### 登录日志
- 记录所有登录尝试
- 包含用户名、IP地址、时间、成功/失败

### Token日志
- 记录Token生成
- 记录Token刷新
- 记录Token失效

### 错误日志
- 记录所有认证错误
- 记录所有API错误

## 常见问题

### 1. Token过期怎么办？
- Access Token过期后，使用Refresh Token自动刷新
- Refresh Token也过期后，需要重新登录

### 2. 如何处理401错误？
- 清除本地Token
- 跳转到登录页面
- 提示用户重新登录

### 3. 如何防止Token被盗用？
- 使用HTTPS
- 设置合理的Token过期时间
- 使用Token黑名单
- 监控异常登录行为

### 4. 如何实现自动登录？
- 前端保存Refresh Token
- 应用启动时检查Token是否有效
- 无效时使用Refresh Token刷新
- 刷新失败时要求重新登录

## 相关文档

- [SECURITY_FEATURES.md](./SECURITY_FEATURES.md) - 安全功能文档
- [JWT文档](https://jwt.io/) - JWT官方文档
- [Flask文档](https://flask.palletsprojects.com/) - Flask官方文档

## 更新日志

### 2024-03-09
- ✅ 完成前后端分离架构改造
- ✅ 统一使用JWT作为主认证机制
- ✅ 移除Session依赖
- ✅ 更新所有API接口
- ✅ 更新前端API调用
- ✅ 创建认证中间件
