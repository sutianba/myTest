#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""数据库连接管理"""

from pymysql import MySQLError
import logging
from db_config import get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def execute_query(self, query, params=None, commit=False):
        """执行查询"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                logger.info(f"执行查询: {query}")
                return cursor
        except MySQLError as e:
            logger.error(f"执行查询失败: {str(e)}")
            raise
    
    def fetch_one(self, query, params=None):
        """获取单条记录"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()
        except MySQLError as e:
            logger.error(f"获取单条记录失败: {str(e)}")
            raise
    
    def fetch_all(self, query, params=None):
        """获取所有记录"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except MySQLError as e:
            logger.error(f"获取所有记录失败: {str(e)}")
            raise
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                logger.info(f"执行更新操作: {query}")
                return cursor.rowcount
        except MySQLError as e:
            logger.error(f"执行更新操作失败: {str(e)}")
            raise
    
    def execute_insert(self, query, params=None):
        """执行插入操作"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                logger.info(f"执行插入操作: {query}")
                return cursor.lastrowid
        except MySQLError as e:
            logger.error(f"执行插入操作失败: {str(e)}")
            raise

# 全局数据库管理器实例
db_manager = DatabaseManager()

def get_db_connection():
    """获取数据库连接"""
    from db_config import get_db_connection as get_db_conn
    return get_db_conn()

def close_db_connection():
    """关闭数据库连接"""
    pass

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
