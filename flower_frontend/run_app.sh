#!/bin/bash
# 运行app.py

export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=""
export DB_NAME=flower_recognition

cd /Users/ringconn/Downloads/花卉识别/myTest/flower_frontend
python3 app.py