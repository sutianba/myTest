# API 规范文档

## 概述

本项目使用统一的API规范，包括统一的响应格式、错误码、参数校验、异常处理、分页规范和鉴权机制。

## 目录

- [统一响应格式](#统一响应格式)
- [错误码定义](#错误码定义)
- [参数校验](#参数校验)
- [异常处理](#异常处理)
- [分页规范](#分页规范)
- [鉴权机制](#鉴权机制)
- [API文档](#api文档)

## 统一响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "user_id": 1,
    "username": "testuser"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 错误响应

```json
{
  "code": 1001,
  "message": "参数错误",
  "data": {
    "field": "username",
    "reason": "用户名不能为空"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "帖子标题"
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 10,
      "total_items": 100,
      "total_pages": 10,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 错误码定义

### 通用错误 (1000-1999)

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 200 | 成功 | 200 |
| 1000 | 未知错误 | 500 |
| 1001 | 参数错误 | 400 |
| 1002 | 请求方法不允许 | 405 |

### 认证授权错误 (2000-2999)

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 2001 | 未授权 | 401 |
| 2002 | 令牌已过期 | 401 |
| 2003 | 令牌无效 | 401 |
| 2004 | 权限不足 | 403 |
| 2005 | 账号已锁定 | 403 |
| 2006 | 账号未验证 | 403 |

### 业务逻辑错误 (3000-3999)

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 3001 | 用户不存在 | 404 |
| 3002 | 用户已存在 | 409 |
| 3003 | 密码错误 | 401 |
| 3004 | 邮箱已存在 | 409 |
| 3005 | 邮箱不存在 | 404 |
| 3006 | 验证码错误 | 400 |
| 3007 | 验证码已过期 | 400 |

### 资源错误 (4000-4999)

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 4001 | 资源不存在 | 404 |
| 4002 | 资源已存在 | 409 |
| 4003 | 资源已锁定 | 423 |

### 服务器错误 (5000-5999)

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 5000 | 服务器内部错误 | 500 |
| 5001 | 数据库错误 | 500 |
| 5002 | 外部服务错误 | 502 |

## 参数校验

### 使用装饰器进行参数校验

```python
from api_response import validate_params

@app.route('/api/example', methods=['POST'])
@validate_params(
    required_params=['username', 'password'],
    optional_params=[('email', 'email'), ('age', 'int')]
)
def example():
    data = request.get_json()
    # 业务逻辑
    return success_response(data, '操作成功')
```

### 参数类型

- `email`: 邮箱格式
- `int`: 整数
- `str`: 字符串
- `float`: 浮点数
- `bool`: 布尔值

## 异常处理

### 自动异常处理

所有未捕获的异常都会被自动处理并返回统一的错误响应。

```python
from api_response import handle_exception

@app.route('/api/example', methods=['GET'])
def example():
    try:
        # 业务逻辑
        pass
    except Exception as e:
        return handle_exception(e)
```

### 手动返回错误

```python
from api_response import error_response, ErrorCode

@app.route('/api/example', methods=['GET'])
def example():
    if not user_exists:
        return error_response(ErrorCode.USER_NOT_FOUND, '用户不存在')
    
    return success_response(user_data, '获取成功')
```

## 分页规范

### 获取分页参数

```python
from api_response import get_pagination_params

@app.route('/api/posts', methods=['GET'])
def get_posts():
    pagination = get_pagination_params()
    # pagination = {
    #     'page': 1,
    #     'per_page': 10,
    #     'offset': 0,
    #     'limit': 10
    # }
    
    # 查询数据库
    items = query_posts(pagination['offset'], pagination['limit'])
    total = count_posts()
    
    return success_response(
        format_pagination_response(items, total, pagination),
        '获取成功'
    )
```

### 分页参数

- `page`: 页码（默认：1）
- `per_page`: 每页数量（默认：10，最大：100）

## 鉴权机制

### 需要认证的接口

```python
from auth_middleware import auth_required

@app.route('/api/profile', methods=['GET'])
@auth_required
def get_profile():
    user_id = g.user_id
    username = g.username
    # 业务逻辑
    return success_response(user_data, '获取成功')
```

### 需要特定角色的接口

```python
from auth_middleware import role_required, admin_required

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    # 只有管理员可以访问
    return success_response(users, '获取成功')

@app.route('/api/moderate', methods=['POST'])
@role_required('admin', 'moderator')
def moderate_content():
    # 管理员和版主可以访问
    return success_response(result, '审核成功')
```

### 可选认证的接口

```python
from auth_middleware import optional_auth

@app.route('/api/posts', methods=['GET'])
@optional_auth
def get_posts():
    if hasattr(g, 'user_id'):
        # 已登录用户
        user_id = g.user_id
    else:
        # 未登录用户
        user_id = None
    
    return success_response(posts, '获取成功')
```

### 获取当前用户信息

```python
from auth_middleware import get_current_user, is_authenticated, is_admin

@app.route('/api/example', methods=['GET'])
@auth_required
def example():
    user = get_current_user()
    # user = {
    #     'user_id': 1,
    #     'username': 'testuser',
    #     'role': 'user'
    # }
    
    if is_authenticated():
        # 用户已登录
        pass
    
    if is_admin():
        # 用户是管理员
        pass
    
    return success_response(data, '操作成功')
```

### Token刷新

```python
from auth_middleware import refresh_access_token

@app.route('/api/refresh-token', methods=['POST'])
def refresh_token():
    refresh_token = request.json.get('refresh_token')
    success, result = refresh_access_token(refresh_token)
    
    if success:
        return success_response(result, '刷新成功')
    else:
        return error_response(ErrorCode.TOKEN_INVALID, result.get('message'))
```

## API文档

### Swagger UI

访问 `http://localhost:5000/api/docs` 查看交互式API文档。

### 生成Swagger JSON

```python
from swagger_config import save_swagger_json

# 生成并保存Swagger JSON文档
swagger_file = save_swagger_json()
```

### 在app.py中注册Swagger UI

```python
from flask import Flask
from swagger_config import swaggerui_blueprint

app = Flask(__name__)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

## 使用示例

### 注册API

```python
@app.route('/api/register', methods=['POST'])
@log_api_call
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # 参数校验
        if not username or not password:
            return error_response(ErrorCode.PARAMETER_ERROR, '用户名和密码不能为空')
        
        if len(password) < 6:
            return error_response(ErrorCode.PARAMETER_ERROR, '密码长度不能少于6位')

        # 业务逻辑
        # ...

        # 返回成功响应
        return success_response({
            'user_id': user_id,
            'username': username
        }, '注册成功')
        
    except Exception as e:
        return handle_exception(e)
```

### 登录API

```python
@app.route('/api/login', methods=['POST'])
@log_api_call
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # 验证用户
        user = authenticate_user(username, password)
        if not user:
            return error_response(ErrorCode.PASSWORD_ERROR, '用户名或密码错误')

        # 生成Token
        access_token = generate_access_token(user['id'], user['username'], user['role'])
        refresh_token = generate_refresh_token(user['id'], user['username'])

        # 返回成功响应
        return success_response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 1800
        }, '登录成功')
        
    except Exception as e:
        return handle_exception(e)
```

### 获取帖子列表（分页）

```python
@app.route('/api/posts', methods=['GET'])
@log_api_call
def get_posts():
    try:
        pagination = get_pagination_params()
        
        # 查询数据库
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT * FROM posts LIMIT %s OFFSET %s",
            (pagination['limit'], pagination['offset'])
        )
        items = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as total FROM posts")
        total = cursor.fetchone()['total']
        
        cursor.close()
        connection.close()
        
        # 返回分页响应
        return success_response(
            format_pagination_response(items, total, pagination),
            '获取成功'
        )
        
    except Exception as e:
        return handle_exception(e)
```

### 创建帖子（需要认证）

```python
@app.route('/api/posts', methods=['POST'])
@log_api_call
@auth_required
def create_post():
    try:
        data = request.get_json()
        content = data.get('content')
        image_url = data.get('image_url')

        if not content:
            return error_response(ErrorCode.PARAMETER_ERROR, '帖子内容不能为空')

        # 创建帖子
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO posts (user_id, content, image_url) VALUES (%s, %s, %s)",
            (g.user_id, content, image_url)
        )
        post_id = cursor.lastrowid
        connection.commit()
        
        cursor.close()
        connection.close()

        return success_response({
            'post_id': post_id,
            'user_id': g.user_id,
            'content': content,
            'image_url': image_url
        }, '创建成功')
        
    except Exception as e:
        return handle_exception(e)
```

## 最佳实践

1. **始终使用统一的响应格式**
   - 成功：`success_response(data, message)`
   - 失败：`error_response(error_code, message)`

2. **使用装饰器进行参数校验**
   - 减少重复代码
   - 提高代码可读性

3. **使用鉴权装饰器保护接口**
   - `@auth_required`: 需要登录
   - `@admin_required`: 需要管理员权限
   - `@role_required('admin', 'moderator')`: 需要特定角色

4. **统一异常处理**
   - 使用`handle_exception(e)`处理未捕获的异常
   - 提供友好的错误消息

5. **遵循分页规范**
   - 使用`get_pagination_params()`获取分页参数
   - 使用`format_pagination_response()`格式化分页响应

6. **保持API文档更新**
   - 定期更新Swagger文档
   - 提供清晰的接口说明

## 常见问题

### Q: 如何添加新的错误码？

A: 在`api_response.py`的`ErrorCode`类中添加新的错误码，并在`get_error_message`函数中添加对应的错误消息。

### Q: 如何自定义参数校验规则？

A: 可以扩展`validate_params`装饰器，添加更多的参数类型和校验规则。

### Q: 如何添加新的鉴权规则？

A: 可以在`auth_middleware.py`中添加新的装饰器或修改现有的鉴权逻辑。

### Q: 如何生成API文档？

A: 运行`save_swagger_json()`函数生成Swagger JSON文档，然后访问`/api/docs`查看交互式文档。
