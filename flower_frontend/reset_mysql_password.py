#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
重置MySQL root密码
"""

import subprocess
import sys

def reset_mysql_password():
    """重置MySQL root密码"""
    print("开始重置MySQL root密码...")
    
    # 获取临时密码
    temp_password = "Ksjy9RvkvF/O"
    
    try:
        # 使用临时密码连接并重置密码
        cmd = [
            "mysql",
            "-u", "root",
            f"-p{temp_password}",
            "--connect-expired-password",
            "-e",
            "ALTER USER 'root'@'localhost' IDENTIFIED BY '';"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("MySQL root密码重置成功（密码设置为空）")
            return True
        else:
            print(f"密码重置失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"重置密码时出错: {str(e)}")
        return False

if __name__ == "__main__":
    success = reset_mysql_password()
    sys.exit(0 if success else 1)