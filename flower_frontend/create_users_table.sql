-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,  -- SHA-256哈希值为64个字符
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入初始测试用户
-- 密码: password123
INSERT INTO users (username, password_hash) VALUES ('admin', 'e10adc3949ba59abbe56e057f20f883e');

-- 密码: test123
INSERT INTO users (username, password_hash) VALUES ('test', 'cc03e747a6afbbcbf8be7668acfebee5');
