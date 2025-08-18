"""
图像绘制模块

实现图像上绘制彩色框框的功能
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional, Union
import logging
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class ImageDrawer:
    """图像绘制器类"""

    def __init__(self):
        self.image_utils = ImageUtils()

    def draw_colored_boxes(
        self,
        image: Union[np.ndarray, str],
        boxes: List[Dict],
        line_thickness: Optional[int] = None
    ) -> np.ndarray:
        """
        在图像上绘制彩色框框

        Args:
            image: 输入图像（OpenCV格式的numpy数组或base64编码的字符串）
            boxes: 框框信息列表，每个元素包含：
                - points: 点的坐标列表 [(x1, y1), (x2, y2), ...]
                - color: 颜色 (R, G, B) 或颜色名称
                - thickness: 线条粗细（可选，如果未提供则使用line_thickness参数）
            line_thickness: 默认线条粗细（如果box中未指定）

        Returns:
            np.ndarray: 绘制了框框的图像
        """
        try:
            # 如果image是base64字符串，转换为OpenCV格式
            if isinstance(image, str):
                # 解码base64
                if image.startswith('data:image/'):
                    image = image.split(',')[1]
                
                import base64
                image_bytes = base64.b64decode(image)
                from PIL import Image
                import io
                pil_image = Image.open(io.BytesIO(image_bytes))
                cv_image = self.image_utils.pil_to_cv2(pil_image)
            else:
                # 确保是OpenCV格式的numpy数组
                cv_image = image.copy()

            # 设置默认线条粗细
            if line_thickness is None:
                # 根据图像大小自动计算线条粗细
                height, width = cv_image.shape[:2]
                line_thickness = max(1, min(height, width) // 150)
                logger.info(f"自动计算线条粗细: {line_thickness}")

            # 在图像上绘制每个框框
            result_image = cv_image.copy()
            
            for i, box in enumerate(boxes):
                try:
                    # 获取框框的点
                    points = box.get('points')
                    if not points or len(points) < 2:
                        logger.warning(f"Box {i} 至少需要2个点")
                        continue

                    # 转换点为numpy数组
                    points_array = np.array(points, dtype=np.int32)
                    
                    # 获取颜色
                    color = box.get('color', (255, 0, 0))  # 默认红色 (RGB格式)
                    if isinstance(color, list) or isinstance(color, tuple):
                        # 确保颜色是BGR格式 (OpenCV使用BGR)
                        if len(color) == 3:
                            color = (color[2], color[1], color[0])  # RGB转BGR
                        else:
                            color = (0, 0, 255)  # 默认红色 (BGR)
                    elif isinstance(color, str):
                        color = self._color_name_to_bgr(color)
                    else:
                        color = (0, 0, 255)  # 默认红色 (BGR)
                    
                    # 获取线条粗细
                    thickness = box.get('thickness', line_thickness)
                    
                    # 根据点的数量选择绘制方式
                    if len(points) == 2:
                        # 绘制线段
                        pt1 = tuple(points[0])
                        pt2 = tuple(points[1])
                        cv2.line(result_image, pt1, pt2, color, thickness)
                        logger.info(f"成功绘制第 {i+1} 条线段")
                    elif len(points) == 4:
                        # 绘制四边形框框
                        cv2.polylines(
                            result_image, 
                            [points_array], 
                            isClosed=True, 
                            color=color, 
                            thickness=thickness
                        )
                        logger.info(f"成功绘制第 {i+1} 个四边形框框")
                    else:
                        # 绘制多边形
                        cv2.polylines(
                            result_image, 
                            [points_array], 
                            isClosed=True, 
                            color=color, 
                            thickness=thickness
                        )
                        logger.info(f"成功绘制第 {i+1} 个多边形，包含 {len(points)} 个点")
                    
                except Exception as e:
                    logger.error(f"绘制第 {i+1} 个图形时出错: {str(e)}")
                    continue

            logger.info(f"成功在图像上绘制 {len(boxes)} 个图形")
            return result_image

        except Exception as e:
            logger.error(f"绘制彩色框框失败: {str(e)}")
            # 返回原图作为失败保护
            if isinstance(image, str):
                # 如果是base64字符串，需要返回OpenCV格式
                if image.startswith('data:image/'):
                    image = image.split(',')[1]
                import base64
                image_bytes = base64.b64decode(image)
                from PIL import Image
                import io
                pil_image = Image.open(io.BytesIO(image_bytes))
                return self.image_utils.pil_to_cv2(pil_image)
            else:
                return image

    def _color_name_to_bgr(self, color_name: str) -> Tuple[int, int, int]:
        """
        将颜色名称转换为BGR值

        Args:
            color_name: 颜色名称

        Returns:
            Tuple[int, int, int]: BGR颜色值
        """
        color_map = {
            'red': (0, 0, 255),
            'green': (0, 255, 0),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'cyan': (255, 255, 0),
            'magenta': (255, 0, 255),
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'orange': (0, 165, 255),
            'purple': (128, 0, 128),
        }
        
        # 如果颜色名称存在，返回对应的BGR值
        if color_name.lower() in color_map:
            return color_map[color_name.lower()]
        
        # 默认返回红色
        logger.warning(f"未知的颜色名称: {color_name}，使用默认红色")
        return (0, 0, 255)