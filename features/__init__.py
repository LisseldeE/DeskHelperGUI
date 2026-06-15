# -*- coding: utf-8 -*-
"""
DeskHelperGUI 功能模块
"""

from .quick_compress import QuickCompressWidget
from .file_name_extractor import FileNameExtractorWidget
from .image_processor import ImageProcessorWidget
from .format_converter import FormatConverterWidget
from .pdf_tool import PDFToolWidget
from .hash_checker import HashCheckerWidget
from .utils import get_unique_filepath

__all__ = [
    'QuickCompressWidget', 
    'FileNameExtractorWidget', 
    'ImageProcessorWidget', 
    'FormatConverterWidget', 
    'PDFToolWidget',
    'HashCheckerWidget',
    'get_unique_filepath'
]