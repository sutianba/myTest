-- 花卉识别系统数据库结构
-- 创建时间: 2026-01-26

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- 创建角色表
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- 创建权限表
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- 创建用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
);

-- 创建角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
);

-- 创建花卉识别结果表
CREATE TABLE IF NOT EXISTS recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- 插入初始角色数据
INSERT OR IGNORE INTO roles (name, description) VALUES
('admin', '系统管理员'),
('user', '普通用户');

-- 插入初始权限数据
INSERT OR IGNORE INTO permissions (name, description) VALUES
('view_results', '查看识别结果'),
('upload_images', '上传图片'),
('manage_users', '管理用户'),
('manage_roles', '管理角色和权限');

-- 为admin角色分配所有权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'admin'), 1),
((SELECT id FROM roles WHERE name = 'admin'), 2),
((SELECT id FROM roles WHERE name = 'admin'), 3),
((SELECT id FROM roles WHERE name = 'admin'), 4);

-- 为user角色分配基本权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'user'), 1),
((SELECT id FROM roles WHERE name = 'user'), 2);

-- 显示初始化完成信息
SELECT '数据库初始化完成！' AS message;
SELECT '创建的表：users, roles, permissions, user_roles, role_permissions, recognition_results' AS info;
SELECT '初始角色：admin, user' AS info;
SELECT '初始权限：view_results, upload_images, manage_users, manage_roles' AS info;
SELECT 'admin角色已分配所有权限' AS info;
SELECT 'user角色已分配基本权限' AS info;
