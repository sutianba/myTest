#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
运行app.py
"""

import subprocess
import sys
import os

def run_app():
    """运行app.py"""
    env = os.environ.copy()
    env['DB_HOST'] = 'localhost'
    env['DB_PORT'] = '3306'
    env['DB_USER'] = 'root'
    env['DB_PASSWORD'] = ''
    env['DB_NAME'] = 'flower_recognition'
    
    try:
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # 读取输出
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n[提示] 应用已停止")
        if 'process' in locals():
            process.terminate()
            process.wait()
    except Exception as e:
        print(f"运行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_app()