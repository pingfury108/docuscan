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
            method: 处理方法 ("median_division", "natural_enhancement", "adaptive_threshold", "color_separation", "ultra_whitening")
            **kwargs: 方法特定参数

        Returns:
            np.ndarray: 处理后的图像
        """
        try:
            if method == "median_division":
                return self.median_division_whitening(image, **kwargs)
            elif method == "natural_enhancement":
                return self.natural_background_enhancement(image, **kwargs)
            elif method == "adaptive_threshold":
                return self.adaptive_background_removal(image, **kwargs)
            elif method == "color_separation":
                return self.color_based_separation(image, **kwargs)
            elif method == "ultra_whitening":
                return self.ultra_background_whitening(image, **kwargs)
            else:
                logger.warning(f"未知的背景处理方法: {method}")
                return image

        except Exception as e:
            logger.error(f"背景处理失败: {str(e)}")
            return image

    def median_division_whitening(self, image: np.ndarray,
                                 kernel_size: int = 31,
                                 brightness_adjustment: float = 1.25,
                                 contrast_adjustment: float = 1.12) -> np.ndarray:
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

    def ultra_background_whitening(self, image: np.ndarray,
                                 kernel_size: int = 25,
                                 whitening_strength: float = 1.3,
                                 background_threshold: float = 0.7) -> np.ndarray:
        """
        超强背景白化处理 - 专门解决背景不够白净的问题

        Args:
            image: 输入图像
            kernel_size: 中值滤波核大小
            whitening_strength: 白化强度 (1.0-2.0)
            background_threshold: 背景检测阈值 (0.5-0.9)

        Returns:
            np.ndarray: 超白化处理后的图像
        """
        try:
            logger.info(f"开始超强背景白化，核大小: {kernel_size}, 白化强度: {whitening_strength}")

            # 确保核大小为奇数
            if kernel_size % 2 == 0:
                kernel_size += 1

            # 如果是彩色图像，分别处理每个通道
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    result[:, :, i] = self._ultra_whiten_channel(
                        image[:, :, i], kernel_size, whitening_strength, background_threshold)
                return result
            else:
                # 灰度图像直接处理
                return self._ultra_whiten_channel(
                    image, kernel_size, whitening_strength, background_threshold)

        except Exception as e:
            logger.error(f"超强背景白化失败: {str(e)}")
            return image

    def _ultra_whiten_channel(self, channel: np.ndarray,
                             kernel_size: int,
                             whitening_strength: float,
                             background_threshold: float) -> np.ndarray:
        """
        对单个通道进行超强白化处理

        Args:
            channel: 单通道图像
            kernel_size: 中值滤波核大小
            whitening_strength: 白化强度
            background_threshold: 背景检测阈值

        Returns:
            np.ndarray: 超白化处理后的通道
        """
        # 转换为浮点数进行计算
        channel_float = channel.astype(np.float32)

        # 1. 使用中值滤波获取背景估计
        background = cv2.medianBlur(channel, kernel_size).astype(np.float32)
        background = np.maximum(background, 1.0)  # 避免除零

        # 2. 计算背景掩码 - 使用多重方法确保准确性
        # 方法1: 基于亮度的背景检测
        brightness_threshold = np.percentile(channel_float, 100 * background_threshold)
        bright_mask = channel_float >= brightness_threshold

        # 方法2: 基于局部方差的背景检测（背景区域方差较小）
        kernel = np.ones((5, 5), np.float32) / 25
        channel_f32 = channel_float.astype(np.float32)
        local_mean = cv2.filter2D(channel_f32, cv2.CV_32F, kernel)
        local_variance = cv2.filter2D((channel_f32 - local_mean) ** 2, cv2.CV_32F, kernel)
        variance_threshold = np.percentile(local_variance, 30)  # 低方差区域
        smooth_mask = local_variance <= variance_threshold

        # 方法3: Otsu自动阈值
        _, otsu_mask = cv2.threshold(channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_background = otsu_mask == 255

        # 综合背景掩码
        background_mask = np.logical_and(
            np.logical_or(bright_mask, smooth_mask),
            otsu_background
        )

        # 3. 背景区域超强白化
        result = channel_float.copy()

        if np.any(background_mask):
            background_pixels = result[background_mask]
            if len(background_pixels) > 0:
                # 计算背景像素的统计信息
                bg_mean = np.mean(background_pixels)

                # 目标白度
                target_white = 250

                # 如果背景不够白，进行强化
                if bg_mean < target_white:
                    # 计算白化因子
                    white_factor = min(float(target_white / bg_mean), whitening_strength) if bg_mean > 0 else whitening_strength

                    # 应用白化，保持像素相对关系
                    whitened_bg = np.clip(
                        background_pixels * white_factor + (target_white - bg_mean * white_factor) * 0.3,
                        background_pixels,  # 不能比原值更暗
                        255
                    )

                    result[background_mask] = whitened_bg

        # 4. 全局亮度优化
        current_mean = np.mean(result)
        if current_mean < 200:  # 如果整体还偏暗
            brightness_boost = min(float(220 / current_mean), 1.2) if current_mean > 0 else 1.2
            result = np.clip(result * brightness_boost, result, 255)

        # 5. 最终背景清洁
        # 使用形态学操作清理背景
        result_uint8 = result.astype(np.uint8)

        # 检测最终的背景区域
        _, final_mask = cv2.threshold(result_uint8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        final_background = final_mask == 255

        # 对背景进行最后的清洁处理
        if np.any(final_background):
            bg_pixels = result[final_background]
            if len(bg_pixels) > 0 and np.mean(bg_pixels) < 248:
                # 轻微推向纯白
                result[final_background] = np.clip(bg_pixels * 1.02 + 3, bg_pixels, 255)

        # 转换回uint8
        return np.clip(result, 0, 255).astype(np.uint8)

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

        # 平衡的除法操作，保持适当的亮度水平
        division_result = channel_float / background

        # 使用自适应标准化，基于原图的亮度分布
        original_mean = np.mean(channel_float)
        target_mean = min(float(original_mean * 1.3), 240)  # 更大幅度提升亮度

        # 标准化到目标亮度水平
        normalized = division_result * 255.0
        current_mean = np.mean(normalized)

        if current_mean > 0:
            scale_factor = target_mean / current_mean
            # 允许更大的缩放范围，实现更白的背景
            scale_factor = np.clip(scale_factor, 1.0, 2.0)
            normalized = normalized * scale_factor

        # 背景区域检测和增强白化
        # 使用Otsu阈值自动检测背景和前景
        gray_for_thresh = normalized.astype(np.uint8)
        _, binary_mask = cv2.threshold(gray_for_thresh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        background_mask = binary_mask == 255  # 亮区域作为背景

        # 对背景区域进行额外白化
        background_enhanced = normalized.copy()
        if np.any(background_mask):
            # 背景区域推向更白
            background_values = normalized[background_mask]
            if len(background_values) > 0:
                bg_mean = np.mean(background_values)
                if bg_mean < 240:  # 如果背景还不够白
                    whitening_factor = min(250 / bg_mean, 1.5) if bg_mean > 0 else 1.2
                    background_enhanced[background_mask] = np.clip(
                        background_values * whitening_factor,
                        background_values,  # 不能比原值更暗
                        255
                    )

        # 限制结果范围
        normalized = np.clip(background_enhanced, 0, 255)

        # 与原图混合，使用更激进的混合比例
        blend_ratio = 0.85  # 85%处理结果 + 15%原图，更强的白化效果
        blended = normalized * blend_ratio + channel_float * (1 - blend_ratio)

        # 更强的亮度和对比度调整
        brightness_factor = (brightness_adjustment - 1.0) * 45
        adjusted = blended * contrast_adjustment + brightness_factor

        # 最终背景区域优化
        final_gray = adjusted.astype(np.uint8)
        _, final_binary = cv2.threshold(final_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        final_bg_mask = final_binary == 255

        # 确保背景区域足够白
        if np.any(final_bg_mask):
            bg_pixels = adjusted[final_bg_mask]
            if len(bg_pixels) > 0 and np.mean(bg_pixels) < 245:
                # 将背景像素进一步推向白色
                adjusted[final_bg_mask] = np.clip(bg_pixels * 1.05 + 10, bg_pixels, 255)

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
            lower_bound = np.array([background_color_threshold])
            upper_bound = np.array([255])
            background_mask = cv2.inRange(hsv[:, :, 2], lower_bound, upper_bound)

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
                                       text_threshold: int = 130) -> np.ndarray:
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
            logger.info(f"开始创建白底文档，文本阈值: {text_threshold}")

            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 多层次内容检测，更准确地识别文本和图形

            # 1. 基础固定阈值
            fixed_mask = gray < text_threshold

            # 2. 自适应阈值 - 更保守的参数
            adaptive_binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 21, 10
            )
            adaptive_mask = adaptive_binary == 0

            # 3. 基于梯度的边缘检测，捕获文本边缘
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            edge_threshold = np.percentile(gradient_magnitude, 85)
            edge_mask = gradient_magnitude > edge_threshold

            # 4. 合并所有掩码，保留更多内容
            content_mask = np.logical_or.reduce([fixed_mask, adaptive_mask, edge_mask])

            # 5. 形态学操作，优化掩码
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

            content_mask_uint8 = content_mask.astype(np.uint8)
            content_mask_uint8 = cv2.morphologyEx(content_mask_uint8, cv2.MORPH_CLOSE, kernel_close)
            content_mask_uint8 = cv2.morphologyEx(content_mask_uint8, cv2.MORPH_OPEN, kernel_open)
            content_mask = content_mask_uint8.astype(bool)

            # 创建白色背景
            if len(image.shape) == 3:
                white_bg = np.full_like(image, 255)
            else:
                white_bg = np.full_like(gray, 255)

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

    def natural_background_enhancement(self, image: np.ndarray,
                                     brightness_boost: float = 1.08,
                                     contrast_boost: float = 1.03,
                                     preserve_ratio: float = 0.6) -> np.ndarray:
        """
        自然背景增强 - 专门针对图片太暗的问题，最大程度保留原图特征

        Args:
            image: 输入图像
            brightness_boost: 亮度提升因子
            contrast_boost: 对比度提升因子
            preserve_ratio: 原图保留比例 (0-1)

        Returns:
            np.ndarray: 自然增强后的图像
        """
        try:
            logger.info(f"开始自然背景增强，亮度提升: {brightness_boost}, 对比度: {contrast_boost}")

            # 如果是彩色图像，分别处理每个通道
            if len(image.shape) == 3:
                result = np.zeros_like(image)
                for i in range(3):
                    result[:, :, i] = self._natural_enhance_channel(
                        image[:, :, i], brightness_boost, contrast_boost, preserve_ratio)
                return result
            else:
                # 灰度图像直接处理
                return self._natural_enhance_channel(
                    image, brightness_boost, contrast_boost, preserve_ratio)

        except Exception as e:
            logger.error(f"自然背景增强失败: {str(e)}")
            return image

    def _natural_enhance_channel(self, channel: np.ndarray,
                                brightness_boost: float,
                                contrast_boost: float,
                                preserve_ratio: float) -> np.ndarray:
        """
        对单个通道进行自然增强

        Args:
            channel: 单通道图像
            brightness_boost: 亮度提升因子
            contrast_boost: 对比度提升因子
            preserve_ratio: 原图保留比例

        Returns:
            np.ndarray: 增强后的通道
        """
        # 转换为浮点数进行计算
        channel_float = channel.astype(np.float32)

        # 计算原图统计信息
        original_mean = np.mean(channel_float)
        original_std = np.std(channel_float)

        # 温和的亮度和对比度调整
        # 使用线性变换: new_value = contrast * (old_value - mean) + new_mean
        target_mean = min(float(original_mean * brightness_boost), 240)  # 避免过度提亮
        target_std = original_std * contrast_boost

        # 应用调整
        if original_std > 0:
            enhanced = (channel_float - original_mean) * (target_std / original_std) + target_mean
        else:
            enhanced = channel_float + (target_mean - original_mean)

        # 限制范围
        enhanced = np.clip(enhanced, 0, 255)

        # 与原图混合，保持自然效果
        result = enhanced * (1 - preserve_ratio) + channel_float * preserve_ratio

        # 最终限制并转换回uint8
        result = np.clip(result, 0, 255).astype(np.uint8)

        return result
