"""
文档扫描器主处理管道

整合所有图像处理模块，提供完整的文档扫描处理功能。
这是一个统一的接口，用于将照片转换为扫描风格的文档图像。
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging
from PIL import Image

from .geometric_correction import GeometricCorrector
from .background_processing import BackgroundProcessor
from .binarization import Binarizer
from .enhancement import ImageEnhancer
from .utils import ImageUtils

logger = logging.getLogger(__name__)


class DocumentScanner:
    """文档扫描器主类"""

    def __init__(self):
        """初始化各个处理模块"""
        self.geometric_corrector = GeometricCorrector()
        self.background_processor = BackgroundProcessor()
        self.binarizer = Binarizer()
        self.image_enhancer = ImageEnhancer()
        self.image_utils = ImageUtils()

        # 默认处理配置
        self.default_config = {
            # 几何校正配置
            'geometric': {
                'enable_perspective': False,  # 关闭透视校正
                'enable_deskew': True,        # 保留去偏斜
                'enable_crop': True           # 保留自动裁剪
            },

            # 背景处理配置
            'background': {
                'method': 'median_division',
                'kernel_size': 31,
                'brightness_adjustment': 1.25,
                'contrast_adjustment': 1.12
            },

            # 二值化配置
            'binarization': {
                'enable': False,  # 默认不进行二值化，保持彩色输出
                'method': 'adaptive_gaussian',
                'block_size': 11,
                'c_constant': 2
            },

            # 图像增强配置
            'enhancement': {
                'enhance_contrast': True,
                'reduce_noise': True,
                'sharpen': True,
                'gamma_correction': False
            },

            # 输出配置
            'output': {
                'white_background': False,  # 默认关闭白底处理，避免过度增白
                'max_width': 2000,
                'max_height': 2000,
                'quality': 95
            }
        }

        # 平衡模式配置 - 更温和的处理选项
        self.balanced_config = {
            # 几何校正配置
            'geometric': {
                'enable_perspective': False,
                'enable_deskew': True,
                'enable_crop': True
            },

            # 背景处理配置 - 更保守的参数
            'background': {
                'method': 'median_division',
                'kernel_size': 25,  # 较小的核，减少过度处理
                'brightness_adjustment': 1.20,  # 更强的亮度提升，改善背景白度
                'contrast_adjustment': 1.08     # 适度增加对比度
            },

            # 二值化配置
            'binarization': {
                'enable': False,
                'method': 'adaptive_gaussian',
                'block_size': 15,  # 更大的块，更平滑的效果
                'c_constant': 5    # 更大的常数，保留更多细节
            },

            # 图像增强配置 - 减少处理强度
            'enhancement': {
                'enhance_contrast': True,
                'reduce_noise': False,  # 关闭降噪，保持原始细节
                'sharpen': False,       # 关闭锐化，避免过度处理
                'gamma_correction': False
            },

            # 输出配置
            'output': {
                'white_background': False,
                'max_width': 2000,
                'max_height': 2000,
                'quality': 95
            }
        }

        # 自然模式配置 - 最大程度保留原图特征，只做必要优化
        self.natural_config = {
            # 几何校正配置
            'geometric': {
                'enable_perspective': False,
                'enable_deskew': True,
                'enable_crop': True
            },

            # 背景处理配置 - 最轻微的处理
            'background': {
                'method': 'natural_enhancement',
                'brightness_boost': 1.15,      # 提升亮度，改善背景白度
                'contrast_boost': 1.05,        # 轻微增加对比度
                'preserve_ratio': 0.5          # 保留50%原图特征，允许更多白化
            },

            # 二值化配置
            'binarization': {
                'enable': False,
                'method': 'adaptive_gaussian',
                'block_size': 21,
                'c_constant': 8
            },

            # 图像增强配置 - 最小化处理
            'enhancement': {
                'enhance_contrast': False,  # 关闭对比度增强
                'reduce_noise': False,      # 关闭降噪
                'sharpen': False,          # 关闭锐化
                'gamma_correction': False
            },

            # 输出配置
            'output': {
                'white_background': False,
                'max_width': 2000,
                'max_height': 2000,
                'quality': 95
            }
        }

        # 超白模式配置 - 专门解决背景不够白净的问题
        self.ultra_white_config = {
            # 几何校正配置
            'geometric': {
                'enable_perspective': False,
                'enable_deskew': True,
                'enable_crop': True
            },

            # 背景处理配置 - 超强白化
            'background': {
                'method': 'ultra_whitening',
                'kernel_size': 25,
                'whitening_strength': 1.3,      # 强力白化
                'background_threshold': 0.7     # 背景检测阈值
            },

            # 二值化配置
            'binarization': {
                'enable': False,
                'method': 'adaptive_gaussian',
                'block_size': 15,
                'c_constant': 3
            },

            # 图像增强配置 - 适度增强
            'enhancement': {
                'enhance_contrast': True,   # 开启对比度增强
                'reduce_noise': False,      # 关闭降噪，保持清晰度
                'sharpen': False,          # 关闭锐化，避免过度处理
                'gamma_correction': False
            },

            # 输出配置
            'output': {
                'white_background': False,  # 已经通过背景处理实现白化
                'max_width': 2000,
                'max_height': 2000,
                'quality': 95
            }
        }

    def scan_document(self, image: np.ndarray,
                     config: Optional[Dict[str, Any]] = None,
                     return_intermediate: bool = False) -> Dict[str, Any]:
        """
        执行完整的文档扫描处理流程

        Args:
            image: 输入图像（PIL或OpenCV格式）
            config: 处理配置（可选）
            return_intermediate: 是否返回中间处理结果

        Returns:
            Dict[str, Any]: 处理结果，包含最终图像和可选的中间结果
        """
        try:
            logger.info("开始文档扫描处理流程")

            # 合并配置
            processing_config = self._merge_config(config)

            # 确保输入是OpenCV格式
            if hasattr(image, 'mode'):  # PIL Image check
                cv_image = self.image_utils.pil_to_cv2(image)
            else:
                cv_image = image.copy()

            # 存储中间结果
            intermediate_results = {}

            # 记录原始尺寸
            original_height, original_width = cv_image.shape[:2]
            original_size = (original_width, original_height)

            # 调整图像大小以提高处理速度
            max_width = processing_config['output']['max_width']
            max_height = processing_config['output']['max_height']
            resized_image, scale_factor = self.image_utils.resize_image(
                cv_image, max_width, max_height
            )

            if return_intermediate:
                intermediate_results['01_resized'] = resized_image.copy()

            current_image = resized_image

            # 步骤1: 几何校正
            #if any(processing_config['geometric'].values()):
            #    logger.info("执行几何校正...")
            #    current_image = self.geometric_corrector.correct_document(
            #        current_image, **processing_config['geometric']
            #    )
            #    if return_intermediate:
            #        intermediate_results['02_geometric_corrected'] = current_image.copy()

            # 步骤2: 背景处理
            logger.info("执行背景处理...")
            current_image = self.background_processor.process_background(
                current_image, **processing_config['background']
            )
            if return_intermediate:
                intermediate_results['03_background_processed'] = current_image.copy()

            # 步骤3: 图像增强
            if any(processing_config['enhancement'].values()):
                logger.info("执行图像增强...")
                current_image = self.image_enhancer.enhance_image(
                    current_image, **processing_config['enhancement']
                )
                if return_intermediate:
                    intermediate_results['04_enhanced'] = current_image.copy()

            # 步骤4: 创建白底文档（如果启用）
            if processing_config['output']['white_background']:
                logger.info("创建白底文档...")
                current_image = self.background_processor.create_white_background_document(
                    current_image
                )
                if return_intermediate:
                    intermediate_results['05_white_background'] = current_image.copy()

            # 步骤5: 二值化（如果启用）
            if processing_config['binarization']['enable']:
                logger.info("执行二值化...")
                current_image = self.binarizer.binarize(
                    current_image, **{k: v for k, v in processing_config['binarization'].items() if k != 'enable'}
                )
                if return_intermediate:
                    intermediate_results['06_binarized'] = current_image.copy()

            # 步骤6: 恢复原始尺寸（如果需要）
            if scale_factor != 1.0:
                logger.info("恢复原始尺寸...")
                current_image = self.image_utils.restore_size(
                    current_image, original_size, scale_factor
                )

            # 最终裁剪白色边框
            final_image = self.geometric_corrector.auto_crop_white_borders(current_image)

            # 构建返回结果
            result = {
                'final_image': final_image,
                'original_size': original_size,
                'final_size': final_image.shape[:2],
                'scale_factor': scale_factor,
                'processing_config': processing_config
            }

            if return_intermediate:
                result['intermediate_results'] = intermediate_results

            logger.info(f"文档扫描处理完成，从 {original_size} 处理到 {final_image.shape[:2]}")
            return result

        except Exception as e:
            logger.error(f"文档扫描处理失败: {str(e)}")
            # 返回原图作为失败保护
            return {
                'final_image': image,
                'original_size': image.shape[:2] if hasattr(image, 'shape') else (0, 0),
                'final_size': image.shape[:2] if hasattr(image, 'shape') else (0, 0),
                'scale_factor': 1.0,
                'processing_config': self.default_config,
                'error': str(e)
            }

    def quick_scan(self, image: np.ndarray) -> np.ndarray:
        """
        快速扫描模式，使用默认配置

        Args:
            image: 输入图像

        Returns:
            np.ndarray: 处理后的图像
        """
        result = self.scan_document(image)
        return result['final_image']

    def scan_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        针对OCR优化的扫描模式

        Args:
            image: 输入图像

        Returns:
            np.ndarray: 适合OCR的处理后图像
        """
        # OCR优化配置
        ocr_config = {
            'geometric': {
                'enable_perspective': True,
                'enable_deskew': True,
                'enable_crop': True
            },
            'background': {
                'method': 'median_division',
                'kernel_size': 61,  # 更大的核以更好地移除背景
                'brightness_adjustment': 1.3,
                'contrast_adjustment': 1.2
            },
            'binarization': {
                'enable': True,  # OCR通常需要二值化
                'method': 'adaptive_gaussian',
                'block_size': 15,
                'c_constant': 4
            },
            'enhancement': {
                'enhance_contrast': True,
                'reduce_noise': True,
                'sharpen': False,  # OCR不需要太多锐化
                'gamma_correction': False
            },
            'output': {
                'white_background': True,
                'max_width': 2000,
                'max_height': 2000
            }
        }

        result = self.scan_document(image, config=ocr_config)
        return result['final_image']

    def scan_for_printing(self, image: np.ndarray) -> np.ndarray:
        """
        针对打印优化的扫描模式

        Args:
            image: 输入图像

        Returns:
            np.ndarray: 适合打印的处理后图像
        """
        # 打印优化配置
        print_config = {
            'geometric': {
                'enable_perspective': True,
                'enable_deskew': True,
                'enable_crop': True
            },
            'background': {
                'method': 'median_division',
                'kernel_size': 45,
                'brightness_adjustment': 1.1,
                'contrast_adjustment': 1.05
            },
            'binarization': {
                'enable': False,  # 保持彩色以获得更好的打印效果
            },
            'enhancement': {
                'enhance_contrast': True,
                'reduce_noise': True,
                'sharpen': True,
                'gamma_correction': True
            },
            'output': {
                'white_background': True,
                'max_width': 3000,  # 更高分辨率用于打印
                'max_height': 3000
            }
        }

        result = self.scan_document(image, config=print_config)
        return result['final_image']

    def detect_document_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检测文档质量并提供建议

        Args:
            image: 输入图像

        Returns:
            Dict[str, Any]: 质量检测结果和建议
        """
        try:
            logger.info("开始文档质量检测")

            # 转换为灰度图进行分析
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            quality_report = {}

            # 1. 检测模糊程度
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = float(np.var(laplacian.astype(np.float64)))
            quality_report['sharpness'] = {
                'score': min(laplacian_var / 1000, 1.0),
                'level': 'good' if laplacian_var > 500 else 'poor',
                'suggestion': '图像较模糊，建议重新拍摄' if laplacian_var <= 100 else '图像清晰度可接受'
            }

            # 2. 检测光照均匀性
            blur = cv2.GaussianBlur(gray, (21, 21), 0)
            illumination_var = float(np.var(blur.astype(np.float64)))
            quality_report['illumination'] = {
                'score': max(0, 1.0 - illumination_var / 5000),
                'level': 'good' if illumination_var < 2000 else 'poor',
                'suggestion': '光照不均匀，建议调整光源' if illumination_var >= 3000 else '光照均匀度良好'
            }

            # 3. 检测倾斜程度
            skew_angle = abs(self.image_utils.calculate_skew_angle(gray))
            quality_report['skew'] = {
                'angle': skew_angle,
                'level': 'good' if skew_angle < 2 else 'poor',
                'suggestion': '文档倾斜严重，建议重新拍摄' if skew_angle > 5 else '文档方向良好'
            }

            # 4. 检测对比度
            contrast = float(np.std(gray.astype(np.float64)))
            quality_report['contrast'] = {
                'score': min(contrast / 100, 1.0),
                'level': 'good' if contrast > 50 else 'poor',
                'suggestion': '对比度较低，建议改善光照条件' if contrast < 30 else '对比度良好'
            }

            # 5. 整体质量评分
            overall_score = (
                quality_report['sharpness']['score'] * 0.3 +
                quality_report['illumination']['score'] * 0.3 +
                (1.0 if skew_angle < 2 else 0.5) * 0.2 +
                quality_report['contrast']['score'] * 0.2
            )

            quality_report['overall'] = {
                'score': overall_score,
                'level': 'excellent' if overall_score > 0.8 else 'good' if overall_score > 0.6 else 'poor',
                'recommendation': self._get_processing_recommendation(quality_report)
            }

            logger.info(f"文档质量检测完成，整体评分: {overall_score:.2f}")
            return quality_report

        except Exception as e:
            logger.error(f"文档质量检测失败: {str(e)}")
            return {'error': str(e)}

    def _merge_config(self, user_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并用户配置和默认配置

        Args:
            user_config: 用户提供的配置

        Returns:
            Dict[str, Any]: 合并后的配置
        """
        if user_config is None:
            return self.default_config.copy()

        merged_config = self.default_config.copy()

        for section, settings in user_config.items():
            if section in merged_config:
                if isinstance(settings, dict):
                    merged_config[section].update(settings)
                else:
                    merged_config[section] = settings
            else:
                merged_config[section] = settings

        return merged_config

    def _get_processing_recommendation(self, quality_report: Dict[str, Any]) -> str:
        """
        根据质量报告推荐处理策略

        Args:
            quality_report: 质量检测报告

        Returns:
            str: 处理建议
        """
        recommendations = []

        if quality_report['sharpness']['level'] == 'poor':
            recommendations.append("启用锐化处理")

        if quality_report['illumination']['level'] == 'poor':
            recommendations.append("使用更大的中值滤波核进行背景均匀化")

        if quality_report['contrast']['level'] == 'poor':
            recommendations.append("启用CLAHE对比度增强")

        if quality_report['skew']['level'] == 'poor':
            recommendations.append("启用去偏斜处理")

        if not recommendations:
            return "图像质量良好，使用标准处理流程即可"

        return "建议: " + "、".join(recommendations)

    def batch_process(self, images: List[np.ndarray],
                     config: Optional[Dict[str, Any]] = None,
                     progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        批量处理多个文档图像

        Args:
            images: 图像列表
            config: 处理配置
            progress_callback: 进度回调函数

        Returns:
            List[Dict[str, Any]]: 处理结果列表
        """
        results = []
        total_images = len(images)

        logger.info(f"开始批量处理 {total_images} 个图像")

        for i, image in enumerate(images):
            try:
                logger.info(f"处理第 {i+1}/{total_images} 个图像")

                result = self.scan_document(image, config)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, total_images)

            except Exception as e:
                logger.error(f"处理第 {i+1} 个图像失败: {str(e)}")
                results.append({'error': str(e), 'final_image': image})

        logger.info("批量处理完成")
        return results

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的图像格式

        Returns:
            List[str]: 支持的格式列表
        """
        return ['JPEG', 'PNG', 'BMP', 'TIFF', 'WEBP', 'GIF']

    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return self.default_config.copy()

    def get_balanced_config(self) -> Dict[str, Any]:
        """
        获取平衡配置 - 更温和的处理选项，避免过度增白

        Returns:
            Dict[str, Any]: 平衡配置字典
        """
        return self.balanced_config.copy()

    def get_natural_config(self) -> Dict[str, Any]:
        """
        获取自然配置 - 最大程度保留原图特征，只做必要优化

        Returns:
            Dict[str, Any]: 自然配置字典
        """
        return self.natural_config.copy()

    def get_ultra_white_config(self) -> Dict[str, Any]:
        """
        获取超白配置 - 专门解决背景不够白净的问题

        Returns:
            Dict[str, Any]: 超白配置字典
        """
        return self.ultra_white_config.copy()
