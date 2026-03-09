#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""安全防护模块 - 登录失败限制、频率限制等"""

import time
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# 配置参数
MAX_LOGIN_FAILURES = 5  # 最大登录失败次数
LOGIN_FAILURE_WINDOW = 300  # 失败窗口时间（秒），5分钟
ACCOUNT_LOCK_DURATION = 300  # 账号锁定时长（秒），5分钟
LOGIN_FAILURE_COOLDOWN = 60  # 登录失败冷却时间（秒）

# 登录失败记录（内存缓存）
login_failures: Dict[str, list] = {}
ip_login_failures: Dict[str, list] = {}

# 账号锁定记录
account_locks: Dict[str, float] = {}
ip_locks: Dict[str, float] = {}


def get_db_connection():
    """获取数据库连接"""
    import sqlite3
    conn = sqlite3.connect('flower_recognition.db')
    conn.row_factory = sqlite3.Row
    return conn


def record_login_failure(username: str, ip_address: str, failure_reason: str = '密码错误') -> bool:
    """记录登录失败"""
    current_time = time.time()
    
    # 记录到内存
    if username not in login_failures:
        login_failures[username] = []
    login_failures[username].append(current_time)
    
    if ip_address not in ip_login_failures:
        ip_login_failures[ip_address] = []
    ip_login_failures[ip_address].append(current_time)
    
    # 记录到数据库
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO login_attempts (username, ip_address, success, failure_reason) 
               VALUES (?, ?, 0, ?)""",
            (username, ip_address, failure_reason)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"记录登录失败到数据库失败: {e}")
    
    return True


def record_login_success(username: str, ip_address: str):
    """记录登录成功"""
    # 清除失败记录
    if username in login_failures:
        del login_failures[username]
    if ip_address in ip_login_failures:
        del ip_login_failures[ip_address]
    
    # 清除锁定
    if username in account_locks:
        del account_locks[username]
    if ip_address in ip_locks:
        del ip_locks[ip_address]
    
    # 记录到数据库
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO login_attempts (username, ip_address, success, failure_reason) 
               VALUES (?, ?, 1, NULL)""",
            (username, ip_address)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"记录登录成功到数据库失败: {e}")
    
    return True


def check_login_failure_limit(username: str, ip_address: str) -> Tuple[bool, Optional[str]]:
    """检查登录失败限制"""
    current_time = time.time()
    
    # 检查账号是否被锁定
    if username in account_locks:
        lock_time = account_locks[username]
        if current_time - lock_time < ACCOUNT_LOCK_DURATION:
            remaining = int(ACCOUNT_LOCK_DURATION - (current_time - lock_time))
            return False, f'账号已被锁定，请{remaining}秒后再试'
        else:
            del account_locks[username]
    
    # 检查IP是否被锁定
    if ip_address in ip_locks:
        lock_time = ip_locks[ip_address]
        if current_time - lock_time < ACCOUNT_LOCK_DURATION:
            remaining = int(ACCOUNT_LOCK_DURATION - (current_time - lock_time))
            return False, f'IP已被锁定，请{remaining}秒后再试'
        else:
            del ip_locks[ip_address]
    
    # 检查账号失败次数
    if username in login_failures:
        failures = login_failures[username]
        # 清理过期记录
        failures = [t for t in failures if current_time - t < LOGIN_FAILURE_WINDOW]
        login_failures[username] = failures
        
        if len(failures) >= MAX_LOGIN_FAILURES:
            account_locks[username] = current_time
            return False, f'登录失败次数过多，账号已被锁定{ACCOUNT_LOCK_DURATION}秒'
    
    # 检查IP失败次数
    if ip_address in ip_login_failures:
        failures = ip_login_failures[ip_address]
        # 清理过期记录
        failures = [t for t in failures if current_time - t < LOGIN_FAILURE_WINDOW]
        ip_login_failures[ip_address] = failures
        
        if len(failures) >= MAX_LOGIN_FAILURES * 2:
            ip_locks[ip_address] = current_time
            return False, f'IP登录失败次数过多，已被锁定{ACCOUNT_LOCK_DURATION}秒'
    
    return True, None


def check_login_cooldown(username: str, ip_address: str) -> Tuple[bool, Optional[str]]:
    """检查登录冷却时间"""
    current_time = time.time()
    
    # 检查账号冷却时间
    if username in login_failures:
        last_failure = login_failures[username][-1]
        if current_time - last_failure < LOGIN_FAILURE_COOLDOWN:
            remaining = int(LOGIN_FAILURE_COOLDOWN - (current_time - last_failure))
            return False, f'登录过于频繁，请{remaining}秒后再试'
    
    # 检查IP冷却时间
    if ip_address in ip_login_failures:
        last_failure = ip_login_failures[ip_address][-1]
        if current_time - last_failure < LOGIN_FAILURE_COOLDOWN:
            remaining = int(LOGIN_FAILURE_COOLDOWN - (current_time - last_failure))
            return False, f'登录过于频繁，请{remaining}秒后再试'
    
    return True, None


def get_login_failures_count(username: str, ip_address: str) -> Dict[str, int]:
    """获取登录失败次数"""
    current_time = time.time()
    
    username_count = 0
    if username in login_failures:
        failures = login_failures[username]
        username_count = len([t for t in failures if current_time - t < LOGIN_FAILURE_WINDOW])
    
    ip_count = 0
    if ip_address in ip_login_failures:
        failures = ip_login_failures[ip_address]
        ip_count = len([t for t in failures if current_time - t < LOGIN_FAILURE_WINDOW])
    
    return {
        'username': username_count,
        'ip': ip_count,
        'max_allowed': MAX_LOGIN_FAILURES
    }


def clear_login_failures(username: str, ip_address: str):
    """清除登录失败记录"""
    if username in login_failures:
        del login_failures[username]
    if ip_address in ip_login_failures:
        del ip_login_failures[ip_address]
    if username in account_locks:
        del account_locks[username]
    if ip_address in ip_locks:
        del ip_locks[ip_address]
