# -*- coding: utf-8 -*-
"""
DeskHelperGUI 设置对话框
用于修改全局保存路径
"""

import os
import platform

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t
from ui_components.animated_button import AnimatedButton


def get_desktop_path():
    """获取系统桌面路径"""
    import ctypes
    from ctypes import wintypes
    
    # Windows 系统使用 API 获取真实桌面路径
    if platform.system() == 'Windows':
        try:
            # 使用 SHGetFolderPath API 获取桌面路径
            # CSIDL_DESKTOP = 0x0000
            CSIDL_DESKTOP = 0
            SHGFP_TYPE_CURRENT = 0  # 获取当前路径，不是默认路径
            
            # 创建缓冲区
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            
            # 调用 SHGetFolderPathW
            ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf
            )
            
            path = buf.value
            if path and os.path.exists(path):
                return path
        except Exception:
            pass
        
        # 如果 API 失败，尝试备用方法
        home = os.path.expanduser('~')
        desktop_names = ['Desktop', '桌面']
        for name in desktop_names:
            path = os.path.join(home, name)
            if os.path.exists(path):
                return path
        return os.path.join(home, 'Desktop')
    else:
        # macOS 和 Linux
        home = os.path.expanduser('~')
        return os.path.join(home, 'Desktop')


class SettingsDialog(QDialog):
    """设置弹窗"""

    def __init__(self, lang='zh', config=None, parent=None, is_startup=False):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.is_startup = is_startup  # 是否为启动时弹出的配置对话框
        set_language(lang)
        self.setWindowTitle(t('settings_title'))
        # 移除右上角的问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(450, 200)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(25, 20, 25, 20)

        # 提示信息
        if self.is_startup:
            tip_label = QLabel(t('settings_no_path_tip'))
            tip_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #fa5252;
                    font-weight: 500;
                }
            """)
        else:
            tip_label = QLabel(t('settings_save_path_tip'))
            tip_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    color: #495057;
                }
            """)
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)

        # 保存路径输入区域
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)

        self.save_input = QLineEdit()
        self.save_input.setPlaceholderText(t('settings_save_placeholder'))
        self.save_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        # 加载当前保存路径（若为空则使用桌面路径作为默认值）
        if self.config:
            current_path = self.config.get_save_path()
            if current_path:
                self.save_input.setText(current_path)
            else:
                # 路径为空时，自动设置桌面路径作为默认值
                desktop_path = get_desktop_path()
                self.save_input.setText(desktop_path.replace('\\', '/'))
        else:
            # 无配置时，使用桌面路径作为默认值
            desktop_path = get_desktop_path()
            self.save_input.setText(desktop_path.replace('\\', '/'))
        path_layout.addWidget(self.save_input, 1)

        self.browse_btn = AnimatedButton(t('settings_browse'))
        self.browse_btn.setFixedSize(90, 36)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_save_path)
        path_layout.addWidget(self.browse_btn)

        layout.addLayout(path_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 保存按钮
        save_btn = AnimatedButton(t('settings_save'))
        save_btn.setFixedSize(100, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        # 如果不是启动时弹出，则显示关闭按钮
        if not self.is_startup:
            btn_layout.addSpacing(10)
            close_btn = AnimatedButton(t('settings_close'))
            close_btn.setFixedSize(100, 36)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e9ecef;
                    color: #495057;
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #dee2e6;
                }
            """)
            close_btn.clicked.connect(self.reject)
            btn_layout.addWidget(close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _browse_save_path(self):
        """浏览选择保存路径"""
        folder = QFileDialog.getExistingDirectory(
            self, t('settings_select_folder'), ""
        )
        if folder:
            # 统一使用 / 作为路径分隔符
            folder = folder.replace('\\', '/')
            self.save_input.setText(folder)

    def _save_settings(self):
        """保存设置"""
        save_path = self.save_input.text().strip()
        
        if not save_path:
            QMessageBox.warning(self, t('settings_warning'), t('settings_empty_path'))
            return
        
        if not os.path.isdir(save_path):
            QMessageBox.warning(self, t('settings_warning'), t('settings_invalid_path'))
            return
        
        # 保存到配置
        if self.config:
            self.config.set_save_path(save_path)
        
        self.accept()