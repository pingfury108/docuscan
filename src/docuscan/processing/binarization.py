"""
二值化处理模块

实现文档图像的二值化功能，包括：
- 自适应阈值化 (Adaptive Thresholding)
- 全局阈值化 (Global Thresholding)  
- 多种二值化算法
- 预处理和后处理优化
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Union, Dict, Any
import logging
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class Binarizer:
    """二值化处理器类"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def binarize(self, image: np.ndarray, 
                method: str = "adaptive_gaussian",
                **kwargs) -> np.ndarray:
        """
        对图像进行二值化处理
        
        Args:
            image: 输入图像
            method: 二值化方法 ("adaptive_gaussian", "adaptive_mean", "otsu", "triangle", "sauvola")
            **kwargs: 方法特定参数
            
        Returns:
            np.ndarray: 二值化后的图像
        """
        try:
            logger.info(f"开始二值化处理，方法: {method}")
            
            # 预处理
            preprocessed = self.preprocess_for_binarization(image, **kwargs)
            
            # 应用指定的二值化方法
            if method == "adaptive_gaussian":
                result = self.adaptive_threshold_gaussian(preprocessed, **kwargs)
            elif method == "adaptive_mean":
                result = self.adaptive_threshold_mean(preprocessed, **kwargs)
            elif method == "otsu":
                result = self.otsu_threshold(preprocessed, **kwargs)
            elif method == "triangle":
                result = self.triangle_threshold(preprocessed, **kwargs)
            elif method == "sauvola":
                result = self.sauvola_threshold(preprocessed, **kwargs)
            elif method == "combined":
                result = self.combined_threshold(preprocessed, **kwargs)
            else:
                logger.warning(f"未知的二值化方法: {method}，使用默认方法")
                result = self.adaptive_threshold_gaussian(preprocessed, **kwargs)
            
            # 后处理
            result = self.postprocess_binary(result, **kwargs)
            
            logger.info("二值化处理完成")
            return result
            
        except Exception as e:
            logger.error(f"二值化处理失败: {str(e)}")
            return image
    
    def preprocess_for_binarization(self, image: np.ndarray,
                                   denoise: bool = True,
                                   enhance_contrast: bool = True,
                                   gaussian_blur_kernel: int = 3) -> np.ndarray:
        """
        二值化预处理
        
        Args:
            image: 输入图像
            denoise: 是否降噪
            enhance_contrast: 是否增强对比度
            gaussian_blur_kernel: 高斯模糊核大小
            
        Returns:
            np.ndarray: 预处理后的灰度图像
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 降噪
            if denoise and gaussian_blur_kernel > 0:
                if gaussian_blur_kernel % 2 == 0:
                    gaussian_blur_kernel += 1
                gray = cv2.GaussianBlur(gray, (gaussian_blur_kernel, gaussian_blur_kernel), 0)
            
            # 对比度增强
            if enhance_contrast:
                gray = self.image_utils.enhance_contrast(gray)
            
            return gray
            
        except Exception as e:
            logger.error(f"二值化预处理失败: {str(e)}")
            return image
    
    def adaptive_threshold_gaussian(self, gray: np.ndarray,
                                   max_value: int = 255,
                                   block_size: int = 11,
                                   c_constant: float = 2) -> np.ndarray:
        """
        自适应高斯阈值化
        
        Args:
            gray: 灰度图像
            max_value: 最大值
            block_size: 邻域大小（必须为奇数）
            c_constant: 从平均值中减去的常数
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            # 确保block_size为奇数且大于等于3
            if block_size % 2 == 0:
                block_size += 1
            if block_size < 3:
                block_size = 3
            
            result = cv2.adaptiveThreshold(
                gray, max_value, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, block_size, c_constant
            )
            
            logger.debug(f"自适应高斯阈值化完成，block_size={block_size}, C={c_constant}")
            return result
            
        except Exception as e:
            logger.error(f"自适应高斯阈值化失败: {str(e)}")
            return gray
    
    def adaptive_threshold_mean(self, gray: np.ndarray,
                               max_value: int = 255,
                               block_size: int = 11,
                               c_constant: float = 2) -> np.ndarray:
        """
        自适应均值阈值化
        
        Args:
            gray: 灰度图像
            max_value: 最大值
            block_size: 邻域大小（必须为奇数）
            c_constant: 从平均值中减去的常数
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            # 确保block_size为奇数且大于等于3
            if block_size % 2 == 0:
                block_size += 1
            if block_size < 3:
                block_size = 3
            
            result = cv2.adaptiveThreshold(
                gray, max_value, cv2.ADAPTIVE_THRESH_MEAN_C, 
                cv2.THRESH_BINARY, block_size, c_constant
            )
            
            logger.debug(f"自适应均值阈值化完成，block_size={block_size}, C={c_constant}")
            return result
            
        except Exception as e:
            logger.error(f"自适应均值阈值化失败: {str(e)}")
            return gray
    
    def otsu_threshold(self, gray: np.ndarray,
                      max_value: int = 255) -> np.ndarray:
        """
        Otsu自动阈值化
        
        Args:
            gray: 灰度图像
            max_value: 最大值
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            threshold_value, result = cv2.threshold(
                gray, 0, max_value, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            logger.debug(f"Otsu阈值化完成，阈值: {threshold_value}")
            return result
            
        except Exception as e:
            logger.error(f"Otsu阈值化失败: {str(e)}")
            return gray
    
    def triangle_threshold(self, gray: np.ndarray,
                          max_value: int = 255) -> np.ndarray:
        """
        Triangle自动阈值化
        
        Args:
            gray: 灰度图像
            max_value: 最大值
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            threshold_value, result = cv2.threshold(
                gray, 0, max_value, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE
            )
            
            logger.debug(f"Triangle阈值化完成，阈值: {threshold_value}")
            return result
            
        except Exception as e:
            logger.error(f"Triangle阈值化失败: {str(e)}")
            return gray
    
    def sauvola_threshold(self, gray: np.ndarray,
                         window_size: int = 15,
                         k: float = 0.2,
                         r: float = 128) -> np.ndarray:
        """
        Sauvola局部阈值化
        
        适合处理光照不均匀的文档图像
        
        Args:
            gray: 灰度图像
            window_size: 窗口大小
            k: 敏感度参数
            r: 动态范围参数
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            # 确保window_size为奇数
            if window_size % 2 == 0:
                window_size += 1
            
            # 计算局部均值和标准差
            mean = cv2.boxFilter(gray.astype(np.float32), -1, (window_size, window_size))
            sqr_mean = cv2.boxFilter((gray.astype(np.float32))**2, -1, (window_size, window_size))
            
            # 计算标准差
            variance = sqr_mean - mean**2
            variance = np.maximum(variance, 0)  # 确保非负
            std_dev = np.sqrt(variance)
            
            # 计算Sauvola阈值
            threshold = mean * (1 + k * ((std_dev / r) - 1))
            
            # 应用阈值
            result = np.where(gray >= threshold, 255, 0).astype(np.uint8)
            
            logger.debug(f"Sauvola阈值化完成，window_size={window_size}, k={k}")
            return result
            
        except Exception as e:
            logger.error(f"Sauvola阈值化失败: {str(e)}")
            return gray
    
    def combined_threshold(self, gray: np.ndarray,
                          weights: Dict[str, float] = None) -> np.ndarray:
        """
        组合多种阈值化方法
        
        Args:
            gray: 灰度图像
            weights: 各方法的权重
            
        Returns:
            np.ndarray: 二值化图像
        """
        try:
            if weights is None:
                weights = {
                    'adaptive_gaussian': 0.4,
                    'adaptive_mean': 0.3,
                    'otsu': 0.3
                }
            
            logger.info("开始组合阈值化")
            
            results = {}
            
            # 应用各种方法
            if 'adaptive_gaussian' in weights:
                results['adaptive_gaussian'] = self.adaptive_threshold_gaussian(gray)
            
            if 'adaptive_mean' in weights:
                results['adaptive_mean'] = self.adaptive_threshold_mean(gray)
            
            if 'otsu' in weights:
                results['otsu'] = self.otsu_threshold(gray)
            
            if 'triangle' in weights:
                results['triangle'] = self.triangle_threshold(gray)
            
            # 加权组合
            combined = np.zeros_like(gray, dtype=np.float32)
            total_weight = 0
            
            for method, weight in weights.items():
                if method in results:
                    combined += results[method].astype(np.float32) * weight
                    total_weight += weight
            
            # 标准化
            if total_weight > 0:
                combined /= total_weight
            
            # 转换为二值图像
            result = np.where(combined >= 127.5, 255, 0).astype(np.uint8)
            
            logger.info("组合阈值化完成")
            return result
            
        except Exception as e:
            logger.error(f"组合阈值化失败: {str(e)}")
            return gray
    
    def postprocess_binary(self, binary: np.ndarray,
                          remove_noise: bool = True,
                          fill_holes: bool = True,
                          morphology_kernel_size: int = 2) -> np.ndarray:
        """
        二值化后处理
        
        Args:
            binary: 二值图像
            remove_noise: 是否去除噪声
            fill_holes: 是否填充小洞
            morphology_kernel_size: 形态学操作核大小
            
        Returns:
            np.ndarray: 后处理后的二值图像
        """
        try:
            result = binary.copy()
            
            if remove_noise or fill_holes:
                kernel = cv2.getStructuringElement(
                    cv2.MORPH_RECT, 
                    (morphology_kernel_size, morphology_kernel_size)
                )
                
                if remove_noise:
                    # 开运算去除小的噪声点
                    result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel)
                
                if fill_holes:
                    # 闭运算填充小洞
                    result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel)
            
            return result
            
        except Exception as e:
            logger.error(f"二值化后处理失败: {str(e)}")
            return binary
    
    def auto_select_binarization_method(self, image: np.ndarray) -> Tuple[str, Dict[str, Any]]:
        """
        自动选择最佳二值化方法
        
        Args:
            image: 输入图像
            
        Returns:
            Tuple[str, Dict]: (方法名, 参数字典)
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 分析图像特征
            features = self._analyze_image_features(gray)
            
            # 根据特征选择方法
            if features['illumination_variance'] > 2000:
                # 光照变化大，使用自适应方法
                if features['noise_level'] > 0.3:
                    return "adaptive_gaussian", {"block_size": 15, "c_constant": 3}
                else:
                    return "adaptive_gaussian", {"block_size": 11, "c_constant": 2}
            
            elif features['contrast'] < 0.3:
                # 对比度低，使用Sauvola
                return "sauvola", {"window_size": 15, "k": 0.3}
            
            else:
                # 一般情况，使用Otsu
                return "otsu", {}
                
        except Exception as e:
            logger.error(f"自动选择二值化方法失败: {str(e)}")
            return "adaptive_gaussian", {}
    
    def _analyze_image_features(self, gray: np.ndarray) -> Dict[str, float]:
        """
        分析图像特征
        
        Args:
            gray: 灰度图像
            
        Returns:
            Dict[str, float]: 图像特征字典
        """
        features = {}
        
        try:
            # 计算光照变化
            blur = cv2.GaussianBlur(gray, (21, 21), 0)
            illumination_variance = np.var(blur)
            features['illumination_variance'] = float(illumination_variance)
            
            # 计算对比度
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten() / hist.sum()
            contrast = np.sum(hist * np.arange(256)**2) - (np.sum(hist * np.arange(256)))**2
            features['contrast'] = float(contrast) / 65536  # 标准化
            
            # 估计噪声水平
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            noise_level = np.var(laplacian) / 10000  # 标准化
            features['noise_level'] = float(noise_level)
            
            # 计算边缘密度
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            features['edge_density'] = float(edge_density)
            
        except Exception as e:
            logger.error(f"图像特征分析失败: {str(e)}")
            # 返回默认值
            features = {
                'illumination_variance': 1000.0,
                'contrast': 0.5,
                'noise_level': 0.2,
                'edge_density': 0.1
            }
        
        return features
    
    def evaluate_binarization_quality(self, original: np.ndarray, 
                                    binary: np.ndarray) -> Dict[str, float]:
        """
        评估二值化质量
        
        Args:
            original: 原始灰度图像
            binary: 二值化图像
            
        Returns:
            Dict[str, float]: 质量评估指标
        """
        metrics = {}
        
        try:
            # 确保是灰度图
            if len(original.shape) == 3:
                gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            else:
                gray = original.copy()
            
            # 1. 边缘保持度
            original_edges = cv2.Canny(gray, 50, 150)
            binary_edges = cv2.Canny(binary, 50, 150)
            
            edge_preservation = np.sum(original_edges & binary_edges) / max(np.sum(original_edges), 1)
            metrics['edge_preservation'] = float(edge_preservation)
            
            # 2. 前景-背景分离度
            foreground_pixels = binary == 0  # 假设文本是黑色
            background_pixels = binary == 255
            
            if np.sum(foreground_pixels) > 0 and np.sum(background_pixels) > 0:
                fg_mean = np.mean(gray[foreground_pixels])
                bg_mean = np.mean(gray[background_pixels])
                separation = abs(bg_mean - fg_mean) / 255.0
                metrics['fg_bg_separation'] = float(separation)
            else:
                metrics['fg_bg_separation'] = 0.0
            
            # 3. 噪声水平
            # 计算小连通组件的比例（可能是噪声）
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                255 - binary, connectivity=8
            )
            
            small_components = np.sum(stats[1:, cv2.CC_STAT_AREA] < 50)  # 面积小于50的组件
            total_components = num_labels - 1  # 排除背景
            
            if total_components > 0:
                noise_ratio = small_components / total_components
                metrics['noise_level'] = float(noise_ratio)
            else:
                metrics['noise_level'] = 0.0
            
            # 4. 整体质量分数
            overall_score = (
                metrics['edge_preservation'] * 0.4 +
                metrics['fg_bg_separation'] * 0.4 +
                (1 - metrics['noise_level']) * 0.2
            )
            metrics['overall_quality'] = float(overall_score)
            
        except Exception as e:
            logger.error(f"二值化质量评估失败: {str(e)}")
            metrics = {
                'edge_preservation': 0.0,
                'fg_bg_separation': 0.0,
                'noise_level': 1.0,
                'overall_quality': 0.0
            }
        
        return metrics