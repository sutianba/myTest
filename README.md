# 基于Python的园艺相册自动分类工具

## 项目简介

本项目是一个基于Python的园艺相册自动分类工具，旨在帮助用户管理和分类他们的园艺照片，通过人工智能技术自动识别植物种类，并提供相册管理功能。

## 主要功能

- **用户认证**：注册、登录、退出登录
- **相册管理**：创建、查看、更新、删除相册
- **图片上传**：支持批量上传图片到相册
- **自动分类**：使用AI模型自动识别植物种类
- **图片管理**：查看、更新、删除图片
- **标签管理**：创建和管理图片标签
- **响应式设计**：适配不同设备屏幕

## 技术栈

### 后端
- **Python 3.8+**
- **Flask**：Web框架
- **MySQL**：数据库
- **OpenCV**：图像处理
- **TensorFlow/PyTorch**：机器学习模型
- **JWT**：用户认证
- **Flask-CORS**：跨域支持

### 前端
- **React 18**：前端框架
- **TypeScript**：类型系统
- **Tailwind CSS**：样式框架
- **React Router**：路由管理
- **Framer Motion**：动画效果
- **Sonner**：通知组件

## 项目结构

```
myTest/
├── flower_frontend/         # 后端代码
│   ├── app.py               # 主应用文件
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── image_processor.py   # 图片处理和分类引擎
│   ├── upload_manager.py    # 文件上传管理
│   ├── flower_recognition.sql # 数据库结构
│   └── run_app.py           # 启动脚本
├── qianduan/                # 前端代码
│   ├── src/
│   │   ├── components/      # 通用组件
│   │   ├── contexts/        # 上下文管理
│   │   ├── pages/           # 页面组件
│   │   ├── types/           # TypeScript类型定义
│   │   ├── App.tsx          # 应用入口
│   │   └── main.tsx         # 主渲染文件
│   ├── index.html           # HTML模板
│   ├── package.json         # 项目配置
│   └── vite.config.ts       # Vite配置
├── models/                  # 机器学习模型
└── uploads/                 # 上传文件存储
```

## 环境配置

### 后端环境
1. 安装Python 3.8+
2. 安装依赖：
   ```bash
   pip install -r flower_frontend/requirements-frontend.txt
   ```
3. 配置数据库：
   - 修改 `flower_frontend/config.py` 中的数据库配置
   - 运行 `flower_recognition.sql` 创建数据库表结构

### 前端环境
1. 安装Node.js 16+
2. 安装依赖：
   ```bash
   cd qianduan && pnpm install
   ```

## 运行项目

### 后端服务
```bash
cd flower_frontend && python run_app.py
```
后端服务将运行在 `http://localhost:5000`

### 前端服务
```bash
cd qianduan && pnpm dev
```
前端服务将运行在 `http://localhost:3000`

## API文档

后端API文档可以通过以下地址访问：
- Swagger UI: `http://localhost:5000/api/docs`

## 核心API

### 认证API
- `POST /api/register`：用户注册
- `POST /api/login`：用户登录
- `POST /api/logout`：用户退出登录

### 相册API
- `GET /api/albums`：获取相册列表
- `POST /api/albums`：创建相册
- `GET /api/albums/:id`：获取相册详情
- `PUT /api/albums/:id`：更新相册
- `DELETE /api/albums/:id`：删除相册

### 图片API
- `POST /api/photos/upload`：上传图片
- `GET /api/photos/:id`：获取图片详情
- `PUT /api/photos/:id`：更新图片信息
- `DELETE /api/photos/:id`：删除图片

### 分类API
- `POST /api/classify`：批量分类图片

### 标签API
- `GET /api/tags`：获取标签列表
- `POST /api/tags`：创建标签

## 部署方案

### 开发环境
- 使用 `python run_app.py` 启动后端
- 使用 `pnpm dev` 启动前端

### 生产环境
1. 构建前端：
   ```bash
   cd qianduan && pnpm build
   ```
2. 将构建产物复制到后端的静态文件目录
3. 使用 Gunicorn 或 uWSGI 启动后端服务
4. 配置 Nginx 作为反向代理

## 注意事项

- 确保MySQL数据库服务正在运行
- 确保上传目录有写入权限
- 首次运行时，系统会自动创建必要的目录结构
- 模型文件需要单独下载并放置在 `models` 目录中

## 许可证

本项目采用 MIT 许可证。
