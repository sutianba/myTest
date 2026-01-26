import sqlite3
import time

# 数据库路径
DB_PATH = 'flower_recognition.db'

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 创建用户表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
)
''')

# 创建角色表
cursor.execute('''
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
)
''')

# 创建权限表
cursor.execute('''
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
)
''')

# 创建用户角色关联表
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
)
''')

# 创建角色权限关联表
cursor.execute('''
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
)
''')

# 创建花卉识别结果表
cursor.execute('''
CREATE TABLE IF NOT EXISTS recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
)
''')

# 插入初始角色数据
initial_roles = [
    ('admin', '系统管理员'),
    ('user', '普通用户')
]
cursor.executemany('INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)', initial_roles)

# 插入初始权限数据
initial_permissions = [
    ('view_results', '查看识别结果'),
    ('upload_images', '上传图片'),
    ('manage_users', '管理用户'),
    ('manage_roles', '管理角色和权限')
]
cursor.executemany('INSERT OR IGNORE INTO permissions (name, description) VALUES (?, ?)', initial_permissions)

# 为admin角色分配所有权限
cursor.execute('SELECT id FROM roles WHERE name = ?', ('admin',))
admin_role_id = cursor.fetchone()[0]

cursor.execute('SELECT id FROM permissions')
permission_ids = [row[0] for row in cursor.fetchall()]

admin_permissions = [(admin_role_id, perm_id) for perm_id in permission_ids]
cursor.executemany('INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)', admin_permissions)

# 为user角色分配基本权限
cursor.execute('SELECT id FROM roles WHERE name = ?', ('user',))
user_role_id = cursor.fetchone()[0]

basic_permissions = [(user_role_id, 1), (user_role_id, 2)]  # view_results和upload_images
cursor.executemany('INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)', basic_permissions)

# 提交并关闭连接
conn.commit()
conn.close()

print('数据库初始化完成！')
print('创建的表：users, roles, permissions, user_roles, role_permissions, recognition_results')
print('初始角色：admin, user')
print('初始权限：view_results, upload_images, manage_users, manage_roles')
print('admin角色已分配所有权限')
print('user角色已分配基本权限')