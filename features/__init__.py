# -*- coding: utf-8 -*-
"""
DeskHelperGUI 功能模块
"""

from .quick_compress import QuickCompressWidget
from .file_processor import FileProcessorWidget
from .image_processor import ImageProcessorWidget
from .format_converter import FormatConverterWidget
from .pdf_tool import PDFToolWidget
from .hash_checker import HashCheckerWidget
from .file_encrypt import FileEncryptWidget
from .qr_tool import QRToolWidget
from .utils import get_unique_filepath

__all__ = [
    'QuickCompressWidget', 
    'FileProcessorWidget', 
    'ImageProcessorWidget', 
    'FormatConverterWidget', 
    'PDFToolWidget',
    'HashCheckerWidget',
    'FileEncryptWidget',
    'QRToolWidget',
    'get_unique_filepath'
]