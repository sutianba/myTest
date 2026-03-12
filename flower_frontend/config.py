#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""配置管理模块"""

import os
import logging
from typing import Dict, Any

# ==================== 环境配置 ====================

class BaseConfig:
    """基础配置类"""
    # 通用配置
    APP_NAME = "花卉识别与社区系统"
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "flower_recognition"
    
    # JWT配置
    JWT_SECRET_KEY = "your-secret-key-here"
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # 邮件配置
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = ""
    SMTP_PASSWORD = ""
    
    # 目录配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    
    # 模型配置
    PLANT_RECOGNITION_MODEL = "plant_model.h5"
    PLANT_RECOGNITION_LABELS = "plant_labels.json"
    
    # 安全配置
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    
    # CORS配置
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    
    # 限流配置
    RATE_LIMIT_MAX_REQUESTS = 100
    RATE_LIMIT_WINDOW_SECONDS = 60
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_db_url(cls) -> str:
        """获取数据库连接URL"""
        return f"mysql+mysqlconnector://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保必要的目录存在"""
        for directory in [cls.UPLOAD_DIR, cls.LOG_DIR, cls.MODEL_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境数据库
    DB_NAME = "flower_recognition_dev"
    
    # 开发环境日志
    LOG_LEVEL = logging.DEBUG

class TestConfig(BaseConfig):
    """测试环境配置"""
    DEBUG = False
    TESTING = True
    
    # 测试环境数据库
    DB_NAME = "flower_recognition_test"
    
    # 测试环境日志
    LOG_LEVEL = logging.WARNING

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境数据库
    DB_NAME = "flower_recognition"
    
    # 生产环境日志
    LOG_LEVEL = logging.ERROR

# ==================== 配置加载 ====================

class ConfigManager:
    """配置管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = None
        return cls._instance
    
    def load_config(self, env: str = "development") -> BaseConfig:
        """加载配置"""
        config_classes = {
            "development": DevelopmentConfig,
            "test": TestConfig,
            "production": ProductionConfig
        }
        
        config_class = config_classes.get(env, DevelopmentConfig)
        self._config = config_class()
        
        # 确保目录存在
        self._config.ensure_directories()
        
        # 加载环境变量
        self._load_env()
        
        return self._config
    
    def _load_env(self) -> None:
        """加载环境变量"""
        # 尝试加载.env文件
        env_file = os.path.join(self._config.BASE_DIR, ".env")
        if os.path.exists(env_file):
            self._load_env_file(env_file)
        
        # 从系统环境变量加载
        self._load_system_env()
    
    def _load_env_file(self, env_file: str) -> None:
        """加载.env文件"""
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        setattr(self._config, key, value)
            print(f"Loaded environment variables from {env_file}")
        except Exception as e:
            print(f"Error loading .env file: {str(e)}")
    
    def _load_system_env(self) -> None:
        """加载系统环境变量"""
        # 数据库配置
        if os.environ.get("DB_HOST"):
            self._config.DB_HOST = os.environ.get("DB_HOST")
        if os.environ.get("DB_PORT"):
            self._config.DB_PORT = int(os.environ.get("DB_PORT"))
        if os.environ.get("DB_USER"):
            self._config.DB_USER = os.environ.get("DB_USER")
        if os.environ.get("DB_PASSWORD"):
            self._config.DB_PASSWORD = os.environ.get("DB_PASSWORD")
        if os.environ.get("DB_NAME"):
            self._config.DB_NAME = os.environ.get("DB_NAME")
        
        # JWT配置
        if os.environ.get("JWT_SECRET_KEY"):
            self._config.JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
        
        # 邮件配置
        if os.environ.get("SMTP_SERVER"):
            self._config.SMTP_SERVER = os.environ.get("SMTP_SERVER")
        if os.environ.get("SMTP_PORT"):
            self._config.SMTP_PORT = int(os.environ.get("SMTP_PORT"))
        if os.environ.get("SMTP_USER"):
            self._config.SMTP_USER = os.environ.get("SMTP_USER")
        if os.environ.get("SMTP_PASSWORD"):
            self._config.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
        
        # 目录配置
        if os.environ.get("UPLOAD_DIR"):
            self._config.UPLOAD_DIR = os.environ.get("UPLOAD_DIR")
        if os.environ.get("LOG_DIR"):
            self._config.LOG_DIR = os.environ.get("LOG_DIR")
        if os.environ.get("MODEL_DIR"):
            self._config.MODEL_DIR = os.environ.get("MODEL_DIR")
        
        # 模型配置
        if os.environ.get("PLANT_RECOGNITION_MODEL"):
            self._config.PLANT_RECOGNITION_MODEL = os.environ.get("PLANT_RECOGNITION_MODEL")
        if os.environ.get("PLANT_RECOGNITION_LABELS"):
            self._config.PLANT_RECOGNITION_LABELS = os.environ.get("PLANT_RECOGNITION_LABELS")
    
    def get_config(self) -> BaseConfig:
        """获取配置"""
        if self._config is None:
            self.load_config()
        return self._config

# ==================== 全局配置实例 ====================

config_manager = ConfigManager()
config = config_manager.get_config()
