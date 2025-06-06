from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import base64
import io
from PIL import Image
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuScan API",
    description="API for processing base64 images",
    version="0.1.0"
)

# 设置静态文件服务
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

class ImageRequest(BaseModel):
    img: str  # base64 编码的图片字符串

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
    接受base64格式的图片，处理后返回图片格式的响应
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

        # 使用PIL打开图片进行验证和处理
        image = Image.open(io.BytesIO(image_bytes))

        # 这里可以添加你的图片处理逻辑
        # 例如：调整大小、格式转换、添加水印等
        # 目前只是简单地返回原图

        # 将图片转换为字节流
        output_buffer = io.BytesIO()

        # 确定输出格式
        format_mapping = {
            'JPEG': 'JPEG',
            'PNG': 'PNG',
            'GIF': 'GIF',
            'BMP': 'BMP',
            'WEBP': 'WEBP'
        }

        output_format = format_mapping.get(image.format, 'JPEG')

        # 如果是JPEG格式，确保没有透明通道
        if output_format == 'JPEG' and image.mode in ('RGBA', 'LA'):
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            else:
                background.paste(image)
            image = background

        # 保存处理后的图片
        image.save(output_buffer, format=output_format, quality=95)
        image_bytes = output_buffer.getvalue()

        # 确定MIME类型
        mime_types = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'BMP': 'image/bmp',
            'WEBP': 'image/webp'
        }

        media_type = mime_types.get(output_format, 'image/jpeg')

        logger.info(f"Successfully processed image. Format: {output_format}, Size: {len(image_bytes)} bytes")

        # 返回图片响应
        return Response(
            content=image_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=processed_image.{output_format.lower()}"
            }
        )

    except base64.binascii.Error:
        logger.error("Invalid base64 encoding")
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
