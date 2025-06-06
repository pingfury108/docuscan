# DocuScan API

一个基于 FastAPI 的图片处理 API，提供 Web UI 界面和 REST API，支持图片上传、处理和下载。

## 功能特性

- 🌐 **Web UI 界面**: 支持拖拽、粘贴、点击上传图片
- 📝 **REST API**: 接受 base64 编码的图片数据
- 🖼️ **多格式支持**: JPEG, PNG, GIF, BMP, WEBP
- 🔄 **图片对比**: 显示处理前后的图片对比
- 📥 **一键下载**: 处理后可直接下载图片
- ⌨️ **快捷键支持**: 键盘快捷操作
- 🛡️ **错误处理**: 详细的错误提示和日志记录
- 📱 **响应式设计**: 支持移动端和桌面端

## 安装

1. 克隆项目：
```bash
git clone <repository-url>
cd docuscan
```

2. 安装依赖：
```bash
pip install -r requirements.lock
# 或者使用 rye
rye sync
```

## 快速开始

### 启动服务器

```bash
# 方式1: 普通启动
python run.py

# 方式2: 测试模式（自动打开浏览器）
python test_ui.py
```

服务器将在 `http://localhost:8000` 启动。

## 使用方法

### Web UI 界面

访问 `http://localhost:8000` 打开 Web 界面，支持以下操作：

#### 上传图片
- **拖拽上传**: 直接将图片文件拖拽到上传区域
- **粘贴上传**: 使用 `Ctrl+V` 粘贴剪贴板中的图片
- **点击上传**: 点击上传区域选择本地文件

#### 快捷键
- `Enter`: 处理当前上传的图片
- `Ctrl+V`: 粘贴图片
- `Ctrl+R`: 重置工具，清除所有内容

#### 功能说明
1. 上传图片后，界面会显示原始图片预览
2. 点击"处理图片"按钮进行处理
3. 处理完成后显示前后对比效果
4. 可以下载处理后的图片或重新开始

#### 支持特性
- 文件大小限制：最大 10MB
- 支持格式：JPEG, PNG, GIF, BMP, WEBP
- 自动错误提示和处理状态显示
- 响应式设计，支持手机和平板

### API 端点

#### 1. Web UI 界面
- **URL**: `GET /`
- **描述**: 返回图片处理 Web 界面

#### 2. 静态文件
- **URL**: `GET /static/*`
- **描述**: 提供 CSS、JS 等静态文件

#### 3. 图片处理 API
- **URL**: `POST /process-image`
- **描述**: 处理 base64 格式的图片
- **请求体**:
  ```json
  {
    "img": "base64_encoded_image_string"
  }
  ```
- **响应**: 返回处理后的图片文件

### 请求示例

#### 使用 curl

```bash
# 基本的 base64 图片数据
curl -X POST "http://localhost:8000/process-image" \
     -H "Content-Type: application/json" \
     -d '{"img":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}' \
     --output output.png

# 带有 data URL 前缀的图片数据
curl -X POST "http://localhost:8000/process-image" \
     -H "Content-Type: application/json" \
     -d '{"img":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}' \
     --output output_dataurl.png
```

#### 使用 Python

```python
import requests
import base64

# 读取本地图片并转换为 base64
with open("input_image.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
response = requests.post(
    "http://localhost:8000/process-image",
    json={"img": img_data}
)

# 保存返回的图片
if response.status_code == 200:
    with open("output_image.jpg", "wb") as f:
        f.write(response.content)
    print("图片处理成功！")
else:
    print(f"请求失败: {response.text}")
```

#### 使用 JavaScript

```javascript
// 将文件转换为 base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// 发送请求
async function processImage(file) {
    try {
        const base64 = await fileToBase64(file);
        
        const response = await fetch('http://localhost:8000/process-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                img: base64
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            // 创建下载链接
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'processed_image.jpg';
            a.click();
        } else {
            console.error('请求失败:', await response.text());
        }
    } catch (error) {
        console.error('错误:', error);
    }
}
```

## 测试

### Web UI 测试

```bash
# 启动测试服务器（自动打开浏览器）
python test_ui.py
```

### API 测试

```bash
# 运行 API 测试脚本
python test_api.py
```

测试脚本将：
1. 创建一个测试图片
2. 测试所有 API 端点
3. 验证不同格式的 base64 输入
4. 保存处理后的图片到本地

### 手动测试步骤

1. 启动服务器: `python run.py`
2. 打开浏览器访问: `http://localhost:8000`
3. 尝试以下操作：
   - 拖拽图片到上传区域
   - 复制图片后按 `Ctrl+V` 粘贴
   - 点击上传区域选择文件
   - 使用快捷键操作

## API 文档

启动服务器后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 支持的图片格式

### 输入格式
- JPEG/JPG
- PNG
- GIF
- BMP
- WEBP

### 输出格式
API 会保持原始图片格式，或在必要时进行智能转换（例如，将带透明通道的图片转换为 JPEG 时会添加白色背景）。

## 错误处理

API 提供详细的错误信息：

- `400 Bad Request`: 无效的 base64 编码或图片数据
- `422 Unprocessable Entity`: 请求格式错误
- `500 Internal Server Error`: 服务器内部错误

## 配置

### 环境变量
- `HOST`: 服务器主机地址（默认: 0.0.0.0）
- `PORT`: 服务器端口（默认: 8000）
- `LOG_LEVEL`: 日志级别（默认: info）

### 修改配置
编辑 `run.py` 文件来修改服务器配置：

```python
uvicorn.run(
    app,
    host="0.0.0.0",      # 修改主机地址
    port=8000,           # 修改端口
    reload=True,         # 开发模式
    log_level="info"     # 日志级别
)
```

## 开发

### 项目结构
```
docuscan/
├── src/
│   └── docuscan/
│       ├── __init__.py
│       └── main.py          # 主应用文件
├── static/                  # 静态文件目录
│   ├── index.html          # Web UI 界面
│   ├── style.css           # 样式文件
│   └── script.js           # JavaScript 文件
├── run.py                   # 启动脚本
├── test_api.py             # API 测试脚本
├── test_ui.py              # UI 测试脚本
├── pyproject.toml          # 项目配置
└── README.md               # 本文件
```

### 添加新功能

#### 后端功能
1. 编辑 `src/docuscan/main.py`
2. 在 `process_image` 函数中添加图片处理逻辑
3. 运行测试确保功能正常

#### 前端功能
1. 修改 `static/index.html` 添加新的 UI 元素
2. 在 `static/style.css` 中添加样式
3. 在 `static/script.js` 中添加交互逻辑
4. 测试新功能的用户体验

### 扩展图片处理功能
你可以在 `process_image` 函数中添加各种图片处理操作：

```python
# 调整图片大小
image = image.resize((new_width, new_height))

# 旋转图片
image = image.rotate(90)

# 应用滤镜
from PIL import ImageFilter
image = image.filter(ImageFilter.BLUR)

# 转换格式
image = image.convert('RGB')
```

## 界面截图

### 主界面
- 简洁的拖拽上传区域
- 支持多种上传方式的提示
- Bootstrap 响应式设计

### 处理界面
- 原始图片预览
- 一键处理按钮
- 加载状态指示

### 结果界面
- 前后对比显示
- 下载和重置按钮
- 操作快捷键提示

## 浏览器支持

- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

## 许可证

本项目使用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 作者: pingfury
- 邮箱: pingfury@outlook.com