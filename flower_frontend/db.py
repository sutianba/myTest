import sqlite3
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

# 数据库路径
DB_PATH = 'flower_recognition.db'

# SQL文件路径
SCHEMA_SQL = 'database.sql'
BACKUP_SQL = 'database_backup.sql'

class SQLDatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(self.db_path):
            self.initialize_from_sql(SCHEMA_SQL)
    
    def initialize_from_sql(self, sql_file):
        """从SQL文件初始化数据库"""
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 执行SQL语句
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()
        
        print(f"数据库已从 {sql_file} 初始化完成")
    
    def execute_sql_file(self, sql_file):
        """执行SQL文件"""
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.executescript(sql_content)
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
        conn = sqlite3.connect(self.db_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        conn.close()
        print(f"数据库已导出到 {output_file}")
        return True
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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

if __name__ == '__main__':
    # 测试数据库连接
    if test_connection():
        print('数据库连接成功！')
    else:
        print('数据库连接失败！')
    
    # 导出当前数据库为SQL文件
    db_manager.export_to_sql('flower_frontend/current_database.sql')
    print('数据库已导出为SQL文件')
