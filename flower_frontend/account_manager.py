#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""个人账户管理系统 - 头像、昵称、密码、邮箱等管理"""

import os
import secrets
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('account_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AccountManager')

# 配置参数
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 最大头像大小：2MB
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
AVATAR_UPLOAD_DIR = 'avatars'

# Token存储（实际生产环境应使用Redis等缓存）
password_reset_tokens = {}
email_change_tokens = {}


def get_db_connection():
    """获取数据库连接"""
    from db_config import get_db_connection as get_conn
    return get_conn()


def ensure_user_profile(user_id: int) -> bool:
    """确保用户资料存在"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户资料是否存在
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            # 创建默认用户资料
            cursor.execute(
                """INSERT INTO user_profiles (user_id, nickname, avatar_url, bio) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, '', '', '')
            )
            conn.commit()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"确保用户资料失败: {e}")
        return False


def get_user_profile(user_id: int) -> Optional[Dict]:
    """获取用户资料"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, user_id, nickname, avatar_url, bio, gender, 
                      birthday, location, created_at, updated_at
               FROM user_profiles WHERE user_id = %s""",
            (user_id,)
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return {
                'id': result['id'],
                'user_id': result['user_id'],
                'nickname': result['nickname'],
                'avatar_url': result['avatar_url'],
                'bio': result['bio'],
                'gender': result['gender'],
                'birthday': str(result['birthday']) if result['birthday'] else None,
                'location': result['location'],
                'created_at': str(result['created_at']),
                'updated_at': str(result['updated_at'])
            }
        
        return None
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return None


def update_user_profile(user_id: int, nickname: str = None, 
                       bio: str = None, gender: str = None,
                       birthday: str = None, location: str = None) -> Tuple[bool, Optional[str]]:
    """更新用户资料"""
    try:
        # 确保用户资料存在
        if not ensure_user_profile(user_id):
            return False, "用户资料不存在"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建更新语句
        updates = []
        values = []
        
        if nickname is not None:
            updates.append("nickname = %s")
            values.append(nickname[:50])  # 限制长度
        
        if bio is not None:
            updates.append("bio = %s")
            values.append(bio[:500])  # 限制长度
        
        if gender is not None:
            if gender in ['male', 'female', 'other']:
                updates.append("gender = %s")
                values.append(gender)
        
        if birthday is not None:
            updates.append("birthday = %s")
            values.append(birthday)
        
        if location is not None:
            updates.append("location = %s")
            values.append(location[:100])  # 限制长度
        
        if not updates:
            cursor.close()
            conn.close()
            return True, None
        
        values.append(user_id)
        sql = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = %s"
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'update_profile', f'更新资料: {nickname or ""}')
        
        return True, None
        
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return False, str(e)


def upload_avatar(user_id: int, file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """上传头像"""
    try:
        # 检查文件大小
        if len(file_content) > MAX_AVATAR_SIZE:
            return False, None, f"文件大小超过限制（最大{MAX_AVATAR_SIZE // (1024*1024)}MB）"
        
        # 检查文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_AVATAR_EXTENSIONS:
            return False, None, "不支持的文件类型"
        
        # 确保用户资料存在
        if not ensure_user_profile(user_id):
            return False, None, "用户资料不存在"
        
        # 生成安全的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = secrets.token_hex(8)
        secure_filename = f"user_{user_id}_{timestamp}_{random_str}{ext}"
        
        # 确保上传目录存在
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, AVATAR_UPLOAD_DIR)
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 保存文件
        filepath = os.path.join(upload_dir, secure_filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # 生成缩略图
        from PIL import Image
        import io
        
        try:
            image = Image.open(io.BytesIO(file_content))
            if image.mode in ['RGBA', 'P']:
                image = image.convert('RGB')
            
            image.thumbnail((200, 200), Image.LANCZOS)
            
            thumbnail_path = filepath + '.thumb.jpg'
            image.save(thumbnail_path, format='JPEG', quality=85)
            image.close()
            
            thumbnail_url = f'/uploads/avatars/{os.path.basename(thumbnail_path)}'
        except:
            thumbnail_url = None
        
        # 更新数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        avatar_url = f'/uploads/avatars/{os.path.basename(filepath)}'
        cursor.execute(
            "UPDATE user_profiles SET avatar_url = %s WHERE user_id = %s",
            (avatar_url, user_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'upload_avatar', f'上传头像: {secure_filename}')
        
        return True, avatar_url, None
        
    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, f"上传失败: {str(e)}"


def generate_password_reset_token(user_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """生成密码重置Token"""
    try:
        token = secrets.token_urlsafe(32)
        
        # 存储token信息
        password_reset_tokens[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'expires_at': time.time() + 3600,  # 1小时有效
            'used': False
        }
        
        return True, token, None
        
    except Exception as e:
        logger.error(f"生成密码重置Token失败: {e}")
        return False, None, str(e)


def verify_password_reset_token(token: str) -> Dict:
    """验证密码重置Token"""
    if token not in password_reset_tokens:
        return {'success': False, 'error': '验证链接无效或已过期'}
    
    token_data = password_reset_tokens[token]
    
    # 检查是否已使用
    if token_data['used']:
        return {'success': False, 'error': '验证链接已被使用'}
    
    # 检查是否过期
    if time.time() > token_data['expires_at']:
        del password_reset_tokens[token]
        return {'success': False, 'error': '验证链接已过期'}
    
    return {'success': True, 'data': token_data}


def mark_password_reset_token_as_used(token: str):
    """标记密码重置Token为已使用"""
    if token in password_reset_tokens:
        password_reset_tokens[token]['used'] = True
        password_reset_tokens[token]['used_at'] = time.time()


def generate_email_change_token(user_id: int, new_email: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """生成邮箱修改Token"""
    try:
        token = secrets.token_urlsafe(32)
        
        # 存储token信息
        email_change_tokens[token] = {
            'user_id': user_id,
            'new_email': new_email,
            'created_at': time.time(),
            'expires_at': time.time() + 3600,  # 1小时有效
            'used': False
        }
        
        return True, token, None
        
    except Exception as e:
        logger.error(f"生成邮箱修改Token失败: {e}")
        return False, None, str(e)


def verify_email_change_token(token: str) -> Dict:
    """验证邮箱修改Token"""
    if token not in email_change_tokens:
        return {'success': False, 'error': '验证链接无效或已过期'}
    
    token_data = email_change_tokens[token]
    
    # 检查是否已使用
    if token_data['used']:
        return {'success': False, 'error': '验证链接已被使用'}
    
    # 检查是否过期
    if time.time() > token_data['expires_at']:
        del email_change_tokens[token]
        return {'success': False, 'error': '验证链接已过期'}
    
    return {'success': True, 'data': token_data}


def mark_email_change_token_as_used(token: str):
    """标记邮箱修改Token为已使用"""
    if token in email_change_tokens:
        email_change_tokens[token]['used'] = True
        email_change_tokens[token]['used_at'] = time.time()


def change_user_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """修改密码"""
    try:
        from password_hash import verify_password, hash_password
        
        # 获取用户信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return False, "用户不存在"
        
        # 验证旧密码
        if not verify_password(old_password, result['password']):
            cursor.close()
            conn.close()
            return False, "原密码错误"
        
        # 验证新密码强度
        if len(new_password) < 6:
            cursor.close()
            conn.close()
            return False, "密码长度至少为6位"
        
        # 哈希新密码
        new_password_hash = hash_password(new_password)
        if not new_password_hash:
            cursor.close()
            conn.close()
            return False, "密码哈希失败"
        
        # 更新密码
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (new_password_hash, user_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'change_password', '修改密码')
        
        return True, None
        
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return False, str(e)


def reset_user_password(user_id: int, new_password: str) -> Tuple[bool, Optional[str]]:
    """重置密码（通过Token）"""
    try:
        from password_hash import hash_password
        
        # 验证新密码强度
        if len(new_password) < 6:
            return False, "密码长度至少为6位"
        
        # 哈希新密码
        new_password_hash = hash_password(new_password)
        if not new_password_hash:
            return False, "密码哈希失败"
        
        # 更新密码
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (new_password_hash, user_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'reset_password', '重置密码')
        
        return True, None
        
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        return False, str(e)


def change_user_email(user_id: int, new_email: str) -> Tuple[bool, Optional[str]]:
    """修改邮箱"""
    try:
        # 检查邮箱是否已存在
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (new_email, user_id))
        result = cursor.fetchone()
        
        if result:
            cursor.close()
            conn.close()
            return False, "该邮箱已被使用"
        
        # 更新邮箱
        cursor.execute(
            "UPDATE users SET email = %s WHERE id = %s",
            (new_email, user_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'change_email', f'修改邮箱: {new_email}')
        
        return True, None
        
    except Exception as e:
        logger.error(f"修改邮箱失败: {e}")
        return False, str(e)


def delete_user_account(user_id: int, reason: str = None) -> Tuple[bool, Optional[str]]:
    """注销账号"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return False, "用户不存在"
        
        # 记录操作日志
        log_user_action(user_id, 'delete_account', f'注销账号: {reason or ""}')
        
        # 删除用户（级联删除）
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, None
        
    except Exception as e:
        logger.error(f"注销账号失败: {e}")
        return False, str(e)


def ban_user(user_id: int, ban_reason: str = None, ban_hours: int = 24) -> Tuple[bool, Optional[str]]:
    """封禁账号"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否已被封禁
        cursor.execute("SELECT id FROM account_bans WHERE user_id = %s AND ban_end > NOW()", (user_id,))
        result = cursor.fetchone()
        
        if result:
            cursor.close()
            conn.close()
            return False, "该账号已被封禁"
        
        # 计算封禁结束时间
        ban_end = datetime.now() + timedelta(hours=ban_hours)
        
        # 插入封禁记录
        cursor.execute(
            """INSERT INTO account_bans (user_id, ban_reason, ban_end) 
               VALUES (%s, %s, %s)""",
            (user_id, ban_reason, ban_end)
        )
        
        # 更新用户状态
        cursor.execute("UPDATE users SET status = 'disabled' WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'ban_account', f'账号被封禁: {ban_reason or ""}')
        
        return True, None
        
    except Exception as e:
        logger.error(f"封禁账号失败: {e}")
        return False, str(e)


def unban_user(user_id: int, unban_reason: str = None) -> Tuple[bool, Optional[str]]:
    """解封账号"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新封禁记录
        cursor.execute(
            """UPDATE account_bans SET unbanned_at = NOW(), unban_reason = %s 
               WHERE user_id = %s AND ban_end > NOW()""",
            (unban_reason, user_id)
        )
        
        # 更新用户状态
        cursor.execute("UPDATE users SET status = 'active' WHERE id = %s", (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 记录操作日志
        log_user_action(user_id, 'unban_account', f'账号被解封: {unban_reason or ""}')
        
        return True, None
        
    except Exception as e:
        logger.error(f"解封账号失败: {e}")
        return False, str(e)


def log_user_action(user_id: int, action_type: str, action_details: str, ip_address: str = None) -> bool:
    """记录用户操作日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO account_logs (user_id, action_type, action_details, ip_address) 
               VALUES (%s, %s, %s, %s)""",
            (user_id, action_type, action_details, ip_address)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"记录用户操作日志失败: {e}")
        return False


def get_user_action_logs(user_id: int, page: int = 1, page_size: int = 20) -> Dict:
    """获取用户操作日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取日志
        cursor.execute(
            """SELECT id, action_type, action_details, ip_address, created_at 
               FROM account_logs 
               WHERE user_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (user_id, page_size, offset)
        )
        logs = cursor.fetchall()
        
        # 获取总数
        cursor.execute("SELECT COUNT(*) as total FROM account_logs WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return {
            'logs': logs,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"获取用户操作日志失败: {e}")
        return {'logs': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}


def check_user_banned(user_id: int) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """检查用户是否被封禁"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT ban_reason, ban_end FROM account_bans 
               WHERE user_id = %s AND ban_end > NOW()""",
            (user_id,)
        )
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return True, result['ban_reason'], result['ban_end']
        
        return False, None, None
        
    except Exception as e:
        logger.error(f"检查用户封禁状态失败: {e}")
        return False, None, None


def get_user_info(user_id: int) -> Optional[Dict]:
    """获取用户信息（包括资料）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, username, email, status, role, created_at 
               FROM users WHERE id = %s""",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return None
        
        # 获取用户资料
        profile = get_user_profile(user_id)
        
        cursor.close()
        conn.close()
        
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'status': user['status'],
            'role': user['role'],
            'created_at': str(user['created_at']),
            'profile': profile
        }
        
        return user_info
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return None
