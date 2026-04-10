#!/usr/bin/env python3
# 启动服务器的脚本
import os
import sys

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("正在启动服务器...")

# 导入并运行app模块
import app

# 启动Flask应用
if __name__ == "__main__":
    app.app.run(debug=True, host='127.0.0.1', port=5000)
