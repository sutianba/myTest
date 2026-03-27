#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试用户管理API
"""
import sys
sys.path.insert(0, '.')

from db import db_manager, get_users

def test_users_api():
    try:
        print("=" * 60)
        print("测试用户管理API")
        print("=" * 60)
        
        # 测试获取用户列表
        users, total = get_users(search='', role='', limit=10, offset=0)
        
        print(f"\n获取到 {len(users)} 个用户，总计 {total} 个")
        
        if users:
            print("\n用户列表：")
            for user in users:
                print(f"  ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user.get('email', '-')}, 角色: {user['role']}, 注册时间: {user.get('created_at', '-')}")
        else:
            print("\n⚠️ 没有获取到用户数据")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_users_api()
