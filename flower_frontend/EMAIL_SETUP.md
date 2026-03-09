# 邮件系统配置指南

## 功能特性

已实现以下功能：

1. ✅ **SMTP真实配置** - 支持配置SMTP服务器
2. ✅ **发件邮箱与授权码配置** - 通过环境变量配置
3. ✅ **邮件发送失败重试** - 最多重试3次，每次重试间隔递增
4. ✅ **邮件发送异常日志** - 记录到email.log文件
5. ✅ **HTML邮件模板美化** - 精美的HTML邮件模板
6. ✅ **防止重复频繁发送** - 同一邮箱60秒内只能发送一次
7. ✅ **开发/生产环境邮件策略区分** - DEBUG_MODE控制

## 配置方法

### 1. 复制示例配置文件

```bash
cp .env.example .env
```

### 2. 编辑配置文件

编辑 `.env` 文件，填写真实的邮箱配置：

```bash
# 邮件服务器配置
EMAIL_HOST=smtp.163.com
EMAIL_PORT=25
EMAIL_FROM=your_email@163.com
EMAIL_PASSWORD=your_email_authorization_code

# 使用TLS加密（默认False）
EMAIL_USE_TLS=True

# 使用SSL加密（默认False，如果同时启用SSL和TLS，SSL优先）
EMAIL_USE_SSL=False

# 验证链接基础URL
VERIFY_URL_BASE=http://localhost:5000/api/verify-email

# 邮件发送配置
MAX_RETRY_COUNT=3
RETRY_DELAY=2
MIN_SEND_INTERVAL=60

# 开发/生产环境区分
DEBUG_MODE=True
```

### 3. 获取邮箱授权码

以163邮箱为例：

1. 登录163邮箱
2. 进入"设置" → "POP3/SMTP/IMAP"
3. 开启"客户端授权密码"
4. 设置授权码并保存
5. 将授权码填入 `EMAIL_PASSWORD`

### 4. 常用邮箱SMTP服务器配置

| 邮箱服务商 | SMTP服务器 | 端口 | TLS | SSL |
|-----------|-----------|------|-----|-----|
| 163邮箱 | smtp.163.com | 25 | 是 | 否 |
| QQ邮箱 | smtp.qq.com | 465 | 否 | 是 |
| Gmail | smtp.gmail.com | 587 | 是 | 否 |
| Outlook | smtp-mail.outlook.com | 587 | 是 | 否 |

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|-------|--------|------|
| EMAIL_HOST | smtp.163.com | SMTP服务器地址 |
| EMAIL_PORT | 25 | SMTP服务器端口 |
| EMAIL_FROM | your_email@163.com | 发件邮箱地址 |
| EMAIL_PASSWORD | your_email_password | 邮箱授权码（不是登录密码） |
| EMAIL_USE_TLS | False | 是否使用TLS加密 |
| EMAIL_USE_SSL | False | 是否使用SSL加密 |
| VERIFY_URL_BASE | http://localhost:5000/api/verify-email | 验证链接基础URL |
| MAX_RETRY_COUNT | 3 | 最大重试次数 |
| RETRY_DELAY | 2 | 重试间隔（秒） |
| MIN_SEND_INTERVAL | 60 | 最小发送间隔（秒） |
| DEBUG_MODE | False | 是否为开发环境 |

## 日志文件

邮件发送日志会记录在 `email.log` 文件中，包括：

- ✅ 邮件发送成功记录
- ❌ 邮件发送失败记录
- ⚠️ 邮件发送频率过高警告
- 🔐 SMTP认证失败记录

## 开发环境配置

在开发环境中，建议设置 `DEBUG_MODE=True`，此时系统会：

- 模拟发送邮件（不实际发送）
- 在日志中打印邮件内容
- 不限制发送频率
- 便于调试

## 生产环境配置

在生产环境中，需要：

1. 设置 `DEBUG_MODE=False`
2. 配置真实的邮箱账号和授权码
3. 确保SMTP服务器可访问
4. 监控 `email.log` 文件中的错误信息

## 故障排查

### 1. SMTP认证失败

**错误信息**: `SMTP认证失败: (535, b'Error: user in gray list')`

**解决方案**:
- 检查邮箱地址是否正确
- 检查授权码是否正确（不是登录密码）
- 确认已开启SMTP服务
- 检查IP是否被加入黑名单

### 2. 连接超时

**错误信息**: `Connection timed out`

**解决方案**:
- 检查网络连接
- 检查防火墙设置
- 确认SMTP服务器地址和端口正确

### 3. 邮件发送失败

**解决方案**:
- 查看 `email.log` 文件中的详细错误信息
- 检查收件人邮箱地址是否有效
- 确认邮件内容没有被识别为垃圾邮件

## 邮件模板预览

邮件包含HTML和纯文本两种格式：

### HTML格式
- 精美的渐变色头部
- 醒目的验证按钮
- 清晰的说明文字
- 注意事项提示框
- 专业的底部信息

### 纯文本格式
- 简洁明了的文本内容
- 包含所有必要信息
- 适合不支持HTML的邮件客户端
