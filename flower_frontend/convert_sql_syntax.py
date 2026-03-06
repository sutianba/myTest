#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
将app.py中的SQLite语法转换为MySQL语法
"""

def convert_sqlite_to_mysql(file_path):
    """将文件中的SQLite语法转换为MySQL语法"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按行分割
    lines = content.split('\n')
    converted_lines = []
    
    for line in lines:
        # 检查是否包含SQL关键字
        has_sql_keyword = any(keyword in line for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'FROM', 'JOIN', 'LIMIT', 'OFFSET'])
        
        if has_sql_keyword:
            # 将独立的?替换为%s
            new_line = line.replace('?', '%s')
            converted_lines.append(new_line)
        else:
            converted_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(converted_lines))
    
    print(f"已将 {file_path} 中的SQLite语法转换为MySQL语法")

if __name__ == "__main__":
    convert_sqlite_to_mysql('app.py')