# -*- coding: utf-8 -*-
"""
DeskHelperGUI 国际化模块
管理多语言文本
"""

# 语言文本字典
LANGUAGES = {
    'zh': {
        # 主窗口
        'app_name': 'DeskHelperGUI',
        'lang_switch': 'EN',
        'about': '关于',
        'about_title': '关于',

        # 侧边栏功能
        'feature_quick_compress': '快捷压缩',
        'feature_file_extractor': '文件名提取',

        # 关于对话框
        'about_version': '版本：R2',
        'about_desc': '桌面办公小助手，提供多种快捷实用功能，让日常办公更高效',
        'about_author': '作者：Lisselde_E',
        'about_check_update': '检查更新',
        'about_close': '关闭',
        'about_email_copied': '邮箱已复制到剪贴板',
        'about_no_tags': '未找到版本标签',
        'about_parse_error': '无法解析当前版本号',
        'about_remote_parse_error': '无法解析远程版本号',
        'about_new_version': '发现新版本 {}！\n是否前往GitHub下载？',
        'about_latest': '当前已是最新版本',
        'about_network_error': '网络错误：{}\n请检查网络连接',
        'about_check_failed': '检查更新失败：{}',
        'about_yes': '是',
        'about_no': '否',
        'about_info': '提示',

        # 设置对话框
        'settings_title': '设置',
        'settings_no_path_tip': '未配置保存路径，在下方选择文件保存路径',
        'settings_save_path_tip': '修改全局保存路径',
        'settings_save_placeholder': '选择保存路径',
        'settings_browse': '浏览...',
        'settings_save': '保存',
        'settings_close': '关闭',
        'settings_select_folder': '选择保存文件夹',
        'settings_warning': '提示',
        'settings_empty_path': '请选择保存路径',
        'settings_invalid_path': '路径不存在，请选择有效的文件夹',

        # 快捷压缩
        'compress_title': '文件列表',
        'compress_tip': '拖拽文件/文件夹到此处，或点击空白区域添加',
        'compress_add_file': '添加文件',
        'compress_add_folder': '添加文件夹',
        'compress_clear': '清空列表',
        'compress_remove': '移除选中',
        'compress_settings': '压缩设置',
        'compress_name': '压缩包名称：',
        'compress_name_placeholder': '留空则使用默认名称',
        'compress_format': '压缩格式：',
        'compress_level': '压缩级别：',
        'compress_level_fastest': '最快',
        'compress_level_fast': '较快',
        'compress_level_normal': '标准',
        'compress_level_slow': '较慢',
        'compress_level_slowest': '最慢',
        'compress_encrypt': '加密压缩',
        'compress_no_password': '无密码',
        'compress_password': '密码：',
        'compress_password_placeholder': '输入密码',
        'compress_show_password': '显示',
        'compress_save_path': '保存路径：',
        'compress_save_placeholder': '选择保存路径',
        'compress_output_path': '输出路径：{}',
        'compress_browse': '浏览...',
        'compress_start': '开始压缩',
        'compress_select_files': '选择文件',
        'compress_select_folder': '选择文件夹',
        'compress_all_files': '所有文件 (*.*)',
        'compress_select_save': '选择保存路径',

        # 解压功能
        'extract_start': '开始解压',
        'extract_password_title': '当前压缩包存在加密',
        'extract_password_placeholder': '输入解压密码',
        'extract_confirm': '确认',
        'extract_done': '解压完成！\n文件已保存至：{}',
        'extract_failed': '解压失败：{}',
        'extract_need_password': '压缩包需要密码',
        'extract_wrong_password': '密码错误',
        'extract_no_compress_files': '列表中需要只包含压缩文件（ZIP、7z、TAR）才能解压',

        # 提示消息
        'msg_warning': '提示',
        'msg_error': '错误',
        'msg_success': '成功',
        'msg_add_files': '请先添加要压缩的文件或文件夹',
        'msg_select_path': '请选择保存路径',
        'msg_enter_password': '请输入密码',
        'msg_need_py7zr': '需要安装 py7zr 库才能使用 7z 格式\n请运行: pip install py7zr',
        'msg_compress_done': '压缩完成！\n文件已保存至：{}',
        'msg_compress_failed': '压缩失败：{}',

        # 文件名提取
        'extractor_folder': '文件夹选择',
        'extractor_folder_placeholder': '拖拽文件夹到此处，或点击右侧按钮选择',
        'extractor_tip': '拖拽文件夹到上方输入框，或点击"浏览..."按钮选择',
        'extractor_browse': '浏览...',
        'extractor_include_ext': '包含扩展名',
        'extractor_preview': '文件预览',
        'extractor_status_ready': '准备就绪',
        'extractor_status_found': '找到 {} 个文件',
        'extractor_output_path': '输出路径：{}',
        'extractor_no_folder': '请先选择文件夹',
        'extractor_no_files': '文件夹中没有找到文件',
        'extractor_save_path': '保存路径',
        'extractor_save_placeholder': '选择保存路径（留空则保存到源文件夹）',
        'extractor_select_folder': '选择目标文件夹',
        'extractor_select_save': '选择保存位置',
        'extractor_preview_btn': '刷新预览',
        'extractor_export': '导出到Excel',
        'extractor_need_pandas': '需要安装 pandas 和 openpyxl 库才能导出Excel\n请运行: pip install pandas openpyxl',
        'extractor_export_failed': '导出失败：{}',
        'extractor_export_done': '导出完成！\n文件已保存至：{}',

        # 图片处理
        'feature_image_processor': '图片处理',
        'image_import': '图片导入',
        'image_import_placeholder': '拖拽图片到此处，或点击右侧按钮选择',
        'image_import_tip': '支持 PNG、JPG、JPEG、BMP、GIF、WebP 格式',
        'image_browse': '浏览...',
        'image_file_info': '尺寸：{}×{} | 大小：{}',
        'image_process_mode': '处理方式',
        'image_rotate': '旋转图片',
        'image_crop': '裁剪尺寸',
        'image_compress': '压缩大小',
        'image_rotate_settings': '旋转设置',
        'image_angle': '旋转角度：',
        'image_angle_custom': '自定义',
        'image_custom_angle': '自定义角度：',
        'image_crop_settings': '裁剪设置',
        'image_preset_size': '预设尺寸：',
        'image_custom': '自定义尺寸',
        'image_custom_size': '自定义尺寸：',
        'image_keep_ratio': '保持纵横比',
        'image_compress_settings': '压缩设置',
        'image_target_size': '目标大小：',
        'image_size_larger': '目标大小大于原文件，将保持原质量',
        'image_compress_ratio': '压缩至原大小的 {:.1f}%',
        'image_preview': '图片预览',
        'image_preview_placeholder': '请先导入图片',
        'image_preview_size': '预览尺寸：{}×{}',
        'image_preview_btn': '预览效果',
        'image_reset': '重置',
        'image_save': '保存图片',
        'image_save_path': '保存路径',
        'image_save_placeholder': '选择保存路径',
        'image_output_path': '输出路径：{}',
        'image_select_file': '选择图片文件',
        'image_select_save': '选择保存位置',
        'image_files': '图片文件',
        'image_need_pil': '需要安装 Pillow 库才能处理图片\n请运行: pip install Pillow',
        'image_no_image': '请先导入图片',
        'image_load_failed': '图片加载失败：{}',
        'image_process_failed': '图片处理失败：{}',
        'image_no_effect': '请至少启用一项处理功能',
        'image_enable': '启用',
        'image_disable': '禁用',
        'image_done': '图片处理完成！\n文件已保存至：{}',
        'image_failed': '图片处理失败：{}',

        # 格式转换
        'feature_format_converter': '格式转换',
        'converter_import': '文件导入',
        'converter_single_file': '单个文件',
        'converter_folder': '文件夹',
        'converter_import_placeholder': '拖拽文件/文件夹到此处，或点击右侧按钮选择',
        'converter_import_tip': '支持 PNG、JPG、JPEG、BMP、GIF、WebP、ICO、PDF 格式',
        'converter_browse': '浏览...',
        'converter_format_settings': '格式设置',
        'converter_target_format': '目标格式：',
        'converter_ico_settings': 'ICO设置',
        'converter_ico_size': '输出尺寸：',
        'converter_ico_size_tip': '尺寸上限由图片原始像素动态调整',
        'converter_file_list': '文件列表',
        'converter_file_count': '共 {} 个文件',
        'converter_output_path': '输出路径：{}',
        'converter_clear': '清空列表',
        'converter_start': '开始转换',
        'converter_image_files': '图片文件',
        'converter_all_files': '所有文件',
        'converter_select_file': '选择图片文件',
        'converter_select_folder': '选择文件夹',
        'converter_select_save': '选择保存位置',
        'converter_need_pil': '需要安装 Pillow 库才能转换图片\n请运行: pip install Pillow',
        'converter_need_pymupdf': '需要安装 PyMuPDF 库才能转换PDF\n请运行: pip install PyMuPDF',
        'converter_no_files': '请先添加要转换的文件',
        'converter_no_save_path': '请先在设置中配置全局保存路径',
        'converter_create_path_failed': '无法创建保存目录：{}',
        'converter_all_done': '转换完成！\n文件已保存至：{}',
        'converter_partial_done': '转换完成 {} / {} 个文件\n文件已保存至：{}',
        'converter_failed': '转换失败：{}',
        'converter_done': '格式转换完成！\n{}',

        # PDF工具
        'feature_pdf_tool': 'PDF工具',
        'pdf_import': '文件导入',
        'pdf_import_placeholder': '拖拽PDF文件到此处，或点击右侧按钮选择',
        'pdf_import_tip': '支持 PDF 格式文件，可导入多个文件',
        'pdf_browse': '浏览...',
        'pdf_clear': '清空列表',
        'pdf_operation_mode': '操作模式',
        'pdf_merge': '合并PDF',
        'pdf_split': '拆分PDF',
        'pdf_compress': '压缩PDF',
        'pdf_compress_settings': '压缩设置',
        'pdf_compress_quality': '压缩质量：',
        'pdf_quality_high': '高质量',
        'pdf_quality_medium': '中等质量',
        'pdf_quality_low': '低质量',
        'pdf_file_list': '文件列表',
        'pdf_file_count': '共 {} 个文件',
        'pdf_output_path': '输出路径：{}',
        'pdf_clear': '清空列表',
        'pdf_remove': '移除选中',
        'pdf_start': '开始处理',
        'pdf_files': 'PDF文件',
        'pdf_all_files': '所有文件',
        'pdf_select_file': '选择PDF文件',
        'pdf_need_pymupdf': '需要安装 PyMuPDF 库才能处理PDF\n请运行: pip install PyMuPDF',
        'pdf_no_files': '请先添加要处理的PDF文件',
        'pdf_no_save_path': '请先在设置中配置全局保存路径',
        'pdf_create_path_failed': '无法创建保存目录：{}',
        'pdf_merge_done': 'PDF合并完成！\n文件已保存至：{}',
        'pdf_merge_failed': 'PDF合并失败：{}',
        'pdf_split_done': 'PDF拆分完成！\n文件已保存至：{}',
        'pdf_split_failed': 'PDF拆分失败：{}',
        'pdf_compress_done': 'PDF压缩完成！\n文件已保存至：{}',
        'pdf_compress_partial': 'PDF压缩完成 {} / {} 个文件\n文件已保存至：{}',
        'pdf_compress_failed': 'PDF压缩失败：{}',
    },

    'en': {
        # 主窗口
        'app_name': 'DeskHelperGUI',
        'lang_switch': '中',
        'about': 'About',
        'about_title': 'About',

        # 侧边栏功能
        'feature_quick_compress': 'Quick Compress',
        'feature_file_extractor': 'File Name Extractor',

        # 关于对话框
        'about_version': 'Version: R2',
        'about_desc': 'A compact desktop toolset offering quick utilities for more efficient daily office work',
        'about_author': 'Author: Lisselde_E',
        'about_check_update': 'Check Update',
        'about_close': 'Close',
        'about_email_copied': 'Email copied to clipboard',
        'about_no_tags': 'No version tags found',
        'about_parse_error': 'Cannot parse current version',
        'about_remote_parse_error': 'Cannot parse remote version',
        'about_new_version': 'New version {} found!\nGo to GitHub to download?',
        'about_latest': 'Already the latest version',
        'about_network_error': 'Network error: {}\nPlease check your connection',
        'about_check_failed': 'Check update failed: {}',
        'about_yes': 'Yes',
        'about_no': 'No',
        'about_info': 'Info',

        # 设置对话框
        'settings_title': 'Settings',
        'settings_no_path_tip': 'Save path not configured. Please select a save path below',
        'settings_save_path_tip': 'Modify global save path',
        'settings_save_placeholder': 'Select save path',
        'settings_browse': 'Browse...',
        'settings_save': 'Save',
        'settings_close': 'Close',
        'settings_select_folder': 'Select Save Folder',
        'settings_warning': 'Warning',
        'settings_empty_path': 'Please select a save path',
        'settings_invalid_path': 'Path does not exist, please select a valid folder',

        # 快捷压缩
        'compress_title': 'File List',
        'compress_tip': 'Drag files/folders here, or click empty area to add',
        'compress_add_file': 'Add Files',
        'compress_add_folder': 'Add Folder',
        'compress_clear': 'Clear List',
        'compress_remove': 'Remove Selected',
        'compress_settings': 'Compression Settings',
        'compress_name': 'Archive Name:',
        'compress_name_placeholder': 'Leave empty for default name',
        'compress_format': 'Format:',
        'compress_level': 'Level:',
        'compress_level_fastest': 'Fastest',
        'compress_level_fast': 'Fast',
        'compress_level_normal': 'Normal',
        'compress_level_slow': 'Slow',
        'compress_level_slowest': 'Slowest',
        'compress_encrypt': 'Encrypt',
        'compress_no_password': 'No Password',
        'compress_password': 'Password:',
        'compress_password_placeholder': 'Enter password',
        'compress_show_password': 'Show',
        'compress_save_path': 'Save to:',
        'compress_save_placeholder': 'Select save path',
        'compress_output_path': 'Output: {}',
        'compress_browse': 'Browse...',
        'compress_start': 'Compress',
        'compress_select_files': 'Select Files',
        'compress_select_folder': 'Select Folder',
        'compress_all_files': 'All Files (*.*)',
        'compress_select_save': 'Select Save Path',

        # 解压功能
        'extract_start': 'Extract',
        'extract_password_title': 'Archive is encrypted',
        'extract_password_placeholder': 'Enter extraction password',
        'extract_confirm': 'Confirm',
        'extract_done': 'Extraction completed!\nFiles saved to: {}',
        'extract_failed': 'Extraction failed: {}',
        'extract_need_password': 'Archive requires password',
        'extract_wrong_password': 'Wrong password',
        'extract_no_compress_files': 'List must contain only archive files (ZIP, 7z, TAR) to extract',

        # 提示消息
        'msg_warning': 'Warning',
        'msg_error': 'Error',
        'msg_success': 'Success',
        'msg_add_files': 'Please add files or folders first',
        'msg_select_path': 'Please select save path',
        'msg_enter_password': 'Please enter password',
        'msg_need_py7zr': 'py7zr library required for 7z format\nPlease run: pip install py7zr',
        'msg_compress_done': 'Compression completed!\nFile saved to: {}',
        'msg_compress_failed': 'Compression failed: {}',

        # 文件名提取
        'extractor_folder': 'Folder Selection',
        'extractor_folder_placeholder': 'Drag folder here, or click button to select',
        'extractor_tip': 'Drag folder to the input above, or click "Browse..." button',
        'extractor_browse': 'Browse...',
        'extractor_include_ext': 'Include extension',
        'extractor_preview': 'File Preview',
        'extractor_status_ready': 'Ready',
        'extractor_status_found': 'Found {} files',
        'extractor_output_path': 'Output: {}',
        'extractor_no_folder': 'Please select a folder first',
        'extractor_no_files': 'No files found in folder',
        'extractor_save_path': 'Save Path',
        'extractor_save_placeholder': 'Select save path (leave empty to save in source folder)',
        'extractor_select_folder': 'Select Target Folder',
        'extractor_select_save': 'Select Save Location',
        'extractor_preview_btn': 'Refresh Preview',
        'extractor_export': 'Export to Excel',
        'extractor_need_pandas': 'pandas and openpyxl required for Excel export\nPlease run: pip install pandas openpyxl',
        'extractor_export_failed': 'Export failed: {}',
        'extractor_export_done': 'Export completed!\nFile saved to: {}',

        # 图片处理
        'feature_image_processor': 'Image Processor',
        'image_import': 'Image Import',
        'image_import_placeholder': 'Drag image here, or click button to select',
        'image_import_tip': 'Supports PNG, JPG, JPEG, BMP, GIF, WebP formats',
        'image_browse': 'Browse...',
        'image_file_info': 'Size: {}×{} | File: {}',
        'image_process_mode': 'Processing Mode',
        'image_rotate': 'Rotate Image',
        'image_crop': 'Crop Size',
        'image_compress': 'Compress Size',
        'image_rotate_settings': 'Rotation Settings',
        'image_angle': 'Angle:',
        'image_angle_custom': 'Custom',
        'image_custom_angle': 'Custom Angle:',
        'image_crop_settings': 'Crop Settings',
        'image_preset_size': 'Preset Size:',
        'image_custom': 'Custom Size',
        'image_custom_size': 'Custom Size:',
        'image_keep_ratio': 'Keep Aspect Ratio',
        'image_compress_settings': 'Compression Settings',
        'image_target_size': 'Target Size:',
        'image_size_larger': 'Target size larger than original, will keep original quality',
        'image_compress_ratio': 'Compress to {:.1f}% of original',
        'image_preview': 'Image Preview',
        'image_preview_placeholder': 'Please import an image first',
        'image_preview_size': 'Preview size: {}×{}',
        'image_preview_btn': 'Preview',
        'image_reset': 'Reset',
        'image_save': 'Save Image',
        'image_save_path': 'Save Path',
        'image_save_placeholder': 'Select save path',
        'image_output_path': 'Output: {}',
        'image_select_file': 'Select Image File',
        'image_select_save': 'Select Save Location',
        'image_files': 'Image Files',
        'image_need_pil': 'Pillow library required for image processing\nPlease run: pip install Pillow',
        'image_no_image': 'Please import an image first',
        'image_load_failed': 'Failed to load image: {}',
        'image_process_failed': 'Failed to process image: {}',
        'image_no_effect': 'Please enable at least one processing function',
        'image_enable': 'Enable',
        'image_disable': 'Disable',
        'image_done': 'Image processed!\nFile saved to: {}',
        'image_failed': 'Image processing failed: {}',

        # 格式转换
        'feature_format_converter': 'Format Converter',
        'converter_import': 'File Import',
        'converter_single_file': 'Single File',
        'converter_folder': 'Folder',
        'converter_import_placeholder': 'Drag file/folder here, or click button to select',
        'converter_import_tip': 'Supports PNG, JPG, JPEG, BMP, GIF, WebP, ICO, PDF formats',
        'converter_browse': 'Browse...',
        'converter_format_settings': 'Format Settings',
        'converter_target_format': 'Target Format:',
        'converter_ico_settings': 'ICO Settings',
        'converter_ico_size': 'Output Size:',
        'converter_ico_size_tip': 'Size limit dynamically adjusted by original image pixels',
        'converter_file_list': 'File List',
        'converter_file_count': '{} files total',
        'converter_output_path': 'Output: {}',
        'converter_clear': 'Clear List',
        'converter_start': 'Convert',
        'converter_image_files': 'Image Files',
        'converter_all_files': 'All Files',
        'converter_select_file': 'Select Image File',
        'converter_select_folder': 'Select Folder',
        'converter_select_save': 'Select Save Location',
        'converter_need_pil': 'Pillow library required for image conversion\nPlease run: pip install Pillow',
        'converter_need_pymupdf': 'PyMuPDF library required for PDF conversion\nPlease run: pip install PyMuPDF',
        'converter_no_files': 'Please add files to convert first',
        'converter_no_save_path': 'Please configure global save path in settings first',
        'converter_create_path_failed': 'Failed to create save directory: {}',
        'converter_all_done': 'Conversion completed!\nFiles saved to: {}',
        'converter_partial_done': 'Converted {} / {} files\nFiles saved to: {}',
        'converter_failed': 'Conversion failed: {}',
        'converter_done': 'Format conversion completed!\n{}',

        # PDF工具
        'feature_pdf_tool': 'PDF Tool',
        'pdf_import': 'File Import',
        'pdf_import_placeholder': 'Drag PDF files here, or click button to select',
        'pdf_import_tip': 'Supports PDF format files, multiple files can be imported',
        'pdf_browse': 'Browse...',
        'pdf_clear': 'Clear List',
        'pdf_operation_mode': 'Operation Mode',
        'pdf_merge': 'Merge PDF',
        'pdf_split': 'Split PDF',
        'pdf_compress': 'Compress PDF',
        'pdf_compress_settings': 'Compression Settings',
        'pdf_compress_quality': 'Quality:',
        'pdf_quality_high': 'High Quality',
        'pdf_quality_medium': 'Medium Quality',
        'pdf_quality_low': 'Low Quality',
        'pdf_file_list': 'File List',
        'pdf_file_count': '{} files total',
        'pdf_output_path': 'Output: {}',
        'pdf_clear': 'Clear List',
        'pdf_remove': 'Remove Selected',
        'pdf_start': 'Process',
        'pdf_files': 'PDF Files',
        'pdf_all_files': 'All Files',
        'pdf_select_file': 'Select PDF File',
        'pdf_need_pymupdf': 'PyMuPDF library required for PDF processing\nPlease run: pip install PyMuPDF',
        'pdf_no_files': 'Please add PDF files to process first',
        'pdf_no_save_path': 'Please configure global save path in settings first',
        'pdf_create_path_failed': 'Failed to create save directory: {}',
        'pdf_merge_done': 'PDF merge completed!\nFile saved to: {}',
        'pdf_merge_failed': 'PDF merge failed: {}',
        'pdf_split_done': 'PDF split completed!\nFiles saved to: {}',
        'pdf_split_failed': 'PDF split failed: {}',
        'pdf_compress_done': 'PDF compression completed!\nFiles saved to: {}',
        'pdf_compress_partial': 'PDF compression completed {} / {} files\nFiles saved to: {}',
        'pdf_compress_failed': 'PDF compression failed: {}',
    }
}


class I18n:
    """国际化管理类"""

    def __init__(self, lang='zh'):
        """初始化"""
        self.lang = lang
        self._texts = LANGUAGES.get(lang, LANGUAGES['zh'])

    def set_language(self, lang):
        """设置语言"""
        self.lang = lang
        self._texts = LANGUAGES.get(lang, LANGUAGES['zh'])

    def get(self, key, *args):
        """获取文本"""
        text = self._texts.get(key, key)
        if args:
            return text.format(*args)
        return text

    def __getitem__(self, key):
        """支持字典式访问"""
        return self._texts.get(key, key)

    def get_compress_levels(self):
        """获取压缩级别列表"""
        return [
            self.get('compress_level_fastest'),
            self.get('compress_level_fast'),
            self.get('compress_level_normal'),
            self.get('compress_level_slow'),
            self.get('compress_level_slowest')
        ]


# 全局实例（方便直接使用）
_i18n_instance = None


def get_i18n(lang='zh'):
    """获取国际化实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n(lang)
    return _i18n_instance


def set_language(lang):
    """设置全局语言"""
    global _i18n_instance
    if _i18n_instance:
        _i18n_instance.set_language(lang)
    else:
        _i18n_instance = I18n(lang)


def t(key, *args):
    """快捷翻译函数"""
    if _i18n_instance:
        return _i18n_instance.get(key, *args)
    return key