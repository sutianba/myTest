#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
数据库迁移脚本：添加识别结果反馈和纠正功能支持
"""
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_config import get_db_connection

def migrate_database():
    """执行数据库迁移"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print("开始数据库迁移...")
        
        # 1. 添加新字段到 recognition_results 表
        print("1. 添加新字段到 recognition_results 表...")
        
        # 检查字段是否已存在
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'corrected'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN corrected TINYINT(1) DEFAULT 0 COMMENT '是否已纠正'
            """)
            print("   - 添加 corrected 字段")
        
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'original_result'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN original_result TEXT COMMENT '原始识别结果'
            """)
            print("   - 添加 original_result 字段")
        
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'corrected_at'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN corrected_at TIMESTAMP NULL COMMENT '纠正时间'
            """)
            print("   - 添加 corrected_at 字段")
        
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'renamed'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN renamed TINYINT(1) DEFAULT 0 COMMENT '是否已重命名'
            """)
            print("   - 添加 renamed 字段")
        
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'renamed_at'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN renamed_at TIMESTAMP NULL COMMENT '重命名时间'
            """)
            print("   - 添加 renamed_at 字段")
        
        cursor.execute("SHOW COLUMNS FROM recognition_results LIKE 'image_hash'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD COLUMN image_hash VARCHAR(64) COMMENT '图片哈希值，用于检测重复识别'
            """)
            print("   - 添加 image_hash 字段")
        
        # 2. 创建 recognition_feedback 表
        print("2. 创建 recognition_feedback 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recognition_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                result_id INT NOT NULL COMMENT '识别结果ID',
                user_id INT NOT NULL COMMENT '用户ID',
                feedback_type VARCHAR(20) DEFAULT 'wrong' COMMENT '反馈类型：wrong/other',
                comment TEXT COMMENT '反馈评论',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '反馈时间',
                FOREIGN KEY (result_id) REFERENCES recognition_results(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_result_id (result_id),
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='识别结果反馈表'
        """)
        print("   - recognition_feedback 表已创建")
        
        # 3. 添加索引
        print("3. 添加索引...")
        cursor.execute("SHOW INDEX FROM recognition_results WHERE Key_name = 'idx_image_hash'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE recognition_results 
                ADD INDEX idx_image_hash (image_hash)
            """)
            print("   - 添加 image_hash 索引")
        
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print("\n数据库迁移完成！")
        print("新增功能：")
        print("  - 用户手动纠正识别结果")
        print("  - 错误反馈提交")
        print("  - 重命名标签")
        print("  - 识别历史筛选")
        print("  - 重复图片检测")
        
    except Exception as e:
        print(f"数据库迁移失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'connection' in locals():
            connection.rollback()
            cursor.close()
            connection.close()

if __name__ == '__main__':
    migrate_database()
