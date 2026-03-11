-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_verified TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建识别结果表（增强版）
CREATE TABLE IF NOT EXISTS recognition_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    image_path VARCHAR(255),
    result VARCHAR(255),
    confidence FLOAT,
    corrected TINYINT DEFAULT 0,
    original_result VARCHAR(255),
    corrected_at TIMESTAMP NULL,
    renamed TINYINT DEFAULT 0,
    renamed_at TIMESTAMP NULL,
    image_hash VARCHAR(255),
    -- 园艺工具新增字段
    is_favorite TINYINT DEFAULT 0,
    is_archived TINYINT DEFAULT 0,
    is_deleted TINYINT DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    notes TEXT,
    location VARCHAR(255),
    weather VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20) DEFAULT '#4CAF50',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_user_tag (user_id, name)
);

-- 创建识别结果与标签关联表
CREATE TABLE IF NOT EXISTS result_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT,
    tag_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES recognition_results(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE KEY unique_result_tag (result_id, tag_id)
);

-- 创建收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    result_id INT,
    plant_id INT,
    favorite_type ENUM('result', 'plant') DEFAULT 'result',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (result_id) REFERENCES recognition_results(id) ON DELETE CASCADE,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, result_id, plant_id, favorite_type)
);

-- 创建回收站表（软删除记录）
CREATE TABLE IF NOT EXISTS recycle_bin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    result_id INT,
    original_data JSON,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (result_id) REFERENCES recognition_results(id) ON DELETE CASCADE
);

-- 创建同步记录表
CREATE TABLE IF NOT EXISTS sync_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    device_id VARCHAR(255),
    sync_type ENUM('upload', 'download', 'bidirectional') DEFAULT 'bidirectional',
    last_sync_at TIMESTAMP NULL,
    sync_status ENUM('pending', 'syncing', 'completed', 'failed') DEFAULT 'pending',
    sync_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    auto_sync TINYINT DEFAULT 1,
    sync_interval INT DEFAULT 3600,
    default_view ENUM('grid', 'list', 'timeline') DEFAULT 'grid',
    theme ENUM('light', 'dark', 'auto') DEFAULT 'auto',
    language VARCHAR(10) DEFAULT 'zh-CN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建反馈表
CREATE TABLE IF NOT EXISTS recognition_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT,
    user_id INT,
    feedback_type VARCHAR(50) DEFAULT 'wrong',
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES recognition_results(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建植物信息表
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    family VARCHAR(100),
    description TEXT,
    image_url VARCHAR(255),
    blooming_season VARCHAR(255),
    growth_stage VARCHAR(255),
    sunlight_requirements VARCHAR(255),
    water_needs VARCHAR(255),
    origin VARCHAR(255),
    toxicity VARCHAR(255),
    care_tips TEXT,
    planting_instructions TEXT,
    propagation_methods TEXT,
    pests_and_diseases TEXT,
    similar_plants TEXT,
    benefits TEXT,
    other_names VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for permissions
-- ----------------------------
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_permission_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_roles
-- ----------------------------
DROP TABLE IF EXISTS `user_roles`;
CREATE TABLE `user_roles` (
  `user_id` INT NOT NULL,
  `role_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  KEY `idx_role_id` (`role_id`),
  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for role_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_permissions`;
CREATE TABLE `role_permissions` (
  `role_id` INT NOT NULL,
  `permission_id` INT NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  KEY `idx_permission_id` (`permission_id`),
  CONSTRAINT `fk_role_permissions_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_role_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for recognition_results
-- ----------------------------
DROP TABLE IF EXISTS `recognition_results`;
CREATE TABLE `recognition_results` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT DEFAULT NULL,
  `image_path` VARCHAR(255) DEFAULT NULL,
  `result` VARCHAR(255) DEFAULT NULL,
  `confidence` DECIMAL(5,2) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_recognition_results_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for posts
-- ----------------------------
DROP TABLE IF EXISTS `posts`;
CREATE TABLE `posts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `image_url` VARCHAR(500) DEFAULT NULL,
  `likes_count` INT NOT NULL DEFAULT 0,
  `comments_count` INT NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_posts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for comments
-- ----------------------------
DROP TABLE IF EXISTS `comments`;
CREATE TABLE `comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `post_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_comments_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_comments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for likes
-- ----------------------------
DROP TABLE IF EXISTS `likes`;
CREATE TABLE `likes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `post_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_user` (`post_id`, `user_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_likes_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_likes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for follows
-- ----------------------------
DROP TABLE IF EXISTS `follows`;
CREATE TABLE `follows` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `follower_id` INT NOT NULL,
  `following_id` INT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_follower_following` (`follower_id`, `following_id`),
  KEY `idx_following_id` (`following_id`),
  CONSTRAINT `fk_follows_follower` FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_follows_following` FOREIGN KEY (`following_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for post_recycle_bin
-- ----------------------------
DROP TABLE IF EXISTS `post_recycle_bin`;
CREATE TABLE `post_recycle_bin` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `post_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `image_url` VARCHAR(500) DEFAULT NULL,
  `deleted_at` TIMESTAMP NOT NULL,
  `restored_at` TIMESTAMP NULL DEFAULT NULL,
  `is_permanently_deleted` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_post_recycle_bin_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for comment_recycle_bin
-- ----------------------------
DROP TABLE IF EXISTS `comment_recycle_bin`;
CREATE TABLE `comment_recycle_bin` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `comment_id` INT NOT NULL,
  `post_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `deleted_at` TIMESTAMP NOT NULL,
  `restored_at` TIMESTAMP NULL DEFAULT NULL,
  `is_permanently_deleted` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_comment_recycle_bin_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for operation_logs
-- ----------------------------
DROP TABLE IF EXISTS `operation_logs`;
CREATE TABLE `operation_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `action_type` VARCHAR(50) NOT NULL,
  `target_type` VARCHAR(50) DEFAULT NULL,
  `target_id` INT DEFAULT NULL,
  `details` TEXT,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_operation_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_profiles
-- ----------------------------
DROP TABLE IF EXISTS `user_profiles`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for password_reset_tokens
-- ----------------------------
DROP TABLE IF EXISTS `password_reset_tokens`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for email_change_tokens
-- ----------------------------
DROP TABLE IF EXISTS `email_change_tokens`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for account_logs
-- ----------------------------
DROP TABLE IF EXISTS `account_logs`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for account_bans
-- ----------------------------
DROP TABLE IF EXISTS `account_bans`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_sessions
-- ----------------------------
DROP TABLE IF EXISTS `user_sessions`;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Insert initial data
-- ----------------------------
SET FOREIGN_KEY_CHECKS = 0;

-- Insert users (password: password123, status: active)
INSERT INTO `users` (`id`, `username`, `email`, `password`, `is_verified`, `created_at`) VALUES
(1, 'testuser', 'test@example.com', 'pbkdf2:sha256:1000000$A3wkEuJm94FlOPHg$7b215c12d3c301d920da0a8f6629eba4d69e0804a51a0f6f929f8b5fbbef5a60', 1, FROM_UNIXTIME(1769563038));

-- Insert roles
INSERT INTO `roles` (`id`, `name`, `description`) VALUES
(1, 'admin', '系统管理员'),
(2, 'user', '普通用户');

-- Insert permissions
INSERT INTO `permissions` (`id`, `name`, `description`) VALUES
(1, 'view_results', '查看识别结果'),
(2, 'upload_images', '上传图片'),
(3, 'manage_users', '管理用户'),
(4, 'manage_roles', '管理角色和权限'),
(5, 'view_community', '查看社区内容'),
(6, 'create_posts', '创建帖子'),
(7, 'comment_posts', '评论帖子'),
(8, 'like_posts', '点赞帖子'),
(9, 'follow_users', '关注用户');

-- Insert user_roles
INSERT INTO `user_roles` (`user_id`, `role_id`) VALUES
(1, 2);

-- Insert role_permissions
INSERT INTO `role_permissions` (`role_id`, `permission_id`) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),
(2, 1), (2, 2), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9);

-- Insert posts
INSERT INTO `posts` (`id`, `user_id`, `content`, `image_url`, `likes_count`, `comments_count`, `created_at`, `updated_at`) VALUES
(1, 1, '测试帖子内容，这是我的第一篇社区帖子！', 'https://example.com/flower.jpg', 1, 1, FROM_UNIXTIME(1769563050), FROM_UNIXTIME(1769563050));

-- Insert comments
INSERT INTO `comments` (`id`, `post_id`, `user_id`, `content`, `created_at`) VALUES
(1, 1, 1, '这是对测试帖子的评论！', FROM_UNIXTIME(1769563065));

-- Insert likes
INSERT INTO `likes` (`id`, `post_id`, `user_id`, `created_at`) VALUES
(1, 1, 1, FROM_UNIXTIME(1769563083));

-- ----------------------------
-- Table structure for login_attempts
-- ----------------------------
DROP TABLE IF EXISTS `login_attempts`;
CREATE TABLE `login_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `attempt_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `failure_reason` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_username` (`username`),
  KEY `idx_ip_address` (`ip_address`),
  KEY `idx_attempt_time` (`attempt_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for blacklisted_tokens
-- ----------------------------
DROP TABLE IF EXISTS `blacklisted_tokens`;
CREATE TABLE `blacklisted_tokens` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `token` VARCHAR(500) NOT NULL,
  `blacklisted_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_token` (`token`(255)),
  KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for email_send_records
-- ----------------------------
DROP TABLE IF EXISTS `email_send_records`;
CREATE TABLE `email_send_records` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(100) NOT NULL,
  `send_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `error_message` TEXT,
  PRIMARY KEY (`id`),
  KEY `idx_email` (`email`),
  KEY `idx_send_time` (`send_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for registration_attempts
-- ----------------------------
DROP TABLE IF EXISTS `registration_attempts`;
CREATE TABLE `registration_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) DEFAULT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `attempt_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `success` BOOLEAN NOT NULL DEFAULT FALSE,
  `failure_reason` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_ip_address` (`ip_address`),
  KEY `idx_attempt_time` (`attempt_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入基础植物数据
INSERT IGNORE INTO plants (name, scientific_name, category, family, description, image_url, blooming_season, growth_stage, sunlight_requirements, water_needs, origin, toxicity, care_tips, planting_instructions, propagation_methods, pests_and_diseases, similar_plants, benefits, other_names) VALUES
('玫瑰', 'Rosa', '花卉', '蔷薇科', '玫瑰是一种象征爱情与美丽的花卉，拥有丰富的花色和浓郁的香气。在世界各地广泛栽培，是最受欢迎的观赏花卉之一。', 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Beautiful%20rose%20flower%2C%20garden&sign=25015e95c4b359ce0e75c1b8c4e55e4b', '夏季至秋季', '春季发芽，夏季开花，秋季结果，冬季休眠', '充足阳光（每天至少6小时）', '中等（保持土壤湿润但不过湿）', '欧洲、亚洲、中东', '轻微（刺可能引起皮肤刺激）', '保持土壤湿润但不过湿，定期施肥。避免叶片沾水，以防真菌病害。', '选择排水良好的肥沃土壤，种植在阳光充足的位置。种植前添加有机肥料。', '可以通过扦插、嫁接或分株繁殖。扦插最好在春季或夏季进行。', '常见病虫害有蚜虫、红蜘蛛和白粉病。定期检查并及时防治。', '月季：花型相似但花期更长；蔷薇：攀缘性更强，花小而多', '花朵可用于制作香料、精油和花茶，具有舒缓情绪、促进血液循环的功效。', '玫瑰花,月季'),
('郁金香', 'Tulipa', '花卉', '百合科', '郁金香是春季开花的球根花卉，花色艳丽，花形端庄，是荷兰的国花。已有数百年的栽培历史，品种繁多。', 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Colorful%20tulip%20flowers%2C%20garden&sign=0696ea8d7f0693e3fd18827500f7700a', '春季', '秋季种植，冬季休眠，春季开花，夏季枯萎', '充足阳光（每天至少5小时）', '中等（生长期保持湿润，休眠期减少浇水）', '土耳其、中亚', '轻微（可能引起胃部不适）', '种植在排水良好的土壤中，花后继续养护至叶片枯萎。秋季种植球茎最佳。', '秋季将球茎种植在排水良好的土壤中，深度约为球茎直径的2-3倍。', '主要通过分球繁殖，也可播种繁殖但需要较长时间才能开花。', '可能受到蚜虫、根腐病和灰霉病的影响。保持通风良好可减少病害发生。', '风信子：花穗状，香气浓郁；水仙：花形不同，多为黄色', '是重要的春季观赏花卉，常用于花坛、切花和盆栽观赏。', '洋荷花,草麝香'),
('薰衣草', 'Lavandula', '花卉', '唇形科', '薰衣草是一种芳香植物，以其紫色的花朵和独特的香气而闻名。主要用于香料、药用和观赏。', 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Lavender%20field%2C%20purple%20flowers&sign=18ec56878cd00dafb53d98d7474ef2d4', '夏季', '春季生长，夏季开花，秋季结籽，冬季休眠', '充足阳光（每天至少6-8小时）', '低（耐旱，避免过度浇水）', '地中海地区', '无（但过量使用精油可能引起不适）', '种植在干燥、排水良好的土壤中，避免过度浇水。开花后修剪促进新枝生长。', '选择排水良好的沙质土壤，种植在阳光充足的位置。避免土壤过于湿润。', '可以通过扦插、分株或播种繁殖。扦插繁殖最常用且成功率高。', '较少受到病虫害影响。可能的问题包括根腐病（由于土壤过湿）和蚜虫。', '迷迭香：叶片针状，香气不同；薄荷：叶片较大，生长更旺盛', '具有镇静、抗菌和抗炎作用。常用于制作香水、香薰、护肤品和草药茶。', '灵香草,黄香草'),
('仙人掌', 'Cactaceae', '多肉', '仙人掌科', '仙人掌是一类适应干旱环境的多肉植物，形态各异，易于养护。原产于美洲，现广泛栽培作为观赏植物。', 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Cactus%20plant%2C%20desert&sign=21bd44f25b466835546afac78d000ba0', '春季至夏季（部分品种）', '全年生长缓慢，冬季休眠', '充足阳光（每天至少4-6小时）', '很低（生长期适度浇水，休眠期几乎不浇水）', '美洲', '大多数无', '极少浇水，避免积水，冬季减少浇水频率。使用排水良好的多肉植物专用土。', '使用排水良好的多肉植物专用土壤，种植在阳光充足的位置。花盆底部可添加碎石增加排水性。', '可以通过扦插、分株或播种繁殖。许多种类可以通过单个茎段繁殖。', '常见问题有红蜘蛛、粉蚧和根腐病（由于浇水过多）。', '仙人球：球形，刺密集；多肉植物：形态多样，刺较少', '作为室内观赏植物可以净化空气，减少空气中的污染物。', '仙人球,刺球'),
('绿萝', 'Epipremnum aureum', '藤蔓', '天南星科', '绿萝是一种常见的室内观叶植物，生长迅速，易于养护。因其心形叶片和藤蔓生长习性而受欢迎。', 'https://space.coze.cn/api/coze_space/gen_image?image_size=square_hd&prompt=Pothos%20plant%2C%20indoor%20green&sign=80cca437f333913280f156947d70cc9f', '极少开花（室内几乎不开花）', '全年生长，夏季生长旺盛', '散射光（避免阳光直射）', '中等（待土壤表面干燥后再浇水）', '所罗门群岛', '轻微（对宠物）', '保持土壤湿润但不过湿，避免阳光直射。定期擦拭叶片保持清洁。', '选择排水良好的土壤，种植在散射光充足的位置。可以垂吊或攀爬生长。', '可以通过扦插繁殖，将茎段插入水中或土壤中即可生根。', '可能受到蚜虫、介壳虫和根腐病的影响。保持通风良好可减少病虫害。', '常春藤：叶片较小，攀缘能力强；龟背竹：叶片孔洞状', '可以净化室内空气，吸收甲醛等有害物质。', '黄金葛,魔鬼藤');
