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

-- 花卉识别结果表
CREATE TABLE IF NOT EXISTS recognition_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- 社区帖子表
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    image_url TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 社区评论表
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 社区点赞表
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 社区关注表
CREATE TABLE IF NOT EXISTS follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users (id) ON DELETE CASCADE
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
('manage_roles', '管理角色和权限'),
('view_community', '查看社区内容'),
('create_posts', '创建帖子'),
('comment_posts', '评论帖子'),
('like_posts', '点赞帖子'),
('follow_users', '关注用户');

-- 为admin角色分配所有权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'admin'), 1),
((SELECT id FROM roles WHERE name = 'admin'), 2),
((SELECT id FROM roles WHERE name = 'admin'), 3),
((SELECT id FROM roles WHERE name = 'admin'), 4),
((SELECT id FROM roles WHERE name = 'admin'), 5),
((SELECT id FROM roles WHERE name = 'admin'), 6),
((SELECT id FROM roles WHERE name = 'admin'), 7),
((SELECT id FROM roles WHERE name = 'admin'), 8),
((SELECT id FROM roles WHERE name = 'admin'), 9);

-- 为user角色分配基本权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'user'), 1),
((SELECT id FROM roles WHERE name = 'user'), 2),
((SELECT id FROM roles WHERE name = 'user'), 5),
((SELECT id FROM roles WHERE name = 'user'), 6),
((SELECT id FROM roles WHERE name = 'user'), 7),
((SELECT id FROM roles WHERE name = 'user'), 8),
((SELECT id FROM roles WHERE name = 'user'), 9);

-- 显示初始化完成信息
SELECT '数据库初始化完成！' AS message;
SELECT '创建的表：users, roles, permissions, user_roles, role_permissions, recognition_results, posts, comments, likes, follows' AS info;
SELECT '初始角色：admin, user' AS info;
SELECT '初始权限：view_results, upload_images, manage_users, manage_roles, view_community, create_posts, comment_posts, like_posts, follow_users' AS info;
SELECT 'admin角色已分配所有权限' AS info;
SELECT 'user角色已分配基本权限' AS info;

-- ========================================
-- 超级管理员端相关表
-- ========================================

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id INTEGER,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at INTEGER NOT NULL
);

-- 访问流量统计表
CREATE TABLE IF NOT EXISTS traffic_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    hour INTEGER,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    ip_address TEXT,
    user_id INTEGER,
    response_status INTEGER,
    response_time INTEGER,
    created_at INTEGER NOT NULL
);

-- 访问统计汇总表（按日期汇总）
CREATE TABLE IF NOT EXISTS daily_traffic_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_requests INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- 服务器运行状态表
CREATE TABLE IF NOT EXISTS server_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT,
    status TEXT DEFAULT 'normal',
    created_at INTEGER NOT NULL
);

-- 管理员操作记录表
CREATE TABLE IF NOT EXISTS admin_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    admin_username TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    target_type TEXT,
    target_id INTEGER,
    description TEXT,
    ip_address TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 插入超级管理员角色
INSERT OR IGNORE INTO roles (name, description) VALUES
('super_admin', '超级管理员');

-- 插入超级管理员权限
INSERT OR IGNORE INTO permissions (name, description) VALUES
('manage_admins', '管理管理员'),
('view_system_logs', '查看系统日志'),
('view_traffic_stats', '查看流量统计'),
('monitor_server', '监控服务器状态'),
('system_settings', '系统设置');

-- 为super_admin角色分配所有权限（包括新增权限）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) 
SELECT (SELECT id FROM roles WHERE name = 'super_admin'), id FROM permissions;

-- 添加超级管理员专属权限
INSERT OR IGNORE INTO permissions (name, description) VALUES
('super_admin', '超级管理员所有权限');
