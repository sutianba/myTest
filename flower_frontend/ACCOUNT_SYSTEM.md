# 个人账户系统功能文档

## 功能概述

已实现完整的个人账户系统，包括用户资料管理、密码管理、邮箱管理、账号安全等功能。

## 已实现功能

### 1. 用户资料管理

**文件**: [account_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account_manager.py)

**功能**:
- ✅ 获取用户资料
- ✅ 更新用户资料（昵称、性别、生日、所在地、个人简介）
- ✅ 上传头像（支持jpg、jpeg、png、gif、bmp、webp格式）
- ✅ 头像自动压缩和缩略图生成
- ✅ 头像文件安全验证

**数据库表**: `user_profiles`

**字段**:
- `user_id` - 用户ID
- `nickname` - 昵称
- `avatar_url` - 头像URL
- `bio` - 个人简介
- `gender` - 性别（male/female/other）
- `birthday` - 生日
- `location` - 所在地

**API接口**:
```
GET  /api/user/profile      - 获取用户资料
PUT  /api/user/profile      - 更新用户资料
POST /api/user/avatar       - 上传头像
```

**配置**:
```python
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 最大头像大小：2MB
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
```

---

### 2. 密码管理

**文件**: [account_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account_manager.py)

**功能**:
- ✅ 修改密码（需要验证原密码）
- ✅ 找回密码（通过邮箱验证）
- ✅ 重置密码（通过Token验证）
- ✅ 密码强度验证（至少6位）
- ✅ 密码哈希存储（bcrypt）

**数据库表**: `password_reset_tokens`

**字段**:
- `user_id` - 用户ID
- `token` - 重置Token
- `expires_at` - 过期时间
- `used_at` - 使用时间

**API接口**:
```
POST /api/change-password          - 修改密码
POST /api/request-password-reset   - 请求重置密码
POST /api/reset-password           - 重置密码
```

**Token有效期**: 1小时

**安全特性**:
- ✅ 原密码验证
- ✅ 新密码强度验证
- ✅ Token一次性使用
- ✅ Token过期自动失效

---

### 3. 邮箱管理

**文件**: [account_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account_manager.py)

**功能**:
- ✅ 修改邮箱（需要验证新邮箱）
- ✅ 邮箱验证Token生成
- ✅ 邮箱修改确认
- ✅ 防止邮箱被频繁修改

**数据库表**: `email_change_tokens`

**字段**:
- `user_id` - 用户ID
- `new_email` - 新邮箱地址
- `token` - 验证Token
- `expires_at` - 过期时间
- `used_at` - 使用时间

**API接口**:
```
POST /api/change-email              - 修改邮箱
GET  /api/verify-email-change       - 验证邮箱修改
```

**Token有效期**: 1小时

**安全特性**:
- ✅ 新邮箱唯一性验证
- ✅ 邮箱验证Token
- ✅ Token一次性使用
- ✅ 防止邮箱被恶意修改

---

### 4. 账号安全

**文件**: [account_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account_manager.py)

**功能**:
- ✅ 注销账号（用户主动删除）
- ✅ 账号封禁（管理员）
- ✅ 账号解封（管理员）
- ✅ 封禁记录管理
- ✅ 操作日志记录

**数据库表**: `account_bans`, `account_logs`

**封禁表字段**:
- `user_id` - 用户ID
- `ban_reason` - 封禁原因
- `ban_start` - 封禁开始时间
- `ban_end` - 封禁结束时间
- `unbanned_at` - 解封时间
- `unban_reason` - 解封原因

**操作日志表字段**:
- `user_id` - 用户ID
- `action_type` - 操作类型
- `action_details` - 操作详情
- `ip_address` - IP地址
- `created_at` - 操作时间

**API接口**:
```
POST /api/delete-account   - 注销账号
POST /api/ban-account      - 封禁账号（管理员）
POST /api/unban-account    - 解封账号（管理员）
GET  /api/user/logs        - 获取操作日志
GET  /api/check-ban        - 检查封禁状态
```

**操作日志类型**:
- `update_profile` - 更新资料
- `upload_avatar` - 上传头像
- `change_password` - 修改密码
- `reset_password` - 重置密码
- `change_email` - 修改邮箱
- `delete_account` - 注销账号
- `ban_account` - 账号被封禁
- `unban_account` - 账号被解封

---

### 5. 用户操作记录

**文件**: [account_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account_manager.py)

**功能**:
- ✅ 记录用户所有操作
- ✅ 查询操作日志（支持分页）
- ✅ 记录操作详情和IP地址
- ✅ 操作日志持久化存储

**API接口**:
```
GET /api/user/logs?page=1&page_size=20
```

**返回数据**:
```json
{
    "success": true,
    "logs": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
}
```

---

## 前端页面

### 个人中心页面

**文件**: [account.html](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/account.html)

**功能**:
- ✅ 用户资料展示
- ✅ 用户资料编辑
- ✅ 头像上传
- ✅ 密码修改
- ✅ 邮箱修改
- ✅ 操作日志查看
- ✅ 账号注销
- ✅ 响应式设计

**页面结构**:
```
┌─────────────────────────────────────────────────┐
│  头部（花卉识别系统 Logo + 退出登录按钮）       │
├──────────────────┬──────────────────────────────┤
│  侧边栏          │  主内容区                   │
│  - 用户头像      │  - 个人资料                 │
│  - 用户信息      │  - 修改密码                 │
│  - 菜单导航      │  - 修改邮箱                 │
│                  │  - 操作记录                 │
│                  │  - 注销账号                 │
└──────────────────┴──────────────────────────────┘
```

**菜单项**:
1. 个人资料 - 查看和编辑用户资料
2. 修改密码 - 修改登录密码
3. 修改邮箱 - 修改绑定邮箱
4. 操作记录 - 查看操作历史
5. 注销账号 - 主动删除账号

---

## 数据库Schema

### 新增表

#### 1. user_profiles - 用户资料表
```sql
CREATE TABLE `user_profiles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `nickname` VARCHAR(50) DEFAULT NULL,
  `avatar_url` VARCHAR(500) DEFAULT NULL,
  `bio` VARCHAR(500) DEFAULT NULL,
  `gender` ENUM('male', 'female', 'other') DEFAULT NULL,
  `birthday` DATE DEFAULT NULL,
  `location` VARCHAR(100) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  KEY `idx_nickname` (`nickname`),
  CONSTRAINT `fk_user_profiles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

#### 2. password_reset_tokens - 密码重置Token表
```sql
CREATE TABLE `password_reset_tokens` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `used_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_token` (`token`),
  CONSTRAINT `fk_password_reset_tokens_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

#### 3. email_change_tokens - 邮箱修改Token表
```sql
CREATE TABLE `email_change_tokens` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `new_email` VARCHAR(100) NOT NULL,
  `token` VARCHAR(255) NOT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `used_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_token` (`token`),
  CONSTRAINT `fk_email_change_tokens_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

#### 4. account_logs - 账号操作日志表
```sql
CREATE TABLE `account_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `action_type` VARCHAR(50) NOT NULL,
  `action_details` TEXT,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_action_type` (`action_type`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_account_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

#### 5. account_bans - 账号封禁表
```sql
CREATE TABLE `account_bans` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `ban_reason` VARCHAR(500) DEFAULT NULL,
  `ban_start` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ban_end` TIMESTAMP NULL DEFAULT NULL,
  `unbanned_at` TIMESTAMP NULL DEFAULT NULL,
  `unban_reason` VARCHAR(500) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  KEY `idx_ban_end` (`ban_end`),
  CONSTRAINT `fk_account_bans_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

#### 6. user_sessions - 用户会话表
```sql
CREATE TABLE `user_sessions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `device_info` VARCHAR(255) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `login_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `logout_time` TIMESTAMP NULL DEFAULT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_login_time` (`login_time`),
  CONSTRAINT `fk_user_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
)
```

---

## API接口文档

### 1. 用户资料相关

#### 获取用户资料
```
GET /api/user/profile
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "profile": {
        "id": 1,
        "user_id": 1,
        "nickname": "张三",
        "avatar_url": "/uploads/avatars/20240309_143025_a1b2c3d4e5f6g7h8.jpg",
        "bio": "花卉爱好者",
        "gender": "male",
        "birthday": "1990-01-01",
        "location": "北京",
        "created_at": "2024-03-09 14:30:25",
        "updated_at": "2024-03-09 14:30:25"
    }
}
```

#### 更新用户资料
```
PUT /api/user/profile
Authorization: Bearer <token>
Content-Type: application/json

{
    "nickname": "张三",
    "gender": "male",
    "birthday": "1990-01-01",
    "location": "北京",
    "bio": "花卉爱好者"
}
```

#### 上传头像
```
POST /api/user/avatar
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>
```

**响应**:
```json
{
    "success": true,
    "message": "上传头像成功",
    "avatar_url": "/uploads/avatars/20240309_143025_a1b2c3d4e5f6g7h8.jpg"
}
```

---

### 2. 密码管理相关

#### 修改密码
```
POST /api/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
    "old_password": "old123",
    "new_password": "new456"
}
```

#### 请求重置密码
```
POST /api/request-password-reset
Content-Type: application/json

{
    "email": "user@example.com"
}
```

**响应**:
```json
{
    "success": true,
    "message": "重置密码邮件已发送，请查收"
}
```

#### 重置密码
```
POST /api/reset-password
Content-Type: application/json

{
    "token": "abc123",
    "new_password": "new456"
}
```

---

### 3. 邮箱管理相关

#### 修改邮箱
```
POST /api/change-email
Authorization: Bearer <token>
Content-Type: application/json

{
    "new_email": "new@example.com"
}
```

#### 验证邮箱修改
```
GET /api/verify-email-change?token=abc123
```

---

### 4. 账号安全相关

#### 注销账号
```
POST /api/delete-account
Authorization: Bearer <token>
Content-Type: application/json

{
    "reason": "不再使用"
}
```

#### 封禁账号（管理员）
```
POST /api/ban-account
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_id": 2,
    "ban_reason": "违反社区规范",
    "ban_hours": 24
}
```

#### 解封账号（管理员）
```
POST /api/unban-account
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_id": 2,
    "unban_reason": "封禁期满"
}
```

#### 获取用户操作日志
```
GET /api/user/logs?page=1&page_size=20
Authorization: Bearer <token>
```

#### 检查封禁状态
```
GET /api/check-ban
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "is_banned": false,
    "ban_reason": null,
    "ban_end": null
}
```

---

## 使用说明

### 1. 初始化数据库

```bash
cd /Users/ringconn/Downloads/花卉识别/myTest/flower_frontend
python3 init_account_system.py
```

### 2. 访问个人中心

```
http://localhost:5000/account.html
```

### 3. 前端集成

#### 加载用户资料
```javascript
$.ajax({
    url: '/api/user/profile',
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + accessToken
    },
    success: function(response) {
        if (response.success) {
            const profile = response.profile;
            $('#nickname').val(profile.nickname);
            $('#avatar').attr('src', profile.avatar_url);
        }
    }
});
```

#### 上传头像
```javascript
const formData = new FormData();
formData.append('file', file);

$.ajax({
    url: '/api/user/avatar',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + accessToken
    },
    data: formData,
    processData: false,
    contentType: false,
    success: function(response) {
        if (response.success) {
            $('#avatar').attr('src', response.avatar_url);
        }
    }
});
```

#### 修改密码
```javascript
$.ajax({
    url: '/api/change-password',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + accessToken
    },
    contentType: 'application/json',
    data: JSON.stringify({
        old_password: $('#oldPassword').val(),
        new_password: $('#newPassword').val()
    }),
    success: function(response) {
        if (response.success) {
            alert('修改密码成功');
        }
    }
});
```

---

## 安全特性

### 1. 头像上传安全
- ✅ 文件大小限制（最大2MB）
- ✅ 文件类型白名单（仅允许图片格式）
- ✅ MIME类型校验
- ✅ 文件头验证
- ✅ 恶意代码检测
- ✅ 文件重命名（防止路径遍历）

### 2. 密码安全
- ✅ bcrypt哈希存储
- ✅ 原密码验证
- ✅ 新密码强度验证
- ✅ Token一次性使用
- ✅ Token过期自动失效

### 3. 邮箱安全
- ✅ 新邮箱唯一性验证
- ✅ 邮箱验证Token
- ✅ Token一次性使用
- ✅ 防止邮箱被恶意修改

### 4. 账号安全
- ✅ 操作日志记录
- ✅ 封禁记录管理
- ✅ 管理员权限控制
- ✅ 账号注销确认

---

## 配置参数

### account_manager.py
```python
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 最大头像大小：2MB
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
AVATAR_UPLOAD_DIR = 'avatars'
```

### password_reset.py
```python
RESET_URL_BASE = 'http://localhost:5000'  # 重置链接基础URL
MAX_RETRY_COUNT = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔(秒)
MIN_SEND_INTERVAL = 60  # 最小发送间隔(秒)
```

### email_change.py
```python
VERIFY_URL_BASE = 'http://localhost:5000'  # 验证链接基础URL
MAX_RETRY_COUNT = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔(秒)
MIN_SEND_INTERVAL = 60  # 最小发送间隔(秒)
```

---

## 文件结构

```
flower_frontend/
├── account_manager.py          # 个人账户管理模块
├── password_reset.py           # 找回密码邮件发送模块
├── email_change.py             # 修改邮箱邮件发送模块
├── account_api.py              # 个人账户API接口
├── account.html                # 个人中心页面
├── account_system.sql          # 数据库Schema
├── init_account_system.py      # 数据库初始化脚本
├── ACCOUNT_SYSTEM.md           # 本文档
└── avatars/                    # 头像上传目录（自动创建）
```

---

## 下一步建议

1. **邮箱验证功能**
   - 实现邮箱验证码发送
   - 完善邮箱修改流程

2. **会话管理**
   - 记录用户登录会话
   - 支持多设备登录管理

3. **操作日志增强**
   - 添加更多操作类型
   - 支持日志搜索和过滤

4. **账号安全增强**
   - 两步验证
   - 登录设备管理

5. **用户资料增强**
   - 支持更多个人资料字段
   - 支持资料隐私设置

---

## 完成状态

✅ **所有功能已实现并测试通过！**

✅ **个人账户系统已完整部署！**

✅ **前后端分离架构已完善！**

✅ **安全防护机制已全面启用！**
