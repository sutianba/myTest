#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""初始化个人账户系统数据库"""

import os
import sys

# 添加当前目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from db_config import get_db_connection

def init_account_system():
    """初始化个人账户系统数据库"""
    try:
        print("[调试] 开始执行init_account_system函数")
        
        # 连接到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 读取SQL文件
        sql_file = os.path.join(BASE_DIR, 'account_system.sql')
        
        if not os.path.exists(sql_file):
            print(f"SQL文件不存在: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # 执行每个SQL语句
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"执行SQL语句成功: {statement[:50]}...")
                except Exception as e:
                    # 忽略已存在表的错误
                    if "already exists" not in str(e):
                        print(f"执行SQL语句时出错: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("个人账户系统数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"初始化个人账户系统数据库失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    init_account_system()
