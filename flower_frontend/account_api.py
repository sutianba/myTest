#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""个人账户API接口"""

import os
import secrets
import time
import logging
from datetime import datetime
from flask import request, jsonify
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('account_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AccountAPI')

# 导入模块
from account_manager import (
    get_user_profile, update_user_profile, upload_avatar,
    generate_password_reset_token, verify_password_reset_token, mark_password_reset_token_as_used,
    reset_user_password, change_user_password,
    generate_email_change_token, verify_email_change_token, mark_email_change_token_as_used,
    change_user_email, delete_user_account, ban_user, unban_user,
    log_user_action, get_user_action_logs, check_user_banned, get_user_info
)

from password_reset import (
    generate_reset_token, verify_reset_token, mark_reset_token_as_used,
    send_password_reset_email
)

from email_change import (
    generate_change_token, verify_change_token, mark_change_token_as_used,
    send_email_change_email
)

from email_config import send_verification_email


def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def account_api(app):
    """注册个人账户API路由"""
    
    # ==================== 用户资料相关 ====================
    
    @app.route('/api/user/profile', methods=['GET'])
    def get_user_profile_api():
        """获取用户资料"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取用户资料
            profile = get_user_profile(current_user['user_id'])
            
            if not profile:
                return jsonify({'success': False, 'error': '用户资料不存在'}), 404
            
            return jsonify({
                'success': True,
                'profile': profile
            })
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取用户资料失败'}), 500
    
    @app.route('/api/user/profile', methods=['PUT'])
    def update_user_profile_api():
        """更新用户资料"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            # 更新用户资料
            success, error = update_user_profile(
                user_id=current_user['user_id'],
                nickname=data.get('nickname'),
                bio=data.get('bio'),
                gender=data.get('gender'),
                birthday=data.get('birthday'),
                location=data.get('location')
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '更新用户资料失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '更新用户资料成功'
            })
            
        except Exception as e:
            logger.error(f"更新用户资料失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '更新用户资料失败'}), 500
    
    @app.route('/api/user/avatar', methods=['POST'])
    def upload_avatar_api():
        """上传头像"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 检查是否有文件
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '未找到上传文件'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'error': '文件名为空'}), 400
            
            # 读取文件内容
            file_content = file.read()
            
            # 上传头像
            success, avatar_url, error = upload_avatar(
                user_id=current_user['user_id'],
                file_content=file_content,
                filename=file.filename
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '上传头像失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '上传头像成功',
                'avatar_url': avatar_url
            })
            
        except Exception as e:
            logger.error(f"上传头像失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '上传头像失败'}), 500
    
    # ==================== 密码管理相关 ====================
    
    @app.route('/api/change-password', methods=['POST'])
    def change_password_api():
        """修改密码"""
        try:
            from auth_middleware import get_current_user
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            
            if not old_password or not new_password:
                return jsonify({'success': False, 'error': '请提供原密码和新密码'}), 400
            
            # 修改密码
            success, error = change_user_password(
                user_id=current_user['user_id'],
                old_password=old_password,
                new_password=new_password
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '修改密码失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '修改密码成功'
            })
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '修改密码失败'}), 500
    
    @app.route('/api/request-password-reset', methods=['POST'])
    def request_password_reset_api():
        """请求重置密码"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            email = data.get('email')
            
            if not email:
                return jsonify({'success': False, 'error': '请提供邮箱地址'}), 400
            
            # 获取用户信息
            from db_config import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not user:
                return jsonify({'success': False, 'error': '该邮箱未注册'}), 404
            
            # 发送重置邮件
            result = send_password_reset_email(email, user['username'])
            
            if not result['success']:
                return jsonify({'success': False, 'error': result.get('error', '发送邮件失败')}), 400
            
            return jsonify({
                'success': True,
                'message': '重置密码邮件已发送，请查收'
            })
            
        except Exception as e:
            logger.error(f"请求重置密码失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '请求重置密码失败'}), 500
    
    @app.route('/api/reset-password', methods=['POST'])
    def reset_password_api():
        """重置密码"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            token = data.get('token')
            new_password = data.get('new_password')
            
            if not token or not new_password:
                return jsonify({'success': False, 'error': '请提供Token和新密码'}), 400
            
            # 验证Token
            result = verify_reset_token(token)
            
            if not result['success']:
                return jsonify({'success': False, 'error': result['error']}), 400
            
            # 标记Token为已使用
            mark_reset_token_as_used(token)
            
            # 重置密码
            success, error = reset_user_password(
                user_id=result['data']['user_id'],
                new_password=new_password
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '重置密码失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '重置密码成功'
            })
            
        except Exception as e:
            logger.error(f"重置密码失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '重置密码失败'}), 500
    
    # ==================== 邮箱管理相关 ====================
    
    @app.route('/api/change-email', methods=['POST'])
    def change_email_api():
        """修改邮箱"""
        try:
            from auth_middleware import get_current_user
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            new_email = data.get('new_email')
            
            if not new_email:
                return jsonify({'success': False, 'error': '请提供新邮箱地址'}), 400
            
            # 获取用户信息
            from db_config import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT username FROM users WHERE id = %s", (current_user['user_id'],))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not user:
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 发送验证邮件
            result = send_email_change_email(
                user_id=current_user['user_id'],
                username=user['username'],
                new_email=new_email
            )
            
            if not result['success']:
                return jsonify({'success': False, 'error': result.get('error', '发送邮件失败')}), 400
            
            return jsonify({
                'success': True,
                'message': '验证邮件已发送，请查收'
            })
            
        except Exception as e:
            logger.error(f"修改邮箱失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '修改邮箱失败'}), 500
    
    @app.route('/api/verify-email-change', methods=['GET'])
    def verify_email_change_api():
        """验证邮箱修改"""
        try:
            token = request.args.get('token')
            
            if not token:
                return jsonify({'success': False, 'error': '请提供Token'}), 400
            
            # 验证Token
            result = verify_change_token(token)
            
            if not result['success']:
                return jsonify({'success': False, 'error': result['error']}), 400
            
            # 标记Token为已使用
            mark_change_token_as_used(token)
            
            # 修改邮箱
            success, error = change_user_email(
                user_id=result['data']['user_id'],
                new_email=result['data']['new_email']
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '修改邮箱失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '邮箱修改成功'
            })
            
        except Exception as e:
            logger.error(f"验证邮箱修改失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '验证邮箱修改失败'}), 500
    
    # ==================== 账号管理相关 ====================
    
    @app.route('/api/delete-account', methods=['DELETE'])
    def delete_account_api():
        """注销账号"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            reason = data.get('reason', '')
            
            # 注销账号
            success, error = delete_user_account(
                user_id=current_user['user_id'],
                reason=reason
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '注销账号失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '注销账号成功'
            })
            
        except Exception as e:
            logger.error(f"注销账号失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '注销账号失败'}), 500
    
    @app.route('/api/ban-account', methods=['POST'])
    def ban_account_api():
        """封禁账号（管理员）"""
        try:
            from auth_middleware import get_current_user
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 检查是否为管理员
            if current_user['role'] != 'admin':
                return jsonify({'success': False, 'error': '无权限执行此操作'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            user_id = data.get('user_id')
            ban_reason = data.get('ban_reason', '')
            ban_hours = data.get('ban_hours', 24)
            
            if not user_id:
                return jsonify({'success': False, 'error': '请提供用户ID'}), 400
            
            # 封禁账号
            success, error = ban_user(
                user_id=user_id,
                ban_reason=ban_reason,
                ban_hours=ban_hours
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '封禁账号失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '封禁账号成功'
            })
            
        except Exception as e:
            logger.error(f"封禁账号失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '封禁账号失败'}), 500
    
    @app.route('/api/unban-account', methods=['POST'])
    def unban_account_api():
        """解封账号（管理员）"""
        try:
            from auth_middleware import get_current_user
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 检查是否为管理员
            if current_user['role'] != 'admin':
                return jsonify({'success': False, 'error': '无权限执行此操作'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            user_id = data.get('user_id')
            unban_reason = data.get('unban_reason', '')
            
            if not user_id:
                return jsonify({'success': False, 'error': '请提供用户ID'}), 400
            
            # 解封账号
            success, error = unban_user(
                user_id=user_id,
                unban_reason=unban_reason
            )
            
            if not success:
                return jsonify({'success': False, 'error': error or '解封账号失败'}), 400
            
            return jsonify({
                'success': True,
                'message': '解封账号成功'
            })
            
        except Exception as e:
            logger.error(f"解封账号失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '解封账号失败'}), 500
    
    @app.route('/api/user/logs', methods=['GET'])
    def get_user_logs_api():
        """获取用户操作日志"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取分页参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            
            # 获取用户操作日志
            result = get_user_action_logs(
                user_id=current_user['user_id'],
                page=page,
                page_size=page_size
            )
            
            return jsonify({
                'success': True,
                'logs': result['logs'],
                'total': result['total'],
                'page': result['page'],
                'page_size': result['page_size'],
                'total_pages': result['total_pages']
            })
            
        except Exception as e:
            logger.error(f"获取用户操作日志失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取用户操作日志失败'}), 500
    
    @app.route('/api/user/info', methods=['GET'])
    def get_user_info_api():
        """获取用户信息（包括资料）"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 获取用户信息
            user_info = get_user_info(current_user['user_id'])
            
            if not user_info:
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            return jsonify({
                'success': True,
                'user': user_info
            })
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取用户信息失败'}), 500
    
    @app.route('/api/check-ban', methods=['GET'])
    def check_ban_api():
        """检查用户是否被封禁"""
        try:
            from jwt_manager import get_current_user_from_token
            
            # 获取Token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '未提供认证Token'}), 401
            
            token = auth_header.split(' ')[1]
            current_user = get_current_user_from_token(token)
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Token无效或已过期'}), 401
            
            # 检查是否被封禁
            is_banned, reason, ban_end = check_user_banned(current_user['user_id'])
            
            return jsonify({
                'success': True,
                'is_banned': is_banned,
                'ban_reason': reason,
                'ban_end': str(ban_end) if ban_end else None
            })
            
        except Exception as e:
            logger.error(f"检查封禁状态失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '检查封禁状态失败'}), 500
