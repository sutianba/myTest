import sqlite3
import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

# 数据库路径
DB_PATH = 'flower_recognition.db'
SQL_DIR = 'flower_frontend'

# SQL文件路径
SCHEMA_SQL = os.path.join(SQL_DIR, 'database.sql')
BACKUP_SQL = os.path.join(SQL_DIR, 'database_backup.sql')

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
        password_hash = generate_password_hash(password)
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
