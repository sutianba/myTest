#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
运行app.py并捕获输出
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
        
        # 读取前50行输出
        lines = []
        for i, line in enumerate(process.stdout):
            if i >= 50:
                break
            lines.append(line)
            print(line, end='')
        
        # 如果进程还在运行，终止它
        if process.poll() is None:
            print("\n[提示] app.py正在运行，按Ctrl+C停止")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
    except Exception as e:
        print(f"运行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_app()