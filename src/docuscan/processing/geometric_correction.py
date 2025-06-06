"""
几何校正模块

实现文档图像的几何校正功能，包括：
- 去偏斜 (Deskewing)
- 透视校正 (Perspective Transformation)
- 边框检测与裁剪 (Border Detection and Cropping)
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
import logging
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class GeometricCorrector:
    """几何校正器类"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def correct_document(self, image: np.ndarray, 
                        enable_perspective: bool = True,
                        enable_deskew: bool = True,
                        enable_crop: bool = True) -> np.ndarray:
        """
        对文档图像进行完整的几何校正
        
        Args:
            image: 输入图像
            enable_perspective: 是否启用透视校正
            enable_deskew: 是否启用去偏斜
            enable_crop: 是否启用裁剪
            
        Returns:
            np.ndarray: 校正后的图像
        """
        result = image.copy()
        
        try:
            # 1. 透视校正（如果启用）
            if enable_perspective:
                logger.info("开始透视校正...")
                result = self.perspective_correction(result)
            
            # 2. 去偏斜（如果启用）
            if enable_deskew:
                logger.info("开始去偏斜...")
                result = self.deskew(result)
            
            # 3. 边框检测与裁剪（如果启用）
            if enable_crop:
                logger.info("开始边框检测与裁剪...")
                result = self.crop_document(result)
            
            logger.info("几何校正完成")
            return result
            
        except Exception as e:
            logger.error(f"几何校正失败: {str(e)}")
            return image
    
    def find_document_contour(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        查找文档轮廓
        
        Args:
            image: 输入图像
            
        Returns:
            Optional[np.ndarray]: 文档轮廓，如果未找到则返回None
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 高斯模糊降噪
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 自适应阈值化
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # 形态学操作，连接文本区域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # 边缘检测
        edges = cv2.Canny(morph, 75, 200)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 按面积排序，选择最大的几个轮廓
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # 查找矩形轮廓
        for contour in contours[:5]:  # 只检查前5个最大的轮廓
            # 计算轮廓的面积
            area = cv2.contourArea(contour)
            
            # 过滤太小的轮廓
            image_area = image.shape[0] * image.shape[1]
            if area < image_area * 0.1:  # 至少占图像面积的10%
                continue
            
            # 近似轮廓
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 检查是否为四边形
            if len(approx) == 4:
                logger.info(f"找到文档轮廓，面积: {area}")
                return approx
        
        logger.warning("未找到合适的文档轮廓")
        return None
    
    def perspective_correction(self, image: np.ndarray) -> np.ndarray:
        """
        透视校正
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 透视校正后的图像
        """
        # 查找文档轮廓
        document_contour = self.find_document_contour(image)
        
        if document_contour is None:
            logger.warning("未找到文档轮廓，跳过透视校正")
            return image
        
        try:
            # 排序轮廓点
            ordered_points = self.image_utils.order_rectangle_points(document_contour)
            
            # 计算目标矩形的尺寸
            width_top = np.linalg.norm(ordered_points[1] - ordered_points[0])
            width_bottom = np.linalg.norm(ordered_points[2] - ordered_points[3])
            max_width = max(int(width_top), int(width_bottom))
            
            height_left = np.linalg.norm(ordered_points[3] - ordered_points[0])
            height_right = np.linalg.norm(ordered_points[2] - ordered_points[1])
            max_height = max(int(height_left), int(height_right))
            
            # 定义目标点
            dst_points = np.array([
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1]
            ], dtype=np.float32)
            
            # 计算透视变换矩阵
            transform_matrix = cv2.getPerspectiveTransform(ordered_points, dst_points)
            
            # 应用透视变换
            corrected = cv2.warpPerspective(image, transform_matrix, (max_width, max_height))
            
            logger.info(f"透视校正完成，输出尺寸: {max_width}x{max_height}")
            return corrected
            
        except Exception as e:
            logger.error(f"透视校正失败: {str(e)}")
            return image
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        去偏斜
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 去偏斜后的图像
        """
        try:
            # 计算偏斜角度
            skew_angle = self._calculate_skew_angle_advanced(image)
            
            if abs(skew_angle) < 0.5:  # 角度太小，不需要校正
                logger.info(f"偏斜角度很小({skew_angle:.2f}°)，跳过去偏斜")
                return image
            
            # 旋转图像
            corrected = self.image_utils.rotate_image(image, -skew_angle)
            
            logger.info(f"去偏斜完成，旋转角度: {-skew_angle:.2f}°")
            return corrected
            
        except Exception as e:
            logger.error(f"去偏斜失败: {str(e)}")
            return image
    
    def _calculate_skew_angle_advanced(self, image: np.ndarray) -> float:
        """
        高级偏斜角度计算，结合多种方法
        
        Args:
            image: 输入图像
            
        Returns:
            float: 偏斜角度（度）
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        angles = []
        
        # 方法1: 基于霍夫直线检测
        try:
            angle1 = self._hough_line_skew_detection(gray)
            if angle1 is not None:
                angles.append(angle1)
        except:
            pass
        
        # 方法2: 基于投影剖面
        try:
            angle2 = self._projection_profile_skew_detection(gray)
            if angle2 is not None:
                angles.append(angle2)
        except:
            pass
        
        # 方法3: 基于文本行检测
        try:
            angle3 = self._text_line_skew_detection(gray)
            if angle3 is not None:
                angles.append(angle3)
        except:
            pass
        
        if not angles:
            return 0.0
        
        # 返回角度的中位数
        return float(np.median(angles))
    
    def _hough_line_skew_detection(self, gray: np.ndarray) -> Optional[float]:
        """基于霍夫直线的偏斜检测"""
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 霍夫直线检测
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None or len(lines) < 5:
            return None
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = theta * 180 / np.pi - 90
            
            # 只考虑接近水平的线
            if abs(angle) < 30:
                angles.append(angle)
        
        if len(angles) < 3:
            return None
        
        return float(np.median(angles))
    
    def _projection_profile_skew_detection(self, gray: np.ndarray) -> Optional[float]:
        """基于投影剖面的偏斜检测"""
        angles_to_test = np.arange(-10, 11, 0.5)
        variances = []
        
        height, width = gray.shape
        center = (width // 2, height // 2)
        
        for angle in angles_to_test:
            # 旋转图像
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(gray, rotation_matrix, (width, height))
            
            # 计算水平投影
            projection = np.sum(rotated, axis=1)
            
            # 计算投影的方差
            variance = np.var(projection)
            variances.append(variance)
        
        if not variances:
            return None
        
        # 找到方差最大的角度（文本行最清晰）
        best_angle_index = np.argmax(variances)
        return float(angles_to_test[best_angle_index])
    
    def _text_line_skew_detection(self, gray: np.ndarray) -> Optional[float]:
        """基于文本行的偏斜检测"""
        # 形态学操作，连接文本
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 3:
            return None
        
        # 计算每个轮廓的最小外接矩形
        angles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 过滤小的轮廓
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                
                # 调整角度到 -45 到 45 度范围
                if angle < -45:
                    angle += 90
                elif angle > 45:
                    angle -= 90
                
                if abs(angle) < 30:  # 只考虑接近水平的角度
                    angles.append(angle)
        
        if len(angles) < 3:
            return None
        
        return float(np.median(angles))
    
    def crop_document(self, image: np.ndarray, margin: int = 10) -> np.ndarray:
        """
        裁剪文档边框
        
        Args:
            image: 输入图像
            margin: 边距（像素）
            
        Returns:
            np.ndarray: 裁剪后的图像
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 反转二值图像（背景为黑色，前景为白色）
            binary_inv = cv2.bitwise_not(binary)
            
            # 查找非零像素的边界
            coords = cv2.findNonZero(binary_inv)
            
            if coords is None:
                logger.warning("未找到文档内容，跳过裁剪")
                return image
            
            # 获取边界框
            x, y, w, h = cv2.boundingRect(coords)
            
            # 添加边距
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(image.shape[1] - x, w + 2 * margin)
            h = min(image.shape[0] - y, h + 2 * margin)
            
            # 裁剪图像
            cropped = image[y:y+h, x:x+w]
            
            logger.info(f"文档裁剪完成，裁剪区域: ({x}, {y}, {w}, {h})")
            return cropped
            
        except Exception as e:
            logger.error(f"文档裁剪失败: {str(e)}")
            return image
    
    def auto_crop_white_borders(self, image: np.ndarray, threshold: int = 240) -> np.ndarray:
        """
        自动裁剪白色边框
        
        Args:
            image: 输入图像
            threshold: 白色阈值
            
        Returns:
            np.ndarray: 裁剪后的图像
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 找到非白色区域
            mask = gray < threshold
            
            # 找到非零像素的坐标
            coords = np.column_stack(np.where(mask))
            
            if len(coords) == 0:
                return image
            
            # 获取边界
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            
            # 裁剪图像
            cropped = image[y_min:y_max+1, x_min:x_max+1]
            
            logger.info(f"白色边框裁剪完成，从 {image.shape} 裁剪到 {cropped.shape}")
            return cropped
            
        except Exception as e:
            logger.error(f"白色边框裁剪失败: {str(e)}")
            return image