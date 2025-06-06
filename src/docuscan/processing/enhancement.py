"""
图像质量增强模块

实现文档图像的质量增强功能，包括：
- 降噪 (Noise Reduction)
- 对比度与锐度调整 (Contrast and Sharpness Adjustment)
- 直方图均衡化
- 锐化处理
- 伽马校正
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Union, Dict, Any
import logging
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """图像质量增强器类"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def enhance_image(self, image: np.ndarray,
                     enhance_contrast: bool = True,
                     reduce_noise: bool = True,
                     sharpen: bool = True,
                     gamma_correction: bool = False,
                     **kwargs) -> np.ndarray:
        """
        对图像进行完整的质量增强
        
        Args:
            image: 输入图像
            enhance_contrast: 是否增强对比度
            reduce_noise: 是否降噪
            sharpen: 是否锐化
            gamma_correction: 是否进行伽马校正
            **kwargs: 各种方法的参数
            
        Returns:
            np.ndarray: 增强后的图像
        """
        try:
            logger.info("开始图像质量增强")
            result = image.copy()
            
            # 1. 降噪（如果启用）
            if reduce_noise:
                logger.info("应用降噪处理...")
                result = self.reduce_noise(result, **kwargs)
            
            # 2. 对比度增强（如果启用）
            if enhance_contrast:
                logger.info("应用对比度增强...")
                result = self.enhance_contrast(result, **kwargs)
            
            # 3. 锐化（如果启用）
            if sharpen:
                logger.info("应用锐化处理...")
                result = self.sharpen_image(result, **kwargs)
            
            # 4. 伽马校正（如果启用）
            if gamma_correction:
                logger.info("应用伽马校正...")
                result = self.gamma_correction(result, **kwargs)
            
            logger.info("图像质量增强完成")
            return result
            
        except Exception as e:
            logger.error(f"图像质量增强失败: {str(e)}")
            return image
    
    def reduce_noise(self, image: np.ndarray,
                    method: str = "bilateral",
                    **kwargs) -> np.ndarray:
        """
        图像降噪
        
        Args:
            image: 输入图像
            method: 降噪方法 ("gaussian", "bilateral", "median", "non_local_means")
            **kwargs: 方法特定参数
            
        Returns:
            np.ndarray: 降噪后的图像
        """
        try:
            if method == "gaussian":
                return self.gaussian_denoise(image, **kwargs)
            elif method == "bilateral":
                return self.bilateral_denoise(image, **kwargs)
            elif method == "median":
                return self.median_denoise(image, **kwargs)
            elif method == "non_local_means":
                return self.non_local_means_denoise(image, **kwargs)
            else:
                logger.warning(f"未知的降噪方法: {method}，使用双边滤波")
                return self.bilateral_denoise(image, **kwargs)
                
        except Exception as e:
            logger.error(f"降噪处理失败: {str(e)}")
            return image
    
    def gaussian_denoise(self, image: np.ndarray,
                        kernel_size: int = 5,
                        sigma_x: float = 0,
                        sigma_y: float = 0) -> np.ndarray:
        """
        高斯降噪
        
        Args:
            image: 输入图像
            kernel_size: 核大小
            sigma_x: X方向标准差
            sigma_y: Y方向标准差
            
        Returns:
            np.ndarray: 降噪后的图像
        """
        try:
            # 确保kernel_size为奇数
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            result = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x, sigmaY=sigma_y)
            logger.debug(f"高斯降噪完成，kernel_size={kernel_size}")
            return result
            
        except Exception as e:
            logger.error(f"高斯降噪失败: {str(e)}")
            return image
    
    def bilateral_denoise(self, image: np.ndarray,
                         d: int = 9,
                         sigma_color: float = 75,
                         sigma_space: float = 75) -> np.ndarray:
        """
        双边滤波降噪
        
        保持边缘的同时降噪
        
        Args:
            image: 输入图像
            d: 邻域直径
            sigma_color: 颜色空间过滤器的sigma值
            sigma_space: 坐标空间过滤器的sigma值
            
        Returns:
            np.ndarray: 降噪后的图像
        """
        try:
            result = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            logger.debug(f"双边滤波降噪完成，d={d}, sigma_color={sigma_color}")
            return result
            
        except Exception as e:
            logger.error(f"双边滤波降噪失败: {str(e)}")
            return image
    
    def median_denoise(self, image: np.ndarray,
                      kernel_size: int = 5) -> np.ndarray:
        """
        中值滤波降噪
        
        对椒盐噪声效果很好
        
        Args:
            image: 输入图像
            kernel_size: 核大小（必须为奇数）
            
        Returns:
            np.ndarray: 降噪后的图像
        """
        try:
            # 确保kernel_size为奇数
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            result = cv2.medianBlur(image, kernel_size)
            logger.debug(f"中值滤波降噪完成，kernel_size={kernel_size}")
            return result
            
        except Exception as e:
            logger.error(f"中值滤波降噪失败: {str(e)}")
            return image
    
    def non_local_means_denoise(self, image: np.ndarray,
                               h: float = 10,
                               template_window_size: int = 7,
                               search_window_size: int = 21) -> np.ndarray:
        """
        非局部均值降噪
        
        Args:
            image: 输入图像
            h: 过滤强度
            template_window_size: 模板窗口大小
            search_window_size: 搜索窗口大小
            
        Returns:
            np.ndarray: 降噪后的图像
        """
        try:
            if len(image.shape) == 3:
                result = cv2.fastNlMeansDenoisingColored(
                    image, None, h, h, template_window_size, search_window_size
                )
            else:
                result = cv2.fastNlMeansDenoising(
                    image, None, h, template_window_size, search_window_size
                )
            
            logger.debug(f"非局部均值降噪完成，h={h}")
            return result
            
        except Exception as e:
            logger.error(f"非局部均值降噪失败: {str(e)}")
            return image
    
    def enhance_contrast(self, image: np.ndarray,
                        method: str = "clahe",
                        **kwargs) -> np.ndarray:
        """
        对比度增强
        
        Args:
            image: 输入图像
            method: 增强方法 ("clahe", "histogram_equalization", "adaptive_equalization")
            **kwargs: 方法特定参数
            
        Returns:
            np.ndarray: 对比度增强后的图像
        """
        try:
            if method == "clahe":
                return self.clahe_enhancement(image, **kwargs)
            elif method == "histogram_equalization":
                return self.histogram_equalization(image, **kwargs)
            elif method == "adaptive_equalization":
                return self.adaptive_histogram_equalization(image, **kwargs)
            else:
                logger.warning(f"未知的对比度增强方法: {method}，使用CLAHE")
                return self.clahe_enhancement(image, **kwargs)
                
        except Exception as e:
            logger.error(f"对比度增强失败: {str(e)}")
            return image
    
    def clahe_enhancement(self, image: np.ndarray,
                         clip_limit: float = 2.0,
                         tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        CLAHE (Contrast Limited Adaptive Histogram Equalization) 增强
        
        Args:
            image: 输入图像
            clip_limit: 对比度限制阈值
            tile_grid_size: 网格大小
            
        Returns:
            np.ndarray: 增强后的图像
        """
        try:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            
            if len(image.shape) == 3:
                # 彩色图像：在LAB色彩空间的L通道应用CLAHE
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            else:
                # 灰度图像直接应用
                result = clahe.apply(image)
            
            logger.debug(f"CLAHE增强完成，clip_limit={clip_limit}")
            return result
            
        except Exception as e:
            logger.error(f"CLAHE增强失败: {str(e)}")
            return image
    
    def histogram_equalization(self, image: np.ndarray) -> np.ndarray:
        """
        直方图均衡化
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 均衡化后的图像
        """
        try:
            if len(image.shape) == 3:
                # 彩色图像：在YUV色彩空间的Y通道应用
                yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
                result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            else:
                # 灰度图像直接应用
                result = cv2.equalizeHist(image)
            
            logger.debug("直方图均衡化完成")
            return result
            
        except Exception as e:
            logger.error(f"直方图均衡化失败: {str(e)}")
            return image
    
    def adaptive_histogram_equalization(self, image: np.ndarray,
                                      window_size: int = 8) -> np.ndarray:
        """
        自适应直方图均衡化
        
        Args:
            image: 输入图像
            window_size: 窗口大小
            
        Returns:
            np.ndarray: 均衡化后的图像
        """
        try:
            clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(window_size, window_size))
            
            if len(image.shape) == 3:
                # 彩色图像处理
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                hsv[:, :, 2] = clahe.apply(hsv[:, :, 2])  # 对V通道应用
                result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            else:
                # 灰度图像
                result = clahe.apply(image)
            
            logger.debug(f"自适应直方图均衡化完成，window_size={window_size}")
            return result
            
        except Exception as e:
            logger.error(f"自适应直方图均衡化失败: {str(e)}")
            return image
    
    def sharpen_image(self, image: np.ndarray,
                     method: str = "unsharp_mask",
                     **kwargs) -> np.ndarray:
        """
        图像锐化
        
        Args:
            image: 输入图像
            method: 锐化方法 ("unsharp_mask", "laplacian", "custom_kernel")
            **kwargs: 方法特定参数
            
        Returns:
            np.ndarray: 锐化后的图像
        """
        try:
            if method == "unsharp_mask":
                return self.unsharp_mask_sharpen(image, **kwargs)
            elif method == "laplacian":
                return self.laplacian_sharpen(image, **kwargs)
            elif method == "custom_kernel":
                return self.custom_kernel_sharpen(image, **kwargs)
            else:
                logger.warning(f"未知的锐化方法: {method}，使用非锐化掩模")
                return self.unsharp_mask_sharpen(image, **kwargs)
                
        except Exception as e:
            logger.error(f"图像锐化失败: {str(e)}")
            return image
    
    def unsharp_mask_sharpen(self, image: np.ndarray,
                            sigma: float = 1.0,
                            strength: float = 1.5,
                            threshold: int = 0) -> np.ndarray:
        """
        非锐化掩模锐化
        
        Args:
            image: 输入图像
            sigma: 高斯模糊的标准差
            strength: 锐化强度
            threshold: 阈值
            
        Returns:
            np.ndarray: 锐化后的图像
        """
        try:
            # 创建模糊版本
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            
            # 计算差异
            if len(image.shape) == 3:
                diff = image.astype(np.float32) - blurred.astype(np.float32)
            else:
                diff = image.astype(np.float32) - blurred.astype(np.float32)
            
            # 应用阈值
            if threshold > 0:
                mask = np.abs(diff) >= threshold
                diff = diff * mask
            
            # 应用锐化
            sharpened = image.astype(np.float32) + strength * diff
            
            # 限制像素值范围
            result = np.clip(sharpened, 0, 255).astype(np.uint8)
            
            logger.debug(f"非锐化掩模锐化完成，sigma={sigma}, strength={strength}")
            return result
            
        except Exception as e:
            logger.error(f"非锐化掩模锐化失败: {str(e)}")
            return image
    
    def laplacian_sharpen(self, image: np.ndarray,
                         strength: float = 0.5) -> np.ndarray:
        """
        拉普拉斯锐化
        
        Args:
            image: 输入图像
            strength: 锐化强度
            
        Returns:
            np.ndarray: 锐化后的图像
        """
        try:
            # 拉普拉斯核
            kernel = np.array([[0, -1, 0],
                              [-1, 5, -1],
                              [0, -1, 0]])
            
            # 应用卷积
            if len(image.shape) == 3:
                sharpened = cv2.filter2D(image, -1, kernel)
            else:
                sharpened = cv2.filter2D(image, -1, kernel)
            
            # 混合原图和锐化图
            result = cv2.addWeighted(image, 1 - strength, sharpened, strength, 0)
            
            logger.debug(f"拉普拉斯锐化完成，strength={strength}")
            return result
            
        except Exception as e:
            logger.error(f"拉普拉斯锐化失败: {str(e)}")
            return image
    
    def custom_kernel_sharpen(self, image: np.ndarray,
                             kernel: Optional[np.ndarray] = None,
                             strength: float = 1.0) -> np.ndarray:
        """
        自定义核锐化
        
        Args:
            image: 输入图像
            kernel: 自定义卷积核
            strength: 锐化强度
            
        Returns:
            np.ndarray: 锐化后的图像
        """
        try:
            if kernel is None:
                # 默认锐化核
                kernel = np.array([[-1, -1, -1],
                                  [-1,  9, -1],
                                  [-1, -1, -1]])
            
            # 应用卷积
            sharpened = cv2.filter2D(image, -1, kernel)
            
            # 混合原图和锐化图
            result = cv2.addWeighted(image, 1 - strength, sharpened, strength, 0)
            
            logger.debug(f"自定义核锐化完成，strength={strength}")
            return result
            
        except Exception as e:
            logger.error(f"自定义核锐化失败: {str(e)}")
            return image
    
    def gamma_correction(self, image: np.ndarray,
                        gamma: float = 1.2) -> np.ndarray:
        """
        伽马校正
        
        Args:
            image: 输入图像
            gamma: 伽马值（>1提亮，<1变暗）
            
        Returns:
            np.ndarray: 伽马校正后的图像
        """
        try:
            # 构建查找表
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 
                             for i in np.arange(0, 256)]).astype(np.uint8)
            
            # 应用查找表
            result = cv2.LUT(image, table)
            
            logger.debug(f"伽马校正完成，gamma={gamma}")
            return result
            
        except Exception as e:
            logger.error(f"伽马校正失败: {str(e)}")
            return image
    
    def adjust_brightness_contrast(self, image: np.ndarray,
                                  alpha: float = 1.0,
                                  beta: int = 0) -> np.ndarray:
        """
        调整亮度和对比度
        
        Args:
            image: 输入图像
            alpha: 对比度调整因子 (1.0-3.0)
            beta: 亮度调整值 (-100到100)
            
        Returns:
            np.ndarray: 调整后的图像
        """
        try:
            result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            logger.debug(f"亮度对比度调整完成，alpha={alpha}, beta={beta}")
            return result
            
        except Exception as e:
            logger.error(f"亮度对比度调整失败: {str(e)}")
            return image
    
    def enhance_text_clarity(self, image: np.ndarray) -> np.ndarray:
        """
        专门针对文本的清晰度增强
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 增强后的图像
        """
        try:
            logger.info("开始文本清晰度增强")
            
            # 1. 轻微降噪
            denoised = self.bilateral_denoise(image, d=5, sigma_color=50, sigma_space=50)
            
            # 2. CLAHE增强对比度
            contrast_enhanced = self.clahe_enhancement(denoised, clip_limit=3.0, tile_grid_size=(8, 8))
            
            # 3. 轻微锐化
            sharpened = self.unsharp_mask_sharpen(contrast_enhanced, sigma=0.5, strength=1.2)
            
            logger.info("文本清晰度增强完成")
            return sharpened
            
        except Exception as e:
            logger.error(f"文本清晰度增强失败: {str(e)}")
            return image
    
    def auto_enhance(self, image: np.ndarray) -> np.ndarray:
        """
        自动图像增强
        
        根据图像特征自动选择合适的增强方法
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 自动增强后的图像
        """
        try:
            logger.info("开始自动图像增强")
            
            # 分析图像特征
            features = self._analyze_image_quality(image)
            
            result = image.copy()
            
            # 根据特征选择增强方法
            if features['noise_level'] > 0.3:
                logger.info("检测到较高噪声，应用降噪")
                result = self.bilateral_denoise(result)
            
            if features['contrast'] < 0.4:
                logger.info("检测到低对比度，应用CLAHE增强")
                result = self.clahe_enhancement(result, clip_limit=2.5)
            
            if features['sharpness'] < 0.5:
                logger.info("检测到模糊，应用锐化")
                result = self.unsharp_mask_sharpen(result, strength=1.3)
            
            if features['brightness'] < 0.3:
                logger.info("检测到偏暗，应用亮度调整")
                result = self.adjust_brightness_contrast(result, alpha=1.1, beta=15)
            elif features['brightness'] > 0.8:
                logger.info("检测到偏亮，应用亮度调整")
                result = self.adjust_brightness_contrast(result, alpha=0.9, beta=-10)
            
            logger.info("自动图像增强完成")
            return result
            
        except Exception as e:
            logger.error(f"自动图像增强失败: {str(e)}")
            return image
    
    def _analyze_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """
        分析图像质量特征
        
        Args:
            image: 输入图像
            
        Returns:
            Dict[str, float]: 图像质量特征字典
        """
        features = {}
        
        try:
            # 转换为灰度图用于分析
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 1. 亮度分析
            mean_brightness = np.mean(gray) / 255.0
            features['brightness'] = float(mean_brightness)
            
            # 2. 对比度分析
            std_dev = np.std(gray) / 128.0
            features['contrast'] = float(min(std_dev, 1.0))
            
            # 3. 锐度分析（基于拉普拉斯方差）
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = np.var(laplacian) / 10000.0
            features['sharpness'] = float(min(sharpness, 1.0))
            
            # 4. 噪声水平估计
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = np.var(gray.astype(np.float32) - blur.astype(np.float32)) / 1000.0
            features['noise_level'] = float(min(noise, 1.0))
            
        except Exception as e:
            logger.error(f"图像质量分析失败: {str(e)}")
            # 返回默认值
            features = {
                'brightness': 0.5,
                'contrast': 0.5,
                'sharpness': 0.5,
                'noise_level': 0.2
            }
        
        return features