"""
文档扫描图像处理模块

该模块提供了完整的文档扫描处理功能，包括：
- 几何校正（去偏斜、透视校正）
- 背景处理（美白、移除）
- 二值化处理
- 图像质量增强

主要组件：
- geometric_correction: 几何校正模块
- background_processing: 背景处理模块
- binarization: 二值化处理模块
- enhancement: 图像质量增强模块
- document_scanner: 主处理管道
- utils: 工具函数
"""

from .document_scanner import DocumentScanner
from .geometric_correction import GeometricCorrector
from .background_processing import BackgroundProcessor
from .binarization import Binarizer
from .enhancement import ImageEnhancer
from .utils import ImageUtils

__all__ = [
    'DocumentScanner',
    'GeometricCorrector',
    'BackgroundProcessor', 
    'Binarizer',
    'ImageEnhancer',
    'ImageUtils'
]

__version__ = "0.1.0"