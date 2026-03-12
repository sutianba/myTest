#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""API文档配置"""

from flask import jsonify, Blueprint
import os

# ==================== Swagger UI配置 ====================

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

# 暂时注释掉 Swagger UI 导入，因为 flask-swagger-ui 包不存在
# from flask_swagger_ui import get_swaggerui_blueprint
# swaggerui_blueprint = get_swaggerui_blueprint(
#     SWAGGER_URL,
#     API_URL,
#     config={
#         'app_name': "花卉识别与社区系统 API",
#         'dom_id': '#swagger-ui',
#         'defaultModelsExpandDepth': 1,
#         'defaultModelExpandDepth': 1,
#         'docExpansion': 'list',
#         'deepLinking': True,
#         'persistAuthorization': True,
#         'displayRequestDuration': True,
#         'filter': True,
#         'showRequestHeaders': True,
#         'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch']
#     }
# )

# 创建一个空的蓝图，避免导入错误
swaggerui_blueprint = Blueprint('swagger_ui', __name__)

# ==================== API文档生成 ====================

def generate_swagger_json():
    """生成Swagger JSON文档"""
    swagger = {
        "openapi": "3.0.0",
        "info": {
            "title": "花卉识别与社区系统 API",
            "description": "提供花卉识别、用户认证、社区功能等API接口",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "开发服务器"
            },
            {
                "url": "http://127.0.0.1:5000",
                "description": "本地服务器"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "状态码",
                            "example": 200
                        },
                        "message": {
                            "type": "string",
                            "description": "响应消息",
                            "example": "操作成功"
                        },
                        "data": {
                            "type": "object",
                            "description": "响应数据"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "响应时间戳"
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "错误码",
                            "example": 1001
                        },
                        "message": {
                            "type": "string",
                            "description": "错误消息",
                            "example": "参数错误"
                        },
                        "data": {
                            "type": "object",
                            "description": "错误详情"
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "响应时间戳"
                        }
                    }
                },
                "PaginationResponse": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "description": "数据列表"
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "current_page": {
                                    "type": "integer",
                                    "description": "当前页码"
                                },
                                "per_page": {
                                    "type": "integer",
                                    "description": "每页数量"
                                },
                                "total_items": {
                                    "type": "integer",
                                    "description": "总条数"
                                },
                                "total_pages": {
                                    "type": "integer",
                                    "description": "总页数"
                                },
                                "has_next": {
                                    "type": "boolean",
                                    "description": "是否有下一页"
                                },
                                "has_prev": {
                                    "type": "boolean",
                                    "description": "是否有上一页"
                                }
                            }
                        }
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "用户ID"
                        },
                        "username": {
                            "type": "string",
                            "description": "用户名"
                        },
                        "email": {
                            "type": "string",
                            "description": "邮箱"
                        },
                        "is_verified": {
                            "type": "boolean",
                            "description": "是否已验证"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "创建时间"
                        }
                    }
                },
                "Post": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "帖子ID"
                        },
                        "user_id": {
                            "type": "integer",
                            "description": "用户ID"
                        },
                        "content": {
                            "type": "string",
                            "description": "帖子内容"
                        },
                        "image_url": {
                            "type": "string",
                            "description": "图片URL"
                        },
                        "likes_count": {
                            "type": "integer",
                            "description": "点赞数"
                        },
                        "comments_count": {
                            "type": "integer",
                            "description": "评论数"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "创建时间"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "更新时间"
                        }
                    }
                },
                "Comment": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "评论ID"
                        },
                        "post_id": {
                            "type": "integer",
                            "description": "帖子ID"
                        },
                        "user_id": {
                            "type": "integer",
                            "description": "用户ID"
                        },
                        "content": {
                            "type": "string",
                            "description": "评论内容"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "创建时间"
                        }
                    }
                }
            }
        },
        "paths": {
            "/api/register": {
                "post": {
                    "tags": ["认证"],
                    "summary": "用户注册",
                    "description": "注册新用户账号，支持邮箱验证",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "用户名",
                                            "minLength": 3,
                                            "maxLength": 50
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码",
                                            "minLength": 6,
                                            "maxLength": 100
                                        },
                                        "email": {
                                            "type": "string",
                                            "description": "邮箱（可选）",
                                            "format": "email"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "注册成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            }
                        },
                        "1001": {
                            "description": "参数错误",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "3002": {
                            "description": "用户已存在",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/login": {
                "post": {
                    "tags": ["认证"],
                    "summary": "用户登录",
                    "description": "使用用户名和密码登录",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "用户名"
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "登录成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            }
                        },
                        "2001": {
                            "description": "未授权",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        },
                        "3003": {
                            "description": "密码错误",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/community/posts": {
                "get": {
                    "tags": ["社区"],
                    "summary": "获取帖子列表",
                    "description": "分页获取帖子列表",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "页码",
                            "schema": {
                                "type": "integer",
                                "default": 1
                            }
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "description": "每页数量",
                            "schema": {
                                "type": "integer",
                                "default": 10,
                                "maximum": 100
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "获取成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {
                                                "$ref": "#/components/schemas/SuccessResponse"
                                            },
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "data": {
                                                        "$ref": "#/components/schemas/PaginationResponse"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["社区"],
                    "summary": "创建帖子",
                    "description": "创建新帖子",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["content"],
                                    "properties": {
                                        "content": {
                                            "type": "string",
                                            "description": "帖子内容"
                                        },
                                        "image_url": {
                                            "type": "string",
                                            "description": "图片URL"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "创建成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SuccessResponse"
                                    }
                                }
                            }
                        },
                        "2001": {
                            "description": "未授权",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return swagger

def save_swagger_json():
    """保存Swagger JSON文档到文件"""
    swagger_json = generate_swagger_json()
    
    # 确保static目录存在
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 保存swagger.json文件
    swagger_file = os.path.join(static_dir, 'swagger.json')
    with open(swagger_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(swagger_json, f, ensure_ascii=False, indent=2)
    
    print(f"Swagger JSON文档已保存到: {swagger_file}")
    return swagger_file
