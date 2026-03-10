-- 管理员后台初始化脚本
-- 添加举报、社区审核相关的表

-- ----------------------------
-- Table structure for reports
-- ----------------------------
DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `reporter_id` INT NOT NULL,
  `reported_type` ENUM('post', 'comment', 'user') NOT NULL,
  `reported_id` INT NOT NULL,
  `reason` VARCHAR(500) NOT NULL,
  `status` ENUM('pending', 'reviewing', 'resolved', 'rejected') DEFAULT 'pending',
  `admin_action` VARCHAR(500) DEFAULT NULL,
  `resolved_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_reporter_id` (`reporter_id`),
  KEY `idx_reported_type_id` (`reported_type`, `reported_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_reports_reporter` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for content_reviews
-- ----------------------------
DROP TABLE IF EXISTS `content_reviews`;
CREATE TABLE `content_reviews` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `content_type` ENUM('post', 'comment') NOT NULL,
  `content_id` INT NOT NULL,
  `reviewer_id` INT DEFAULT NULL,
  `status` ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
  `review_reason` VARCHAR(500) DEFAULT NULL,
  `reviewed_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_content_type_id` (`content_type`, `content_id`),
  KEY `idx_reviewer_id` (`reviewer_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_content_reviews_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for admin_actions
-- ----------------------------
DROP TABLE IF EXISTS `admin_actions`;
CREATE TABLE `admin_actions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `admin_id` INT NOT NULL,
  `action_type` VARCHAR(50) NOT NULL,
  `target_type` VARCHAR(50) NOT NULL,
  `target_id` INT NOT NULL,
  `details` TEXT DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_admin_id` (`admin_id`),
  KEY `idx_action_type` (`action_type`),
  KEY `idx_target_type_id` (`target_type`, `target_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_admin_actions_admin` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Insert default roles
-- ----------------------------
INSERT INTO `roles` (`name`, `description`) VALUES
('admin', '系统管理员 - 拥有所有权限'),
('moderator', '社区管理员 - 负责内容审核和用户管理'),
('user', '普通用户 - 基础功能权限');

-- ----------------------------
-- Insert default permissions
-- ----------------------------
INSERT INTO `permissions` (`name`, `description`) VALUES
('user_view', '查看用户列表'),
('user_edit', '编辑用户信息'),
('user_ban', '封禁/解封用户'),
('user_delete', '删除用户'),
('post_view', '查看所有帖子'),
('post_approve', '审核帖子'),
('post_delete', '删除帖子'),
('comment_view', '查看所有评论'),
('comment_approve', '审核评论'),
('comment_delete', '删除评论'),
('report_view', '查看所有举报'),
('report_handle', '处理举报'),
('review_view', '查看待审核内容'),
('review_approve', '批准审核内容'),
('review_reject', '拒绝审核内容'),
('log_view', '查看操作日志'),
('permission_assign', '分配权限'),
('role_assign', '分配角色');

-- ----------------------------
-- Assign permissions to admin role
-- ----------------------------
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin';

-- ----------------------------
-- Assign permissions to moderator role
-- ----------------------------
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'moderator'
AND p.name IN (
    'user_view', 'user_edit', 'user_ban', 'post_view', 'post_approve', 
    'post_delete', 'comment_view', 'comment_approve', 'comment_delete',
    'report_view', 'report_handle', 'review_view', 'review_approve', 
    'review_reject', 'log_view'
);
