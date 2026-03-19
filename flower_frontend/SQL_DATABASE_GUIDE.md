# 花卉识别系统 - SQL数据库管理指南

## 概述

本系统现在采用基于SQL文件的数据库管理方式，所有数据库结构定义和初始数据都存储在SQL文件中，便于版本控制和跨环境部署。

## 文件结构

```
flower_frontend/
├── database.sql              # 数据库结构定义和初始数据（主文件）
├── database_backup.sql       # 数据库备份文件
├── current_database.sql      # 当前数据库状态导出文件
├── db.py                     # 数据库操作模块（主要使用）
└── db_manager.py             # SQL数据库管理器类
```

## 核心特性

### 1. SQL文件管理
- **database.sql**: 包含完整的数据库表结构定义和初始数据
- **自动初始化**: 当数据库文件不存在时，自动从SQL文件创建
- **版本控制**: SQL文件可以纳入Git版本控制，便于追踪数据库结构变更

### 2. 数据库操作
- **导出功能**: 可以将当前数据库状态导出为SQL文件
- **导入功能**: 可以从SQL文件重建数据库
- **备份功能**: 支持数据库备份和恢复

## 使用方法

### 1. 初始化数据库

数据库会在首次使用时自动从 `database.sql` 文件初始化：

```python
from flower_frontend.db import db_manager

# 自动初始化（如果数据库文件不存在）
db = SQLDatabaseManager()
```

### 2. 手动从SQL文件初始化

```bash
# 使用sqlite3命令行工具
sqlite3 flower_recognition.db < flower_frontend/database.sql
```

### 3. 导出当前数据库为SQL文件

```python
from flower_frontend.db import db_manager

# 导出当前数据库
db_manager.export_to_sql('flower_frontend/backup.sql')
```

### 4. 执行自定义SQL文件

```python
from flower_frontend.db import db_manager

# 执行SQL文件
success = db_manager.execute_sql_file('flower_frontend/custom.sql')
```

## 数据库操作API

### 用户管理

```python
from flower_frontend.db import create_user, get_user_by_username, get_user_by_id, verify_password

# 创建用户
user_id = create_user('username', 'email@example.com', 'password123')

# 获取用户信息
user = get_user_by_username('username')
user = get_user_by_id(user_id)

# 验证密码
is_valid = verify_password(user['password_hash'], 'password123')
```

### 权限管理

```python
from flower_frontend.db import get_user_roles, get_user_permissions, check_user_permission

# 获取用户角色
roles = get_user_roles(user_id)

# 获取用户权限
permissions = get_user_permissions(user_id)

# 检查用户权限
has_permission = check_user_permission(user_id, 'upload_images')
```

### 识别结果管理

```python
from flower_frontend.db import save_recognition_result, get_user_recognition_results

# 保存识别结果
result_id = save_recognition_result(user_id, '/path/to/image.jpg', '玫瑰', 0.95)

# 获取用户的识别结果
results = get_user_recognition_results(user_id)
```

## 数据库表结构

### users（用户表）
- id: 用户ID（主键）
- username: 用户名（唯一）
- email: 邮箱（唯一）
- password_hash: 密码哈希
- created_at: 创建时间
- updated_at: 更新时间

### roles（角色表）
- id: 角色ID（主键）
- name: 角色名称（唯一）
- description: 角色描述

### permissions（权限表）
- id: 权限ID（主键）
- name: 权限名称（唯一）
- description: 权限描述

### user_roles（用户角色关联表）
- user_id: 用户ID（外键）
- role_id: 角色ID（外键）

### role_permissions（角色权限关联表）
- role_id: 角色ID（外键）
- permission_id: 权限ID（外键）

### recognition_results（识别结果表）
- id: 结果ID（主键）
- user_id: 用户ID（外键）
- image_path: 图片路径
- result: 识别结果
- confidence: 置信度
- created_at: 创建时间

## 初始数据

### 角色
- **admin**: 系统管理员（拥有所有权限）
- **user**: 普通用户（拥有基本权限）

### 权限
- **view_results**: 查看识别结果
- **upload_images**: 上传图片
- **manage_users**: 管理用户
- **manage_roles**: 管理角色和权限

### 权限分配
- **admin角色**: 拥有所有权限
- **user角色**: 拥有 view_results 和 upload_images 权限

## 维护和备份

### 定期备份

```bash
# 导出当前数据库状态
sqlite3 flower_recognition.db .dump > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
# 从备份恢复
sqlite3 flower_recognition.db < backup_20260126.sql
```

### 更新数据库结构

1. 修改 `database.sql` 文件中的表结构定义
2. 备份当前数据库：`db_manager.export_to_sql('backup.sql')`
3. 删除现有数据库文件
4. 重新初始化：系统会自动从新的SQL文件创建数据库

## 故障排除

### 数据库文件损坏
```bash
# 删除损坏的数据库文件
rm flower_recognition.db

# 重新初始化（系统会自动从SQL文件创建）
python3 flower_frontend/db.py
```

### SQL文件语法错误
```bash
# 验证SQL文件语法
sqlite3 :memory: < flower_frontend/database.sql
```

### 连接问题
```python
# 测试数据库连接
from flower_frontend.db import test_connection
if test_connection():
    print("数据库连接正常")
else:
    print("数据库连接失败")
```

## 优势

1. **版本控制友好**: SQL文件可以纳入Git版本控制
2. **跨环境一致性**: 确保不同环境的数据库结构一致
3. **易于维护**: 清晰的SQL语句便于理解和修改
4. **备份简单**: 导出的SQL文件就是完整的备份
5. **快速部署**: 可以快速在新环境中初始化数据库

## 注意事项

1. **SQL文件优先**: 修改数据库结构时，优先修改SQL文件
2. **数据安全**: 定期备份数据库，特别是生产环境
3. **权限管理**: 合理分配用户权限，避免安全风险
4. **性能优化**: 根据实际使用情况添加适当的索引

## 技术支持

如有问题，请查看：
- SQLite官方文档: https://www.sqlite.org/docs.html
- Python sqlite3模块文档: https://docs.python.org/3/library/sqlite3.html
