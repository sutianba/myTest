-- MySQL Database Schema for Account System
-- Database: flower_recognition

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
