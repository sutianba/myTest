# 花卉识别AI系统 - 前端界面

这是一个基于HTML、CSS和JavaScript开发的花卉识别系统前端界面，与YOLOv5后端模型配合使用。

## 功能特点

- 🎨 现代化、美观的用户界面
- 📁 支持拖拽上传图片
- ⚡ 实时图片预览
- 📊 清晰的识别结果展示
- 📱 响应式设计，支持移动端

## 技术栈

- HTML5
- CSS3
- JavaScript (ES6+)
- Flask (后端API)

## 安装和运行

### 1. 安装后端依赖

在项目根目录下运行：

```bash
pip install -r requirements.txt
```

### 2. 安装前端API依赖

在`flower_frontend`目录下运行：

```bash
pip install -r requirements.txt
```

### 3. 启动Flask服务器

在`flower_frontend`目录下运行：

```bash
python app.py
```

服务器将在`http://localhost:5000`启动。

### 4. 访问前端界面

在浏览器中访问：

```
http://localhost:5000
```

## 使用说明

1. **上传图片**：
   - 拖拽图片到上传区域
   - 或点击"选择花卉图片"按钮选择文件

2. **查看结果**：
   - 系统将自动识别图片中的花卉
   - 识别结果将显示花卉名称和置信度
   - 支持上传多张图片进行连续识别

## 项目结构

```
flower_frontend/
├── index.html          # 前端主页面
├── app.py             # Flask后端API
├── requirements.txt   # 后端依赖
└── README.md          # 项目说明
```

## 注意事项

1. 确保已经安装了YOLOv5模型文件`testflowers.pt`，并放置在项目根目录下
2. 确保Flask服务器正在运行
3. 推荐使用Chrome、Firefox等现代浏览器

## 开发说明

前端界面采用了模块化设计，易于扩展和定制：

- `index.html`：包含页面结构和样式
- `app.py`：处理图片上传和花卉识别逻辑
- 可以根据需要修改UI样式、添加新功能或优化识别算法

## License

MIT

----------------------------------
# TODO
 - [ ] 优化【识别分类】的操作，增加识别结果导出功能
 - [ ] 内存配比问题（很困难，优先级往后放）
 - [ ] 【识别分类】图片是略缩图，这个跟内存有关，但是不好放大？有待处理