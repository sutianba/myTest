#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""数据库连接管理"""

import mysql.connector
from mysql.connector import Error
import logging
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        """获取数据库连接"""
        if self.connection and self.connection.is_connected():
            return self.connection
        
        try:
            self.connection = mysql.connector.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info(f"成功连接到数据库: {config.DB_NAME}")
            return self.connection
        except Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                logger.info("数据库连接已关闭")
            except Error as e:
                logger.error(f"关闭数据库连接失败: {str(e)}")
    
    def execute_query(self, query, params=None, commit=False):
        """执行查询"""
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute(query, params or ())
            
            if commit:
                connection.commit()
                logger.info(f"执行并提交查询: {query}")
            else:
                logger.info(f"执行查询: {query}")
            
            return cursor
        except Error as e:
            logger.error(f"执行查询失败: {str(e)}")
            if commit:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
    
    def fetch_one(self, query, params=None):
        """获取单条记录"""
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query, params=None):
        """获取所有记录"""
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        cursor = self.execute_query(query, params, commit=True)
        return cursor.rowcount
    
    def execute_insert(self, query, params=None):
        """执行插入操作"""
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params or ())
            connection.commit()
            logger.info(f"执行插入操作: {query}")
            return cursor.lastrowid
        except Error as e:
            logger.error(f"执行插入操作失败: {str(e)}")
            connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

# 全局数据库管理器实例
db_manager = DatabaseManager()

def get_db_connection():
    """获取数据库连接"""
    return db_manager.get_connection()

def close_db_connection():
    """关闭数据库连接"""
    db_manager.close_connection()

def execute_query(query, params=None, commit=False):
    """执行查询"""
    return db_manager.execute_query(query, params, commit)

def fetch_one(query, params=None):
    """获取单条记录"""
    return db_manager.fetch_one(query, params)

def fetch_all(query, params=None):
    """获取所有记录"""
    return db_manager.fetch_all(query, params)

def execute_update(query, params=None):
    """执行更新操作"""
    return db_manager.execute_update(query, params)

def execute_insert(query, params=None):
    """执行插入操作"""
    return db_manager.execute_insert(query, params)
