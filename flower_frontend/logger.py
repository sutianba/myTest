#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""统一日志管理系统

提供完整的日志记录功能，包括：
- 登录/注册日志
- 邮件发送日志
- 上传失败日志
- 模型推理异常日志
- 数据库异常日志
- API请求日志
- 管理员操作日志
- 错误告警机制
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, g
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class LogType(Enum):
    """日志类型枚举"""
    LOGIN = "login"                    # 登录日志
    REGISTER = "register"              # 注册日志
    EMAIL = "email"                    # 邮件发送日志
    UPLOAD = "upload"                  # 上传日志
    MODEL_INFERENCE = "model_inference" # 模型推理日志
    DATABASE = "database"              # 数据库日志
    API_REQUEST = "api_request"        # API请求日志
    ADMIN_ACTION = "admin_action"      # 管理员操作日志
    ERROR = "error"                    # 错误日志
    SECURITY = "security"              # 安全日志


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class UnifiedLogger:
    """统一日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志管理器
        
        Args:
            log_dir: 日志文件存放目录
        """
        self.log_dir = log_dir
        self._ensure_log_dir()
        self._setup_loggers()
        self._setup_alert_config()
        
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def _setup_loggers(self):
        """设置各类日志记录器"""
        # 主日志记录器
        self.main_logger = self._create_logger("main", "main.log")
        
        # 分类日志记录器
        self.loggers = {
            LogType.LOGIN: self._create_logger("login", "login.log"),
            LogType.REGISTER: self._create_logger("register", "register.log"),
            LogType.EMAIL: self._create_logger("email", "email.log"),
            LogType.UPLOAD: self._create_logger("upload", "upload.log"),
            LogType.MODEL_INFERENCE: self._create_logger("model_inference", "model_inference.log"),
            LogType.DATABASE: self._create_logger("database", "database.log"),
            LogType.API_REQUEST: self._create_logger("api_request", "api_request.log"),
            LogType.ADMIN_ACTION: self._create_logger("admin_action", "admin_action.log"),
            LogType.ERROR: self._create_logger("error", "error.log"),
            LogType.SECURITY: self._create_logger("security", "security.log"),
        }
        
    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """创建日志记录器
        
        Args:
            name: 记录器名称
            filename: 日志文件名
            
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(f"flower_recognition.{name}")
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
            
        # 文件处理器 - 按天轮转
        log_path = os.path.join(self.log_dir, filename)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_path,
            when="midnight",
            interval=1,
            backupCount=30,  # 保留30天
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _setup_alert_config(self):
        """设置告警配置"""
        self.alert_config = {
            "enabled": os.environ.get("ALERT_ENABLED", "true").lower() == "true",
            "email": {
                "smtp_server": os.environ.get("ALERT_SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.environ.get("ALERT_SMTP_PORT", "587")),
                "username": os.environ.get("ALERT_EMAIL_USERNAME", ""),
                "password": os.environ.get("ALERT_EMAIL_PASSWORD", ""),
                "to_addresses": os.environ.get("ALERT_TO_ADDRESSES", "").split(","),
            },
            "thresholds": {
                AlertLevel.ERROR: 10,      # 10分钟内错误数超过10次告警
                AlertLevel.CRITICAL: 1,    # 出现严重错误立即告警
            }
        }
        
        # 错误计数器（用于告警）
        self.error_counts = {
            AlertLevel.ERROR: [],
            AlertLevel.CRITICAL: [],
        }
        
    def log(self, log_type: LogType, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录日志
        
        Args:
            log_type: 日志类型
            message: 日志消息
            extra: 额外信息
        """
        logger = self.loggers.get(log_type, self.main_logger)
        
        # 构建日志数据
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type.value,
            "message": message,
        }
        
        if extra:
            log_data.update(extra)
            
        # 记录日志
        logger.info(json.dumps(log_data, ensure_ascii=False))
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """记录错误日志
        
        Args:
            error: 异常对象
            context: 上下文信息
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": LogType.ERROR.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        if context:
            log_data["context"] = context
            
        self.loggers[LogType.ERROR].error(json.dumps(log_data, ensure_ascii=False))
        
        # 检查是否需要告警
        self._check_alert(AlertLevel.ERROR, str(error))
        
    def log_login(self, user_id: int, username: str, success: bool, ip_address: str, 
                  user_agent: str = "", reason: str = ""):
        """记录登录日志
        
        Args:
            user_id: 用户ID
            username: 用户名
            success: 是否成功
            ip_address: IP地址
            user_agent: 用户代理
            reason: 失败原因
        """
        self.log(LogType.LOGIN, f"用户登录: {username}", {
            "user_id": user_id,
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "reason": reason,
        })
        
        if not success:
            self._check_alert(AlertLevel.WARNING, f"登录失败: {username} - {reason}")
            
    def log_register(self, user_id: int, username: str, email: str, success: bool, 
                     ip_address: str, reason: str = ""):
        """记录注册日志
        
        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            success: 是否成功
            ip_address: IP地址
            reason: 失败原因
        """
        self.log(LogType.REGISTER, f"用户注册: {username}", {
            "user_id": user_id,
            "username": username,
            "email": email,
            "success": success,
            "ip_address": ip_address,
            "reason": reason,
        })
        
    def log_email(self, to_email: str, subject: str, success: bool, 
                  email_type: str = "", reason: str = ""):
        """记录邮件发送日志
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            success: 是否成功
            email_type: 邮件类型
            reason: 失败原因
        """
        self.log(LogType.EMAIL, f"邮件发送: {to_email}", {
            "to_email": to_email,
            "subject": subject,
            "success": success,
            "email_type": email_type,
            "reason": reason,
        })
        
        if not success:
            self._check_alert(AlertLevel.WARNING, f"邮件发送失败: {to_email}")
            
    def log_upload(self, user_id: int, filename: str, success: bool, 
                   file_size: int = 0, reason: str = ""):
        """记录上传日志
        
        Args:
            user_id: 用户ID
            filename: 文件名
            success: 是否成功
            file_size: 文件大小
            reason: 失败原因
        """
        self.log(LogType.UPLOAD, f"文件上传: {filename}", {
            "user_id": user_id,
            "filename": filename,
            "success": success,
            "file_size": file_size,
            "reason": reason,
        })
        
        if not success:
            self._check_alert(AlertLevel.WARNING, f"上传失败: {filename} - {reason}")
            
    def log_model_inference(self, user_id: int, image_path: str, success: bool, 
                           result: str = "", confidence: float = 0.0, 
                           inference_time: float = 0.0, error: str = ""):
        """记录模型推理日志
        
        Args:
            user_id: 用户ID
            image_path: 图片路径
            success: 是否成功
            result: 识别结果
            confidence: 置信度
            inference_time: 推理时间
            error: 错误信息
        """
        self.log(LogType.MODEL_INFERENCE, f"模型推理: {image_path}", {
            "user_id": user_id,
            "image_path": image_path,
            "success": success,
            "result": result,
            "confidence": confidence,
            "inference_time": inference_time,
            "error": error,
        })
        
        if not success:
            self._check_alert(AlertLevel.ERROR, f"模型推理失败: {error}")
            
    def log_database(self, operation: str, table: str, success: bool, 
                     query: str = "", error: str = "", execution_time: float = 0.0):
        """记录数据库操作日志
        
        Args:
            operation: 操作类型
            table: 表名
            success: 是否成功
            query: SQL语句
            error: 错误信息
            execution_time: 执行时间
        """
        # 不记录完整SQL，只记录操作类型和表名（安全考虑）
        self.log(LogType.DATABASE, f"数据库操作: {operation} {table}", {
            "operation": operation,
            "table": table,
            "success": success,
            "execution_time": execution_time,
            "error": error,
        })
        
        if not success:
            self._check_alert(AlertLevel.ERROR, f"数据库操作失败: {operation} {table}")
            
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       response_time: float, user_id: int = 0, ip_address: str = ""):
        """记录API请求日志
        
        Args:
            method: HTTP方法
            endpoint: 请求端点
            status_code: 状态码
            response_time: 响应时间
            user_id: 用户ID
            ip_address: IP地址
        """
        self.log(LogType.API_REQUEST, f"API请求: {method} {endpoint}", {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
            "ip_address": ip_address,
        })
        
        # 记录慢请求
        if response_time > 5.0:  # 超过5秒认为是慢请求
            self._check_alert(AlertLevel.WARNING, f"慢请求: {endpoint} - {response_time:.2f}s")
            
    def log_admin_action(self, admin_id: int, admin_username: str, action: str, 
                        target_type: str, target_id: int, details: str = ""):
        """记录管理员操作日志
        
        Args:
            admin_id: 管理员ID
            admin_username: 管理员用户名
            action: 操作类型
            target_type: 目标类型
            target_id: 目标ID
            details: 详细信息
        """
        self.log(LogType.ADMIN_ACTION, f"管理员操作: {admin_username} - {action}", {
            "admin_id": admin_id,
            "admin_username": admin_username,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
        })
        
    def _check_alert(self, level: AlertLevel, message: str):
        """检查是否需要发送告警
        
        Args:
            level: 告警级别
            message: 告警消息
        """
        if not self.alert_config["enabled"]:
            return
            
        now = datetime.now()
        
        # 清理过期的错误记录
        window_minutes = 10
        cutoff_time = now - timedelta(minutes=window_minutes)
        self.error_counts[level] = [
            t for t in self.error_counts[level] if t > cutoff_time
        ]
        
        # 添加当前错误
        self.error_counts[level].append(now)
        
        # 检查是否超过阈值
        threshold = self.alert_config["thresholds"].get(level, 10)
        if len(self.error_counts[level]) >= threshold:
            self._send_alert(level, message)
            
    def _send_alert(self, level: AlertLevel, message: str):
        """发送告警通知
        
        Args:
            level: 告警级别
            message: 告警消息
        """
        try:
            email_config = self.alert_config["email"]
            
            if not email_config["username"] or not email_config["to_addresses"]:
                return
                
            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = email_config["username"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            msg["Subject"] = f"[植物识别系统告警] {level.value.upper()}: {message[:50]}"
            
            body = f"""
告警级别: {level.value.upper()}
告警时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
告警内容: {message}

请及时处理！
            """
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # 发送邮件
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
            
            self.main_logger.info(f"告警邮件已发送: {message}")
            
        except Exception as e:
            self.main_logger.error(f"发送告警邮件失败: {e}")


# 创建全局日志管理器实例
logger = UnifiedLogger()


def log_api_call(f):
    """API调用日志装饰器
    
    使用示例：
        @app.route('/api/test')
        @log_api_call
        def test_api():
            return jsonify({'success': True})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            response = f(*args, **kwargs)
            
            # 获取响应状态码
            status_code = 200
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            elif isinstance(response, tuple) and len(response) == 2:
                status_code = response[1]
                
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 获取用户信息
            user_id = getattr(g, 'current_user', {}).get('user_id', 0)
            ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '')
            
            # 记录日志
            logger.log_api_request(
                method=request.method,
                endpoint=request.endpoint or request.path,
                status_code=status_code,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address
            )
            
            return response
            
        except Exception as e:
            # 记录异常
            response_time = (datetime.now() - start_time).total_seconds()
            logger.log_error(e, {
                "endpoint": request.endpoint or request.path,
                "method": request.method,
                "response_time": response_time,
            })
            raise
            
    return decorated_function
