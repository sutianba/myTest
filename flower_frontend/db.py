import pymysql
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'flower_recognition',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# SQL文件路径
SCHEMA_SQL = 'flower_recognition.sql'
BACKUP_SQL = 'database_backup.sql'

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
                    cursor.execute(statement)
            conn.commit()
            print(f"数据库已从 {sql_file} 初始化完成")
        except Exception as e:
            conn.rollback()
            print(f"初始化数据库失败: {str(e)}")
            raise
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
    def create_user(self, username, email, password):
        """创建新用户"""
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, current_time, current_time))
            
            user_id = cursor.lastrowid
            
            cursor.execute('SELECT id FROM roles WHERE name = ?', ('user',))
            role_id = cursor.fetchone()['id']
            
            cursor.execute('''
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
            ''', (user_id, role_id))
            
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            conn.rollback()
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
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
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
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
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
            WHERE ur.user_id = ?
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
            WHERE ur.user_id = ?
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
            WHERE ur.user_id = ? AND p.name = ?
            ''', (user_id, permission_name))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            raise Exception(f'检查用户权限失败: {str(e)}')
        finally:
            conn.close()
    
    # 花卉识别结果相关操作
    def save_recognition_result(self, user_id, image_path, result, confidence):
        """保存花卉识别结果"""
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO recognition_results (user_id, image_path, result, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, image_path, result, confidence, current_time))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
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
            WHERE user_id = ?
            ORDER BY created_at DESC
            ''', (user_id,))
            results = cursor.fetchall()
            return [dict(result) for result in results]
        except Exception as e:
            raise Exception(f'获取识别结果失败: {str(e)}')
        finally:
            conn.close()
    
    # 帖子相关操作
    def create_post(self, user_id, content, image_url=None):
        """创建新帖子"""
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO posts (user_id, content, image_url, likes_count, comments_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, content, image_url, 0, 0, current_time, current_time))
            
            post_id = cursor.lastrowid
            conn.commit()
            return post_id
        except Exception as e:
            conn.rollback()
            raise Exception(f'创建帖子失败: {str(e)}')
        finally:
            conn.close()
    
    def get_posts(self, limit=20, offset=0):
        """获取帖子列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT p.*, u.username FROM posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
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
            WHERE p.id = ?
            ''', (post_id,))
            post = cursor.fetchone()
            return dict(post) if post else None
        except Exception as e:
            raise Exception(f'获取帖子详情失败: {str(e)}')
        finally:
            conn.close()
    
    def update_post(self, post_id, content, image_url=None):
        """更新帖子"""
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE posts
            SET content = ?, image_url = ?, updated_at = ?
            WHERE id = ?
            ''', (content, image_url, current_time, post_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新帖子失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_post(self, post_id):
        """删除帖子"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
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
            WHERE id = ?
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
            WHERE id = ?
            ''', (post_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f'更新评论数失败: {str(e)}')
        finally:
            conn.close()
    
    # 评论相关操作
    def create_comment(self, post_id, user_id, content):
        """创建评论"""
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建评论
            cursor.execute('''
            INSERT INTO comments (post_id, user_id, content, created_at)
            VALUES (?, ?, ?, ?)
            ''', (post_id, user_id, content, current_time))
            
            # 增加帖子评论数
            cursor.execute('''
            UPDATE posts
            SET comments_count = comments_count + 1
            WHERE id = ?
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
            cursor.execute('''
            SELECT c.*, u.username FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
            ''', (post_id,))
            comments = cursor.fetchall()
            return [dict(comment) for comment in comments]
        except Exception as e:
            raise Exception(f'获取评论列表失败: {str(e)}')
        finally:
            conn.close()
    
    def delete_comment(self, comment_id):
        """删除评论"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 先获取评论信息以更新帖子评论数
            cursor.execute('SELECT post_id FROM comments WHERE id = ?', (comment_id,))
            comment = cursor.fetchone()
            if not comment:
                return False
            
            post_id = comment['post_id']
            
            # 删除评论
            cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
            
            # 减少帖子评论数
            cursor.execute('''
            UPDATE posts
            SET comments_count = MAX(0, comments_count - 1)
            WHERE id = ?
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
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已经点赞
            cursor.execute('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
            if cursor.fetchone():
                return False  # 已经点赞过
            
            # 创建点赞记录
            cursor.execute('''
            INSERT INTO likes (post_id, user_id, created_at)
            VALUES (?, ?, ?)
            ''', (post_id, user_id, current_time))
            
            # 增加帖子点赞数
            cursor.execute('''
            UPDATE posts
            SET likes_count = likes_count + 1
            WHERE id = ?
            ''', (post_id,))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
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
            cursor.execute('DELETE FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
            
            if cursor.rowcount > 0:
                # 减少帖子点赞数
                cursor.execute('''
                UPDATE posts
                SET likes_count = MAX(0, likes_count - 1)
                WHERE id = ?
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
            cursor.execute('SELECT id FROM likes WHERE post_id = ? AND user_id = ?', (post_id, user_id))
            return cursor.fetchone() is not None
        except Exception as e:
            raise Exception(f'检查点赞状态失败: {str(e)}')
        finally:
            conn.close()
    
    # 关注相关操作
    def follow_user(self, follower_id, following_id):
        """关注用户"""
        current_time = int(time.time())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已经关注
            cursor.execute('SELECT id FROM follows WHERE follower_id = ? AND following_id = ?', (follower_id, following_id))
            if cursor.fetchone():
                return False  # 已经关注过
            
            # 创建关注记录
            cursor.execute('''
            INSERT INTO follows (follower_id, following_id, created_at)
            VALUES (?, ?, ?)
            ''', (follower_id, following_id, current_time))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
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
            cursor.execute('DELETE FROM follows WHERE follower_id = ? AND following_id = ?', (follower_id, following_id))
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
            cursor.execute('SELECT id FROM follows WHERE follower_id = ? AND following_id = ?', (follower_id, following_id))
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
            WHERE f.follower_id = ?
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
            WHERE f.following_id = ?
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                query += ' AND log_level = ?'
                params.append(log_level)
            if module:
                query += ' AND module = ?'
                params.append(module)
            if start_time:
                query += ' AND created_at >= ?'
                params.append(start_time)
            if end_time:
                query += ' AND created_at <= ?'
                params.append(end_time)
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            WHERE date = ?
            ''', (date_str,))
            
            result = cursor.fetchone()
            current_time = int(time.time())
            
            cursor.execute('''
            INSERT OR REPLACE INTO daily_traffic_summary (date, total_requests, unique_visitors, avg_response_time, error_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
                query += ' AND date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY date DESC LIMIT ?'
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
                query += ' AND date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            query += ' GROUP BY endpoint, method ORDER BY request_count DESC LIMIT ?'
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
            VALUES (?, ?, ?, ?, ?)
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
                WHERE metric_name = ?
                ORDER BY created_at DESC LIMIT ?
                ''', (metric_name, limit))
            else:
                cursor.execute('''
                SELECT * FROM server_status 
                ORDER BY created_at DESC LIMIT ?
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                query += ' AND admin_id = ?'
                params.append(admin_id)
            if operation_type:
                query += ' AND operation_type = ?'
                params.append(operation_type)
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
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
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role = cursor.fetchone()
            
            if not role:
                raise Exception(f'角色不存在: {role_name}')
            
            role_id = role['id']
            
            cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
            
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
            
            cursor.execute('SELECT COUNT(*) as count FROM system_logs WHERE created_at > ?', (int(time.time()) - 86400,))
            summary['today_logs'] = cursor.fetchone()['count']
            
            today = time.strftime('%Y-%m-%d')
            cursor.execute('SELECT * FROM daily_traffic_summary WHERE date = ?', (today,))
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

# 创建全局数据库管理器实例
db_manager = SQLDatabaseManager()

# 导出便捷函数
def create_user(username, email, password):
    return db_manager.create_user(username, email, password)

def get_user_by_username(username):
    return db_manager.get_user_by_username(username)

def get_user_by_id(user_id):
    return db_manager.get_user_by_id(user_id)

def verify_password(stored_password_hash, provided_password):
    return db_manager.verify_password(stored_password_hash, provided_password)

def get_user_roles(user_id):
    return db_manager.get_user_roles(user_id)

def get_user_permissions(user_id):
    return db_manager.get_user_permissions(user_id)

def check_user_permission(user_id, permission_name):
    return db_manager.check_user_permission(user_id, permission_name)

def save_recognition_result(user_id, image_path, result, confidence):
    return db_manager.save_recognition_result(user_id, image_path, result, confidence)

def get_user_recognition_results(user_id):
    return db_manager.get_user_recognition_results(user_id)

# 帖子相关便捷函数
def create_post(user_id, content, image_url=None):
    return db_manager.create_post(user_id, content, image_url)

def get_posts(limit=20, offset=0):
    return db_manager.get_posts(limit, offset)

def get_post_by_id(post_id):
    return db_manager.get_post_by_id(post_id)

def update_post(post_id, content, image_url=None):
    return db_manager.update_post(post_id, content, image_url)

def delete_post(post_id):
    return db_manager.delete_post(post_id)

# 评论相关便捷函数
def create_comment(post_id, user_id, content):
    return db_manager.create_comment(post_id, user_id, content)

def get_comments_by_post_id(post_id):
    return db_manager.get_comments_by_post_id(post_id)

def delete_comment(comment_id):
    return db_manager.delete_comment(comment_id)

# 点赞相关便捷函数
def like_post(post_id, user_id):
    return db_manager.like_post(post_id, user_id)

def unlike_post(post_id, user_id):
    return db_manager.unlike_post(post_id, user_id)

def is_post_liked_by_user(post_id, user_id):
    return db_manager.is_post_liked_by_user(post_id, user_id)

# 关注相关便捷函数
def follow_user(follower_id, following_id):
    return db_manager.follow_user(follower_id, following_id)

def unfollow_user(follower_id, following_id):
    return db_manager.unfollow_user(follower_id, following_id)

def is_following(follower_id, following_id):
    return db_manager.is_following(follower_id, following_id)

def get_user_following(user_id):
    return db_manager.get_user_following(user_id)

def get_user_followers(user_id):
    return db_manager.get_user_followers(user_id)

def test_connection():
    return db_manager.test_connection()

def create_system_log(log_level, module, message, user_id=None, username=None, ip_address=None, user_agent=None):
    return db_manager.create_system_log(log_level, module, message, user_id, username, ip_address, user_agent)

def get_system_logs(limit=100, offset=0, log_level=None, module=None, start_time=None, end_time=None):
    return db_manager.get_system_logs(limit, offset, log_level, module, start_time, end_time)

def record_traffic(endpoint, method, ip_address=None, user_id=None, response_status=200, response_time=0):
    return db_manager.record_traffic(endpoint, method, ip_address, user_id, response_status, response_time)

def get_traffic_stats(start_date=None, end_date=None, limit=100):
    return db_manager.get_traffic_stats(start_date, end_date, limit)

def get_traffic_by_endpoint(start_date=None, end_date=None, limit=20):
    return db_manager.get_traffic_by_endpoint(start_date, end_date, limit)

def record_server_status(metric_name, metric_value, unit=None, status='normal'):
    return db_manager.record_server_status(metric_name, metric_value, unit, status)

def get_server_status(metric_name=None, limit=100):
    return db_manager.get_server_status(metric_name, limit)

def get_latest_server_metrics():
    return db_manager.get_latest_server_metrics()

def record_admin_operation(admin_id, admin_username, operation_type, target_type=None, target_id=None, description=None, ip_address=None):
    return db_manager.record_admin_operation(admin_id, admin_username, operation_type, target_type, target_id, description, ip_address)

def get_admin_operations(admin_id=None, operation_type=None, limit=100, offset=0):
    return db_manager.get_admin_operations(admin_id, operation_type, limit, offset)

def get_all_admins():
    return db_manager.get_all_admins()

def update_user_role(user_id, role_name):
    return db_manager.update_user_role(user_id, role_name)

def get_system_summary():
    return db_manager.get_system_summary()

if __name__ == '__main__':
    # 测试数据库连接
    if test_connection():
        print('数据库连接成功！')
    else:
        print('数据库连接失败！')
    
    # 导出当前数据库为SQL文件
    db_manager.export_to_sql('flower_frontend/current_database.sql')
    print('数据库已导出为SQL文件')
    
    # 删除数据库文件（只保留SQL文件）
    db_manager.delete_database()
    print('数据库文件已删除，只保留SQL文件作为数据源')
