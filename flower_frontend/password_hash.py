#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""密码哈希处理模块"""

import bcrypt

def hash_password(password):
    """对密码进行bcrypt哈希处理"""
    try:
        # 生成盐值并哈希密码
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    except Exception as e:
        print(f"密码哈希失败: {str(e)}")
        return None

def verify_password(password, password_hash):
    """验证密码是否正确"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"密码验证失败: {str(e)}")
        return False
