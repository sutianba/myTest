import sqlite3
import time
from werkzeug.security import generate_password_hash, check_password_hash

# 数据库路径
DB_PATH = 'flower_recognition.db'

# 数据库连接上下文管理器
class DatabaseConnection:
    def __enter__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row  # 启用字典式游标
        self.cursor = self.conn.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

# 用户相关操作
def create_user(username, email, password):
    """创建新用户"""
    password_hash = generate_password_hash(password)
    current_time = int(time.time())
    
    try:
        with DatabaseConnection() as cursor:
            # 插入用户数据
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, current_time, current_time))
            
            # 获取新创建的用户ID
            user_id = cursor.lastrowid
            
            # 为新用户分配默认角色（user）
            cursor.execute('SELECT id FROM roles WHERE name = ?', ('user',))
            role_id = cursor.fetchone()['id']
            
            cursor.execute('''
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
            ''', (user_id, role_id))
            
            return user_id
    except sqlite3.IntegrityError:
        raise ValueError('用户名或邮箱已存在')
    except Exception as e:
        raise Exception(f'创建用户失败: {str(e)}')

def get_user_by_username(username):
    """根据用户名获取用户信息"""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        raise Exception(f'获取用户信息失败: {str(e)}')

def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        raise Exception(f'获取用户信息失败: {str(e)}')

def verify_password(stored_password_hash, provided_password):
    """验证密码"""
    return check_password_hash(stored_password_hash, provided_password)

# 角色和权限相关操作
def get_user_roles(user_id):
    """获取用户的所有角色"""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('''
            SELECT r.* FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
            ''', (user_id,))
            roles = cursor.fetchall()
            return [dict(role) for role in roles]
    except Exception as e:
        raise Exception(f'获取用户角色失败: {str(e)}')

def get_user_permissions(user_id):
    """获取用户的所有权限"""
    try:
        with DatabaseConnection() as cursor:
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

def check_user_permission(user_id, permission_name):
    """检查用户是否有指定权限"""
    try:
        with DatabaseConnection() as cursor:
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

# 花卉识别结果相关操作
def save_recognition_result(user_id, image_path, result, confidence):
    """保存花卉识别结果"""
    current_time = int(time.time())
    
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('''
            INSERT INTO recognition_results (user_id, image_path, result, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, image_path, result, confidence, current_time))
            return cursor.lastrowid
    except Exception as e:
        raise Exception(f'保存识别结果失败: {str(e)}')

def get_user_recognition_results(user_id):
    """获取用户的识别结果"""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('''
            SELECT * FROM recognition_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            ''', (user_id,))
            results = cursor.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        raise Exception(f'获取识别结果失败: {str(e)}')

# 初始化数据库连接测试
def test_connection():
    """测试数据库连接"""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute('SELECT 1')
            return True
    except Exception as e:
        print(f'数据库连接测试失败: {str(e)}')
        return False

if __name__ == '__main__':
    # 测试数据库连接
    if test_connection():
        print('数据库连接成功！')
    else:
        print('数据库连接失败！')
