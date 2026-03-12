#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""API统一响应格式和错误码"""

from typing import Any, Dict, Optional, Tuple
from functools import wraps
from flask import jsonify, Response
import traceback
import logging
import datetime

logger = logging.getLogger(__name__)

# ==================== 统一错误码定义 ====================

class ErrorCode:
    """错误码枚举"""
    # 通用错误 (1000-1999)
    SUCCESS = 200
    UNKNOWN_ERROR = 1000
    PARAMETER_ERROR = 1001
    METHOD_NOT_ALLOWED = 1002
    
    # 认证授权错误 (2000-2999)
    UNAUTHORIZED = 2001
    TOKEN_EXPIRED = 2002
    TOKEN_INVALID = 2003
    PERMISSION_DENIED = 2004
    ACCOUNT_LOCKED = 2005
    ACCOUNT_NOT_VERIFIED = 2006
    
    # 业务逻辑错误 (3000-3999)
    USER_NOT_FOUND = 3001
    USER_ALREADY_EXISTS = 3002
    PASSWORD_ERROR = 3003
    EMAIL_ALREADY_EXISTS = 3004
    EMAIL_NOT_FOUND = 3005
    VERIFICATION_CODE_ERROR = 3006
    VERIFICATION_CODE_EXPIRED = 3007
    
    # 资源错误 (4000-4999)
    RESOURCE_NOT_FOUND = 4001
    RESOURCE_ALREADY_EXISTS = 4002
    RESOURCE_LOCKED = 4003
    
    # 服务器错误 (5000-5999)
    INTERNAL_SERVER_ERROR = 5000
    DATABASE_ERROR = 5001
    EXTERNAL_SERVICE_ERROR = 5002

# ==================== 统一响应格式 ====================

def success_response(data: Any = None, message: str = "操作成功", code: int = ErrorCode.SUCCESS) -> Tuple[Response, int]:
    """成功响应格式"""
    response = {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    return jsonify(response), code

def error_response(error_code: int, message: str = None, data: Any = None) -> Tuple[Response, int]:
    """错误响应格式"""
    if message is None:
        message = get_error_message(error_code)
    
    response = {
        "code": error_code,
        "message": message,
        "data": data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    return jsonify(response), error_code

def get_error_message(error_code: int) -> str:
    """获取错误消息"""
    error_messages = {
        ErrorCode.UNKNOWN_ERROR: "未知错误",
        ErrorCode.PARAMETER_ERROR: "参数错误",
        ErrorCode.METHOD_NOT_ALLOWED: "请求方法不允许",
        ErrorCode.UNAUTHORIZED: "未授权",
        ErrorCode.TOKEN_EXPIRED: "令牌已过期",
        ErrorCode.TOKEN_INVALID: "令牌无效",
        ErrorCode.PERMISSION_DENIED: "权限不足",
        ErrorCode.ACCOUNT_LOCKED: "账号已锁定",
        ErrorCode.ACCOUNT_NOT_VERIFIED: "账号未验证",
        ErrorCode.USER_NOT_FOUND: "用户不存在",
        ErrorCode.USER_ALREADY_EXISTS: "用户已存在",
        ErrorCode.PASSWORD_ERROR: "密码错误",
        ErrorCode.EMAIL_ALREADY_EXISTS: "邮箱已存在",
        ErrorCode.EMAIL_NOT_FOUND: "邮箱不存在",
        ErrorCode.VERIFICATION_CODE_ERROR: "验证码错误",
        ErrorCode.VERIFICATION_CODE_EXPIRED: "验证码已过期",
        ErrorCode.RESOURCE_NOT_FOUND: "资源不存在",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "资源已存在",
        ErrorCode.RESOURCE_LOCKED: "资源已锁定",
        ErrorCode.INTERNAL_SERVER_ERROR: "服务器内部错误",
        ErrorCode.DATABASE_ERROR: "数据库错误",
        ErrorCode.EXTERNAL_SERVICE_ERROR: "外部服务错误"
    }
    return error_messages.get(error_code, "未知错误")

# ==================== 参数校验装饰器 ====================

def validate_params(required_params: list = None, optional_params: list = None):
    """参数校验装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            # 检查必填参数
            if required_params:
                missing_params = [p for p in required_params if p not in data]
                if missing_params:
                    return error_response(ErrorCode.PARAMETER_ERROR, f"缺少必填参数: {', '.join(missing_params)}")
            
            # 检查参数类型
            if optional_params:
                for param, param_type in optional_params:
                    if param in data:
                        if param_type == 'email':
                            if not isinstance(data[param], str) or '@' not in data[param]:
                                return error_response(ErrorCode.PARAMETER_ERROR, f"参数 {param} 格式错误")
                        elif param_type == 'int':
                            if not isinstance(data[param], int):
                                return error_response(ErrorCode.PARAMETER_ERROR, f"参数 {param} 必须为整数")
                        elif param_type == 'str':
                            if not isinstance(data[param], str):
                                return error_response(ErrorCode.PARAMETER_ERROR, f"参数 {param} 必须为字符串")
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ==================== 异常处理中间件 ====================

def handle_exception(e: Exception) -> Tuple[Response, int]:
    """异常处理"""
    logger.error(f"异常发生: {type(e).__name__}: {str(e)}")
    logger.error(traceback.format_exc())
    
    # 数据库错误
    if "MySQL" in str(e) or "database" in str(e).lower():
        return error_response(ErrorCode.DATABASE_ERROR, "数据库操作失败")
    
    # 认证错误
    if "token" in str(e).lower() or "jwt" in str(e).lower():
        return error_response(ErrorCode.TOKEN_INVALID, "认证失败")
    
    # 默认错误
    return error_response(ErrorCode.INTERNAL_SERVER_ERROR, "服务器内部错误")

# ==================== 分页参数处理 ====================

def get_pagination_params() -> Dict[str, int]:
    """获取分页参数"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        return {
            'page': page,
            'per_page': per_page,
            'offset': offset,
            'limit': per_page
        }
    except ValueError:
        return {
            'page': 1,
            'per_page': 10,
            'offset': 0,
            'limit': 10
        }

def format_pagination_response(items: list, total: int, pagination: Dict[str, int]) -> Dict[str, Any]:
    """格式化分页响应"""
    total_pages = (total + pagination['per_page'] - 1) // pagination['per_page']
    
    return {
        'items': items,
        'pagination': {
            'current_page': pagination['page'],
            'per_page': pagination['per_page'],
            'total_items': total,
            'total_pages': total_pages,
            'has_next': pagination['page'] < total_pages,
            'has_prev': pagination['page'] > 1
        }
    }
