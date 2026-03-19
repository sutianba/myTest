-- MySQL数据库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS flower_recognition DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE flower_recognition;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at INT NOT NULL,
    updated_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 识别结果表
CREATE TABLE IF NOT EXISTS recognition_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_path TEXT NOT NULL,
    result VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at INT NOT NULL,
    deleted_at INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 帖子表
CREATE TABLE IF NOT EXISTS posts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    image_url TEXT,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    created_at INT NOT NULL,
    updated_at INT NOT NULL,
    deleted_at INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at INT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 点赞表
CREATE TABLE IF NOT EXISTS likes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at INT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_like (post_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 关注表
CREATE TABLE IF NOT EXISTS follows (
    id INT PRIMARY KEY AUTO_INCREMENT,
    follower_id INT NOT NULL,
    following_id INT NOT NULL,
    created_at INT NOT NULL,
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_follow (follower_id, following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    log_level VARCHAR(20) NOT NULL,
    module VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    user_id INT,
    username VARCHAR(50),
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 流量统计表
CREATE TABLE IF NOT EXISTS traffic_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date VARCHAR(10) NOT NULL,
    hour INT NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    ip_address VARCHAR(50),
    user_id INT,
    response_status INT NOT NULL,
    response_time FLOAT NOT NULL,
    created_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 每日流量汇总表
CREATE TABLE IF NOT EXISTS daily_traffic_summary (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date VARCHAR(10) UNIQUE NOT NULL,
    total_requests INT DEFAULT 0,
    unique_visitors INT DEFAULT 0,
    avg_response_time FLOAT DEFAULT 0,
    error_count INT DEFAULT 0,
    created_at INT NOT NULL,
    updated_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 服务器状态表
CREATE TABLE IF NOT EXISTS server_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    metric_name VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    unit VARCHAR(20),
    status VARCHAR(20) NOT NULL,
    created_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 管理员操作记录表
CREATE TABLE IF NOT EXISTS admin_operations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    admin_username VARCHAR(50) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id INT,
    description TEXT,
    ip_address VARCHAR(50),
    created_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 反馈表
CREATE TABLE IF NOT EXISTS user_feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    response TEXT,
    created_at INT NOT NULL,
    updated_at INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 公告表
CREATE TABLE IF NOT EXISTS announcements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    announcement_type VARCHAR(50) DEFAULT 'general',
    is_active TINYINT(1) DEFAULT 1,
    admin_id INT NOT NULL,
    admin_username VARCHAR(50),
    created_at INT NOT NULL,
    updated_at INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 相册表
CREATE TABLE IF NOT EXISTS albums (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    cover_image TEXT,
    description TEXT,
    image_count INT DEFAULT 0,
    created_at INT NOT NULL,
    updated_at INT NOT NULL,
    deleted_at INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 相册图片表
CREATE TABLE IF NOT EXISTS album_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    album_id INT NOT NULL,
    user_id INT NOT NULL,
    image_path TEXT NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    image_description TEXT,
    created_at INT NOT NULL,
    deleted_at INT,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 回收站表
CREATE TABLE IF NOT EXISTS recycle_bin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    original_id INT NOT NULL,
    item_data TEXT,
    deleted_at INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 初始化数据
-- 插入角色
INSERT IGNORE INTO roles (name, description) VALUES
('super_admin', '超级管理员'),
('admin', '系统管理员'),
('user', '普通用户');

-- 插入权限
INSERT IGNORE INTO permissions (name, description) VALUES
('view_results', '查看识别结果'),
('upload_images', '上传图片'),
('manage_users', '管理用户'),
('manage_roles', '管理角色和权限'),
('view_community', '查看社区内容'),
('create_posts', '创建帖子'),
('comment_posts', '评论帖子'),
('like_posts', '点赞帖子'),
('follow_users', '关注用户'),
('manage_posts', '管理帖子'),
('manage_feedback', '管理用户反馈'),
('view_system_logs', '查看系统日志'),
('view_traffic_stats', '查看流量统计'),
('view_server_status', '查看服务器状态'),
('manage_announcements', '管理系统公告'),
('manage_albums', '管理相册');

-- 角色权限关联
-- 超级管理员权限
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'view_results')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'upload_images')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_users')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_roles')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'view_community')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'create_posts')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'comment_posts')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'like_posts')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'follow_users')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_posts')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_feedback')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'view_system_logs')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'view_traffic_stats')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'view_server_status')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_announcements')),
((SELECT id FROM roles WHERE name = 'super_admin'), (SELECT id FROM permissions WHERE name = 'manage_albums'));

-- 管理员权限
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'view_results')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'upload_images')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'view_community')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'create_posts')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'comment_posts')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'like_posts')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'follow_users')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'manage_posts')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'manage_feedback')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'view_system_logs')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'view_traffic_stats')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'view_server_status')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'manage_announcements')),
((SELECT id FROM roles WHERE name = 'admin'), (SELECT id FROM permissions WHERE name = 'manage_albums'));

-- 普通用户权限
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'view_results')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'upload_images')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'view_community')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'create_posts')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'comment_posts')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'like_posts')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'follow_users')),
((SELECT id FROM roles WHERE name = 'user'), (SELECT id FROM permissions WHERE name = 'manage_albums'));

-- 插入测试用户
INSERT IGNORE INTO users (username, email, password_hash, created_at, updated_at) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:1000000$A3wkEuJm94FlOPHg$7b215c12d3c301d920da0a8f6629eba4d69e0804a51a0f6f929f8b5fbbef5a60', 1769563038, 1769563038),
('testuser', 'test@example.com', 'pbkdf2:sha256:1000000$A3wkEuJm94FlOPHg$7b215c12d3c301d920da0a8f6629eba4d69e0804a51a0f6f929f8b5fbbef5a60', 1769563038, 1769563038);

-- 给用户分配角色
INSERT IGNORE INTO user_roles (user_id, role_id) VALUES
((SELECT id FROM users WHERE username = 'admin'), (SELECT id FROM roles WHERE name = 'super_admin')),
((SELECT id FROM users WHERE username = 'testuser'), (SELECT id FROM roles WHERE name = 'user'));