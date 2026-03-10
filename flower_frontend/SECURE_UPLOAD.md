# 安全上传功能文档

## 功能概述

已实现完整的图片上传安全防护机制，防止各类上传攻击和存储问题。

## 安全防护措施

### 1. 文件大小限制

**配置**: `MAX_FILE_SIZE = 5 * 1024 * 1024` (5MB)

**实现**:
```python
def check_file_size(file_content: bytes, max_size: int = MAX_FILE_SIZE) -> bool:
    """检查文件大小"""
    return len(file_content) <= max_size
```

**作用**: 防止大文件攻击和存储空间耗尽

### 2. 文件类型白名单校验

**允许的扩展名**:
```python
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
```

**实现**:
```python
def check_file_extension(filename: str, allowed_extensions: set = ALLOWED_EXTENSIONS) -> bool:
    """检查文件扩展名是否在白名单中"""
    ext = get_file_extension(filename)
    return ext in allowed_extensions
```

**作用**: 防止上传可执行文件、脚本文件等危险类型

### 3. 图片 MIME 校验

**允许的 MIME 类型**:
```python
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp'
}
```

**实现**:
```python
def check_mime_type(file_content: bytes, allowed_mime_types: set = ALLOWED_MIME_TYPES) -> Tuple[bool, Optional[str]]:
    """检查MIME类型"""
    # 使用多种方法进行校验
    # 1. 使用mimetypes
    # 2. 使用PIL检查是否为图片
    # 3. 检查文件头（Magic Number）
```

**作用**: 防止通过修改扩展名绕过白名单校验

### 4. 恶意文件拦截

**检测的恶意模式**:
- PHP代码: `<?php`, `<?`
- JavaScript: `<script`, `javascript:`
- 事件处理器: `onerror=`, `onload=`
- 执行函数: `eval(`, `exec(`, `system(`
- Shell命令: `passthru(`, `shell_exec(`, `assert(`
- 编码函数: `base64_decode(`, `gzinflate(`

**实现**:
```python
def check_for_malicious_content(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """检查恶意内容"""
    # 检查是否包含PHP代码
    # 检查文件头
```

**作用**: 防止上传WebShell、恶意脚本等

### 5. 上传路径隔离

**实现**:
```python
def get_upload_dir(base_dir: str) -> str:
    """获取上传目录"""
    upload_dir = os.path.join(base_dir, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir
```

**作用**: 将上传文件隔离到独立目录，防止路径遍历攻击

### 6. 文件重命名防覆盖

**命名规则**: `时间戳_随机字符串.扩展名`

**实现**:
```python
def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = secrets.token_hex(8)
    secure_name = f"{timestamp}_{random_str}{ext}"
    return secure_name
```

**示例**: `20240309_143025_a1b2c3d4e5f6g7h8.jpg`

**作用**: 防止文件名冲突和路径遍历攻击

### 7. 上传失败清理机制

**实现**:
```python
def cleanup_failed_upload(filepath: str):
    """清理上传失败的文件"""
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(filepath + '.thumb.jpg'):
        os.remove(filepath + '.thumb.jpg')
```

**作用**: 防止上传失败后残留临时文件

### 8. 图片压缩与缩略图生成

**压缩配置**:
- 目标大小: 1MB
- 压缩质量: 85%
- 优化: 启用

**缩略图配置**:
- 尺寸: 200x200
- 格式: JPEG

**实现**:
```python
def compress_image(file_content: bytes, max_size: int = 1024 * 1024) -> Tuple[bytes, bool]:
    """压缩图片"""
    # 如果图片已经很小，不需要压缩
    # 转换为RGB模式（去除透明通道）
    # 压缩图片
    # 如果压缩后仍然很大，进一步压缩

def generate_thumbnail(file_content: bytes, size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
    """生成缩略图"""
    # 转换为RGB模式
    # 生成缩略图
```

**作用**: 节省存储空间，提高加载速度

## 完整验证流程

```python
def validate_upload(file_content: bytes, filename: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """验证上传文件"""
    # 1. 检查文件大小
    if not check_file_size(file_content):
        return False, None, "文件大小超过限制"
    
    # 2. 检查文件扩展名
    if not check_file_extension(filename):
        return False, None, "不支持的文件类型"
    
    # 3. 检查MIME类型
    mime_valid, mime_type = check_mime_type(file_content)
    if not mime_valid:
        return False, None, "MIME类型验证失败"
    
    # 4. 检查图片完整性
    integrity_valid, integrity_error = check_image_integrity(file_content)
    if not integrity_valid:
        return False, None, integrity_error
    
    # 5. 检查恶意内容
    malicious_valid, malicious_error = check_for_malicious_content(file_content)
    if not malicious_valid:
        return False, None, malicious_error
    
    # 6. 获取文件信息
    file_info = get_file_info(file_content)
    
    return True, file_info, None
```

## API接口

### 上传接口 `/api/upload`

**请求**:
```
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>
```

**响应**:
```json
{
    "success": true,
    "result": "rose (0.95), tulip (0.05)",
    "predictions": [...],
    "file_info": {
        "original_name": "flower.jpg",
        "saved_name": "20240309_143025_a1b2c3d4e5f6g7h8.jpg",
        "size": 524288,
        "mime_type": "image/jpeg",
        "dimensions": [800, 600]
    }
}
```

**错误响应**:
```json
{
    "success": false,
    "error": "文件大小超过限制（最大5MB）"
}
```

## 安全特性

| 特性 | 状态 | 说明 |
|------|------|------|
| 文件大小限制 | ✅ | 最大5MB |
| 文件类型白名单 | ✅ | 仅允许图片格式 |
| MIME类型校验 | ✅ | 多重校验机制 |
| 恶意文件拦截 | ✅ | 检测WebShell和恶意代码 |
| 上传路径隔离 | ✅ | 独立uploads目录 |
| 文件重命名 | ✅ | 防止路径遍历和覆盖 |
| 失败清理 | ✅ | 自动清理失败文件 |
| 图片压缩 | ✅ | 自动压缩到1MB |
| 缩略图生成 | ✅ | 生成200x200缩略图 |

## 使用示例

### 前端上传

```javascript
function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const accessToken = localStorage.getItem('access_token');
    
    $.ajax({
        url: '/api/upload',
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + accessToken
        },
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                console.log('上传成功');
                console.log('文件信息:', response.file_info);
                console.log('识别结果:', response.result);
            } else {
                console.error('上传失败:', response.error);
            }
        },
        error: function(xhr) {
            console.error('上传失败:', xhr.responseText);
        }
    });
}
```

### 后端调用

```python
from upload_manager import (
    validate_upload,
    save_upload_file,
    cleanup_failed_upload,
    get_upload_dir,
    MAX_FILE_SIZE
)

# 验证上传文件
valid, file_info, error = validate_upload(file_content, filename)
if not valid:
    return jsonify({'success': False, 'error': error})

# 保存上传文件
success, filepath, error = save_upload_file(file_content, upload_dir, filename)
if not success:
    cleanup_failed_upload(filepath)
    return jsonify({'success': False, 'error': error})
```

## 防护效果

### 防止的攻击

1. **路径遍历攻击**
   - 通过文件名检查防止 `../../etc/passwd` 等攻击
   - 通过文件重命名确保文件在指定目录

2. **WebShell上传**
   - 检测PHP、ASP等恶意代码
   - 检查文件头确保为有效图片

3. **DoS攻击**
   - 文件大小限制防止大文件攻击
   - 防止存储空间耗尽

4. **文件类型欺骗**
   - MIME类型多重校验
   - 文件头检查

5. **文件覆盖**
   - 文件重命名确保唯一性
   - 时间戳+随机字符串

6. **存储问题**
   - 图片压缩节省空间
   - 缩略图提高加载速度

## 最佳实践

1. **定期清理**
   - 定期清理过期的上传文件
   - 定期清理缩略图缓存

2. **监控日志**
   - 记录所有上传尝试
   - 监控异常上传行为

3. **备份策略**
   - 定期备份上传文件
   - 异地备份重要数据

4. **权限控制**
   - 上传目录无执行权限
   - 限制目录写入权限

## 相关文档

- [upload_manager.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/upload_manager.py) - 上传管理模块源码
- [app.py](file:///Users/ringconn/Downloads/花卉识别/myTest/flower_frontend/app.py#L560) - 上传API实现

## 更新日志

### 2024-03-09
- ✅ 创建安全上传模块
- ✅ 实现文件大小限制
- ✅ 实现文件类型白名单
- ✅ 实现MIME类型校验
- ✅ 实现恶意文件拦截
- ✅ 实现上传路径隔离
- ✅ 实现文件重命名
- ✅ 实现上传失败清理
- ✅ 实现图片压缩
- ✅ 实现缩略图生成
