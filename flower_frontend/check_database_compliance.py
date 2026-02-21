#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3
import json

def check_database_compliance():
    conn = sqlite3.connect('flower_recognition.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("数据库合规性检查报告")
    print("=" * 80)
    
    # 检查所有表是否存在
    print("\n1. 表结构检查")
    print("-" * 80)
    
    required_tables = {
        'users': ['id', 'username', 'password_hash', 'role', 'created_at', 'updated_at'],
        'posts': ['id', 'user_id', 'title', 'content', 'image_data', 'recognition_result', 
                'category', 'views', 'status', 'created_at', 'updated_at', 'topics'],
        'comments': ['id', 'post_id', 'user_id', 'content', 'parent_id', 'created_at'],
        'likes': ['id', 'user_id', 'target_type', 'target_id', 'created_at'],
        'follows': ['id', 'follower_id', 'following_id', 'created_at'],
        'favorites': ['id', 'user_id', 'post_id', 'created_at'],
        'topics': ['id', 'name', 'display_name', 'post_count', 'created_at', 'updated_at']
    }
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    compliance_issues = []
    
    for table_name, required_columns in required_tables.items():
        if table_name in existing_tables:
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = [col[1] for col in cursor.fetchall()]
            
            missing_columns = set(required_columns) - set(columns)
            if missing_columns:
                compliance_issues.append(f"  ❌ 表 {table_name} 缺少字段: {', '.join(missing_columns)}")
            else:
                print(f"  ✓ 表 {table_name} 结构完整")
        else:
            compliance_issues.append(f"  ❌ 表 {table_name} 不存在")
    
    if compliance_issues:
        print("\n发现的问题:")
        for issue in compliance_issues:
            print(issue)
    else:
        print("\n✓ 所有表结构检查通过")
    
    # 检查外键约束
    print("\n2. 外键约束检查")
    print("-" * 80)
    
    foreign_key_checks = [
        ('posts', 'user_id', 'users', 'id'),
        ('comments', 'post_id', 'posts', 'id'),
        ('comments', 'user_id', 'users', 'id'),
        ('comments', 'parent_id', 'comments', 'id'),
        ('likes', 'user_id', 'users', 'id'),
        ('follows', 'follower_id', 'users', 'id'),
        ('follows', 'following_id', 'users', 'id'),
        ('favorites', 'user_id', 'users', 'id'),
        ('favorites', 'post_id', 'posts', 'id')
    ]
    
    fk_issues = []
    for table, fk_column, ref_table, ref_column in foreign_key_checks:
        if table in existing_tables and ref_table in existing_tables:
            # 检查是否有孤立数据
            cursor.execute(f'''
                SELECT COUNT(*) FROM {table} 
                WHERE {fk_column} NOT IN (SELECT {ref_column} FROM {ref_table})
            ''')
            orphan_count = cursor.fetchone()[0]
            
            if orphan_count > 0:
                fk_issues.append(f"  ⚠️  表 {table}.{fk_column} 有 {orphan_count} 条孤立数据")
            else:
                print(f"  ✓ 表 {table}.{fk_column} 外键约束正常")
        else:
            fk_issues.append(f"  ❌ 无法检查 {table}.{fk_column} - 表不存在")
    
    if fk_issues:
        print("\n外键问题:")
        for issue in fk_issues:
            print(issue)
    else:
        print("\n✓ 所有外键约束检查通过")
    
    # 检查数据完整性
    print("\n3. 数据完整性检查")
    print("-" * 80)
    
    # 检查users表
    cursor.execute("SELECT COUNT(*) FROM users WHERE username IS NULL OR username = ''")
    null_usernames = cursor.fetchone()[0]
    if null_usernames > 0:
        print(f"  ⚠️  users表中有 {null_usernames} 条记录的用户名为空")
    else:
        print("  ✓ users表用户名字段完整")
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE password_hash IS NULL OR password_hash = ''")
    null_passwords = cursor.fetchone()[0]
    if null_passwords > 0:
        print(f"  ⚠️  users表中有 {null_passwords} 条记录的密码哈希为空")
    else:
        print("  ✓ users表密码哈希字段完整")
    
    # 检查posts表
    cursor.execute("SELECT COUNT(*) FROM posts WHERE title IS NULL OR title = ''")
    null_titles = cursor.fetchone()[0]
    if null_titles > 0:
        print(f"  ⚠️  posts表中有 {null_titles} 条记录的标题为空")
    else:
        print("  ✓ posts表标题字段完整")
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE content IS NULL OR content = ''")
    null_contents = cursor.fetchone()[0]
    if null_contents > 0:
        print(f"  ⚠️  posts表中有 {null_contents} 条记录的内容为空")
    else:
        print("  ✓ posts表内容字段完整")
    
    # 检查topics表
    cursor.execute("SELECT COUNT(*) FROM topics WHERE name IS NULL OR name = ''")
    null_topic_names = cursor.fetchone()[0]
    if null_topic_names > 0:
        print(f"  ⚠️  topics表中有 {null_topic_names} 条记录的话题名为空")
    else:
        print("  ✓ topics表话题名字段完整")
    
    # 检查数据一致性
    print("\n4. 数据一致性检查")
    print("-" * 80)
    
    # 检查topics表的post_count是否准确
    cursor.execute('''
        SELECT t.id, t.name, t.post_count, 
               (SELECT COUNT(*) FROM posts WHERE topics LIKE '%' || t.name || '%') as actual_count
        FROM topics t
    ''')
    topic_count_issues = cursor.fetchall()
    
    if topic_count_issues:
        has_issues = False
        for topic_id, topic_name, stored_count, actual_count in topic_count_issues:
            if stored_count != actual_count:
                has_issues = True
                print(f"  ⚠️  话题 '{topic_name}' 的帖子计数不准确: 存储值={stored_count}, 实际值={actual_count}")
        
        if not has_issues:
            print("  ✓ topics表帖子计数准确")
    else:
        print("  ✓ topics表为空或计数准确")
    
    # 检查posts表的topics字段格式
    cursor.execute("SELECT id, topics FROM posts WHERE topics IS NOT NULL AND topics != ''")
    posts_with_topics = cursor.fetchall()
    
    topic_format_issues = 0
    for post_id, topics_json in posts_with_topics:
        try:
            topics_list = json.loads(topics_json)
            if not isinstance(topics_list, list):
                topic_format_issues += 1
        except json.JSONDecodeError:
            topic_format_issues += 1
    
    if topic_format_issues > 0:
        print(f"  ⚠️  posts表中有 {topic_format_issues} 条记录的topics字段格式不正确")
    else:
        print("  ✓ posts表topics字段格式正确")
    
    # 检查索引
    print("\n5. 索引优化检查")
    print("-" * 80)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing_indexes = [row[0] for row in cursor.fetchall()]
    
    recommended_indexes = [
        'idx_posts_user_id',
        'idx_posts_category',
        'idx_posts_created_at',
        'idx_comments_post_id',
        'idx_likes_target',
        'idx_follows_follower',
        'idx_favorites_user_id'
    ]
    
    missing_indexes = set(recommended_indexes) - set(existing_indexes)
    
    if missing_indexes:
        print(f"  ⚠️  缺少推荐的索引: {', '.join(missing_indexes)}")
    else:
        print("  ✓ 所有推荐索引都已创建")
    
    # 数据统计
    print("\n6. 数据统计")
    print("-" * 80)
    
    for table_name in required_tables.keys():
        if table_name in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} 条记录")
    
    # 安全性检查
    print("\n7. 安全性检查")
    print("-" * 80)
    
    # 检查是否有默认密码
    cursor.execute("SELECT COUNT(*) FROM users WHERE password_hash = '5f4dcc3b5aa765d61d8327deb882cf99'")  # 'password'的md5
    default_password_users = cursor.fetchone()[0]
    if default_password_users > 0:
        print(f"  ⚠️  有 {default_password_users} 个用户使用默认密码")
    else:
        print("  ✓ 没有发现使用默认密码的用户")
    
    # 检查用户名唯一性
    cursor.execute('''
        SELECT username, COUNT(*) as count 
        FROM users 
        GROUP BY username 
        HAVING count > 1
    ''')
    duplicate_users = cursor.fetchall()
    if duplicate_users:
        print(f"  ⚠️  发现重复的用户名: {', '.join([u[0] for u in duplicate_users])}")
    else:
        print("  ✓ 用户名唯一性检查通过")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("数据库合规性检查完成")
    print("=" * 80)

if __name__ == "__main__":
    check_database_compliance()
