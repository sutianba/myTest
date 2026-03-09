# 安全功能实现文档

## 已实现的安全功能

### 1. 登录失败次数限制

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

### 2. 防邮箱轰炸

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

### 3. 图形验证码

**文件**: [captcha.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/captcha.py)

**功能**:
- 生成随机4位验证码（去除容易混淆的字符）
- 随机颜色、旋转、干扰线、噪点
- Base64编码返回图片
- 5分钟有效期
- 一次性使用（防止重放攻击）

**API**:
```javascript
// 获取验证码
GET /api/captcha

// 验证码响应
{
  "success": true,
  "captcha_id": "abc123",
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
}

// 验证验证码
POST /api/verify-captcha
{
  "captcha_id": "abc123",
  "captcha_text": "ABCD"
}
```

### 4. JWT失效/刷新机制

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

### 5. 退出登录后的token处理

**文件**: [app.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/app.py)

**功能**:
- 退出登录时将Token加入黑名单
- Token黑名单存储到数据库 `blacklisted_tokens` 表
- 黑名单Token在过期后自动清理

### 6. 统一认证机制为纯JWT

**文件**: [app.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/app.py)

**变更**:
- 登录API返回 `access_token` 和 `refresh_token`
- 用户信息API使用 `Authorization` Header
- 装饰器 `login_required` 使用JWT验证
- 移除Session依赖

### 7. 注册接口频率限制

**文件**: [security.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/security.py)

**功能**:
- 同一邮箱60秒内只能注册一次
- 防止批量注册

### 8. 防暴力破解综合防护

**实现**: 已包含在登录失败限制中

## 数据库表

### 1. login_attempts - 登录失败记录
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

### 2. blacklisted_tokens - Token黑名单
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

### 3. email_send_records - 邮件发送记录
```sql
CREATE TABLE `email_send_records` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(100) DEFAULT NULL,
  `send_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `error_message` VARCHAR(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_email` (`email`),
  KEY `idx_send_time` (`send_time`)
)
```

### 4. registration_attempts - 注册失败记录
```sql
CREATE TABLE `registration_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) DEFAULT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `attempt_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `failure_reason` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_email` (`email`),
  KEY `idx_ip_address` (`ip_address`),
  KEY `idx_attempt_time` (`attempt_time`)
)
```

## API变更

### 1. 登录API `/api/login`
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

### 3. 获取验证码 API `/api/captcha`
**请求**: GET `/api/captcha`

**响应**:
```json
{
  "success": true,
  "captcha_id": "abc123",
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
}
```

### 4. 验证验证码 API `/api/verify-captcha`
**请求**:
```json
{
  "captcha_id": "abc123",
  "captcha_text": "ABCD"
}
```

**响应**:
```json
{
  "success": true,
  "message": "验证成功"
}
```

### 5. 登出API `/api/logout`
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

## 使用说明

### 前端集成

#### 1. 登录
```javascript
// 加载验证码
function loadCaptcha(captchaImgId, captchaInputId, captchaIdInputId) {
    $.ajax({
        url: '/api/captcha',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                $(captchaImgId).attr('src', response.image);
                $(captchaIdInputId).val(response.captcha_id);
            }
        }
    });
}

// 登录
$('#loginForm').submit(function(e) {
    e.preventDefault();
    const username = $('#loginUsername').val();
    const password = $('#loginPassword').val();
    const captchaId = $('#loginCaptchaId').val();
    const captchaText = $('#loginCaptchaInput').val();

    $.ajax({
        url: '/api/login',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ 
            username, 
            password, 
            captcha_id: captchaId, 
            captcha_text: captchaText 
        }),
        success: function(response) {
            if (response.success) {
                // 保存JWT Token
                localStorage.setItem('access_token', response.access_token);
                localStorage.setItem('refresh_token', response.refresh_token);
                localStorage.setItem('token_expires', Date.now() + response.expires_in * 1000);
            }
        }
    });
});

// 初始化验证码
$(document).ready(function() {
    loadCaptcha('#loginCaptchaImage', '#loginCaptchaInput', '#loginCaptchaId');
});
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

## 安全建议

1. **Token存储**: 建议使用HttpOnly Cookie存储Token，防止XSS攻击
2. **HTTPS**: 生产环境必须使用HTTPS
3. **CSRF保护**: 建议添加CSRF Token
4. **密码强度**: 建议前端验证密码强度
5. **验证码**: 已添加图形验证码防止自动化攻击

## 测试建议

1. 测试登录失败限制（连续5次失败）
2. 测试Token刷新机制
3. 测试退出登录后Token失效
4. 测试邮箱发送频率限制
5. 测试验证码生成和验证
6. 测试图形验证码刷新功能
