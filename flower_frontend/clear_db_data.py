#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""清空数据库数据，保留表结构"""

from db_config import get_db_connection

def clear_database_data():
    """清空数据库中的所有数据，保留表结构"""
    print("开始清空数据库数据...")
    
    try:
        # 连接到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # 禁用外键约束
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 对每个表执行TRUNCATE TABLE
        for table in tables:
            table_name = list(table.values())[0]
            try:
                cursor.execute(f"TRUNCATE TABLE `{table_name}`")
                print(f"已清空表: {table_name}")
            except Exception as e:
                print(f"清空表 {table_name} 时出错: {str(e)}")
        
        # 重新启用外键约束
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 提交事务
        conn.commit()
        
        print("\n数据库数据清空完成！")
        
    except Exception as e:
        print(f"操作失败: {type(e).__name__}: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_database_data()
