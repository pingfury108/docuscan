"""
图像处理工具函数模块

提供文档扫描处理中常用的工具函数，包括：
- 图像格式转换
- 几何计算
- 轮廓处理
- 调试可视化
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
import math
import logging

logger = logging.getLogger(__name__)


class ImageUtils:
    """图像处理工具类"""
    
    @staticmethod
    def pil_to_cv2(pil_image) -> np.ndarray:
        """
        将PIL图像转换为OpenCV格式
        
        Args:
            pil_image: PIL Image对象
            
        Returns:
            np.ndarray: OpenCV格式的图像数组
        """
        # 转换为RGB（如果不是的话）
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # PIL使用RGB，OpenCV使用BGR
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv_image
    
    @staticmethod
    def cv2_to_pil(cv_image: np.ndarray):
        """
        将OpenCV图像转换为PIL格式
        
        Args:
            cv_image: OpenCV格式的图像数组
            
        Returns:
            PIL Image对象
        """
        from PIL import Image
        
        # 如果是灰度图像
        if len(cv_image.shape) == 2:
            return Image.fromarray(cv_image, mode='L')
        
        # 如果是彩色图像，转换BGR到RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)
    
    @staticmethod
    def resize_image(image: np.ndarray, max_width: int = 1500, max_height: int = 1500) -> Tuple[np.ndarray, float]:
        """
        调整图像大小以适应处理需求
        
        Args:
            image: 输入图像
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            Tuple[np.ndarray, float]: (调整后的图像, 缩放比例)
        """
        height, width = image.shape[:2]
        
        # 计算缩放比例
        scale_width = max_width / width
        scale_height = max_height / height
        scale = min(scale_width, scale_height, 1.0)  # 不放大图像
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized, scale
        
        return image, 1.0
    
    @staticmethod
    def restore_size(image: np.ndarray, original_size: Tuple[int, int], scale: float) -> np.ndarray:
        """
        将图像恢复到原始大小
        
        Args:
            image: 处理后的图像
            original_size: 原始尺寸 (width, height)
            scale: 之前的缩放比例
            
        Returns:
            np.ndarray: 恢复尺寸后的图像
        """
        if scale != 1.0:
            return cv2.resize(image, original_size, interpolation=cv2.INTER_CUBIC)
        return image
    
    @staticmethod
    def get_contour_area(contour: np.ndarray) -> float:
        """计算轮廓面积"""
        return cv2.contourArea(contour)
    
    @staticmethod
    def get_contour_perimeter(contour: np.ndarray, closed: bool = True) -> float:
        """计算轮廓周长"""
        return cv2.arcLength(contour, closed)
    
    @staticmethod
    def approximate_contour(contour: np.ndarray, epsilon_factor: float = 0.02) -> np.ndarray:
        """
        轮廓近似，用于简化轮廓形状
        
        Args:
            contour: 输入轮廓
            epsilon_factor: 近似精度因子，值越小越精确
            
        Returns:
            np.ndarray: 近似后的轮廓
        """
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        return cv2.approxPolyDP(contour, epsilon, True)
    
    @staticmethod
    def is_rectangle(contour: np.ndarray, min_area: float = 1000) -> bool:
        """
        判断轮廓是否为矩形
        
        Args:
            contour: 输入轮廓
            min_area: 最小面积阈值
            
        Returns:
            bool: 是否为矩形
        """
        # 面积检查
        area = cv2.contourArea(contour)
        if area < min_area:
            return False
        
        # 近似为多边形
        approx = ImageUtils.approximate_contour(contour)
        
        # 矩形应该有4个顶点
        return len(approx) == 4
    
    @staticmethod
    def order_rectangle_points(points: np.ndarray) -> np.ndarray:
        """
        将矩形的4个点按顺序排列：左上、右上、右下、左下
        
        Args:
            points: 4个点的坐标数组
            
        Returns:
            np.ndarray: 排序后的点坐标
        """
        if len(points) != 4:
            raise ValueError("必须提供4个点")
        
        # 重塑为 (4, 2) 形状
        points = points.reshape(4, 2)
        
        # 计算中心点
        center_x = np.mean(points[:, 0])
        center_y = np.mean(points[:, 1])
        
        # 根据相对于中心点的位置对点进行分类
        ordered_points = np.zeros((4, 2), dtype=np.float32)
        
        for point in points:
            x, y = point
            if x < center_x and y < center_y:  # 左上
                ordered_points[0] = point
            elif x >= center_x and y < center_y:  # 右上
                ordered_points[1] = point
            elif x >= center_x and y >= center_y:  # 右下
                ordered_points[2] = point
            else:  # 左下
                ordered_points[3] = point
        
        return ordered_points
    
    @staticmethod
    def calculate_angle(line_points: np.ndarray) -> float:
        """
        计算线段与水平线的角度
        
        Args:
            line_points: 线段的两个端点 [[x1, y1], [x2, y2]]
            
        Returns:
            float: 角度（度）
        """
        x1, y1, x2, y2 = line_points.flatten()
        return math.degrees(math.atan2(y2 - y1, x2 - x1))
    
    @staticmethod
    def rotate_image(image: np.ndarray, angle: float, center: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        旋转图像
        
        Args:
            image: 输入图像
            angle: 旋转角度（度）
            center: 旋转中心，默认为图像中心
            
        Returns:
            np.ndarray: 旋转后的图像
        """
        height, width = image.shape[:2]
        
        if center is None:
            center = (width // 2, height // 2)
        
        # 获取旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 计算新的边界框尺寸
        cos_val = abs(rotation_matrix[0, 0])
        sin_val = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_val) + (width * cos_val))
        new_height = int((height * cos_val) + (width * sin_val))
        
        # 调整旋转矩阵以适应新尺寸
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # 执行旋转
        rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, 
                                borderValue=(255, 255, 255))
        
        return rotated
    
    @staticmethod
    def create_white_background(width: int, height: int, channels: int = 3) -> np.ndarray:
        """
        创建白色背景图像
        
        Args:
            width: 图像宽度
            height: 图像高度
            channels: 通道数（1为灰度，3为彩色）
            
        Returns:
            np.ndarray: 白色背景图像
        """
        if channels == 1:
            return np.full((height, width), 255, dtype=np.uint8)
        else:
            return np.full((height, width, channels), 255, dtype=np.uint8)
    
    @staticmethod
    def safe_divide(numerator: np.ndarray, denominator: np.ndarray, default_value: float = 255.0) -> np.ndarray:
        """
        安全除法，避免除零错误
        
        Args:
            numerator: 分子
            denominator: 分母
            default_value: 当分母为0时的默认值
            
        Returns:
            np.ndarray: 除法结果
        """
        # 创建结果数组
        result = np.full_like(numerator, default_value, dtype=np.float32)
        
        # 只在分母不为0的地方进行除法
        mask = denominator != 0
        result[mask] = numerator[mask] / denominator[mask]
        
        return result
    
    @staticmethod
    def visualize_contours(image: np.ndarray, contours: List[np.ndarray], 
                          title: str = "Contours", save_path: Optional[str] = None) -> np.ndarray:
        """
        可视化轮廓（用于调试）
        
        Args:
            image: 原始图像
            contours: 轮廓列表
            title: 窗口标题
            save_path: 保存路径（可选）
            
        Returns:
            np.ndarray: 绘制了轮廓的图像
        """
        # 创建副本避免修改原图
        vis_image = image.copy()
        
        # 如果是灰度图，转换为彩色以便绘制彩色轮廓
        if len(vis_image.shape) == 2:
            vis_image = cv2.cvtColor(vis_image, cv2.COLOR_GRAY2BGR)
        
        # 绘制所有轮廓
        cv2.drawContours(vis_image, contours, -1, (0, 255, 0), 2)
        
        # 如果提供了保存路径，保存图像
        if save_path:
            cv2.imwrite(save_path, vis_image)
            logger.info(f"轮廓可视化已保存到: {save_path}")
        
        return vis_image
    
    @staticmethod
    def calculate_skew_angle(image: np.ndarray) -> float:
        """
        计算图像偏斜角度
        
        Args:
            image: 输入图像（灰度）
            
        Returns:
            float: 偏斜角度（度）
        """
        # 确保是灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 霍夫直线检测
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None:
            return 0.0
        
        # 计算所有直线的角度
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = theta * 180 / np.pi
            
            # 转换到 -90 到 90 度范围
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180
            
            # 只考虑接近水平或垂直的线
            if abs(angle) < 45:
                angles.append(angle)
            elif abs(angle - 90) < 45 or abs(angle + 90) < 45:
                angles.append(angle - 90 if angle > 0 else angle + 90)
        
        if not angles:
            return 0.0
        
        # 返回角度的中位数
        return float(np.median(angles))
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        使用CLAHE增强对比度
        
        Args:
            image: 输入图像
            clip_limit: 对比度限制
            tile_grid_size: 网格大小
            
        Returns:
            np.ndarray: 增强后的图像
        """
        # 如果是彩色图像，转换到LAB色彩空间
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            
            # 对L通道应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            l_channel = clahe.apply(l_channel)
            
            # 重新组合
            lab[:, :, 0] = l_channel
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # 灰度图像直接应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            return clahe.apply(image)