import pymysql
import time
import os
import json
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20031221',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 基准目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQL文件路径
SCHEMA_SQL = os.path.join(BASE_DIR, 'database.sql')
BACKUP_SQL = os.path.join(BASE_DIR, 'database_backup.sql')

class SQLDatabaseManager:
    def __init__(self, db_config=DB_CONFIG):
        self.db_config = db_config
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """确保数据库存在，从SQL文件初始化"""
        try:
            # 尝试连接数据库
            conn = pymysql.connect(**self.db_config)
            conn.close()
        except pymysql.MySQLError as e:
            if "1049" in str(e):  # 数据库不存在
                self.create_database()
            else:
                raise
        
        # 初始化表结构
        self.initialize_from_sql(SCHEMA_SQL)
    
    def create_database(self):
        """创建数据库"""
        config = self.db_config.copy()
        db_name = config.pop('database')
        
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            print(f"数据库 {db_name} 已创建")
        finally:
            conn.close()
    
    def initialize_from_sql(self, sql_file):
        """从SQL文件初始化数据库"""
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 执行SQL语句（MySQL不支持executescript，需要逐句执行）
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    # 跳过SQLite特有语句
                    if statement.startswith('PRAGMA ') or statement.startswith('BEGIN TRANSACTION'):
                        continue
                    # 跳过CREATE TABLE语句，避免表已存在的错误
                    if statement.startswith('CREATE TABLE'):
                        continue
                    # 跳过INSERT IGNORE INTO users语句，避免password_hash字段错误
                    if 'INSERT IGNORE INTO users' in statement:
                        continue
                    cursor.execute(statement)
            conn.commit()
            print(f"数据库已从 {sql_file} 初始化完成")
        except Exception as e:
            conn.rollback()
            print(f"初始化数据库失败: {str(e)}")
            # 不抛出异常，允许应用继续启动
        finally:
            conn.close()
    
    def delete_database(self):
        """删除数据库"""
        config = self.db_config.copy()
        db_name = config.pop('database')
        
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            conn.commit()
            print(f"数据库 {db_name} 已删除")
            return True
        except Exception as e:
            print(f"删除数据库失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def execute_sql_file(self, sql_file):
        """执行SQL文件"""
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 执行SQL语句（MySQL不支持executescript，需要逐句执行）
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            conn.commit()
            print(f"SQL文件 {sql_file} 执行成功")
            return True
        except Exception as e:
            conn.rollback()
            print(f"执行SQL文件失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def export_to_sql(self, output_file):
        """将当前数据库导出为SQL文件"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 导出表结构
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = list(table.values())[0]
                # 获取表结构
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_table = cursor.fetchone()
                f.write(create_table['Create Table'] + ';\n\n')
                
                # 获取数据
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    columns = [col for col in rows[0].keys()]
                    for row in rows:
                        values = tuple(row.values())
                        # 处理字符串值，添加引号
                        formatted_values = []
                        for val in values:
                            if isinstance(val, str):
                                formatted_values.append("'" + val + "'")
                            elif val is None:
                                formatted_values.append('NULL')
                            else:
                                formatted_values.append(str(val))
                        f.write("INSERT INTO " + table_name + " (" + ", ".join(columns) + ") VALUES (" + ", ".join(formatted_values) + ");\n")
                f.write('\n')
        
        conn.close()
        print(f"数据库已导出到 {output_file}")
        return True
    
    def get_connection(self):
        """获取数据库连接"""
        conn = pymysql.connect(**self.db_config)
        return conn
    
    # 用户相关操作
    def create_user(self, username, email, password, role='user'):
        """创建新用户"""
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 插入用户数据，使用password_hash，created_at使用数据库默认值
            cursor.execute('''
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, %s)
            ''', (username, email, password_hash, role))
            
            user_id = cursor.lastrowid
            
            # 检查roles表是否存在对应的角色
            role_name = role if role == 'admin' else 'user'
            cursor.execute('SELECT id FROM roles WHERE name = %s', (role_name,))
            role_record = cursor.fetchone()
            if role_record:
                role_id = role_record['id']
                # 插入用户角色关联
                cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
                ''', (user_id, role_id))
            
            conn.commit()
            return user_id
        except pymysql.IntegrityError as e:
            conn.rollback()
            if 'Duplicate entry' in str(e):
                if 'email' in str(e):
                    raise ValueError('邮箱已存在')
                else:
                    raise ValueError('用户名已存在')
            else:
                raise ValueError('用户名或邮箱已存在')
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建用户失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_by_username(self, username):
        """根据用户名获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise Exception(f'获取用户信息失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise Exception(f'获取用户信息失败: {str(e)}')
        finally:
            conn.close()
    
    def verify_password(self, stored_password_hash, provided_password):
        """验证密码"""
        return check_password_hash(stored_password_hash, provided_password)
    
    # 角色和权限相关操作
    def get_user_roles(self, user_id):
        """获取用户的所有角色"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT r.* FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s
            ''', (user_id,))
            roles = cursor.fetchall()
            return [dict(role) for role in roles]
        except Exception as e:
            raise Exception(f'获取用户角色失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_permissions(self, user_id):
        """获取用户的所有权限"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT DISTINCT p.* FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = %s
            ''', (user_id,))
            permissions = cursor.fetchall()
            return [dict(perm) for perm in permissions]
        except Exception as e:
            raise Exception(f'获取用户权限失败: {str(e)}')
        finally:
            conn.close()
    
    def check_user_permission(self, user_id, permission_name):
        """检查用户是否有指定权限"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT COUNT(*) FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = %s AND p.name = %s
            ''', (user_id, permission_name))
            result = cursor.fetchone()
            count = result[0] if result else 0
            return count > 0
        except Exception as e:
            raise Exception(f'检查用户权限失败: {str(e)}')
        finally:
            conn.close()
    
    # 植物花卉识别结果相关操作
    def save_recognition_result(self, user_id, image_path, result, confidence, shoot_time=None, shoot_year=None, shoot_month=None, shoot_season=None, latitude=None, longitude=None, location_text=None, region_label=None, final_category=None):
        """保存植物花卉识别结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"[DB] 保存识别结果: user_id={user_id}, image_path={image_path}, result={result}, confidence={confidence}")
            cursor.execute('''
            INSERT INTO recognition_results (user_id, image_path, result, confidence, shoot_time, shoot_year, shoot_month, shoot_season, latitude, longitude, location_text, region_label, final_category, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (user_id, image_path, result, confidence, shoot_time, shoot_year, shoot_month, shoot_season, latitude, longitude, location_text, region_label, final_category))
            conn.commit()
            result_id = cursor.lastrowid
            print(f"[DB] 识别结果保存成功: result_id={result_id}")
            return result_id
        except Exception as e:
            conn.rollback()
            print(f"[DB] 保存识别结果失败: {str(e)}")
            raise Exception(f'保存识别结果失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_recognition_results(self, user_id):
        """获取用户的识别结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT * FROM recognition_results
            WHERE user_id = %s
            ORDER BY created_at DESC
            ''', (user_id,))
            results = cursor.fetchall()
            return [dict(result) for result in results]
        except Exception as e:
            raise Exception(f'获取识别结果失败: {str(e)}')
        finally:
            conn.close()
    
    def get_recognition_result(self, result_id):
        """根据ID获取单个识别记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT * FROM recognition_results
            WHERE id = %s
            ''', (result_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            raise Exception(f'获取识别记录失败: {str(e)}')
        finally:
            conn.close()
    
    # 帖子相关操作
    def create_post(self, user_id, content, image_url=None, topics=None, tags=None, source_type=None, source_id=None):
        """创建新帖子"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO posts (user_id, content, image_url, topics, tags, source_type, source_id, likes_count, comments_count, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, content, image_url, topics, tags, source_type, source_id, 0, 0))
            
            post_id = cursor.lastrowid
            conn.commit()
            return post_id
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建帖子失败: {str(e)}')
        finally:
            conn.close()
    
    def get_posts(self, limit=20, offset=0):
        """获取帖子列表（排除已删除的）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT p.*, u.username FROM posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
            ''', (limit, offset))
            posts = cursor.fetchall()
            return [dict(post) for post in posts]
        except Exception as e:
            raise Exception(f'获取帖子列表失败: {str(e)}')
        finally:
            conn.close()
    
    def get_post_by_id(self, post_id):
        """获取单个帖子详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT p.*, u.username FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
            ''', (post_id,))
            post = cursor.fetchone()
            return dict(post) if post else None
        except Exception as e:
            raise Exception(f'获取帖子详情失败: {str(e)}')
        finally:
            conn.close()
    
    def update_post(self, post_id, content, image_url=None):
        """更新帖子"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE posts
            SET content = %s, image_url = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''', (content, image_url, post_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新帖子失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_post(self, post_id):
        """删除帖子（硬删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除帖子失败: {str(e)}')
        finally:
            conn.close()
    
    def increment_comments_count(self, post_id):
        """增加帖子评论数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE posts
            SET comments_count = comments_count + 1
            WHERE id = %s
            ''', (post_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新评论数失败: {str(e)}')
        finally:
            conn.close()
    
    def decrement_comments_count(self, post_id):
        """减少帖子评论数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE posts
            SET comments_count = MAX(0, comments_count - 1)
            WHERE id = %s
            ''', (post_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新评论数失败: {str(e)}')
        finally:
            conn.close()
    
    # 评论相关操作
    def create_comment(self, post_id, user_id, content, parent_comment_id=None, reply_to_user_id=None):
        """创建评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            floor_number = None
            # 计算楼层号（只有一级评论需要）
            if parent_comment_id is None:
                cursor.execute('''
                SELECT COUNT(*) as count
                FROM comments
                WHERE post_id = %s AND parent_comment_id IS NULL
                ''', (post_id,))
                count = cursor.fetchone()['count']
                floor_number = count + 1
            
            # 创建评论
            cursor.execute('''
            INSERT INTO comments (post_id, user_id, content, parent_comment_id, reply_to_user_id, floor_number, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ''', (post_id, user_id, content, parent_comment_id, reply_to_user_id, floor_number))
            
            # 增加帖子评论数
            cursor.execute('''
            UPDATE posts
            SET comments_count = comments_count + 1
            WHERE id = %s
            ''', (post_id,))
            
            comment_id = cursor.lastrowid
            conn.commit()
            return comment_id
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建评论失败: {str(e)}')
        finally:
            conn.close()
    
    def get_comments_by_post_id(self, post_id):
        """获取帖子的评论列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 先查询一级评论
            cursor.execute('''
            SELECT c.*, u.username FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = %s AND c.parent_comment_id IS NULL
            ORDER BY c.floor_number ASC
            ''', (post_id,))
            primary_comments = cursor.fetchall()
            
            result = []
            for comment in primary_comments:
                comment_dict = dict(comment)
                # 查询该评论的回复
                cursor.execute('''
                SELECT c.*, u.username, ru.username as reply_to_username FROM comments c
                JOIN users u ON c.user_id = u.id
                LEFT JOIN users ru ON c.reply_to_user_id = ru.id
                WHERE c.parent_comment_id = %s
                ORDER BY c.created_at ASC
                ''', (comment['id'],))
                replies = cursor.fetchall()
                comment_dict['replies'] = [dict(reply) for reply in replies]
                # 获取评论点赞数
                cursor.execute('''
                SELECT COUNT(*) as likes_count
                FROM comment_likes
                WHERE comment_id = %s
                ''', (comment['id'],))
                likes_count = cursor.fetchone()['likes_count']
                comment_dict['likes_count'] = likes_count
                # 获取每个回复的点赞数
                for reply in comment_dict['replies']:
                    cursor.execute('''
                    SELECT COUNT(*) as likes_count
                    FROM comment_likes
                    WHERE comment_id = %s
                    ''', (reply['id'],))
                    reply_likes_count = cursor.fetchone()['likes_count']
                    reply['likes_count'] = reply_likes_count
                result.append(comment_dict)
            
            return result
        except Exception as e:
            raise Exception(f'获取评论列表失败: {str(e)}')
        finally:
            conn.close()
    
    def like_comment(self, comment_id, user_id):
        """点赞评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已经点赞
            cursor.execute('SELECT id FROM comment_likes WHERE comment_id = %s AND user_id = %s', (comment_id, user_id))
            if cursor.fetchone():
                return False  # 已经点赞过
            
            # 创建点赞记录
            cursor.execute('''
            INSERT INTO comment_likes (comment_id, user_id, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ''', (comment_id, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'点赞评论失败: {str(e)}')
        finally:
            conn.close()
    
    def unlike_comment(self, comment_id, user_id):
        """取消点赞评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 删除点赞记录
            cursor.execute('DELETE FROM comment_likes WHERE comment_id = %s AND user_id = %s', (comment_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False  # 没有点赞记录
        except Exception as e:
            conn.rollback()
            raise Exception(f'取消点赞失败: {str(e)}')
        finally:
            conn.close()
    
    def is_comment_liked(self, comment_id, user_id):
        """检查用户是否已点赞评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM comment_likes WHERE comment_id = %s AND user_id = %s', (comment_id, user_id))
            return cursor.fetchone() is not None
        except Exception as e:
            raise Exception(f'检查点赞状态失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_comment(self, comment_id):
        """删除评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 先获取评论信息以更新帖子评论数
            cursor.execute('SELECT post_id FROM comments WHERE id = %s', (comment_id,))
            comment = cursor.fetchone()
            if not comment:
                return False
            
            post_id = comment['post_id']
            
            # 删除评论
            cursor.execute('DELETE FROM comments WHERE id = %s', (comment_id,))
            
            # 减少帖子评论数
            cursor.execute('''
            UPDATE posts
            SET comments_count = MAX(0, comments_count - 1)
            WHERE id = %s
            ''', (post_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除评论失败: {str(e)}')
        finally:
            conn.close()
    
    # 点赞相关操作
    def like_post(self, post_id, user_id):
        """点赞帖子"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已经点赞
            cursor.execute('SELECT id FROM likes WHERE post_id = %s AND user_id = %s', (post_id, user_id))
            if cursor.fetchone():
                return False  # 已经点赞过
            
            # 创建点赞记录
            cursor.execute('''
            INSERT INTO likes (post_id, user_id, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ''', (post_id, user_id))
            
            # 增加帖子点赞数
            cursor.execute('''
            UPDATE posts
            SET likes_count = likes_count + 1
            WHERE id = %s
            ''', (post_id,))
            
            conn.commit()
            return True
        except pymysql.IntegrityError:
            conn.rollback()
            return False  # 唯一约束冲突，说明已经点赞过
        except Exception as e:
            conn.rollback()
            raise Exception(f'点赞失败: {str(e)}')
        finally:
            conn.close()
    
    def unlike_post(self, post_id, user_id):
        """取消点赞"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 删除点赞记录
            cursor.execute('DELETE FROM likes WHERE post_id = %s AND user_id = %s', (post_id, user_id))
            
            if cursor.rowcount > 0:
                # 减少帖子点赞数
                cursor.execute('''
                UPDATE posts
                SET likes_count = MAX(0, likes_count - 1)
                WHERE id = %s
                ''', (post_id,))
                conn.commit()
                return True
            else:
                conn.commit()
                return False  # 没有点赞记录
        except Exception as e:
            conn.rollback()
            raise Exception(f'取消点赞失败: {str(e)}')
        finally:
            conn.close()
    
    def is_post_liked_by_user(self, post_id, user_id):
        """检查用户是否已点赞帖子"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM likes WHERE post_id = %s AND user_id = %s', (post_id, user_id))
            return cursor.fetchone() is not None
        except Exception as e:
            raise Exception(f'检查点赞状态失败: {str(e)}')
        finally:
            conn.close()
    
    # 关注相关操作
    def follow_user(self, follower_id, following_id):
        """关注用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已经关注
            cursor.execute('SELECT id FROM follows WHERE follower_id = %s AND following_id = %s', (follower_id, following_id))
            if cursor.fetchone():
                return False  # 已经关注过
            
            # 创建关注记录
            cursor.execute('''
            INSERT INTO follows (follower_id, following_id, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ''', (follower_id, following_id))
            
            conn.commit()
            return True
        except pymysql.IntegrityError:
            conn.rollback()
            return False  # 唯一约束冲突，说明已经关注过
        except Exception as e:
            conn.rollback()
            raise Exception(f'关注用户失败: {str(e)}')
        finally:
            conn.close()
    
    def unfollow_user(self, follower_id, following_id):
        """取消关注"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM follows WHERE follower_id = %s AND following_id = %s', (follower_id, following_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'取消关注失败: {str(e)}')
        finally:
            conn.close()
    
    def is_following(self, follower_id, following_id):
        """检查是否已关注"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM follows WHERE follower_id = %s AND following_id = %s', (follower_id, following_id))
            return cursor.fetchone() is not None
        except Exception as e:
            raise Exception(f'检查关注状态失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_following(self, user_id):
        """获取用户的关注列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT u.id, u.username FROM users u
            JOIN follows f ON u.id = f.following_id
            WHERE f.follower_id = %s
            ''', (user_id,))
            users = cursor.fetchall()
            return [dict(user) for user in users]
        except Exception as e:
            raise Exception(f'获取关注列表失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_followers(self, user_id):
        """获取用户的粉丝列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT u.id, u.username FROM users u
            JOIN follows f ON u.id = f.follower_id
            WHERE f.following_id = %s
            ''', (user_id,))
            users = cursor.fetchall()
            return [dict(user) for user in users]
        except Exception as e:
            raise Exception(f'获取粉丝列表失败: {str(e)}')
        finally:
            conn.close()
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except Exception as e:
            print(f'数据库连接测试失败: {str(e)}')
            return False
    
    # ==================== 超级管理员端相关操作 ====================
    
    def create_system_log(self, log_level, module, message, user_id=None, username=None, ip_address=None, user_agent=None):
        """创建系统日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = int(time.time())
            cursor.execute('''
            INSERT INTO system_logs (log_level, module, message, user_id, username, ip_address, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (log_level, module, message, user_id, username, ip_address, user_agent, current_time))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f'创建系统日志失败: {str(e)}')
        finally:
            conn.close()
    
    def get_system_logs(self, limit=100, offset=0, log_level=None, module=None, start_time=None, end_time=None):
        """获取系统日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM system_logs WHERE 1=1'
            params = []
            
            if log_level:
                query += ' AND log_level = %s'
                params.append(log_level)
            if module:
                query += ' AND module = %s'
                params.append(module)
            if start_time:
                query += ' AND created_at >= %s'
                params.append(start_time)
            if end_time:
                query += ' AND created_at <= %s'
                params.append(end_time)
            
            query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            return [dict(log) for log in logs]
        except Exception as e:
            raise Exception(f'获取系统日志失败: {str(e)}')
        finally:
            conn.close()
    
    def record_traffic(self, endpoint, method, ip_address=None, user_id=None, response_status=200, response_time=0):
        """记录访问流量"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = int(time.time())
            date_str = time.strftime('%Y-%m-%d')
            hour = int(time.strftime('%H'))
            
            cursor.execute('''
            INSERT INTO traffic_stats (date, hour, endpoint, method, ip_address, user_id, response_status, response_time, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (date_str, hour, endpoint, method, ip_address, user_id, response_status, response_time, current_time))
            conn.commit()
            
            self._update_daily_traffic_summary(date_str)
            
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f'记录访问流量失败: {str(e)}')
        finally:
            conn.close()
    
    def _update_daily_traffic_summary(self, date_str):
        """更新每日流量汇总"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                COUNT(DISTINCT ip_address) as unique_visitors,
                AVG(response_time) as avg_response_time,
                SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
            FROM traffic_stats
            WHERE date = %s
            ''', (date_str,))
            
            result = cursor.fetchone()
            current_time = int(time.time())
            
            cursor.execute('''
            INSERT INTO daily_traffic_summary (date, total_requests, unique_visitors, avg_response_time, error_count, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_requests = VALUES(total_requests),
                unique_visitors = VALUES(unique_visitors),
                avg_response_time = VALUES(avg_response_time),
                error_count = VALUES(error_count),
                updated_at = VALUES(updated_at)
            ''', (date_str, result['total_requests'], result['unique_visitors'], result['avg_response_time'], result['error_count'], current_time, current_time))
            
            conn.commit()
        except Exception as e:
            print(f'更新每日流量汇总失败: {str(e)}')
        finally:
            conn.close()
    
    def get_traffic_stats(self, start_date=None, end_date=None, limit=100):
        """获取流量统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM daily_traffic_summary WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND date >= %s'
                params.append(start_date)
            if end_date:
                query += ' AND date <= %s'
                params.append(end_date)
            
            query += ' ORDER BY date DESC LIMIT %s'
            params.append(limit)
            
            cursor.execute(query, params)
            stats = cursor.fetchall()
            return [dict(stat) for stat in stats]
        except Exception as e:
            raise Exception(f'获取流量统计失败: {str(e)}')
        finally:
            conn.close()
    
    def get_traffic_by_endpoint(self, start_date=None, end_date=None, limit=20):
        """按端点获取流量统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
            SELECT endpoint, method, 
                   COUNT(*) as request_count,
                   AVG(response_time) as avg_response_time,
                   SUM(CASE WHEN response_status >= 400 THEN 1 ELSE 0 END) as error_count
            FROM traffic_stats
            WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += ' AND date >= %s'
                params.append(start_date)
            if end_date:
                query += ' AND date <= %s'
                params.append(end_date)
            
            query += ' GROUP BY endpoint, method ORDER BY request_count DESC LIMIT %s'
            params.append(limit)
            
            cursor.execute(query, params)
            stats = cursor.fetchall()
            return [dict(stat) for stat in stats]
        except Exception as e:
            raise Exception(f'获取端点流量统计失败: {str(e)}')
        finally:
            conn.close()
    
    def record_server_status(self, metric_name, metric_value, unit=None, status='normal'):
        """记录服务器状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = int(time.time())
            cursor.execute('''
            INSERT INTO server_status (metric_name, metric_value, unit, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ''', (metric_name, metric_value, unit, status, current_time))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f'记录服务器状态失败: {str(e)}')
        finally:
            conn.close()
    
    def get_server_status(self, metric_name=None, limit=100):
        """获取服务器状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if metric_name:
                cursor.execute('''
                SELECT * FROM server_status 
                WHERE metric_name = %s
                ORDER BY created_at DESC LIMIT %s
                ''', (metric_name, limit))
            else:
                cursor.execute('''
                SELECT * FROM server_status 
                ORDER BY created_at DESC LIMIT %s
                ''', (limit,))
            
            status = cursor.fetchall()
            return [dict(s) for s in status]
        except Exception as e:
            raise Exception(f'获取服务器状态失败: {str(e)}')
        finally:
            conn.close()
    
    def get_latest_server_metrics(self):
        """获取最新的服务器指标"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT metric_name, metric_value, unit, status, created_at
            FROM server_status
            WHERE id IN (
                SELECT MAX(id) FROM server_status GROUP BY metric_name
            )
            ''')
            metrics = cursor.fetchall()
            return [dict(metric) for metric in metrics]
        except Exception as e:
            raise Exception(f'获取最新服务器指标失败: {str(e)}')
        finally:
            conn.close()
    
    def record_admin_operation(self, admin_id, admin_username, operation_type, target_type=None, target_id=None, description=None, ip_address=None):
        """记录管理员操作"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = int(time.time())
            cursor.execute('''
            INSERT INTO admin_operations (admin_id, admin_username, operation_type, target_type, target_id, description, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (admin_id, admin_username, operation_type, target_type, target_id, description, ip_address, current_time))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            raise Exception(f'记录管理员操作失败: {str(e)}')
        finally:
            conn.close()
    
    def get_admin_operations(self, admin_id=None, operation_type=None, limit=100, offset=0):
        """获取管理员操作记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM admin_operations WHERE 1=1'
            params = []
            
            if admin_id:
                query += ' AND admin_id = %s'
                params.append(admin_id)
            if operation_type:
                query += ' AND operation_type = %s'
                params.append(operation_type)
            
            query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            operations = cursor.fetchall()
            return [dict(op) for op in operations]
        except Exception as e:
            raise Exception(f'获取管理员操作记录失败: {str(e)}')
        finally:
            conn.close()
    
    def get_all_admins(self):
        """获取所有管理员"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT u.id, u.username, u.email, u.created_at, r.name as role_name, r.description as role_description
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name IN ('admin', 'super_admin')
            ORDER BY u.created_at DESC
            ''')
            admins = cursor.fetchall()
            return [dict(admin) for admin in admins]
        except Exception as e:
            raise Exception(f'获取管理员列表失败: {str(e)}')
        finally:
            conn.close()
    
    def update_user_role(self, user_id, role_name):
        """更新用户角色"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM roles WHERE name = %s', (role_name,))
            role = cursor.fetchone()
            
            if not role:
                raise Exception(f'角色不存在: {role_name}')
            
            role_id = role['id']
            
            cursor.execute('DELETE FROM user_roles WHERE user_id = %s', (user_id,))
            cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)', (user_id, role_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新用户角色失败: {str(e)}')
        finally:
            conn.close()
    
    def get_system_summary(self):
        """获取系统概要统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            summary = {}
            
            cursor.execute('SELECT COUNT(*) as count FROM users')
            summary['total_users'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM posts')
            summary['total_posts'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM recognition_results')
            summary['total_recognitions'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM system_logs WHERE created_at > %s', (int(time.time()) - 86400,))
            summary['today_logs'] = cursor.fetchone()['count']
            
            today = time.strftime('%Y-%m-%d')
            cursor.execute('SELECT * FROM daily_traffic_summary WHERE date = %s', (today,))
            traffic = cursor.fetchone()
            if traffic:
                summary['today_requests'] = traffic['total_requests']
                summary['today_visitors'] = traffic['unique_visitors']
            else:
                summary['today_requests'] = 0
                summary['today_visitors'] = 0
            
            return summary
        except Exception as e:
            raise Exception(f'获取系统概要统计失败: {str(e)}')
        finally:
            conn.close()
    
    def update_user_profile(self, user_id, email=None, password_hash=None):
        """更新用户个人信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if email:
                updates.append("email = %s")
                params.append(email)
            if password_hash:
                updates.append("password = %s")
                params.append(password_hash)
            
            if updates:
                # 使用当前时间的标准格式，而不是 Unix 时间戳
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(sql, params)
                conn.commit()
                return True
            return False
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新用户信息失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_recognition_history(self, user_id, limit=20, offset=0):
        """获取用户历史识别记录（排除已删除的）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM recognition_results WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )
            results = cursor.fetchall()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM recognition_results WHERE user_id = %s",
                (user_id,)
            )
            total = cursor.fetchone()['count']
            
            return results, total
        except Exception as e:
            raise Exception(f'获取历史识别记录失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_recognition_result(self, result_id, user_id):
        """删除识别记录（硬删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM recognition_results WHERE id = %s AND user_id = %s",
                (result_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除识别记录失败: {str(e)}')
        finally:
            conn.close()
    
    def create_album(self, user_id, name, category=None, cover_image=None, description=None):
        """创建相册"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO albums (user_id, name, category, cover_image, description, image_count, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (user_id, name, category, cover_image, description, 0)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建相册失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_albums(self, user_id, category=None):
        """获取用户相册列表（排除已软删除的）"""
        conn = self.get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 获取用户所有未删除的相册
            cursor.execute(
                "SELECT * FROM albums WHERE user_id = %s AND deleted_at IS NULL ORDER BY created_at DESC",
                (user_id,)
            )
            albums = cursor.fetchall()
            
            # 如果指定了 category，在 Python 中过滤
            if category:
                albums = [album for album in albums if category in album.get('name', '')]
            
            return albums
        except Exception as e:
            raise Exception(f'获取相册列表失败: {str(e)}')
        finally:
            conn.close()
    
    def get_album_by_id(self, album_id, user_id):
        """获取相册详情（排除已软删除的）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM albums WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (album_id, user_id)
            )
            return cursor.fetchone()
        except Exception as e:
            raise Exception(f'获取相册详情失败: {str(e)}')
        finally:
            conn.close()
    
    def update_album(self, album_id, user_id, name=None, description=None):
        """更新相册信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = %s")
                params.append(name)
            if description:
                updates.append("description = %s")
                params.append(description)
            
            if updates:
                updates.append("updated_at = %s")
                params.append(int(time.time()))
                params.append(album_id)
                params.append(user_id)
                
                sql = f"UPDATE albums SET {', '.join(updates)} WHERE id = %s AND user_id = %s"
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount > 0
            return False
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新相册失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_album(self, album_id, user_id):
        """删除相册（软删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 软删除：更新 deleted_at 字段
            now = int(time.time())
            cursor.execute(
                "UPDATE albums SET deleted_at = %s, updated_at = %s WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (now, now, album_id, user_id)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"[DB] 相册软删除成功: album_id={album_id}, user_id={user_id}")
                return True
            else:
                print(f"[DB] 相册软删除失败: album_id={album_id} 不存在或已被删除")
                return False
        except Exception as e:
            conn.rollback()
            print(f"[DB] 删除相册失败: {str(e)}")
            raise Exception(f'删除相册失败: {str(e)}')
        finally:
            conn.close()
    
    def add_image_to_album(self, album_id, user_id, image_path, flower_name=None, confidence=None, recognition_result_id=None):
        """添加图片到相册"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"[DB] 添加图片到相册: album_id={album_id}, user_id={user_id}, image_path={image_path}, flower_name={flower_name}, recognition_result_id={recognition_result_id}")
            
            # 从image_path提取image_name
            import os
            image_name = os.path.basename(image_path)
            image_description = f"{flower_name} - 识别置信度：{confidence:.2f}" if flower_name and confidence else ""
            
            # 1. 检查是否存在重复的识别结果
            if recognition_result_id:
                cursor.execute(
                    "SELECT id FROM album_images WHERE recognition_result_id = %s AND deleted_at IS NULL",
                    (recognition_result_id,)
                )
                if cursor.fetchone():
                    # 已存在，避免重复插入
                    print(f"[DB] 识别结果 {recognition_result_id} 已存在于相册中，跳过重复插入")
                    return None
            
            # 2. 确保有相册ID，如果没有则创建默认相册
            if not album_id:
                # 检查是否已有默认相册
                cursor.execute(
                    "SELECT id FROM albums WHERE user_id = %s AND name = '默认相册'",
                    (user_id,)
                )
                default_album = cursor.fetchone()
                
                if not default_album:
                    # 创建默认相册
                    now = int(time.time())
                    cursor.execute(
                        "INSERT INTO albums (user_id, name, category, cover_image, description, image_count, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (user_id, '默认相册', '默认', None, '默认相册', 0, now, now)
                    )
                    album_id = cursor.lastrowid
                    print(f"[DB] 创建默认相册成功，album_id={album_id}")
                else:
                    album_id = default_album['id']
                    print(f"[DB] 使用现有默认相册，album_id={album_id}")
            
            # 获取相册当前状态
            cursor.execute("SELECT name, image_count, cover_image FROM albums WHERE id = %s", (album_id,))
            album_before = cursor.fetchone()
            print(f"[DB] 相册状态(更新前): name={album_before['name']}, image_count={album_before['image_count']}, cover_image={album_before['cover_image']}")
            
            # 3. 插入图片到相册
            cursor.execute(
                "INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, recognition_result_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (album_id, user_id, image_path, image_name, image_description, recognition_result_id, int(time.time()))
            )
            image_id = cursor.lastrowid
            print(f"[DB] 图片插入成功: image_id={image_id}")
            
            # 4. 更新相册图片数量
            cursor.execute(
                "UPDATE albums SET image_count = image_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (album_id,)
            )
            print(f"[DB] 相册图片数量已更新: album_id={album_id}")
            
            # 5. 如果相册没有封面图，将当前图片设为封面
            cursor.execute(
                "SELECT cover_image FROM albums WHERE id = %s",
                (album_id,)
            )
            album = cursor.fetchone()
            if album and not album['cover_image']:
                cursor.execute(
                    "UPDATE albums SET cover_image = %s WHERE id = %s",
                    (image_path, album_id)
                )
                print(f"[DB] 更新相册封面: album_id={album_id}, cover_image={image_path}")
            else:
                print(f"[DB] 相册已有封面，不更新: cover_image={album['cover_image']}")
            
            # 获取相册更新后状态
            cursor.execute("SELECT image_count, cover_image FROM albums WHERE id = %s", (album_id,))
            album_after = cursor.fetchone()
            print(f"[DB] 相册状态(更新后): image_count={album_after['image_count']}, cover_image={album_after['cover_image']}")
            
            conn.commit()
            print(f"[DB] 添加图片到相册成功: image_id={image_id}")
            return image_id
        except Exception as e:
            conn.rollback()
            print(f"[DB] 添加图片到相册失败: {str(e)}")
            raise Exception(f'添加图片到相册失败: {str(e)}')
        finally:
            conn.close()
    
    def get_album_images(self, album_id, user_id, limit=50, offset=0):
        """获取相册中的图片（排除已删除的）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM album_images WHERE album_id = %s AND deleted_at IS NULL ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (album_id, limit, offset)
            )
            images = cursor.fetchall()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM album_images WHERE album_id = %s AND deleted_at IS NULL",
                (album_id,)
            )
            total = cursor.fetchone()['count']
            
            return images, total
        except Exception as e:
            raise Exception(f'获取相册图片失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_album_image(self, image_id, album_id, user_id):
        """删除相册中的图片（软删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取被删除图片的路径
            cursor.execute(
                "SELECT image_path FROM album_images WHERE id = %s AND album_id = %s",
                (image_id, album_id)
            )
            image = cursor.fetchone()
            deleted_image_path = image['image_path'] if image else None
            
            # 2. 软删除图片
            now = int(time.time())
            cursor.execute(
                "UPDATE album_images SET deleted_at = %s WHERE id = %s AND album_id = %s AND album_id IN (SELECT id FROM albums WHERE user_id = %s)",
                (now, image_id, album_id, user_id)
            )
            
            if cursor.rowcount > 0:
                # 3. 更新相册图片数量
                cursor.execute(
                    "UPDATE albums SET image_count = image_count - 1 WHERE id = %s",
                    (album_id,)
                )
                
                # 4. 如果被删除的是封面图，重新设置封面
                cursor.execute(
                    "SELECT cover_image FROM albums WHERE id = %s",
                    (album_id,)
                )
                album = cursor.fetchone()
                if album and album['cover_image'] == deleted_image_path:
                    # 查找相册中最早的一张图片作为新封面
                    cursor.execute(
                        "SELECT image_path FROM album_images WHERE album_id = %s AND deleted_at IS NULL ORDER BY created_at ASC LIMIT 1",
                        (album_id,)
                    )
                    new_cover = cursor.fetchone()
                    if new_cover:
                        cursor.execute(
                            "UPDATE albums SET cover_image = %s WHERE id = %s",
                            (new_cover['image_path'], album_id)
                        )
                        print(f"更新相册封面: album_id={album_id}, new_cover={new_cover['image_path']}")
                    else:
                        # 相册没有图片了，清空封面
                        cursor.execute(
                            "UPDATE albums SET cover_image = NULL, image_count = 0 WHERE id = %s",
                            (album_id,)
                        )
                        print(f"相册已空，清空封面: album_id={album_id}")
                
                conn.commit()
                return True
            return False
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除图片失败: {str(e)}')
        finally:
            conn.close()
    
    def get_album_categories(self, user_id):
        """获取用户相册的所有分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT DISTINCT category FROM albums WHERE user_id = %s ORDER BY category",
                (user_id,)
            )
            results = cursor.fetchall()
            return [row['category'] for row in results]
        except Exception as e:
            raise Exception(f'获取相册分类失败: {str(e)}')
        finally:
            conn.close()
    
    def create_feedback(self, user_id, title, content, feedback_type):
        """创建用户反馈"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time())
            cursor.execute(
                "INSERT INTO user_feedback (user_id, title, content, feedback_type, status, created_at, updated_at) VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
                (user_id, title, content, feedback_type, now, now)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建反馈失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_feedback(self, user_id, limit=20, offset=0):
        """获取用户反馈列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM user_feedback WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )
            results = cursor.fetchall()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM user_feedback WHERE user_id = %s",
                (user_id,)
            )
            total = cursor.fetchone()['count']
            
            return results, total
        except Exception as e:
            raise Exception(f'获取反馈列表失败: {str(e)}')
        finally:
            conn.close()
    
    def get_feedback_by_id(self, feedback_id, user_id):
        """获取反馈详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM user_feedback WHERE id = %s AND user_id = %s",
                (feedback_id, user_id)
            )
            return cursor.fetchone()
        except Exception as e:
            raise Exception(f'获取反馈详情失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_feedback(self, feedback_id, user_id):
        """删除反馈"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM user_feedback WHERE id = %s AND user_id = %s",
                (feedback_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除反馈失败: {str(e)}')
        finally:
            conn.close()
    
    def get_all_feedback(self, status=None, limit=50, offset=0):
        """获取所有反馈（管理员用）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute(
                    "SELECT f.*, u.username FROM user_feedback f JOIN users u ON f.user_id = u.id WHERE f.status = %s ORDER BY f.created_at DESC LIMIT %s OFFSET %s",
                    (status, limit, offset)
                )
            else:
                cursor.execute(
                    "SELECT f.*, u.username FROM user_feedback f JOIN users u ON f.user_id = u.id ORDER BY f.created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
            results = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM user_feedback")
            total = cursor.fetchone()['count']
            
            return results, total
        except Exception as e:
            raise Exception(f'获取所有反馈失败: {str(e)}')
        finally:
            conn.close()
    
    def respond_feedback(self, feedback_id, response):
        """回复反馈（管理员用）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time())
            cursor.execute(
                "UPDATE user_feedback SET response = %s, status = 'responded', updated_at = %s WHERE id = %s",
                (response, now, feedback_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'回复反馈失败: {str(e)}')
        finally:
            conn.close()
    
    def create_announcement(self, title, content, announcement_type, admin_id, admin_username):
        """创建公告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time())
            cursor.execute(
                "INSERT INTO announcements (title, content, announcement_type, is_active, admin_id, admin_username, created_at, updated_at) VALUES (%s, %s, %s, 1, %s, %s, %s, %s)",
                (title, content, announcement_type, admin_id, admin_username, now, now)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建公告失败: {str(e)}')
        finally:
            conn.close()
    
    def get_announcements(self, is_active=None, limit=20, offset=0):
        """获取公告列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if is_active is not None:
                cursor.execute(
                    "SELECT * FROM announcements WHERE is_active = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (is_active, limit, offset)
                )
            else:
                cursor.execute(
                    "SELECT * FROM announcements ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
            results = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as count FROM announcements")
            total = cursor.fetchone()['count']
            
            return results, total
        except Exception as e:
            raise Exception(f'获取公告列表失败: {str(e)}')
        finally:
            conn.close()
    
    def update_announcement(self, announcement_id, title, content, announcement_type, admin_id):
        """更新公告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time())
            cursor.execute(
                "UPDATE announcements SET title = %s, content = %s, announcement_type = %s, updated_at = %s WHERE id = %s AND admin_id = %s",
                (title, content, announcement_type, now, announcement_id, admin_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新公告失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_announcement(self, announcement_id, admin_id):
        """删除公告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE announcements SET is_active = 0 WHERE id = %s AND admin_id = %s",
                (announcement_id, admin_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'删除公告失败: {str(e)}')
        finally:
            conn.close()
    
    def move_to_recycle_bin(self, user_id, item_type, original_id, item_data=None):
        """将项目移入回收站"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = int(time.time())
            import json
            item_data_json = json.dumps(item_data) if item_data else None
            cursor.execute(
                "INSERT INTO recycle_bin (user_id, item_type, original_id, item_data, deleted_at) VALUES (%s, %s, %s, %s, %s)",
                (user_id, item_type, original_id, item_data_json, now)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise Exception(f'移入回收站失败: {str(e)}')
        finally:
            conn.close()
    
    def get_recycle_bin_items(self, user_id, item_type=None, limit=50, offset=0):
        """获取回收站项目列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            import json
            if item_type:
                cursor.execute(
                    "SELECT * FROM recycle_bin WHERE user_id = %s AND item_type = %s ORDER BY deleted_at DESC LIMIT %s OFFSET %s",
                    (user_id, item_type, limit, offset)
                )
            else:
                cursor.execute(
                    "SELECT * FROM recycle_bin WHERE user_id = %s ORDER BY deleted_at DESC LIMIT %s OFFSET %s",
                    (user_id, limit, offset)
                )
            results = cursor.fetchall()
            
            for item in results:
                if item.get('item_data'):
                    try:
                        item['item_data'] = json.loads(item['item_data'])
                    except:
                        pass
            
            cursor.execute("SELECT COUNT(*) as count FROM recycle_bin WHERE user_id = %s", (user_id,))
            total = cursor.fetchone()['count']
            
            return results, total
        except Exception as e:
            raise Exception(f'获取回收站项目失败: {str(e)}')
        finally:
            conn.close()
    
    def restore_from_recycle_bin(self, user_id, recycle_id):
        """从回收站恢复项目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM recycle_bin WHERE id = %s AND user_id = %s",
                (recycle_id, user_id)
            )
            item = cursor.fetchone()
            
            if not item:
                return False, "回收站项目不存在"
            
            item_type = item['item_type']
            original_id = item['original_id']
            item_data = item.get('item_data')
            
            if item_type == 'image':
                # 只有相册图片可以恢复，因为它有 deleted_at 字段
                cursor.execute(
                    "UPDATE album_images SET deleted_at = NULL WHERE id = %s",
                    (original_id,)
                )
            # 帖子和识别结果无法从回收站恢复，因为它们没有 deleted_at 字段
            
            cursor.execute(
                "DELETE FROM recycle_bin WHERE id = %s",
                (recycle_id,)
            )
            
            conn.commit()
            return True, f"已恢复{item_type}"
        except Exception as e:
            conn.rollback()
            raise Exception(f'恢复项目失败: {str(e)}')
        finally:
            conn.close()
    
    def permanently_delete(self, user_id, recycle_id):
        """永久删除回收站项目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM recycle_bin WHERE id = %s AND user_id = %s",
                (recycle_id, user_id)
            )
            item = cursor.fetchone()
            
            if not item:
                return False, "回收站项目不存在"
            
            item_type = item['item_type']
            original_id = item['original_id']
            
            if item_type == 'post':
                cursor.execute("DELETE FROM posts WHERE id = %s", (original_id,))
            elif item_type == 'image':
                cursor.execute("DELETE FROM album_images WHERE id = %s", (original_id,))
            elif item_type == 'recognition':
                cursor.execute("DELETE FROM recognition_results WHERE id = %s", (original_id,))
            
            cursor.execute(
                "DELETE FROM recycle_bin WHERE id = %s",
                (recycle_id,)
            )
            
            conn.commit()
            return True, f"已永久删除{item_type}"
        except Exception as e:
            conn.rollback()
            raise Exception(f'永久删除失败: {str(e)}')
        finally:
            conn.close()
    
    def empty_recycle_bin(self, user_id):
        """清空回收站"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM recycle_bin WHERE user_id = %s",
                (user_id,)
            )
            items = cursor.fetchall()
            
            for item in items:
                item_type = item['item_type']
                original_id = item['original_id']
                
                if item_type == 'post':
                    cursor.execute("DELETE FROM posts WHERE id = %s", (original_id,))
                elif item_type == 'image':
                    cursor.execute("DELETE FROM album_images WHERE id = %s", (original_id,))
                elif item_type == 'recognition':
                    cursor.execute("DELETE FROM recognition_results WHERE id = %s", (original_id,))
            
            cursor.execute("DELETE FROM recycle_bin WHERE user_id = %s", (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'清空回收站失败: {str(e)}')
        finally:
            conn.close()
    
    def generate_verification_code(self, length=6):
        """生成指定长度的数字验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def create_email_code(self, email, purpose, expire_seconds=300):
        """创建邮箱验证码记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使该邮箱之前的相同用途的验证码失效
            cursor.execute(
                "UPDATE email_codes SET is_used = 1 WHERE email = %s AND purpose = %s AND is_used = 0",
                (email, purpose)
            )
            
            # 生成新验证码
            code = self.generate_verification_code()
            expire_at = datetime.now() + timedelta(seconds=expire_seconds)
            
            # 打印验证码（仅用于测试）
            print(f"生成验证码: {code} 用于邮箱: {email} 用途: {purpose}")
            
            # 插入新验证码记录
            cursor.execute(
                "INSERT INTO email_codes (email, code, purpose, expire_at) VALUES (%s, %s, %s, %s)",
                (email, code, purpose, expire_at)
            )
            
            conn.commit()
            return code
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建验证码失败: {str(e)}')
        finally:
            conn.close()
    
    def verify_email_code(self, email, code, purpose):
        """验证邮箱验证码"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查找未使用且未过期的验证码
            cursor.execute(
                "SELECT * FROM email_codes WHERE email = %s AND code = %s AND purpose = %s AND is_used = 0 AND expire_at > %s",
                (email, code, purpose, datetime.now())
            )
            
            record = cursor.fetchone()
            if not record:
                return False
            
            # 标记验证码为已使用
            cursor.execute(
                "UPDATE email_codes SET is_used = 1 WHERE id = %s",
                (record['id'],)
            )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'验证验证码失败: {str(e)}')
        finally:
            conn.close()
    
    def check_email_rate_limit(self, email, purpose, limit_seconds=60):
        """检查发送验证码的频率限制"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查找最近指定时间内的验证码记录
            time_limit = datetime.now() - timedelta(seconds=limit_seconds)
            cursor.execute(
                "SELECT COUNT(*) as count FROM email_codes WHERE email = %s AND purpose = %s AND created_at > %s",
                (email, purpose, time_limit)
            )
            
            result = cursor.fetchone()
            return result['count'] > 0
        except Exception as e:
            raise Exception(f'检查频率限制失败: {str(e)}')
        finally:
            conn.close()
    
    def get_user_by_email(self, email):
        """根据邮箱获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise Exception(f'获取用户信息失败: {str(e)}')
        finally:
            conn.close()

# 创建全局数据库管理器实例
try:
    db_manager = SQLDatabaseManager()
except Exception as e:
    print(f"数据库初始化失败: {str(e)}")
    print("应用将以无数据库模式启动")
    db_manager = None

# 导出便捷函数
def create_user(username, email, password, role='user'):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_user(username, email, password, role)

def get_user_by_username(username):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_by_username(username)

def get_user_by_id(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_by_id(user_id)

def verify_password(stored_password_hash, provided_password):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.verify_password(stored_password_hash, provided_password)

def get_user_roles(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_roles(user_id)

def get_user_permissions(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_permissions(user_id)

def check_user_permission(user_id, permission_name):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.check_user_permission(user_id, permission_name)

def save_recognition_result(user_id, image_path, result, confidence, shoot_time=None, shoot_year=None, shoot_month=None, shoot_season=None, latitude=None, longitude=None, location_text=None, region_label=None, final_category=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.save_recognition_result(user_id, image_path, result, confidence, shoot_time, shoot_year, shoot_month, shoot_season, latitude, longitude, location_text, region_label, final_category)

def get_user_recognition_results(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_recognition_results(user_id)

def get_recognition_result(result_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_recognition_result(result_id)

# 帖子相关便捷函数
def create_post(user_id, content, image_url=None, topics=None, tags=None, source_type=None, source_id=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_post(user_id, content, image_url, topics, tags, source_type, source_id)

def get_posts(limit=20, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_posts(limit, offset)

def get_post_by_id(post_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_post_by_id(post_id)

def update_post(post_id, content, image_url=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.update_post(post_id, content, image_url)

def delete_post(post_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_post(post_id)

# 评论点赞相关便捷函数
def like_comment(comment_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.like_comment(comment_id, user_id)

def unlike_comment(comment_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.unlike_comment(comment_id, user_id)

def is_comment_liked(comment_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.is_comment_liked(comment_id, user_id)

# 评论相关便捷函数
def create_comment(post_id, user_id, content, parent_comment_id=None, reply_to_user_id=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_comment(post_id, user_id, content, parent_comment_id, reply_to_user_id)

def get_comments_by_post_id(post_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_comments_by_post_id(post_id)

def delete_comment(comment_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_comment(comment_id)

# 点赞相关便捷函数
def like_post(post_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.like_post(post_id, user_id)

def unlike_post(post_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.unlike_post(post_id, user_id)

def is_post_liked_by_user(post_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.is_post_liked_by_user(post_id, user_id)

# 关注相关便捷函数
def follow_user(follower_id, following_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.follow_user(follower_id, following_id)

def unfollow_user(follower_id, following_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.unfollow_user(follower_id, following_id)

def is_following(follower_id, following_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.is_following(follower_id, following_id)

def get_user_following(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_following(user_id)

def get_user_followers(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_followers(user_id)

def test_connection():
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.test_connection()

def create_system_log(log_level, module, message, user_id=None, username=None, ip_address=None, user_agent=None):
    if db_manager is None:
        return
    return db_manager.create_system_log(log_level, module, message, user_id, username, ip_address, user_agent)

def get_system_logs(limit=100, offset=0, log_level=None, module=None, start_time=None, end_time=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_system_logs(limit, offset, log_level, module, start_time, end_time)

def record_traffic(endpoint, method, ip_address=None, user_id=None, response_status=200, response_time=0):
    if db_manager is None:
        return
    return db_manager.record_traffic(endpoint, method, ip_address, user_id, response_status, response_time)

def get_traffic_stats(start_date=None, end_date=None, limit=100):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_traffic_stats(start_date, end_date, limit)

def get_traffic_by_endpoint(start_date=None, end_date=None, limit=20):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_traffic_by_endpoint(start_date, end_date, limit)

def record_server_status(metric_name, metric_value, unit=None, status='normal'):
    if db_manager is None:
        return
    return db_manager.record_server_status(metric_name, metric_value, unit, status)

def get_server_status(metric_name=None, limit=100):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_server_status(metric_name, limit)

def get_latest_server_metrics():
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_latest_server_metrics()

def record_admin_operation(admin_id, admin_username, operation_type, target_type=None, target_id=None, description=None, ip_address=None):
    if db_manager is None:
        return
    return db_manager.record_admin_operation(admin_id, admin_username, operation_type, target_type, target_id, description, ip_address)

def get_admin_operations(admin_id=None, operation_type=None, limit=100, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_admin_operations(admin_id, operation_type, limit, offset)

def get_all_admins():
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_all_admins()

def update_user_role(user_id, role_name):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.update_user_role(user_id, role_name)

def get_system_summary():
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_system_summary()

def update_user_profile(user_id, email=None, password_hash=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.update_user_profile(user_id, email, password_hash)

def create_email_code(email, purpose, expire_seconds=300):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_email_code(email, purpose, expire_seconds)

def verify_email_code(email, code, purpose):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.verify_email_code(email, code, purpose)

def check_email_rate_limit(email, purpose, limit_seconds=60):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.check_email_rate_limit(email, purpose, limit_seconds)

def get_user_by_email(email):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_by_email(email)

def get_user_recognition_history(user_id, limit=20, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_recognition_history(user_id, limit, offset)

def delete_recognition_result(result_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_recognition_result(result_id, user_id)

def create_album(user_id, name, category, cover_image=None, description=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_album(user_id, name, category, cover_image, description)

def get_user_albums(user_id, category=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_albums(user_id, category)

def get_album_by_id(album_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_album_by_id(album_id, user_id)

def update_album(album_id, user_id, name=None, description=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.update_album(album_id, user_id, name, description)

def delete_album(album_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_album(album_id, user_id)

def add_image_to_album(album_id, user_id, image_path, flower_name=None, confidence=None, recognition_result_id=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.add_image_to_album(album_id, user_id, image_path, flower_name, confidence, recognition_result_id)

def get_album_images(album_id, user_id, limit=50, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_album_images(album_id, user_id, limit, offset)

def delete_album_image(image_id, album_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_album_image(image_id, album_id, user_id)

def get_album_categories(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_album_categories(user_id)

def create_feedback(user_id, title, content, feedback_type):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_feedback(user_id, title, content, feedback_type)

def get_user_feedback(user_id, limit=20, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_user_feedback(user_id, limit, offset)

def get_feedback_by_id(feedback_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_feedback_by_id(feedback_id, user_id)

def delete_feedback(feedback_id, user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_feedback(feedback_id, user_id)

def get_all_feedback(status=None, limit=50, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_all_feedback(status, limit, offset)

def respond_feedback(feedback_id, response):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.respond_feedback(feedback_id, response)

def create_announcement(title, content, announcement_type, admin_id, admin_username):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.create_announcement(title, content, announcement_type, admin_id, admin_username)

def get_announcements(is_active=None, limit=20, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_announcements(is_active, limit, offset)

def update_announcement(announcement_id, title, content, announcement_type, admin_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.update_announcement(announcement_id, title, content, announcement_type, admin_id)

def delete_announcement(announcement_id, admin_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.delete_announcement(announcement_id, admin_id)

def move_to_recycle_bin(user_id, item_type, original_id, item_data=None):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.move_to_recycle_bin(user_id, item_type, original_id, item_data)

def get_recycle_bin_items(user_id, item_type=None, limit=50, offset=0):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.get_recycle_bin_items(user_id, item_type, limit, offset)

def restore_from_recycle_bin(user_id, recycle_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.restore_from_recycle_bin(user_id, recycle_id)

def permanently_delete(user_id, recycle_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.permanently_delete(user_id, recycle_id)

def empty_recycle_bin(user_id):
    if db_manager is None:
        raise Exception("数据库未初始化")
    return db_manager.empty_recycle_bin(user_id)

if __name__ == '__main__':
    # 测试数据库连接
    if test_connection():
        print('数据库连接成功！')
    else:
        print('数据库连接失败！')
