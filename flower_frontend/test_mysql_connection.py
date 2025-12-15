#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pymysql
import traceback

# 测试不同的密码组合
passwords_to_try = ['', 'password', 'root', '123456', 'admin', 'mysql']

def test_mysql_connection(password):
    try:
        print(f"尝试使用密码: '{password}'")
        
        # 连接配置
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': password,
            'charset': 'utf8mb4'
        }
        
        # 尝试连接
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        
        # 获取MySQL版本信息
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ 连接成功! MySQL版本: {version[0]}")
        
        # 关闭连接
        cursor.close()
        connection.close()
        
        return True
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            print(f"✗ 连接失败: 用户名或密码错误")
        elif error_code == 2003:
            print(f"✗ 连接失败: 无法连接到MySQL服务器")
        else:
            print(f"✗ 连接失败: {e}")
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        traceback.print_exc()
    
    return False

def main():
    print("开始测试MySQL连接...")
    print("=" * 50)
    
    for password in passwords_to_try:
        if test_mysql_connection(password):
            print(f"\n找到了正确的密码: '{password}'")
            return
        print()
    
    print("所有密码尝试均失败。请手动检查MySQL root用户的密码设置。")

if __name__ == "__main__":
    main()
