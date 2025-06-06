# DocuScan API

一个基于 FastAPI 的专业文档扫描 API，支持将照片转换为扫描风格的文档，提供 Web UI 界面和 REST API。

## 功能特性

- 🌐 **Web UI 界面**: 支持拖拽、粘贴、点击上传图片
- 📝 **专业文档扫描**: 多种扫描模式（自然、平衡、标准、OCR、打印优化）
- 🔍 **文档质量分析**: 自动检测文档质量并提供改进建议
- 🖼️ **多格式支持**: JPEG, PNG, GIF, BMP, WEBP
- 🔄 **图片对比**: 显示处理前后的图片对比
- 📥 **一键下载**: 处理后可直接下载图片
- ⌨️ **快捷键支持**: 键盘快捷操作
- 🛡️ **错误处理**: 详细的错误提示和日志记录
- 📱 **响应式设计**: 支持移动端和桌面端
- 🐳 **Docker 支持**: 容器化部署

## 快速开始

### 使用 Docker

#### 1. 构建和运行
```bash
# 构建镜像
docker build -t docuscan .

# 运行容器
docker run -p 8000:8000 docuscan
```

#### 2. 使用 Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

访问 `http://localhost:8000` 开始使用！

### 本地开发安装

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

3. 启动服务器：
```bash
# 开发模式（热重载）
python -m uvicorn src.docuscan.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
python -m uvicorn src.docuscan.main:app --host 0.0.0.0 --port 8000
```

## Docker 部署

### 基本使用
```bash
# 停止服务
docker-compose down

# 重新构建
docker-compose up --build -d
```

## 使用方法

### Web UI 界面

访问 `http://localhost:8000` 打开 Web 界面，支持以下操作：

#### 上传图片
- 拖拽图片到上传区域
- 粘贴图片 (`Ctrl+V`)
- 点击选择文件

#### 快捷键
- `Enter`: 处理图片
- `Ctrl+V`: 粘贴图片
- `Ctrl+R`: 重置

### API 端点

#### 1. 专业文档扫描
- **URL**: `POST /scan-document`
- **描述**: 专业文档扫描，支持多种模式
- **请求体**:
  ```json
  {
    "img": "base64_encoded_image_string",
    "mode": "balanced",  // natural, balanced, standard, ocr, printing
    "config": {}  // 可选的自定义配置
  }
  ```

#### 2. 通用图片处理
- **URL**: `POST /process-image`
- **描述**: 通用图片处理
- **请求体**:
  ```json
  {
    "img": "base64_encoded_image_string",
    "config": {}  // 可选配置
  }
  ```

#### 3. 文档质量分析
- **URL**: `POST /analyze-document-quality`
- **描述**: 分析文档图像质量并提供改进建议
- **请求体**:
  ```json
  {
    "img": "base64_encoded_image_string"
  }
  ```

#### 4. 获取配置信息
- **URL**: `GET /processing-config`
- **描述**: 获取支持的处理配置和扫描模式

### 扫描模式

- **natural**: 自然模式，保留原图特征
- **balanced**: 平衡模式（推荐）
- **standard**: 标准扫描模式
- **ocr**: OCR优化模式
- **printing**: 打印优化模式

### 请求示例

#### 使用 curl

```bash
# 专业文档扫描
curl -X POST "http://localhost:8000/scan-document" \
     -H "Content-Type: application/json" \
     -d '{"img":"base64_string", "mode":"balanced"}' \
     --output scanned_document.jpg

# 文档质量分析
curl -X POST "http://localhost:8000/analyze-document-quality" \
     -H "Content-Type: application/json" \
     -d '{"img":"base64_string"}' | jq '.'

# 获取配置信息
curl -X GET "http://localhost:8000/processing-config" | jq '.'
```

#### 使用 Python

```python
import requests
import base64
import json

# 读取本地图片并转换为 base64
with open("document.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode('utf-8')

# 专业文档扫描
response = requests.post(
    "http://localhost:8000/scan-document",
    json={
        "img": img_data,
        "mode": "balanced"  # 或其他模式
    }
)

if response.status_code == 200:
    with open("scanned_document.jpg", "wb") as f:
        f.write(response.content)
    print("✅ 文档扫描成功！")
else:
    print("❌ 扫描失败:", response.text)

# 文档质量分析
quality_response = requests.post(
    "http://localhost:8000/analyze-document-quality",
    json={"img": img_data}
)

if quality_response.status_code == 200:
    quality_report = quality_response.json()
    print("📊 质量分析结果:")
    print(json.dumps(quality_report, indent=2, ensure_ascii=False))
```

#### 使用 JavaScript

```javascript
// 文件转 base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// 扫描文档
async function scanDocument(file, mode = 'balanced') {
    try {
        const base64 = await fileToBase64(file);
        
        const response = await fetch('/scan-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                img: base64,
                mode: mode
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scanned_document_${mode}.jpg`;
            a.click();
            console.log('✅ 文档扫描完成！');
        } else {
            console.error('❌ 扫描失败:', await response.text());
        }
    } catch (error) {
        console.error('❌ 错误:', error);
    }
}
```

## API 文档

启动服务器后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 开发

### 本地开发
```bash
# 安装依赖
rye sync

# 启动开发服务器
python -m uvicorn src.docuscan.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 开发
```bash
# 使用 Docker Compose 开发
docker-compose up --build
```

## 支持的图片格式

- JPEG/JPG
- PNG  
- GIF
- BMP
- WEBP

## 许可证

本项目使用 MIT 许可证。

## 联系方式

- 作者: pingfury  
- 邮箱: pingfury@outlook.com