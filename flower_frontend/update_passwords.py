#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import sqlite3
import time
from werkzeug.security import generate_password_hash

# 连接到数据库
conn = sqlite3.connect('flower_recognition.db')
cursor = conn.cursor()

# 获取所有用户
cursor.execute('SELECT id, username FROM users')
users = cursor.fetchall()

# 更新所有用户的密码哈希为pbkdf2格式
for user_id, username in users:
    # 为每个用户生成默认密码的pbkdf2哈希
    password = 'password123'  # 默认密码
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    current_time = int(time.time())
    
    cursor.execute('''
    UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?
    ''', (password_hash, current_time, user_id))
    print(f'更新用户 {username} 的密码哈希')

conn.commit()
conn.close()

print('所有用户密码哈希已更新为pbkdf2格式')
