#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
检查数据库中的用户表，查询特定用户
"""

import pymysql

# 数据库连接参数
HOST = 'localhost'
USER = 'root'
PASSWORD = '20031221'
DATABASE = 'flower_recognition'

# 连接数据库
try:
    connection = pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset='utf8mb4'
    )
    print("成功连接到数据库")
    
    # 创建游标
    cursor = connection.cursor()
    
    # 查询 testuser_999999 用户
    query = "SELECT id, username, email FROM users WHERE username = 'testuser_999999'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    print("\ntestuser_999999 用户：")
    print("ID	用户名		邮箱")
    print("=" * 50)
    if user:
        user_id, username, email = user
        print(f"{user_id}	{username}		{email}")
    else:
        print("未找到 testuser_999999 用户")
    
    # 查询所有用户
    query = "SELECT id, username, email FROM users ORDER BY id DESC LIMIT 10"
    cursor.execute(query)
    users = cursor.fetchall()
    
    print("\n最近10个用户：")
    print("ID	用户名		邮箱")
    print("=" * 50)
    for user in users:
        user_id, username, email = user
        print(f"{user_id}	{username}		{email}")
    
    # 关闭游标和连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"数据库连接失败: {e}")
