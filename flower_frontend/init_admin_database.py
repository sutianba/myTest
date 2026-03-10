#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
管理员后台数据库初始化脚本
初始化管理员后台所需的表和默认数据
"""

import sys
import os

# 添加基础目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from db_config import get_db_connection

def init_admin_database():
    """初始化管理员后台数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("开始初始化管理员后台数据库...")
        
        # 创建举报表
        print("创建举报表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `reports` (
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
        """)
        
        # 创建内容审核表
        print("创建内容审核表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `content_reviews` (
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
        """)
        
        # 创建管理员操作日志表
        print("创建管理员操作日志表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `admin_actions` (
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
        """)
        
        # 插入默认角色
        print("插入默认角色...")
        cursor.execute("SELECT COUNT(*) as count FROM roles WHERE name = 'admin'")
        if cursor.fetchone()['count'] == 0:
            cursor.execute("INSERT INTO `roles` (`name`, `description`) VALUES ('admin', '系统管理员 - 拥有所有权限')")
        
        cursor.execute("SELECT COUNT(*) as count FROM roles WHERE name = 'moderator'")
        if cursor.fetchone()['count'] == 0:
            cursor.execute("INSERT INTO `roles` (`name`, `description`) VALUES ('moderator', '社区管理员 - 负责内容审核和用户管理')")
        
        # 插入默认权限
        print("插入默认权限...")
        permissions = [
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
            ('role_assign', '分配角色')
        ]
        
        for name, description in permissions:
            cursor.execute("SELECT COUNT(*) as count FROM permissions WHERE name = %s", (name,))
            if cursor.fetchone()['count'] == 0:
                cursor.execute("INSERT INTO `permissions` (`name`, `description`) VALUES (%s, %s)", (name, description))
        
        # 为admin角色分配所有权限
        print("为admin角色分配权限...")
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()
        if admin_role:
            cursor.execute("SELECT id FROM permissions")
            permissions_list = cursor.fetchall()
            for perm in permissions_list:
                try:
                    cursor.execute(
                        "INSERT INTO `role_permissions` (`role_id`, `permission_id`) VALUES (%s, %s)",
                        (admin_role['id'], perm['id'])
                    )
                except Exception as e:
                    # 如果已经存在则跳过
                    pass
        
        # 为moderator角色分配部分权限
        print("为moderator角色分配权限...")
        cursor.execute("SELECT id FROM roles WHERE name = 'moderator'")
        moderator_role = cursor.fetchone()
        if moderator_role:
            moderator_permissions = [
                'user_view', 'user_edit', 'user_ban', 'post_view', 'post_approve', 
                'post_delete', 'comment_view', 'comment_approve', 'comment_delete',
                'report_view', 'report_handle', 'review_view', 'review_approve', 
                'review_reject', 'log_view'
            ]
            
            for perm_name in moderator_permissions:
                cursor.execute("SELECT id FROM permissions WHERE name = %s", (perm_name,))
                perm = cursor.fetchone()
                if perm:
                    try:
                        cursor.execute(
                            "INSERT INTO `role_permissions` (`role_id`, `permission_id`) VALUES (%s, %s)",
                            (moderator_role['id'], perm['id'])
                        )
                    except Exception as e:
                        # 如果已经存在则跳过
                        pass
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("管理员后台数据库初始化完成！")
        print("默认角色:")
        print("  - admin: 系统管理员 (拥有所有权限)")
        print("  - moderator: 社区管理员 (负责内容审核和用户管理)")
        
    except Exception as e:
        print(f"初始化管理员后台数据库失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_admin_database()
