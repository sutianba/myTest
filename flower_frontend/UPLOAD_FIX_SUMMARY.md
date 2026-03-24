# Flask 后端图片上传和识别记录存储修复说明

## 修复内容

### 1. 数据库表结构修复

#### 修改的文件：
- ✅ `db_init.py` - 添加了缺失字段到 `recognition_results` 表
- ✅ `flower_recognition.sql` - 添加了缺失字段到 `recognition_results` 表
- ✅ 新增 `migrate_db.py` - 数据库迁移脚本

#### 添加的字段：
```sql
shoot_time TEXT        -- 拍摄时间
shoot_year INTEGER     -- 拍摄年份
shoot_month INTEGER    -- 拍摄月份
shoot_season TEXT      -- 拍摄季节
latitude REAL          -- 纬度
longitude REAL         -- 经度
location_text TEXT     -- 位置文本
region_label TEXT      -- 区域标签
final_category TEXT    -- 最终分类
deleted_at INTEGER     -- 删除时间（软删除）
```

### 2. 图片保存路径修复

#### 修改的文件：
- ✅ `app.py` - 修改图片保存路径

#### 修改内容：
```python
# 修改前
uploads_dir = os.path.join(BASE_DIR, 'static', 'uploads')
relative_path = f"/static/uploads/{image_filename}"

# 修改后
uploads_dir = os.path.join(BASE_DIR, 'static', 'uploads', 'recognition')
relative_path = f"/static/uploads/recognition/{image_filename}"
```

**说明**：识别图片现在保存到 `static/uploads/recognition/` 子目录，与帖子图片（`static/uploads/posts/`）分开管理。

### 3. 相册图片关联修复

#### 修改的文件：
- ✅ `db.py` - 修复 `add_image_to_album` 函数

#### 修改内容：
```python
# 修改前
cursor.execute(
    "INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
    (album_id, user_id, image_path, image_name, image_description, now)
)

# 修改后
cursor.execute(
    "INSERT INTO album_images (album_id, user_id, image_path, image_name, image_description, recognition_result_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (album_id, user_id, image_path, image_name, image_description, recognition_result_id, now)
)
```

**说明**：现在 `album_images` 表正确关联了 `recognition_result_id`，可以通过外键找到完整的识别记录。

## 数据流程

### 完整的图片上传和识别流程：

1. **前端上传** → Base64 编码的图片数据
2. **后端接收** → `app.py` 的 `process_single_image` 函数
3. **图片保存** → 保存到 `static/uploads/recognition/` 目录
4. **识别处理** → YOLOv5 模型识别花卉
5. **提取信息** → EXIF 信息（时间、GPS 等）
6. **保存识别结果** → `recognition_results` 表（包含所有分类信息）
7. **创建/查找相册** → 根据花卉名称自动创建相册
8. **添加图片到相册** → `album_images` 表（关联 `recognition_result_id`）
9. **更新图片计数** → `albums.image_count` 自动 +1

### 数据库表关系：

```
users (用户表)
  ↓
  └── recognition_results (识别结果表)
        - user_id (外键)
        - image_path (图片路径)
        - result (花卉名称)
        - confidence (置信度)
        - shoot_time, shoot_year, shoot_month, shoot_season (时间信息)
        - latitude, longitude, location_text, region_label (位置信息)
        - final_category (最终分类)
        ↓
        └── album_images (相册图片表)
              - recognition_result_id (外键关联)
              - album_id (外键)
              - image_path
              - flower_name
              - confidence
              ↓
              └── albums (相册表)
                    - user_id
                    - name
                    - category
                    - image_count (自动更新)
```

## 使用方法

### 1. 运行数据库迁移（仅 SQLite）

如果已经存在旧的数据库文件，运行迁移脚本：

```bash
cd flower_frontend
python migrate_db.py
```

### 2. 重新初始化数据库（可选）

如果需要完全重新初始化：

```bash
cd flower_frontend
python db_init.py
```

### 3. 启动 Flask 应用

```bash
cd flower_frontend
python app.py
```

## 验证步骤

### 1. 检查数据库表结构

```sql
-- SQLite
PRAGMA table_info(recognition_results);

-- MySQL
DESC recognition_results;
```

应该看到所有新增的字段。

### 2. 测试图片上传

1. 访问前端页面
2. 上传一张花卉图片
3. 勾选"识别后保存到相册"
4. 查看控制台日志，确认：
   - 图片保存到正确路径
   - 识别结果保存到数据库
   - 相册自动创建
   - 图片添加到相册

### 3. 检查数据库记录

```sql
-- 查看识别结果
SELECT * FROM recognition_results ORDER BY created_at DESC LIMIT 5;

-- 查看相册图片
SELECT * FROM album_images ORDER BY created_at DESC LIMIT 5;

-- 查看相册及图片数量
SELECT id, name, category, image_count FROM albums;
```

## 注意事项

1. **不要修改数据库结构** - 已按照要求保持 MySQL 数据库格式不变
2. **小改动** - 只修改了必要的字段和路径，没有大规模重构
3. **向后兼容** - 迁移脚本确保现有数据库可以升级
4. **图片分类存储** - 识别图片和帖子图片分别存储在不同子目录

## 修复完成清单

- ✅ SQLite 数据库表结构添加缺失字段
- ✅ MySQL 数据库表结构保持不变（已经完整）
- ✅ 图片保存到正确的子目录 `static/uploads/recognition/`
- ✅ 识别记录完整存储（分类、时间、位置等）
- ✅ 相册图片正确关联识别结果
- ✅ 图片数量自动更新
- ✅ 数据库迁移脚本
- ✅ 详细的修复说明文档
