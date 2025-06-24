from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
from PIL import Image
import logging
import os
import numpy as np
from .processing import DocumentScanner

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuScan API",
    description="专业文档扫描API - 将照片转换为扫描风格的文档",
    version="0.1.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 初始化文档扫描器
document_scanner = DocumentScanner()

# 设置静态文件服务
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

class ImageRequest(BaseModel):
    img: str  # base64 编码的图片字符串
    config: dict = None  # 自定义配置（可选）

class DocumentScanRequest(BaseModel):
    img: str  # base64 编码的图片字符串
    mode: str = "balanced"  # 扫描模式: "natural", "balanced", "standard", "ocr", "printing"
    config: dict = None  # 自定义配置（可选）

@app.get("/")
async def get_ui():
    """
    返回图片处理UI页面
    """
    html_file_path = os.path.join(static_path, "index.html")
    return FileResponse(html_file_path)

@app.post("/process-image")
async def process_image(request: ImageRequest):
    """
    接受base64格式的图片，进行文档扫描处理后返回扫描风格的文档图像
    """
    try:
        # 解码base64图片
        # 如果base64字符串包含数据URL前缀，则去除它
        img_data = request.img
        if img_data.startswith('data:image/'):
            # 移除 "data:image/jpeg;base64," 这样的前缀
            img_data = img_data.split(',')[1]

        # 解码base64
        image_bytes = base64.b64decode(img_data)

        # 使用PIL打开图片进行验证
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为RGB模式（如果不是的话）
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        logger.info(f"开始处理图像，原始尺寸: {pil_image.size}")

        # 准备处理配置
        processing_config = request.config if request.config else {}
        
        # 使用文档扫描器处理图像
        scan_result = document_scanner.scan_document(pil_image, config=processing_config)
        processed_cv_image = scan_result['final_image']
        
        # 转换回PIL图像
        from .processing.utils import ImageUtils
        image_utils = ImageUtils()
        processed_pil_image = image_utils.cv2_to_pil(processed_cv_image)

        # 将处理后的图片转换为字节流
        output_buffer = io.BytesIO()
        
        # 保存为JPEG格式（文档扫描通常使用JPEG）
        processed_pil_image.save(output_buffer, format='JPEG', quality=95, optimize=True)
        processed_image_bytes = output_buffer.getvalue()

        logger.info(f"图像处理完成。原始尺寸: {scan_result['original_size']}, "
                   f"最终尺寸: {scan_result['final_size']}, "
                   f"输出大小: {len(processed_image_bytes)} bytes")

        # 返回处理后的图片
        return Response(
            content=processed_image_bytes,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": "inline; filename=scanned_document.jpg",
                "X-Original-Size": f"{scan_result['original_size'][0]}x{scan_result['original_size'][1]}",
                "X-Final-Size": f"{scan_result['final_size'][0]}x{scan_result['final_size'][1]}",
                "X-Processing-Info": "Document scanning completed successfully"
            }
        )

    except base64.binascii.Error:
        logger.error("Invalid base64 encoding")
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/scan-document")
async def scan_document(request: DocumentScanRequest):
    """
    专业文档扫描接口，支持多种扫描模式
    """
    try:
        # 解码base64图片
        img_data = request.img
        if img_data.startswith('data:image/'):
            img_data = img_data.split(',')[1]

        image_bytes = base64.b64decode(img_data)
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        logger.info(f"开始文档扫描，模式: {request.mode}, 原始尺寸: {pil_image.size}")

        # 根据模式选择处理方法
        from .processing.utils import ImageUtils
        image_utils = ImageUtils()
        cv_image = image_utils.pil_to_cv2(pil_image)
        
        if request.mode == "ocr":
            processed_cv_image = document_scanner.scan_for_ocr(cv_image)
        elif request.mode == "printing":
            processed_cv_image = document_scanner.scan_for_printing(cv_image)
        elif request.mode == "balanced":
            # 使用平衡配置，避免过度增白
            balanced_config = document_scanner.get_balanced_config()
            scan_result = document_scanner.scan_document(cv_image, config=balanced_config)
            processed_cv_image = scan_result['final_image']
        elif request.mode == "natural":
            # 使用自然配置，最大程度保留原图特征
            natural_config = document_scanner.get_natural_config()
            scan_result = document_scanner.scan_document(cv_image, config=natural_config)
            processed_cv_image = scan_result['final_image']
        elif request.mode == "custom" and request.config:
            scan_result = document_scanner.scan_document(cv_image, config=request.config)
            processed_cv_image = scan_result['final_image']
        else:  # standard mode
            processed_cv_image = document_scanner.quick_scan(cv_image)

        # 转换回PIL并保存
        processed_pil_image = image_utils.cv2_to_pil(processed_cv_image)
        output_buffer = io.BytesIO()
        processed_pil_image.save(output_buffer, format='JPEG', quality=95, optimize=True)
        processed_image_bytes = output_buffer.getvalue()

        logger.info(f"文档扫描完成，模式: {request.mode}, 输出大小: {len(processed_image_bytes)} bytes")

        return Response(
            content=processed_image_bytes,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=scanned_document_{request.mode}.jpg",
                "X-Scan-Mode": request.mode,
                "X-Processing-Info": f"Document scanned in {request.mode} mode"
            }
        )

    except Exception as e:
        logger.error(f"文档扫描失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document scanning failed: {str(e)}")


@app.post("/analyze-document-quality")
async def analyze_document_quality(request: ImageRequest):
    """
    分析文档图像质量并提供改进建议
    """
    try:
        # 解码图片
        img_data = request.img
        if img_data.startswith('data:image/'):
            img_data = img_data.split(',')[1]

        image_bytes = base64.b64decode(img_data)
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # 转换为OpenCV格式并分析
        from .processing.utils import ImageUtils
        image_utils = ImageUtils()
        cv_image = image_utils.pil_to_cv2(pil_image)
        
        quality_report = document_scanner.detect_document_quality(cv_image)
        
        logger.info(f"文档质量分析完成，整体评分: {quality_report.get('overall', {}).get('score', 0)}")
        
        return {
            "status": "success",
            "quality_report": quality_report,
            "image_size": pil_image.size
        }

    except Exception as e:
        logger.error(f"文档质量分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")


@app.get("/processing-config")
async def get_processing_config():
    """
    获取默认处理配置
    """
    try:
        config = document_scanner.get_default_config()
        return {
            "status": "success",
            "default_config": config,
            "supported_formats": document_scanner.get_supported_formats(),
            "scan_modes": {
                "natural": "自然模式，最大程度保留原图特征（图片太暗时推荐）",
                "balanced": "平衡模式，温和处理避免过度增白（默认推荐）",
                "standard": "标准扫描模式，适合一般文档",
                "ocr": "OCR优化模式，生成二值化图像便于文字识别",
                "printing": "打印优化模式，保持高质量适合打印",
                "custom": "自定义模式，可指定详细配置参数"
            }
        }
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
