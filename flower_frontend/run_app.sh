#!/bin/bash
# 运行app.py

# MySQL数据库配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=""
export DB_NAME=flower_recognition

# 邮箱配置
export EMAIL_HOST='smtp.163.com'
export EMAIL_PORT=25
export EMAIL_FROM='你的邮箱@163.com'
export EMAIL_PASSWORD='你的邮箱授权码'
export EMAIL_USE_TLS=False

cd /Users/ringconn/Downloads/花卉识别/myTest/flower_frontend
python3 app.py