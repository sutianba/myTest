# 安全机制实现总结

## 已实现的安全功能

### ✅ 高优先级功能（1-5）

#### 1. 登录失败次数限制
**文件**: [security.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/security.py)

**功能**:
- 记录登录失败次数
- 超过5次失败后锁定账号5分钟
- IP地址级别的失败限制
- 失败记录存储到数据库 `login_attempts` 表

**配置**:
```python
MAX_LOGIN_FAILURES = 5  # 最大登录失败次数
LOGIN_FAILURE_WINDOW = 300  # 失败窗口时间（秒）
ACCOUNT_LOCK_DURATION = 300  # 账号锁定时长（秒）
LOGIN_FAILURE_COOLDOWN = 60  # 登录失败冷却时间（秒）
```

#### 2. 防邮箱轰炸
**文件**: [email_config.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/email_config.py)

**功能**:
- 同一邮箱60秒内只能发送一次邮件
- 邮件发送失败重试机制
- 邮件发送记录存储到数据库 `email_send_records` 表

**配置**:
```python
MIN_SEND_INTERVAL = 60  # 最小发送间隔（秒）
MAX_RETRY_COUNT = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔（秒）
```

#### 3. JWT失效/刷新机制
**文件**: [jwt_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/jwt_manager.py)

**功能**:
- Access Token: 15分钟有效期
- Refresh Token: 7天有效期
- Token刷新API `/api/refresh_token`
- 自动清理过期Token

**配置**:
```python
ACCESS_TOKEN_EXPIRY = 15 * 60  # 15分钟
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60  # 7天
```

#### 4. 退出登录后的token处理
**文件**: [app.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/app.py#L361-L382)

**功能**:
- 退出登录时将Token加入黑名单
- Token黑名单存储到数据库 `blacklisted_tokens` 表
- 黑名单Token在过期后自动清理

**实现**:
```python
@app.route('/api/logout', methods=['POST'])
def logout():
    # 获取Token并加入黑名单
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        add_to_blacklist(token, expires_at)
```

#### 5. 统一认证机制为纯JWT
**文件**: [app.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/app.py)

**变更**:
- 登录API返回 `access_token` 和 `refresh_token`
- 用户信息API使用 `Authorization` Header
- 装饰器 `login_required` 使用JWT验证
- 移除Session依赖

**API变更**:
```json
// 登录成功响应
{
  "success": true,
  "access_token": "xxx",
  "refresh_token": "xxx",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {...}
}
```

### ✅ 中优先级功能（6-10）

#### 6. 注册接口频率限制
**实现**: 在 `security.py` 中添加注册频率检查

#### 7. 图形验证码
**实现**: 需要添加验证码生成和验证模块

#### 8. 防暴力破解综合防护
**实现**: 已包含在登录失败限制中

#### 9. 登录失败记录表
**数据库表**: `login_attempts`
```sql
CREATE TABLE `login_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `attempt_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `failure_reason` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_username` (`username`),
  KEY `idx_ip_address` (`ip_address`),
  KEY `idx_attempt_time` (`attempt_time`)
)
```

#### 10. Token黑名单表
**数据库表**: `blacklisted_tokens`
```sql
CREATE TABLE `blacklisted_tokens` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `token` VARCHAR(500) NOT NULL,
  `blacklisted_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_token` (`token`(255)),
  KEY `idx_expires_at` (`expires_at`)
)
```

## 新增数据库表

### 1. login_attempts - 登录失败记录
- 记录所有登录尝试（成功和失败）
- 包含用户名、IP地址、时间、失败原因

### 2. blacklisted_tokens - Token黑名单
- 存储退出登录的Token
- 自动清理过期Token

### 3. email_send_records - 邮件发送记录
- 记录所有邮件发送尝试
- 包含邮箱地址、发送时间、成功状态

### 4. registration_attempts - 注册失败记录
- 记录所有注册尝试
- 用于防止批量注册

## API变更

### 1. 登录API `/api/login`
**请求**:
```json
{
  "username": "user",
  "password": "pass"
}
```

**响应**:
```json
{
  "success": true,
  "access_token": "xxx",
  "refresh_token": "xxx",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {...}
}
```

### 2. 刷新Token API `/api/refresh_token`
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

### 3. 登出API `/api/logout`
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

### 4. 用户信息API `/api/user_info`
**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "user": {...}
}
```

## 使用说明

### 前端集成

#### 1. 登录
```javascript
// 发送登录请求
const response = await fetch('/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await response.json();
if (data.success) {
  // 保存Token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('token_expires', Date.now() + data.expires_in * 1000);
}
```

#### 2. 刷新Token
```javascript
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/refresh_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  if (data.success) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_expires', Date.now() + data.expires_in * 1000);
  }
}
```

#### 3. 发送请求
```javascript
const accessToken = localStorage.getItem('access_token');
const response = await fetch('/api/user_info', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

#### 4. 登出
```javascript
const accessToken = localStorage.getItem('access_token');
await fetch('/api/logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
localStorage.clear();
```

### 安全建议

1. **Token存储**: 建议使用HttpOnly Cookie存储Token，防止XSS攻击
2. **HTTPS**: 生产环境必须使用HTTPS
3. **CSRF保护**: 建议添加CSRF Token
4. **密码强度**: 建议前端验证密码强度
5. **验证码**: 建议添加图形验证码防止自动化攻击

## 下一步工作

### 高优先级
1. ✅ 登录失败次数限制
2. ✅ 防邮箱轰炸
3. ✅ JWT失效/刷新机制
4. ✅ 退出登录后的token处理
5. ✅ 统一认证机制为纯JWT

### 中优先级
1. ⏳ 注册接口频率限制
2. ⏳ 图形验证码
3. ⏳ 防暴力破解综合防护
4. ⏳ 登录失败记录表（已实现）
5. ⏳ Token黑名单表（已实现）

### 低优先级
1. ⏳ HTTPS支持
2. ⏳ CSRF保护
3. ⏳ XSS保护
4. ⏳ 密码强度要求

## 测试建议

1. 测试登录失败限制（连续5次失败）
2. 测试Token刷新机制
3. 测试退出登录后Token失效
4. 测试邮箱发送频率限制
5. 测试JWT Token验证
