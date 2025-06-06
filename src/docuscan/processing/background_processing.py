"""
背景处理模块

实现文档图像的背景处理功能，包括：
- 背景美白与移除 (Background Whitening and Removal)
- 中值滤波与除法方法
- 智能背景分离
- 颜色标准化
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Union
import logging
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """背景处理器类"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def process_background(self, image: np.ndarray, 
                          method: str = "median_division",
                          **kwargs) -> np.ndarray:
        """
        处理图像背景
        
        Args:
            image: 输入图像
            method: 处理方法 ("median_division", "adaptive_threshold", "color_separation")
            **kwargs: 方法特定参数
            
        Returns:
            np.ndarray: 处理后的图像
        """
        try:
            if method == "median_division":
                return self.median_division_whitening(image, **kwargs)
            elif method == "adaptive_threshold":
                return self.adaptive_background_removal(image, **kwargs)
            elif method == "color_separation":
                return self.color_based_separation(image, **kwargs)
            else:
                logger.warning(f"未知的背景处理方法: {method}")
                return image
                
        except Exception as e:
            logger.error(f"背景处理失败: {str(e)}")
            return image
    
    def median_division_whitening(self, image: np.ndarray, 
                                 kernel_size: int = 51,
                                 brightness_adjustment: float = 1.2,
                                 contrast_adjustment: float = 1.1) -> np.ndarray:
        """
        中值滤波与除法方法进行背景美白
        
        这是最有效的背景美白方法之一，特别适合处理光照不均的文档
        
        Args:
            image: 输入图像
            kernel_size: 中值滤波核大小（必须为奇数）
            brightness_adjustment: 亮度调整因子
            contrast_adjustment: 对比度调整因子
            
        Returns:
            np.ndarray: 美白后的图像
        """
        try:
            # 确保核大小为奇数
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            logger.info(f"开始中值除法背景美白，核大小: {kernel_size}")
            
            # 如果是彩色图像，分别处理每个通道
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    result[:, :, i] = self._process_single_channel(
                        image[:, :, i], kernel_size, brightness_adjustment, contrast_adjustment)
                return result
            else:
                # 灰度图像直接处理
                return self._process_single_channel(
                    image, kernel_size, brightness_adjustment, contrast_adjustment)
                    
        except Exception as e:
            logger.error(f"中值除法背景美白失败: {str(e)}")
            return image
    
    def _process_single_channel(self, channel: np.ndarray, 
                               kernel_size: int,
                               brightness_adjustment: float,
                               contrast_adjustment: float) -> np.ndarray:
        """
        处理单个通道
        
        Args:
            channel: 单通道图像
            kernel_size: 中值滤波核大小
            brightness_adjustment: 亮度调整
            contrast_adjustment: 对比度调整
            
        Returns:
            np.ndarray: 处理后的通道
        """
        # 转换为浮点数进行计算
        channel_float = channel.astype(np.float32)
        
        # 应用中值滤波获取背景
        background = cv2.medianBlur(channel, kernel_size).astype(np.float32)
        
        # 避免除零，添加小的常数
        background = np.maximum(background, 1.0)
        
        # 执行除法操作
        normalized = (channel_float / background) * 255.0
        
        # 亮度和对比度调整
        adjusted = normalized * contrast_adjustment + (brightness_adjustment - 1.0) * 128
        
        # 限制像素值范围并转换回uint8
        result = np.clip(adjusted, 0, 255).astype(np.uint8)
        
        return result
    
    def adaptive_background_removal(self, image: np.ndarray,
                                  block_size: int = 15,
                                  c_constant: float = 5,
                                  morphology_kernel_size: int = 3) -> np.ndarray:
        """
        自适应背景移除
        
        适合处理复杂背景的文档图像
        
        Args:
            image: 输入图像
            block_size: 自适应阈值块大小
            c_constant: 自适应阈值常数
            morphology_kernel_size: 形态学操作核大小
            
        Returns:
            np.ndarray: 处理后的图像
        """
        try:
            logger.info("开始自适应背景移除")
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 高斯模糊降噪
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 自适应阈值
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, block_size, c_constant
            )
            
            # 形态学操作，清理噪声
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                             (morphology_kernel_size, morphology_kernel_size))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # 如果原图是彩色的，创建彩色输出
            if len(image.shape) == 3:
                result = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
            else:
                result = cleaned
            
            logger.info("自适应背景移除完成")
            return result
            
        except Exception as e:
            logger.error(f"自适应背景移除失败: {str(e)}")
            return image
    
    def color_based_separation(self, image: np.ndarray,
                              background_color_threshold: int = 200,
                              morphology_iterations: int = 2) -> np.ndarray:
        """
        基于颜色的背景分离
        
        适合处理有明显背景色的文档
        
        Args:
            image: 输入图像
            background_color_threshold: 背景色阈值
            morphology_iterations: 形态学操作迭代次数
            
        Returns:
            np.ndarray: 处理后的图像
        """
        try:
            logger.info("开始基于颜色的背景分离")
            
            if len(image.shape) != 3:
                logger.warning("颜色分离需要彩色图像")
                return image
            
            # 转换到HSV色彩空间以更好地处理颜色
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 创建背景掩码（高亮度、低饱和度的区域）
            # 这些通常是背景区域
            background_mask = cv2.inRange(hsv[:, :, 2], background_color_threshold, 255)
            
            # 形态学操作，改善掩码
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_CLOSE, 
                                             kernel, iterations=morphology_iterations)
            background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_OPEN, 
                                             kernel, iterations=morphology_iterations)
            
            # 创建前景掩码
            foreground_mask = cv2.bitwise_not(background_mask)
            
            # 创建白色背景
            result = np.full_like(image, 255)
            
            # 将前景复制到白色背景上
            result[foreground_mask > 0] = image[foreground_mask > 0]
            
            logger.info("基于颜色的背景分离完成")
            return result
            
        except Exception as e:
            logger.error(f"基于颜色的背景分离失败: {str(e)}")
            return image
    
    def remove_shadows(self, image: np.ndarray,
                      shadow_threshold: int = 100,
                      dilate_iterations: int = 3) -> np.ndarray:
        """
        移除阴影
        
        Args:
            image: 输入图像
            shadow_threshold: 阴影检测阈值
            dilate_iterations: 膨胀操作迭代次数
            
        Returns:
            np.ndarray: 移除阴影后的图像
        """
        try:
            logger.info("开始移除阴影")
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 使用大核的中值滤波获取背景
            background = cv2.medianBlur(gray, 19)
            
            # 计算差异
            diff = cv2.absdiff(gray, background)
            
            # 阈值化找到阴影区域
            _, shadow_mask = cv2.threshold(diff, shadow_threshold, 255, cv2.THRESH_BINARY)
            
            # 膨胀阴影区域
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            shadow_mask = cv2.dilate(shadow_mask, kernel, iterations=dilate_iterations)
            
            # 在阴影区域应用背景替换
            result = image.copy()
            if len(image.shape) == 3:
                for i in range(3):
                    result[:, :, i][shadow_mask > 0] = background[shadow_mask > 0]
            else:
                result[shadow_mask > 0] = background[shadow_mask > 0]
            
            logger.info("阴影移除完成")
            return result
            
        except Exception as e:
            logger.error(f"阴影移除失败: {str(e)}")
            return image
    
    def normalize_illumination(self, image: np.ndarray,
                             sigma: float = 30.0) -> np.ndarray:
        """
        标准化光照
        
        处理光照不均匀的问题
        
        Args:
            image: 输入图像
            sigma: 高斯核标准差
            
        Returns:
            np.ndarray: 光照标准化后的图像
        """
        try:
            logger.info("开始光照标准化")
            
            if len(image.shape) == 3:
                # 转换到LAB色彩空间
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l_channel = lab[:, :, 0].astype(np.float32)
                
                # 估计光照
                blur = cv2.GaussianBlur(l_channel, (0, 0), sigma)
                
                # 标准化
                normalized = l_channel - blur + 128
                normalized = np.clip(normalized, 0, 255).astype(np.uint8)
                
                # 重新组合
                lab[:, :, 0] = normalized
                result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            else:
                # 灰度图像处理
                gray_float = image.astype(np.float32)
                blur = cv2.GaussianBlur(gray_float, (0, 0), sigma)
                normalized = gray_float - blur + 128
                result = np.clip(normalized, 0, 255).astype(np.uint8)
            
            logger.info("光照标准化完成")
            return result
            
        except Exception as e:
            logger.error(f"光照标准化失败: {str(e)}")
            return image
    
    def enhance_background_contrast(self, image: np.ndarray,
                                  alpha: float = 1.5,
                                  beta: int = 10) -> np.ndarray:
        """
        增强背景对比度
        
        Args:
            image: 输入图像
            alpha: 对比度调整因子
            beta: 亮度调整值
            
        Returns:
            np.ndarray: 对比度增强后的图像
        """
        try:
            logger.info(f"开始背景对比度增强，alpha={alpha}, beta={beta}")
            
            # 应用线性变换 new_pixel = alpha * old_pixel + beta
            enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            
            logger.info("背景对比度增强完成")
            return enhanced
            
        except Exception as e:
            logger.error(f"背景对比度增强失败: {str(e)}")
            return image
    
    def create_white_background_document(self, image: np.ndarray,
                                       text_threshold: int = 180) -> np.ndarray:
        """
        创建白底文档
        
        将文档转换为纯白底，适合最终输出
        
        Args:
            image: 输入图像
            text_threshold: 文本检测阈值
            
        Returns:
            np.ndarray: 白底文档图像
        """
        try:
            logger.info("开始创建白底文档")
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 创建白色背景
            if len(image.shape) == 3:
                white_bg = np.full_like(image, 255)
            else:
                white_bg = np.full_like(gray, 255)
            
            # 检测文本/内容区域（暗色区域）
            content_mask = gray < text_threshold
            
            # 将内容区域复制到白色背景上
            if len(image.shape) == 3:
                for i in range(3):
                    white_bg[:, :, i][content_mask] = image[:, :, i][content_mask]
            else:
                white_bg[content_mask] = gray[content_mask]
            
            logger.info("白底文档创建完成")
            return white_bg
            
        except Exception as e:
            logger.error(f"白底文档创建失败: {str(e)}")
            return image