import sqlite3
import os

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'flower_recognition.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('albums', 'album_images')")
tables = cursor.fetchall()
print('存在的表:', tables)

# 检查 albums 表结构
print('\nalbums 表结构:')
cursor.execute('PRAGMA table_info(albums)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col}')

# 检查 album_images 表结构
print('\nalbum_images 表结构:')
cursor.execute('PRAGMA table_info(album_images)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col}')

conn.close()
