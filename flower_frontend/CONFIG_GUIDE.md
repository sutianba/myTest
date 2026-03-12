# 环境配置管理

## 概述

本项目使用了统一的配置管理系统，支持开发、测试和生产环境的配置分离。通过 `.env` 文件和配置类，实现了灵活的环境配置管理。

## 配置文件结构

```
flower_frontend/
├── config.py          # 配置管理模块
├── .env.example       # 环境变量示例文件
├── .env               # 实际环境变量文件（需创建）
├── database.py        # 数据库连接管理
└── app.py            # 主应用文件
```

## 环境模式

项目支持三种环境模式：

- **development** - 开发环境（默认）
- **test** - 测试环境
- **production** - 生产环境

## 配置加载顺序

1. 首先加载基础配置（`BaseConfig`）
2. 根据环境模式加载对应环境的配置（`DevelopmentConfig`/`TestConfig`/`ProductionConfig`）
3. 加载 `.env` 文件中的环境变量
4. 加载系统环境变量（优先级最高）

## 快速开始

### 1. 创建 .env 文件

复制 `.env.example` 文件为 `.env` 并填写实际值：

```bash
cp .env.example .env
```

### 2. 配置数据库

在 `.env` 文件中配置数据库连接信息：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=flower_recognition_dev
```

### 3. 配置JWT密钥

在 `.env` 文件中配置JWT密钥：

```env
# JWT配置
JWT_SECRET_KEY=your_secret_key_here
```

### 4. 配置邮件服务

在 `.env` 文件中配置邮件服务信息：

```env
# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password
```

### 5. 配置目录路径

在 `.env` 文件中配置目录路径：

```env
# 目录配置
UPLOAD_DIR=./uploads
LOG_DIR=./logs
MODEL_DIR=./models
```

### 6. 配置模型路径

在 `.env` 文件中配置模型路径：

```env
# 模型配置
PLANT_RECOGNITION_MODEL=plant_model.h5
PLANT_RECOGNITION_LABELS=plant_labels.json
```

## 配置项说明

### 通用配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| APP_NAME | 应用名称 | 花卉识别与社区系统 |
| DEBUG | 调试模式 | False |
| TESTING | 测试模式 | False |

### 数据库配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户名 | root |
| DB_PASSWORD | 数据库密码 | "" |
| DB_NAME | 数据库名称 | flower_recognition |

### JWT配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| JWT_SECRET_KEY | JWT密钥 | your-secret-key-here |
| JWT_ALGORITHM | JWT算法 | HS256 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间（分钟） | 30 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | 刷新令牌过期时间（天） | 7 |

### 邮件配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| SMTP_SERVER | SMTP服务器 | smtp.gmail.com |
| SMTP_PORT | SMTP端口 | 587 |
| SMTP_USER | SMTP用户名 | "" |
| SMTP_PASSWORD | SMTP密码 | "" |

### 目录配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| BASE_DIR | 项目根目录 | 自动计算 |
| UPLOAD_DIR | 上传文件目录 | ./uploads |
| LOG_DIR | 日志目录 | ./logs |
| MODEL_DIR | 模型目录 | ./models |

### 模型配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| PLANT_RECOGNITION_MODEL | 植物识别模型文件 | plant_model.h5 |
| PLANT_RECOGNITION_LABELS | 植物识别标签文件 | plant_labels.json |

### 安全配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| MAX_UPLOAD_SIZE | 最大上传文件大小（字节） | 10485760 (10MB) |
| ALLOWED_EXTENSIONS | 允许的文件扩展名 | {"png", "jpg", "jpeg", "gif", "webp"} |

### CORS配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| CORS_ORIGINS | CORS允许的源 | ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"] |

### 限流配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| RATE_LIMIT_MAX_REQUESTS | 最大请求数 | 100 |
| RATE_LIMIT_WINDOW_SECONDS | 限流窗口（秒） | 60 |

### 日志配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| LOG_LEVEL | 日志级别 | INFO |
| LOG_FORMAT | 日志格式 | %(asctime)s - %(name)s - %(levelname)s - %(message)s |

## 代码中使用配置

### 导入配置

```python
from config import config
```

### 使用配置

```python
# 数据库配置
db_url = config.get_db_url()

# JWT配置
secret_key = config.JWT_SECRET_KEY

# 目录配置
upload_dir = config.UPLOAD_DIR

# 模型配置
model_path = os.path.join(config.MODEL_DIR, config.PLANT_RECOGNITION_MODEL)
```

## 环境切换

### 通过环境变量切换

```bash
# 开发环境（默认）
export FLASK_ENV=development

# 测试环境
export FLASK_ENV=test

# 生产环境
export FLASK_ENV=production
```

### 通过代码切换

```python
from config import config_manager

# 加载测试环境配置
config = config_manager.load_config("test")

# 加载生产环境配置
config = config_manager.load_config("production")
```

## 数据库连接

使用 `database.py` 中的函数进行数据库操作：

```python
from database import get_db_connection, execute_query, fetch_one, fetch_all, execute_update, execute_insert

# 获取连接
connection = get_db_connection()

# 执行查询
cursor = execute_query("SELECT * FROM users")

# 获取单条记录
user = fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))

# 获取所有记录
users = fetch_all("SELECT * FROM users")

# 执行更新
affected_rows = execute_update("UPDATE users SET status = %s WHERE id = %s", (status, user_id))

# 执行插入
new_id = execute_insert("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
```

## 目录结构

配置系统会自动创建以下目录：

- `uploads/` - 用于存储上传的文件
- `logs/` - 用于存储日志文件
- `models/` - 用于存储模型文件

## 安全建议

1. **不要将 .env 文件提交到版本控制系统**
2. **使用强密码和密钥**
3. **在生产环境中禁用 DEBUG 模式**
4. **定期更换 JWT 密钥**
5. **使用环境变量管理敏感信息**

## 故障排除

### 数据库连接失败

- 检查 `.env` 文件中的数据库配置
- 确保 MySQL 服务正在运行
- 确保数据库用户有正确的权限

### 邮件发送失败

- 检查 `.env` 文件中的邮件配置
- 确保 SMTP 服务器地址和端口正确
- 确保 SMTP 用户名和密码正确
- 检查邮箱服务是否允许第三方应用访问

### 模型加载失败

- 检查 `.env` 文件中的模型配置
- 确保模型文件存在于指定路径
- 确保模型文件格式正确

### 上传失败

- 检查 `.env` 文件中的上传目录配置
- 确保上传目录存在且有写权限
- 确保文件大小不超过 MAX_UPLOAD_SIZE
- 确保文件类型在 ALLOWED_EXTENSIONS 中

## 示例配置

### 开发环境

```env
# 环境模式
FLASK_ENV=development

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=flower_recognition_dev

# JWT配置
JWT_SECRET_KEY=dev_secret_key_123456

# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=dev@example.com
SMTP_PASSWORD=dev_password

# 目录配置
UPLOAD_DIR=./uploads
LOG_DIR=./logs
MODEL_DIR=./models

# 日志配置
LOG_LEVEL=DEBUG
```

### 生产环境

```env
# 环境模式
FLASK_ENV=production

# 数据库配置
DB_HOST=db.example.com
DB_PORT=3306
DB_USER=flower_user
DB_PASSWORD=strong_password
DB_NAME=flower_recognition

# JWT配置
JWT_SECRET_KEY=prod_secret_key_789012

# 邮件配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=admin@example.com
SMTP_PASSWORD=prod_password

# 目录配置
UPLOAD_DIR=/var/www/flower/uploads
LOG_DIR=/var/www/flower/logs
MODEL_DIR=/var/www/flower/models

# 日志配置
LOG_LEVEL=ERROR
```
