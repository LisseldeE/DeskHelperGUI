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
        'about_version': '版本：R1',
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
        'extractor_no_folder': '请先选择文件夹',
        'extractor_no_files': '文件夹中没有找到文件',
        'extractor_save_path': '保存路径',
        'extractor_save_placeholder': '选择保存路径（留空则保存到源文件夹）',
        'extractor_select_folder': '选择目标文件夹',
        'extractor_select_save': '选择保存位置',
        'extractor_preview_btn': '预览文件',
        'extractor_export': '导出到Excel',
        'extractor_need_pandas': '需要安装 pandas 和 openpyxl 库才能导出Excel\n请运行: pip install pandas openpyxl',
        'extractor_export_failed': '导出失败：{}',
        'extractor_export_done': '导出完成！\n文件已保存至：{}',
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
        'about_version': 'Version: R1',
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
        'extractor_no_folder': 'Please select a folder first',
        'extractor_no_files': 'No files found in folder',
        'extractor_save_path': 'Save Path',
        'extractor_save_placeholder': 'Select save path (leave empty to save in source folder)',
        'extractor_select_folder': 'Select Target Folder',
        'extractor_select_save': 'Select Save Location',
        'extractor_preview_btn': 'Preview Files',
        'extractor_export': 'Export to Excel',
        'extractor_need_pandas': 'pandas and openpyxl required for Excel export\nPlease run: pip install pandas openpyxl',
        'extractor_export_failed': 'Export failed: {}',
        'extractor_export_done': 'Export completed!\nFile saved to: {}',
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