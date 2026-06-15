# -*- coding: utf-8 -*-
"""
DeskHelperGUI 工具函数模块
"""

import os


def get_unique_filepath(filepath):
    """
    获取不冲突的文件路径（Windows风格）
    
    如果目标路径已存在同名文件，则返回类似 "文件名 (1).ext" 的路径。
    符合Windows系统的命名习惯。
    
    Args:
        filepath: 原始目标文件路径（绝对路径）
    
    Returns:
        不冲突的文件路径
    
    Examples:
        get_unique_filepath("/path/to/file.txt") 
        -> "/path/to/file.txt" (如果不存在)
        -> "/path/to/file (1).txt" (如果已存在)
        -> "/path/to/file (2).txt" (如果file (1).txt也已存在)
    """
    if not os.path.exists(filepath):
        return filepath
    
    # 分离文件名和扩展名
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    
    # 从1开始计数，寻找不冲突的文件名
    counter = 1
    while True:
        # 使用英文括号，符合Windows风格
        new_filename = f"{name} ({counter}){ext}"
        new_filepath = os.path.join(directory, new_filename)
        
        if not os.path.exists(new_filepath):
            return new_filepath
        
        counter += 1
        
        # 安全限制，防止无限循环（极端情况）
        if counter > 10000:
            # 使用时间戳作为后备方案
            import time
            timestamp = int(time.time())
            new_filename = f"{name}_{timestamp}{ext}"
            new_filepath = os.path.join(directory, new_filename)
            return new_filepath