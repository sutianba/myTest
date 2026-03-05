import time
import os
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'flower_recognition')

# SQL文件路径
SCHEMA_SQL = 'flower_recognition.sql'

class SQLDatabaseManager:
    def __init__(self, db_host=DB_HOST, db_port=DB_PORT, db_user=DB_USER, db_password=DB_PASSWORD, db_name=DB_NAME):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.ensure_database_exists()
    
    def get_connection(self):
        """获取数据库连接"""
        if not MYSQL_AVAILABLE:
            raise ImportError("PyMySQL未安装，请运行: pip install pymysql")
        
        conn = pymysql.connect(
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    
    def ensure_database_exists(self):
        """确保数据库存在，从SQL文件初始化"""
        if not MYSQL_AVAILABLE:
            raise ImportError("PyMySQL未安装，请运行: pip install pymysql")
        
        try:
            # 先连接到mysql系统数据库
            conn = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (self.db_name,))
            result = cursor.fetchone()
            
            if not result:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE `{self.db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {self.db_name} 创建成功")
            
            cursor.close()
            conn.close()
            
            # 连接到指定数据库
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 执行SQL文件初始化
            if os.path.exists(SCHEMA_SQL):
                with open(SCHEMA_SQL, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 分割SQL语句
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            # 忽略已存在表的错误
                            if "already exists" not in str(e):
                                print(f"执行SQL语句时出错: {str(e)}")
                
                conn.commit()
                conn.close()
                print(f"数据库已从 {SCHEMA_SQL} 初始化完成")
            else:
                print(f"SQL文件不存在: {SCHEMA_SQL}")
                
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            raise
    
    def delete_database(self):
        """删除数据库"""
        if not MYSQL_AVAILABLE:
            raise ImportError("PyMySQL未安装，请运行: pip install pymysql")
        
        try:
            conn = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS `{self.db_name}`")
            conn.commit()
            conn.close()
            print(f"数据库 {self.db_name} 已删除")
            return True
        except Exception as e:
            print(f"删除数据库失败: {str(e)}")
            return False
    
    def execute_sql_file(self, sql_file):
        """执行SQL文件"""
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            conn.commit()
            print(f"SQL文件 {sql_file} 执行成功")
        except Exception as e:
            conn.rollback()
            raise Exception(f"执行SQL文件失败: {str(e)}")
        finally:
            conn.close()
