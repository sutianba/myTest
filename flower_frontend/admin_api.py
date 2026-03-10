#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
管理员后台 API 接口
提供用户管理、封禁/解禁、识别记录、社区审核、举报处理、操作日志、权限分配等功能
"""

import os
import sys
import logging
from flask import request, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加基础目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from db_config import get_db_connection

# ==================== 辅助函数 ====================

def check_admin_permission(current_user, permission_name):
    """检查用户是否拥有指定权限"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = %s AND p.name = %s
        """, (current_user['user_id'], permission_name))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result['count'] > 0
    except Exception as e:
        logger.error(f"检查权限失败: {e}")
        return False

def log_admin_action(admin_id, action_type, target_type, target_id, details=None):
    """记录管理员操作日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown')
        
        cursor.execute("""
            INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (admin_id, action_type, target_type, target_id, details, ip_address))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"记录管理员操作失败: {e}")
        return False

def admin_api(app):
    """注册管理员后台API路由"""
    
    # ==================== 用户管理相关 ====================
    
    @app.route('/api/admin/users', methods=['GET'])
    def get_users_api():
        """获取用户列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'user_view'):
                return jsonify({'success': False, 'error': '无权查看用户列表'}), 403
            
            # 获取参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            search = request.args.get('search', '')
            status = request.args.get('status', '')
            role = request.args.get('role', '')
            
            offset = (page - 1) * page_size
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 构建查询
            query = """
                SELECT u.id, u.username, u.email, u.status, u.role, u.created_at,
                       p.nickname, p.avatar_url
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
            
            params = []
            
            if search:
                query += " AND (u.username LIKE %s OR u.email LIKE %s)"
                count_query += " AND (username LIKE %s OR email LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])
            
            if status:
                query += " AND u.status = %s"
                count_query += " AND status = %s"
                params.append(status)
            
            if role:
                query += " AND u.role = %s"
                count_query += " AND role = %s"
                params.append(role)
            
            query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
            
            # 获取总数
            cursor.execute(count_query, params if search else [])
            total = cursor.fetchone()['total']
            
            # 获取用户列表
            cursor.execute(query, params + [page_size, offset])
            users = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'users': users,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取用户列表失败'}), 500

    @app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
    def update_user_api(user_id):
        """更新用户信息（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'user_edit'):
                return jsonify({'success': False, 'error': '无权编辑用户信息'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 更新用户信息
            update_fields = []
            update_values = []
            
            if 'status' in data:
                update_fields.append("status = %s")
                update_values.append(data['status'])
            
            if 'role' in data:
                update_fields.append("role = %s")
                update_values.append(data['role'])
            
            if update_fields:
                update_values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, update_values)
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'update_user',
                'user',
                user_id,
                f"更新用户信息: {data}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '更新用户信息成功'
            })
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '更新用户信息失败'}), 500

    @app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
    def delete_user_api(user_id):
        """删除用户（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'user_delete'):
                return jsonify({'success': False, 'error': '无权删除用户'}), 403
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'delete_user',
                'user',
                user_id,
                f"删除用户: {user['username']}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '删除用户成功'
            })
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '删除用户失败'}), 500

    # ==================== 封禁/解禁相关 ====================
    
    @app.route('/api/admin/ban', methods=['POST'])
    def ban_user_api():
        """封禁用户（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'user_ban'):
                return jsonify({'success': False, 'error': '无权封禁用户'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            user_id = data.get('user_id')
            reason = data.get('reason', '')
            duration = data.get('duration')  # 封禁时长（分钟），None表示永久
            
            if not user_id:
                return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 更新用户状态
            cursor.execute(
                "UPDATE users SET status = 'disabled' WHERE id = %s",
                (user_id,)
            )
            
            # 记录封禁日志
            if duration:
                cursor.execute(
                    """INSERT INTO account_bans (user_id, banned_by, reason, duration, expires_at)
                       VALUES (%s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL %s MINUTE))""",
                    (user_id, current_user['user_id'], reason, duration, duration)
                )
            else:
                cursor.execute(
                    """INSERT INTO account_bans (user_id, banned_by, reason, duration, expires_at)
                       VALUES (%s, %s, %s, NULL, NULL)""",
                    (user_id, current_user['user_id'], reason)
                )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'ban_user',
                'user',
                user_id,
                f"封禁用户: {reason}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '封禁用户成功'
            })
            
        except Exception as e:
            logger.error(f"封禁用户失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '封禁用户失败'}), 500

    @app.route('/api/admin/unban', methods=['POST'])
    def unban_user_api():
        """解封用户（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'user_ban'):
                return jsonify({'success': False, 'error': '无权解封用户'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            user_id = data.get('user_id')
            reason = data.get('reason', '')
            
            if not user_id:
                return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 更新用户状态
            cursor.execute(
                "UPDATE users SET status = 'active' WHERE id = %s",
                (user_id,)
            )
            
            # 记录解封日志
            cursor.execute(
                """INSERT INTO account_bans (user_id, banned_by, reason, is_unban)
                   VALUES (%s, %s, %s, 1)""",
                (user_id, current_user['user_id'], reason)
            )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'unban_user',
                'user',
                user_id,
                f"解封用户: {reason}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '解封用户成功'
            })
            
        except Exception as e:
            logger.error(f"解封用户失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '解封用户失败'}), 500

    # ==================== 社区审核相关 ====================
    
    @app.route('/api/admin/content-reviews', methods=['GET'])
    def get_content_reviews_api():
        """获取待审核内容列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'review_view'):
                return jsonify({'success': False, 'error': '无权查看待审核内容'}), 403
            
            # 获取参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            content_type = request.args.get('content_type', '')
            status = request.args.get('status', '')
            
            offset = (page - 1) * page_size
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT cr.id, cr.content_type, cr.content_id, cr.status, cr.review_reason,
                       cr.created_at, cr.reviewed_at,
                       u.username as reviewer_username,
                       CASE 
                           WHEN cr.content_type = 'post' THEN p.content
                           WHEN cr.content_type = 'comment' THEN c.content
                       END as content
                FROM content_reviews cr
                LEFT JOIN users u ON cr.reviewer_id = u.id
                LEFT JOIN posts p ON cr.content_type = 'post' AND cr.content_id = p.id
                LEFT JOIN comments c ON cr.content_type = 'comment' AND cr.content_id = c.id
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) as total FROM content_reviews WHERE 1=1"
            
            params = []
            
            if content_type:
                query += " AND cr.content_type = %s"
                count_query += " AND content_type = %s"
                params.append(content_type)
            
            if status:
                query += " AND cr.status = %s"
                count_query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY cr.created_at DESC LIMIT %s OFFSET %s"
            
            # 获取总数
            cursor.execute(count_query, params if content_type or status else [])
            total = cursor.fetchone()['total']
            
            # 获取待审核内容
            cursor.execute(query, params + [page_size, offset])
            reviews = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'reviews': reviews,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"获取待审核内容失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取待审核内容失败'}), 500

    @app.route('/api/admin/content-reviews/<int:review_id>', methods=['POST'])
    def review_content_api(review_id):
        """审核内容（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'review_approve'):
                return jsonify({'success': False, 'error': '无权审核内容'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            status = data.get('status')
            review_reason = data.get('review_reason', '')
            
            if not status or status not in ['approved', 'rejected']:
                return jsonify({'success': False, 'error': '状态必须为approved或rejected'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查审核记录是否存在
            cursor.execute("SELECT * FROM content_reviews WHERE id = %s", (review_id,))
            review = cursor.fetchone()
            
            if not review:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '审核记录不存在'}), 404
            
            # 更新审核状态
            cursor.execute(
                """UPDATE content_reviews 
                   SET status = %s, reviewer_id = %s, review_reason = %s, reviewed_at = NOW()
                   WHERE id = %s""",
                (status, current_user['user_id'], review_reason, review_id)
            )
            
            # 根据审核结果处理内容
            if status == 'approved':
                if review['content_type'] == 'post':
                    cursor.execute(
                        "UPDATE posts SET is_approved = 1 WHERE id = %s",
                        (review['content_id'],)
                    )
                elif review['content_type'] == 'comment':
                    cursor.execute(
                        "UPDATE comments SET is_approved = 1 WHERE id = %s",
                        (review['content_id'],)
                    )
            elif status == 'rejected':
                if review['content_type'] == 'post':
                    cursor.execute(
                        "UPDATE posts SET is_deleted = 1, deleted_reason = %s WHERE id = %s",
                        (review_reason, review['content_id'])
                    )
                elif review['content_type'] == 'comment':
                    cursor.execute(
                        "UPDATE comments SET is_deleted = 1, deleted_reason = %s WHERE id = %s",
                        (review_reason, review['content_id'])
                    )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'review_content',
                review['content_type'],
                review['content_id'],
                f"审核{status}: {review_reason}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'内容审核{status}成功'
            })
            
        except Exception as e:
            logger.error(f"审核内容失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '审核内容失败'}), 500

    # ==================== 举报处理相关 ====================
    
    @app.route('/api/admin/reports', methods=['GET'])
    def get_reports_api():
        """获取举报列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'report_view'):
                return jsonify({'success': False, 'error': '无权查看举报列表'}), 403
            
            # 获取参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            status = request.args.get('status', '')
            reported_type = request.args.get('reported_type', '')
            
            offset = (page - 1) * page_size
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT r.id, r.reporter_id, r.reported_type, r.reported_id, 
                       r.reason, r.status, r.admin_action, r.resolved_at, r.created_at,
                       u.username as reporter_username,
                       CASE 
                           WHEN r.reported_type = 'post' THEN p.content
                           WHEN r.reported_type = 'comment' THEN c.content
                           WHEN r.reported_type = 'user' THEN CONCAT('用户: ', ur.username)
                       END as reported_content
                FROM reports r
                LEFT JOIN users u ON r.reporter_id = u.id
                LEFT JOIN posts p ON r.reported_type = 'post' AND r.reported_id = p.id
                LEFT JOIN comments c ON r.reported_type = 'comment' AND r.reported_id = c.id
                LEFT JOIN users ur ON r.reported_type = 'user' AND r.reported_id = ur.id
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) as total FROM reports WHERE 1=1"
            
            params = []
            
            if status:
                query += " AND r.status = %s"
                count_query += " AND status = %s"
                params.append(status)
            
            if reported_type:
                query += " AND r.reported_type = %s"
                count_query += " AND reported_type = %s"
                params.append(reported_type)
            
            query += " ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
            
            # 获取总数
            cursor.execute(count_query, params if status or reported_type else [])
            total = cursor.fetchone()['total']
            
            # 获取举报列表
            cursor.execute(query, params + [page_size, offset])
            reports = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'reports': reports,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"获取举报列表失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取举报列表失败'}), 500

    @app.route('/api/admin/reports/<int:report_id>', methods=['POST'])
    def handle_report_api(report_id):
        """处理举报（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'report_handle'):
                return jsonify({'success': False, 'error': '无权处理举报'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            status = data.get('status')
            admin_action = data.get('admin_action', '')
            
            if not status or status not in ['resolved', 'rejected']:
                return jsonify({'success': False, 'error': '状态必须为resolved或rejected'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查举报记录是否存在
            cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()
            
            if not report:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '举报记录不存在'}), 404
            
            # 更新举报状态
            cursor.execute(
                """UPDATE reports 
                   SET status = %s, admin_action = %s, resolved_at = NOW()
                   WHERE id = %s""",
                (status, admin_action, report_id)
            )
            
            # 根据处理结果采取相应措施
            if status == 'resolved':
                if report['reported_type'] == 'post':
                    cursor.execute(
                        "UPDATE posts SET is_deleted = 1, deleted_reason = %s WHERE id = %s",
                        (f"因举报被删除: {admin_action}", report['reported_id'])
                    )
                elif report['reported_type'] == 'comment':
                    cursor.execute(
                        "UPDATE comments SET is_deleted = 1, deleted_reason = %s WHERE id = %s",
                        (f"因举报被删除: {admin_action}", report['reported_id'])
                    )
                elif report['reported_type'] == 'user':
                    cursor.execute(
                        "UPDATE users SET status = 'disabled' WHERE id = %s",
                        (report['reported_id'],)
                    )
                    cursor.execute(
                        """INSERT INTO account_bans (user_id, banned_by, reason)
                           VALUES (%s, %s, %s)""",
                        (report['reported_id'], current_user['user_id'], f"因多次举报被封禁: {admin_action}")
                    )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'handle_report',
                'report',
                report_id,
                f"处理举报: {admin_action}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'举报处理{status}成功'
            })
            
        except Exception as e:
            logger.error(f"处理举报失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '处理举报失败'}), 500

    # ==================== 操作日志相关 ====================
    
    @app.route('/api/admin/logs', methods=['GET'])
    def get_admin_logs_api():
        """获取操作日志（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'log_view'):
                return jsonify({'success': False, 'error': '无权查看操作日志'}), 403
            
            # 获取参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 20, type=int)
            admin_id = request.args.get('admin_id', type=int)
            action_type = request.args.get('action_type', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            offset = (page - 1) * page_size
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT al.id, al.admin_id, u.username as admin_username, al.action_type,
                       al.target_type, al.target_id, al.details, al.ip_address, al.created_at
                FROM admin_actions al
                LEFT JOIN users u ON al.admin_id = u.id
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) as total FROM admin_actions WHERE 1=1"
            
            params = []
            
            if admin_id:
                query += " AND al.admin_id = %s"
                count_query += " AND admin_id = %s"
                params.append(admin_id)
            
            if action_type:
                query += " AND al.action_type = %s"
                count_query += " AND action_type = %s"
                params.append(action_type)
            
            if start_date:
                query += " AND al.created_at >= %s"
                count_query += " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND al.created_at <= %s"
                count_query += " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY al.created_at DESC LIMIT %s OFFSET %s"
            
            # 获取总数
            cursor.execute(count_query, params if admin_id or action_type or start_date or end_date else [])
            total = cursor.fetchone()['total']
            
            # 获取操作日志
            cursor.execute(query, params + [page_size, offset])
            logs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'logs': logs,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"获取操作日志失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取操作日志失败'}), 500

    # ==================== 权限分配相关 ====================
    
    @app.route('/api/admin/roles', methods=['GET'])
    def get_roles_api():
        """获取角色列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'role_assign'):
                return jsonify({'success': False, 'error': '无权查看角色列表'}), 403
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM roles ORDER BY id")
            roles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'roles': roles
                }
            })
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取角色列表失败'}), 500

    @app.route('/api/admin/permissions', methods=['GET'])
    def get_permissions_api():
        """获取权限列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'permission_assign'):
                return jsonify({'success': False, 'error': '无权查看权限列表'}), 403
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM permissions ORDER BY id")
            permissions = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'permissions': permissions
                }
            })
            
        except Exception as e:
            logger.error(f"获取权限列表失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取权限列表失败'}), 500

    @app.route('/api/admin/users/<int:user_id>/roles', methods=['PUT'])
    def update_user_roles_api(user_id):
        """更新用户角色（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'role_assign'):
                return jsonify({'success': False, 'error': '无权分配角色'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            role_ids = data.get('role_ids', [])
            
            if not isinstance(role_ids, list):
                return jsonify({'success': False, 'error': 'role_ids必须是列表'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            # 清空用户现有角色
            cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
            
            # 添加新角色
            for role_id in role_ids:
                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, role_id)
                )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'update_user_roles',
                'user',
                user_id,
                f"更新用户角色: {role_ids}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '更新用户角色成功'
            })
            
        except Exception as e:
            logger.error(f"更新用户角色失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '更新用户角色失败'}), 500

    @app.route('/api/admin/roles/<int:role_id>/permissions', methods=['PUT'])
    def update_role_permissions_api(role_id):
        """更新角色权限（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'permission_assign'):
                return jsonify({'success': False, 'error': '无权分配权限'}), 403
            
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400
            
            permission_ids = data.get('permission_ids', [])
            
            if not isinstance(permission_ids, list):
                return jsonify({'success': False, 'error': 'permission_ids必须是列表'}), 400
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查角色是否存在
            cursor.execute("SELECT * FROM roles WHERE id = %s", (role_id,))
            role = cursor.fetchone()
            
            if not role:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': '角色不存在'}), 404
            
            # 清空角色现有权限
            cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
            
            # 添加新权限
            for permission_id in permission_ids:
                cursor.execute(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                    (role_id, permission_id)
                )
            
            conn.commit()
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'update_role_permissions',
                'role',
                role_id,
                f"更新角色权限: {permission_ids}"
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '更新角色权限成功'
            })
            
        except Exception as e:
            logger.error(f"更新角色权限失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '更新角色权限失败'}), 500

    # ==================== 系统日志查看 ====================
    
    @app.route('/api/admin/system-logs', methods=['GET'])
    def get_system_logs_api():
        """获取系统日志文件内容（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'log_view'):
                return jsonify({'success': False, 'error': '无权查看系统日志'}), 403
            
            # 获取参数
            log_type = request.args.get('log_type', 'main')
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 50, type=int)
            keyword = request.args.get('keyword', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            # 日志文件映射
            log_files = {
                'main': 'main.log',
                'login': 'login.log',
                'register': 'register.log',
                'email': 'email.log',
                'upload': 'upload.log',
                'model_inference': 'model_inference.log',
                'database': 'database.log',
                'api_request': 'api_request.log',
                'admin_action': 'admin_action.log',
                'error': 'error.log',
                'security': 'security.log'
            }
            
            log_filename = log_files.get(log_type, 'main.log')
            log_path = os.path.join('logs', log_filename)
            
            if not os.path.exists(log_path):
                return jsonify({
                    'success': True,
                    'data': {
                        'logs': [],
                        'total': 0,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': 0
                    }
                })
            
            # 读取日志文件
            logs = []
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析日志行
                    try:
                        # 尝试解析JSON格式
                        import json
                        log_entry = json.loads(line)
                        
                        # 时间筛选
                        if start_date and log_entry.get('timestamp', '') < start_date:
                            continue
                        if end_date and log_entry.get('timestamp', '') > end_date:
                            continue
                        
                        # 关键词筛选
                        if keyword:
                            log_str = json.dumps(log_entry, ensure_ascii=False)
                            if keyword.lower() not in log_str.lower():
                                continue
                        
                        logs.append(log_entry)
                    except:
                        # 非JSON格式，按文本处理
                        if keyword and keyword.lower() not in line.lower():
                            continue
                        logs.append({
                            'timestamp': '',
                            'message': line,
                            'raw': True
                        })
            
            # 分页
            total = len(logs)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_logs = logs[start_idx:end_idx]
            
            return jsonify({
                'success': True,
                'data': {
                    'logs': paginated_logs,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"获取系统日志失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取系统日志失败'}), 500
    
    @app.route('/api/admin/system-logs/types', methods=['GET'])
    def get_log_types_api():
        """获取日志类型列表（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'log_view'):
                return jsonify({'success': False, 'error': '无权查看系统日志'}), 403
            
            log_types = [
                {'key': 'main', 'label': '主日志', 'description': '系统主要运行日志'},
                {'key': 'login', 'label': '登录日志', 'description': '用户登录成功/失败记录'},
                {'key': 'register', 'label': '注册日志', 'description': '用户注册成功/失败记录'},
                {'key': 'email', 'label': '邮件日志', 'description': '邮件发送成功/失败记录'},
                {'key': 'upload', 'label': '上传日志', 'description': '文件上传成功/失败记录'},
                {'key': 'model_inference', 'label': '模型推理日志', 'description': 'AI识别推理记录'},
                {'key': 'database', 'label': '数据库日志', 'description': '数据库操作记录'},
                {'key': 'api_request', 'label': 'API请求日志', 'description': 'API接口调用记录'},
                {'key': 'admin_action', 'label': '管理员操作日志', 'description': '管理员后台操作记录'},
                {'key': 'error', 'label': '错误日志', 'description': '系统错误和异常记录'},
                {'key': 'security', 'label': '安全日志', 'description': '安全相关事件记录'}
            ]
            
            return jsonify({
                'success': True,
                'data': {
                    'log_types': log_types
                }
            })
            
        except Exception as e:
            logger.error(f"获取日志类型失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '获取日志类型失败'}), 500
    
    @app.route('/api/admin/system-logs/export', methods=['POST'])
    def export_system_logs_api():
        """导出系统日志（管理员）"""
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
            
            # 检查权限
            if not check_admin_permission(current_user, 'log_view'):
                return jsonify({'success': False, 'error': '无权导出系统日志'}), 403
            
            # 获取请求数据
            data = request.get_json()
            log_type = data.get('log_type', 'main')
            keyword = data.get('keyword', '')
            start_date = data.get('start_date', '')
            end_date = data.get('end_date', '')
            
            # 日志文件映射
            log_files = {
                'main': 'main.log',
                'login': 'login.log',
                'register': 'register.log',
                'email': 'email.log',
                'upload': 'upload.log',
                'model_inference': 'model_inference.log',
                'database': 'database.log',
                'api_request': 'api_request.log',
                'admin_action': 'admin_action.log',
                'error': 'error.log',
                'security': 'security.log'
            }
            
            log_filename = log_files.get(log_type, 'main.log')
            log_path = os.path.join('logs', log_filename)
            
            if not os.path.exists(log_path):
                return jsonify({'success': False, 'error': '日志文件不存在'}), 404
            
            # 生成导出文件
            import tempfile
            import csv
            from datetime import datetime
            
            export_filename = f"{log_type}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            temp_path = os.path.join(tempfile.gettempdir(), export_filename)
            
            with open(log_path, 'r', encoding='utf-8') as f_in, \
                 open(temp_path, 'w', newline='', encoding='utf-8-sig') as f_out:
                writer = csv.writer(f_out)
                writer.writerow(['时间戳', '类型', '消息', '详细信息'])
                
                for line in f_in:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        import json
                        log_entry = json.loads(line)
                        
                        # 时间筛选
                        if start_date and log_entry.get('timestamp', '') < start_date:
                            continue
                        if end_date and log_entry.get('timestamp', '') > end_date:
                            continue
                        
                        # 关键词筛选
                        if keyword:
                            log_str = json.dumps(log_entry, ensure_ascii=False)
                            if keyword.lower() not in log_str.lower():
                                continue
                        
                        writer.writerow([
                            log_entry.get('timestamp', ''),
                            log_entry.get('type', ''),
                            log_entry.get('message', ''),
                            json.dumps({k: v for k, v in log_entry.items() 
                                      if k not in ['timestamp', 'type', 'message']}, ensure_ascii=False)
                        ])
                    except:
                        if keyword and keyword.lower() not in line.lower():
                            continue
                        writer.writerow(['', '', line, ''])
            
            # 记录操作日志
            log_admin_action(
                current_user['user_id'],
                'export_logs',
                'system',
                0,
                f"导出日志: {log_type}"
            )
            
            # 返回文件
            from flask import send_file
            return send_file(
                temp_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=export_filename
            )
            
        except Exception as e:
            logger.error(f"导出系统日志失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': '导出系统日志失败'}), 500
