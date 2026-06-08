# -*- coding: utf-8 -*-
"""
DeskHelperGUI 快捷压缩功能模块
提供文件/文件夹压缩功能，支持ZIP、7z、TAR格式
"""

import os
import zipfile
import tarfile
import threading
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QMessageBox, QGroupBox,
    QAbstractItemView, QFrame, QSizePolicy, QScrollArea, QMenu,
    QGraphicsOpacityEffect, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QMetaObject, Q_ARG, QSize, QPropertyAnimation, QByteArray
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton

# 尝试导入py7zr（用于7z格式支持）
try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

# 尝试导入pyzipper（用于ZIP加密支持）
try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False



class FileListItemWidget(QFrame):
    """文件列表项widget，包含文件路径和删除按钮"""

    # 删除信号
    delete_requested = pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # 文件路径标签
        self.path_label = QLabel(self.file_path)
        self.path_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                background-color: transparent;
                padding: 0px 4px;
            }
        """)
        self.path_label.setToolTip(self.file_path)
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.path_label.setFixedHeight(24)
        layout.addWidget(self.path_label)

        # 删除按钮（红色×图标）
        self.delete_btn = AnimatedButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff6b6b;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #fff5f5;
                color: #fa5252;
            }
        """)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)
        self.setFixedHeight(28)

    def _on_delete_clicked(self):
        """删除按钮点击"""
        self.delete_requested.emit(self.file_path)


class QuickCompressWidget(QWidget):
    """快捷压缩功能界面"""

    # 压缩完成信号
    compress_finished = pyqtSignal(bool, str)  # (成功, 消息)
    # 解压完成信号（与压缩分开，便于显示不同提示）
    extract_finished = pyqtSignal(bool, str)   # (成功, 消息)
    # 请求密码信号（用于线程安全的密码对话框）
    password_requested = pyqtSignal()  # 请求显示密码对话框

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.file_list = []  # 待压缩文件列表
        self.is_compressing = False
        self.list_item_widgets = {}  # 存储列表项widget的字典 {path: widget}

        # 密码请求相关（线程安全）
        self._password_lock = threading.Lock()
        self._password_result = None
        self._password_archive_name = None  # 当前正在解压的压缩包名称
        self._password_event = threading.Event()

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        # 连接压缩/解压完成信号到UI重置方法
        self.compress_finished.connect(self.on_compress_finished)
        self.extract_finished.connect(self.on_compress_finished)
        # 连接密码请求信号到密码对话框处理方法
        self.password_requested.connect(self._show_password_dialog)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 文件列表区域
        self.file_group = QGroupBox(t('compress_title'))
        file_layout = QVBoxLayout()
        file_layout.setSpacing(8)
        file_layout.setContentsMargins(10, 15, 10, 15)

        # 提示标签
        self.tip_label = QLabel(t('compress_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        self.tip_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.tip_label)

        # 文件列表框（使用QScrollArea包裹，防止超出边框）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置滚动区域最小高度，防止窗口过小时完全消失
        self.scroll_area.setMinimumHeight(100)

        # 列表内容容器
        self.file_list_container = QWidget()
        self.file_list_container.setStyleSheet("background-color: transparent;")
        self.file_list_container.setCursor(Qt.PointingHandCursor)
        self.file_list_layout = QVBoxLayout()
        self.file_list_layout.setSpacing(1)
        self.file_list_layout.setContentsMargins(8, 8, 8, 8)
        self.file_list_layout.setAlignment(Qt.AlignTop)  # 确保项目从顶部开始排列
        self.file_list_container.setLayout(self.file_list_layout)
        self.scroll_area.setWidget(self.file_list_container)
        
        # 点击列表容器时打开文件选择对话框
        self.file_list_container.mousePressEvent = self._on_list_clicked
        
        file_layout.addWidget(self.scroll_area)

        # 滚动区域占据groupbox内的剩余空间

        # 清空列表按钮（水平居中）
        file_btn_layout = QHBoxLayout()
        file_btn_layout.addStretch()

        self.clear_btn = AnimatedButton(t('compress_clear'))
        self.clear_btn.setFixedSize(120, 36)  # 固定宽度和高度
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8787;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #fa5252;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_list)
        file_btn_layout.addWidget(self.clear_btn)

        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)

        self.file_group.setLayout(file_layout)
        layout.addWidget(self.file_group)

        # 压缩设置区域
        self.settings_group = QGroupBox(t('compress_settings'))
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(12, 16, 12, 12)  # 增加上下边距

        # 第一行：压缩包名称
        row0_layout = QHBoxLayout()

        self.name_label = QLabel(t('compress_name'))
        row0_layout.addWidget(self.name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t('compress_name_placeholder'))
        self.name_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row0_layout.addWidget(self.name_input)

        row0_layout.addStretch()
        settings_layout.addLayout(row0_layout)

        # 第二行：格式和级别
        row1_layout = QHBoxLayout()

        # 压缩格式
        self.format_label = QLabel(t('compress_format'))
        row1_layout.addWidget(self.format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(['ZIP', '7z', 'TAR'])
        self.format_combo.setMinimumWidth(100)
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 6px 10px;
                padding-right: 30px;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 1px solid #339af0;
                background-color: #e7f5ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                width: 8px;
                height: 8px;
                border-radius: 4px;
                background-color: #495057;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                border-radius: 4px;
                color: #495057;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e7f5ff;
                color: #339af0;
            }
            QComboBox QAbstractItemView::item:hover:!selected {
                background-color: #f1f3f5;
            }
            QComboBox QAbstractItemView::item:disabled {
                color: #adb5bd;
            }
        """)
        if not HAS_PY7ZR:
            # 如果没有安装py7zr，禁用7z选项
            self.format_combo.model().item(1).setEnabled(False)
            self.format_combo.model().item(1).setToolTip(t('msg_need_py7zr'))
        row1_layout.addWidget(self.format_combo)

        row1_layout.addSpacing(30)

        # 压缩级别
        self.level_label = QLabel(t('compress_level'))
        row1_layout.addWidget(self.level_label)

        self.level_combo = QComboBox()
        self.level_combo.setMinimumWidth(100)
        self.level_combo.setStyleSheet(self.format_combo.styleSheet())
        for level_text in get_i18n().get_compress_levels():
            self.level_combo.addItem(level_text)
        self.level_combo.setCurrentIndex(2)  # 默认选择"标准"
        row1_layout.addWidget(self.level_combo)

        row1_layout.addStretch()
        settings_layout.addLayout(row1_layout)

        # 第三行：加密设置
        row2_layout = QHBoxLayout()
        row2_layout.setAlignment(Qt.AlignVCenter)  # 设置垂直居中对齐

        # 加密模式切换按钮
        self.encrypt_mode = False  # 默认无密码
        self.encrypt_btn = AnimatedButton(t('compress_no_password'))
        self.encrypt_btn.setFixedSize(120, 36)
        self.encrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.encrypt_btn.clicked.connect(self._toggle_encrypt_mode)
        row2_layout.addWidget(self.encrypt_btn, 0, Qt.AlignVCenter)

        # 密码输入区域
        self.password_widget = QWidget()
        self.password_widget.setStyleSheet("background-color: transparent;")
        password_layout = QHBoxLayout()
        password_layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        password_layout.setSpacing(10)
        password_layout.setAlignment(Qt.AlignVCenter)

        self.password_label = QLabel(t('compress_password'))
        password_layout.addWidget(self.password_label, 0, Qt.AlignVCenter)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(t('compress_password_placeholder'))
        self.password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_input.setFixedHeight(36)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #4dabf7;
            }
        """)
        password_layout.addWidget(self.password_input, 0, Qt.AlignVCenter)

        # 显示密码复选框
        self.show_pwd_check = QCheckBox(t('compress_show_password'))
        self.show_pwd_check.stateChanged.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.show_pwd_check, 0, Qt.AlignVCenter)

        self.password_widget.setLayout(password_layout)
        self.password_widget.setFixedHeight(36)  # 与输入框高度一致
        # 初始隐藏密码控件
        self.password_widget.setVisible(False)
        row2_layout.addWidget(self.password_widget, 0, Qt.AlignVCenter)

        row2_layout.addStretch()
        settings_layout.addLayout(row2_layout)

        # 第四行：保存路径
        row3_layout = QHBoxLayout()
        row3_layout.setAlignment(Qt.AlignVCenter)  # 设置垂直居中对齐

        self.save_label = QLabel(t('compress_save_path'))
        row3_layout.addWidget(self.save_label, 0, Qt.AlignVCenter)

        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText(t('compress_save_placeholder'))
        self.save_path_input.setReadOnly(True)
        self.save_path_input.setFixedHeight(36)  # 固定高度
        row3_layout.addWidget(self.save_path_input, 0, Qt.AlignVCenter)

        self.browse_btn = AnimatedButton(t('compress_browse'))
        self.browse_btn.setFixedHeight(36)  # 与输入框高度一致，防止中文显示不全
        self.browse_btn.clicked.connect(self._browse_save_path)
        row3_layout.addWidget(self.browse_btn, 0, Qt.AlignVCenter)

        settings_layout.addLayout(row3_layout)

        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)
        # 文件列表区域占据剩余空间弹性，设置区域占自然高度
        layout.setStretchFactor(self.file_group, 1)
        layout.setStretchFactor(self.settings_group, 0)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                background-color: #f1f3f5;
                font-size: 12px;
                color: #495057;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #339af0, stop: 1 #4dabf7
                );
                border-radius: 5px;
            }
        """)
        # 进度条外包装（加上下边距）
        progress_wrapper = QHBoxLayout()
        progress_wrapper.setContentsMargins(0, 4, 0, 4)
        progress_wrapper.addWidget(self.progress_bar)
        layout.addLayout(progress_wrapper)

        # 操作按钮区域（压缩 + 解压）
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 压缩按钮
        self.compress_btn = AnimatedButton(t('compress_start'))
        self.compress_btn.setMinimumWidth(150)
        self.compress_btn.setMinimumHeight(40)
        self.compress_btn.setEnabled(False)  # 默认不可点击
        self.compress_btn.setStyleSheet("""
            QPushButton {
                background-color: #adb5bd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #868e96;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #868e96;
            }
        """)
        self.compress_btn.clicked.connect(self._start_compress)
        btn_layout.addWidget(self.compress_btn)

        # 解压按钮
        self.extract_btn = AnimatedButton(t('extract_start'))
        self.extract_btn.setMinimumWidth(150)
        self.extract_btn.setMinimumHeight(40)
        self.extract_btn.setEnabled(False)  # 默认不可点击
        self.extract_btn.setVisible(False)  # 默认隐藏
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #adb5bd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #868e96;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #868e96;
            }
        """)
        self.extract_btn.clicked.connect(self._start_extract)
        btn_layout.addWidget(self.extract_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        self.setLayout(layout)

    def _load_config(self):
        """从配置加载设置"""
        if self.config:
            # 加载保存路径
            save_path = self.config.get_save_path()
            if save_path and os.path.exists(save_path):
                self.save_path_input.setText(save_path)

            # 加载压缩设置
            compress_settings = self.config.get_compress_settings()
            if compress_settings:
                # 设置压缩格式
                format_type = compress_settings.get('format', 'ZIP')
                index = self.format_combo.findText(format_type)
                if index >= 0:
                    self.format_combo.setCurrentIndex(index)

                # 设置压缩级别
                level = compress_settings.get('level', 2)
                if 0 <= level < self.level_combo.count():
                    self.level_combo.setCurrentIndex(level)

                # 设置加密状态
                encrypt = compress_settings.get('encrypt', False)
                if encrypt:
                    self.encrypt_mode = True
                    self.encrypt_btn.setText(t('compress_encrypt'))
                    self.encrypt_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #339af0;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 0px;
                            font-size: 13px;
                            font-weight: 500;
                        }
                        QPushButton:hover {
                            background-color: #228be6;
                        }
                    """)
                    self._set_password_controls_visible(True)

    def _save_config(self):
        """保存设置到配置"""
        if self.config:
            # 保存保存路径
            save_path = self.save_path_input.text()
            if save_path:
                self.config.set_save_path(save_path)

            # 保存压缩设置（不覆盖save_path）
            self.config.set('compress.format', self.format_combo.currentText())
            self.config.set('compress.level', self.level_combo.currentIndex())
            self.config.set('compress.encrypt', self.encrypt_mode)
            self.config.save_config()

    def _update_compress_btn_state(self):
        """更新压缩按钮和解压按钮状态"""
        # 检查是否有文件和保存路径
        has_files = len(self.file_list) > 0
        has_save_path = bool(self.save_path_input.text())

        # 检查是否只有压缩文件
        only_compress_files = self._check_only_compress_files()

        # 更新压缩按钮状态
        if has_files and has_save_path:
            self.compress_btn.setEnabled(True)
            self.compress_btn.setStyleSheet("""
                QPushButton {
                    background-color: #51cf66;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #40c057;
                }
                QPushButton:pressed {
                    background-color: #37b24d;
                }
            """)
        else:
            self.compress_btn.setEnabled(False)
            self.compress_btn.setStyleSheet("""
                QPushButton {
                    background-color: #adb5bd;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #868e96;
                }
                QPushButton:pressed {
                    background-color: #495057;
                }
                QPushButton:disabled {
                    background-color: #adb5bd;
                    color: #868e96;
                }
            """)

        # 更新解压按钮状态（带渐入渐出动画）
        if only_compress_files and has_save_path:
            # 设置解压按钮样式和启用状态
            self.extract_btn.setEnabled(True)
            self.extract_btn.setStyleSheet("""
                QPushButton {
                    background-color: #51cf66;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #40c057;
                }
                QPushButton:pressed {
                    background-color: #37b24d;
                }
            """)
            # 如果按钮不可见，淡入显示
            if not self.extract_btn.isVisible():
                self._fade_widget(self.extract_btn, True, duration=200)
        else:
            # 淡出隐藏解压按钮
            if self.extract_btn.isVisible():
                self._fade_widget(self.extract_btn, False, duration=200)
            self.extract_btn.setEnabled(False)

    def _check_only_compress_files(self):
        """检查文件列表是否只包含压缩文件（ZIP、7z、TAR）"""
        if len(self.file_list) == 0:
            return False

        compress_extensions = ['.zip', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.bz2']
        for file_path in self.file_list:
            ext = os.path.splitext(file_path)[1].lower()
            # 处理 .tar.gz 等双扩展名
            if ext == '.gz' and file_path.lower().endswith('.tar.gz'):
                ext = '.tar.gz'
            elif ext == '.bz2' and file_path.lower().endswith('.tar.bz2'):
                ext = '.tar.bz2'
            if ext not in compress_extensions:
                return False
        return True

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)

        # 更新所有文本
        self.file_group.setTitle(t('compress_title'))
        self.tip_label.setText(t('compress_tip'))
        self.clear_btn.setText(t('compress_clear'))

        self.settings_group.setTitle(t('compress_settings'))
        self.name_label.setText(t('compress_name'))
        self.name_input.setPlaceholderText(t('compress_name_placeholder'))
        self.format_label.setText(t('compress_format'))
        self.level_label.setText(t('compress_level'))

        # 更新压缩级别选项
        current_level = self.level_combo.currentIndex()
        self.level_combo.clear()
        for level_text in get_i18n().get_compress_levels():
            self.level_combo.addItem(level_text)
        self.level_combo.setCurrentIndex(current_level)

        self.encrypt_btn.setText(t('compress_no_password') if not self.encrypt_mode else t('compress_encrypt'))
        self.password_label.setText(t('compress_password'))
        self.password_input.setPlaceholderText(t('compress_password_placeholder'))
        self.show_pwd_check.setText(t('compress_show_password'))
        self.save_label.setText(t('compress_save_path'))
        self.save_path_input.setPlaceholderText(t('compress_save_placeholder'))
        self.browse_btn.setText(t('compress_browse'))
        self.compress_btn.setText(t('compress_start'))
        self.extract_btn.setText(t('extract_start'))

        # 更新7z提示
        if not HAS_PY7ZR:
            self.format_combo.setToolTip(t('msg_need_py7zr'))
        else:
            self.format_combo.setToolTip('')

    def _fade_widget(self, widget, visible, duration=150):
        """
        控件淡入淡出动画（正确管理动画生命周期）
        Args:
            widget: 要动画的控件
            visible: True 显示（淡入），False 隐藏（淡出）
            duration: 动画持续时间（毫秒）
        """
        if not hasattr(self, '_fade_animations'):
            self._fade_animations = {}  # 改用字典存储 {widget: animation}

        # 停止并清理该widget的旧动画
        old_animation = self._fade_animations.get(widget)
        if old_animation:
            old_animation.stop()
            old_animation.deleteLater()
            self._fade_animations.pop(widget, None)

        # 获取或创建透明度效果
        effect = widget.graphicsEffect()
        if not effect or not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        # 创建动画
        animation = QPropertyAnimation(effect, QByteArray(b"opacity"))
        animation.setDuration(duration)
        self._fade_animations[widget] = animation

        if visible:
            widget.setVisible(True)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
        else:
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            # 使用 functools.partial 避免 lambda 内存问题
            from functools import partial
            animation.finished.connect(partial(self._on_fade_finished, widget))

        animation.start()

    def _on_fade_finished(self, widget):
        """淡出动画完成回调"""
        widget.setVisible(False)
        # 清理动画引用
        if hasattr(self, '_fade_animations'):
            animation = self._fade_animations.pop(widget, None)
            if animation:
                animation.deleteLater()

    def _set_password_controls_visible(self, visible):
        """设置密码输入区域的可见性（带渐入渐出动画）"""
        self._fade_widget(self.password_widget, visible, duration=200)

    def _toggle_encrypt_mode(self):
        """切换加密模式"""
        self.encrypt_mode = not self.encrypt_mode
        
        if self.encrypt_mode:
            # 切换到加密模式
            self.encrypt_btn.setText(t('compress_encrypt'))
            self.encrypt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #339af0;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #228be6;
                }
            """)
            # 显示密码输入区域内部控件
            self._set_password_controls_visible(True)
        else:
            # 切换到无密码模式
            self.encrypt_btn.setText(t('compress_no_password'))
            self.encrypt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e9ecef;
                    color: #495057;
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    padding: 0px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #dee2e6;
                }
            """)
            # 隐藏密码输入区域内部控件
            self._set_password_controls_visible(False)
            # 清空密码
            self.password_input.clear()
            self.show_pwd_check.setChecked(False)

    def _toggle_password_visibility(self, state):
        """切换密码可见性"""
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def _add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            t('compress_select_files'),
            "",
            t('compress_all_files')
        )
        for file in files:
            self._add_to_list(file)

    def _add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            t('compress_select_folder')
        )
        if folder:
            self._add_to_list(folder)

    def _on_list_clicked(self, event):
        """点击列表容器时显示选择菜单"""
        # 创建弹出菜单
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
            }
        """)
        
        # 添加菜单项
        add_files_action = menu.addAction(t('compress_add_file'))
        add_folder_action = menu.addAction(t('compress_add_folder'))
        
        # 显示菜单并获取用户选择
        action = menu.exec_(self.file_list_container.mapToGlobal(event.pos()))
        
        if action == add_files_action:
            # 添加文件
            self._add_files()
        elif action == add_folder_action:
            # 添加文件夹
            self._add_folder()

    def _add_to_list(self, path):
        """添加路径到列表"""
        if path and path not in self.file_list:
            self.file_list.append(path)

            # 创建列表项widget
            item_widget = FileListItemWidget(path)
            item_widget.delete_requested.connect(self._remove_item_by_path)

            # 直接追加到列表末尾，靠AlignTop确保从顶部开始排列
            self.file_list_layout.addWidget(item_widget)

            # 存储引用
            self.list_item_widgets[path] = item_widget

            # 更新压缩按钮状态
            self._update_compress_btn_state()

    def _remove_item_by_path(self, path):
        """根据路径删除列表项"""
        if path in self.list_item_widgets:
            widget = self.list_item_widgets[path]

            # 移除widget
            self.file_list_layout.removeWidget(widget)
            widget.deleteLater()
            self.list_item_widgets.pop(path)

            # 从文件列表中移除
            if path in self.file_list:
                self.file_list.remove(path)

            # 更新压缩按钮状态
            self._update_compress_btn_state()

    def _clear_list(self):
        """清空列表"""
        self.file_list.clear()

        # 清空所有widget
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.list_item_widgets.clear()

        # 更新压缩按钮状态
        self._update_compress_btn_state()

    def _browse_save_path(self):
        """浏览保存路径"""
        folder = QFileDialog.getExistingDirectory(
            self,
            t('compress_select_save')
        )
        if folder:
            self.save_path_input.setText(folder)
            # 立即保存到配置
            self._save_config()
            # 更新压缩按钮状态
            self._update_compress_btn_state()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        event.accept()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if os.path.exists(path):
                self._add_to_list(path)
        event.accept()

    def _start_compress(self):
        """开始压缩"""
        # 验证输入
        if not self.file_list:
            QMessageBox.warning(self, t('msg_warning'), t('msg_add_files'))
            return

        save_path = self.save_path_input.text()
        if not save_path:
            QMessageBox.warning(self, t('msg_warning'), t('msg_select_path'))
            return

        if self.encrypt_mode and not self.password_input.text():
            QMessageBox.warning(self, t('msg_warning'), t('msg_enter_password'))
            return

        # 检查格式依赖
        format_type = self.format_combo.currentText()
        if format_type == '7z' and not HAS_PY7ZR:
            QMessageBox.warning(self, t('msg_warning'), t('msg_need_py7zr'))
            return
        # 保存配置
        self._save_config()

        # 禁用按钮，显示进度条
        self.is_compressing = True
        self.compress_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._fade_widget(self.progress_bar, True, duration=200)

        # 在启动线程前获取所有数据（避免在子线程中访问UI组件）
        format_type = self.format_combo.currentText()
        level_index = self.level_combo.currentIndex()
        password = self.password_input.text() if self.encrypt_mode else None
        save_path = self.save_path_input.text()
        custom_name = self.name_input.text().strip()
        file_list = self.file_list.copy()  # 复制文件列表

        # 在新线程中执行压缩
        thread = threading.Thread(
            target=self._compress_thread,
            args=(format_type, level_index, password, save_path, custom_name, file_list)
        )
        thread.daemon = True
        thread.start()

    def _compress_thread(self, format_type, level_index, password, save_path, custom_name, file_list):
        """压缩线程"""
        output_path = None
        try:
            # 生成输出文件名
            output_name = self._generate_output_name(format_type, custom_name)
            output_path = os.path.join(save_path, output_name)

            # 根据格式选择压缩方法
            if format_type == 'ZIP':
                self._compress_zip(output_path, level_index, password, file_list)
            elif format_type == '7z':
                self._compress_7z(output_path, level_index, password, file_list)
            elif format_type == 'TAR':
                self._compress_tar(output_path, file_list)

            # 验证输出文件
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception(f"压缩失败：输出文件为空或不存在\n路径：{output_path}")

            # 压缩完成
            self.compress_finished.emit(True, output_path)

        except Exception as e:
            # 压缩失败时清理残留的0KB文件
            self._cleanup_output_file(output_path)
            self.compress_finished.emit(False, str(e))

    def _generate_output_name(self, format_type, custom_name=None):
        """生成输出文件名"""
        from datetime import datetime
        
        # 确定扩展名
        ext_map = {'ZIP': '.zip', '7z': '.7z', 'TAR': '.tar'}
        ext = ext_map.get(format_type, '.zip')
        
        # 如果用户输入了名称，使用自定义名称
        if custom_name:
            # 确保名称不以扩展名结尾
            if custom_name.endswith(ext):
                return custom_name
            else:
                return f"{custom_name}{ext}"
        
        # 否则使用默认名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"archive_{timestamp}{ext}"

    def _compress_zip(self, output_path, level_index, password, file_list):
        """ZIP格式压缩"""
        # ZIP压缩级别映射 (0-9)
        level_map = {0: 1, 1: 3, 2: 6, 3: 8, 4: 9}
        compress_level = level_map.get(level_index, 6)

        total_files = sum(len(self._get_all_files(path)) for path in file_list)
        if total_files == 0:
            raise Exception("没有找到可压缩的文件")
        
        processed = 0

        # 如果需要加密，检查是否有pyzipper
        if password:
            if not HAS_PYZIPPER:
                raise Exception("需要安装 pyzipper 库才能加密ZIP文件\n请运行: pip install pyzipper\n或使用7z格式进行加密压缩")
            
            # 使用pyzipper进行AES加密压缩
            with pyzipper.AESZipFile(output_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(password.encode('utf-8'))
                for source_path in file_list:
                    is_file = os.path.isfile(source_path)
                    files = self._get_all_files(source_path)
                    
                    for file_path in files:
                        # 计算归档名称
                        if is_file:
                            # 单个文件，使用文件名
                            arcname = os.path.basename(file_path)
                        else:
                            # 目录，保留相对路径结构
                            arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                        
                        zf.write(file_path, arcname)
                        processed += 1
                        progress = int(processed / total_files * 100)
                        self._update_progress(progress)
        else:
            # 无密码，使用标准zipfile
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compress_level) as zf:
                for source_path in file_list:
                    is_file = os.path.isfile(source_path)
                    files = self._get_all_files(source_path)
                    
                    for file_path in files:
                        # 计算归档名称
                        if is_file:
                            # 单个文件，使用文件名
                            arcname = os.path.basename(file_path)
                        else:
                            # 目录，保留相对路径结构
                            arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                        
                        zf.write(file_path, arcname)
                        processed += 1
                        progress = int(processed / total_files * 100)
                        self._update_progress(progress)

    def _compress_7z(self, output_path, level_index, password, file_list):
        """7z格式压缩"""
        if not HAS_PY7ZR:
            raise Exception("py7zr library not installed")

        # 7z压缩级别映射
        level_map = {0: 1, 1: 3, 2: 5, 3: 7, 4: 9}
        compress_level = level_map.get(level_index, 5)

        total_files = sum(len(self._get_all_files(path)) for path in file_list)
        processed = 0

        with py7zr.SevenZipFile(output_path, 'w', password=password) as archive:
            for source_path in file_list:
                if os.path.isfile(source_path):
                    archive.write(source_path, os.path.basename(source_path))
                    processed += 1
                else:
                    archive.writeall(source_path, os.path.basename(source_path))
                    processed += len(self._get_all_files(source_path))
                if total_files > 0:
                    self._update_progress(int(processed / total_files * 100))

        self._update_progress(100)

    def _compress_tar(self, output_path, file_list):
        """TAR格式压缩"""
        total_files = sum(len(self._get_all_files(path)) for path in file_list)
        processed = 0

        with tarfile.open(output_path, 'w') as tf:
            for source_path in file_list:
                if os.path.isfile(source_path):
                    tf.add(source_path, os.path.basename(source_path))
                    processed += 1
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                            tf.add(file_path, arcname)
                            processed += 1
                            progress = int(processed / total_files * 100) if total_files > 0 else 100
                            self._update_progress(progress)

        self._update_progress(100)

    def _get_all_files(self, path):
        """获取路径下所有文件"""
        files = []
        if os.path.isfile(path):
            files.append(path)
        else:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        return files

    def _cleanup_output_file(self, output_path):
        """清理失败的输出文件"""
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

    def _update_progress(self, value):
        """更新进度条"""
        QMetaObject.invokeMethod(self.progress_bar, "setValue", Qt.QueuedConnection, Q_ARG(int, value))

    def on_compress_finished(self, success, message):
        """压缩/解压完成回调"""
        self.is_compressing = False
        self.compress_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新解压按钮状态
        self._update_compress_btn_state()

        if success:
            self._clear_list()

    def _start_extract(self):
        """开始解压"""
        # 验证输入
        if not self.file_list:
            QMessageBox.warning(self, t('msg_warning'), t('msg_add_files'))
            return

        save_path = self.save_path_input.text()
        if not save_path:
            QMessageBox.warning(self, t('msg_warning'), t('msg_select_path'))
            return

        # 禁用按钮，显示进度条
        self.is_compressing = True
        self.compress_btn.setEnabled(False)
        self.extract_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._fade_widget(self.progress_bar, True, duration=200)

        # 复制文件列表
        file_list = self.file_list.copy()

        # 在新线程中执行解压
        thread = threading.Thread(
            target=self._extract_thread,
            args=(file_list, save_path)
        )
        thread.daemon = True
        thread.start()

    def _extract_thread(self, file_list, save_path):
        """解压线程"""
        try:
            for archive_path in file_list:
                # 规范化路径
                archive_path = os.path.normpath(archive_path)
                save_path = os.path.normpath(save_path)
                
                # 获取压缩包名称（用于密码对话框显示）
                archive_name = os.path.basename(archive_path)
                
                ext = os.path.splitext(archive_path)[1].lower()
                # 处理双扩展名
                if archive_path.lower().endswith('.tar.gz'):
                    ext = '.tar.gz'
                elif archive_path.lower().endswith('.tar.bz2'):
                    ext = '.tar.bz2'

                # 直接解压到保存路径，不创建额外文件夹
                # 这样压缩包内的结构会保持不变
                output_dir = save_path

                # 根据格式解压（密码需求在解压方法内部处理）
                if ext == '.zip':
                    self._extract_zip(archive_path, output_dir)
                elif ext == '.7z':
                    self._extract_7z(archive_path, output_dir)
                elif ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                    self._extract_tar(archive_path, output_dir)

                self._update_progress(100)

            # 解压完成
            self.extract_finished.emit(True, save_path)

        except Exception as e:
            self.extract_finished.emit(False, str(e))

    def _request_password(self, archive_name=None):
        """请求密码（线程安全，通过信号在主线程显示对话框）
        
        Args:
            archive_name: 当前正在解压的压缩包名称，用于在对话框中显示
        """
        with self._password_lock:
            # 重置密码结果和事件
            self._password_result = None
            self._password_archive_name = archive_name
            self._password_event.clear()

            # 发送信号请求显示密码对话框（在主线程中执行）
            self.password_requested.emit()

            # 等待密码输入完成（最多等待60秒）
            if self._password_event.wait(timeout=60):
                if self._password_result is not None:
                    return self._password_result
                else:
                    raise Exception(t('extract_need_password'))
            else:
                raise Exception(t('extract_need_password'))

    def _show_password_dialog(self):
        """在主线程中显示密码对话框"""
        from PyQt5.QtWidgets import QDialog
        
        dialog = PasswordDialog(self, archive_name=self._password_archive_name)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self._password_result = dialog.get_password()
        else:
            self._password_result = None
        
        # 设置事件，通知等待线程
        self._password_event.set()

    def _extract_zip(self, archive_path, output_dir):
        """解压ZIP文件（密码对话框只在需要时弹出一次）"""
        os.makedirs(output_dir, exist_ok=True)

        password = None
        first_try = True

        while True:
            try:
                if password:
                    if not HAS_PYZIPPER:
                        raise Exception("需要安装 pyzipper 库才能解压加密ZIP文件\n请运行: pip install pyzipper")
                    with pyzipper.AESZipFile(archive_path, 'r') as zf:
                        zf.setpassword(password.encode('utf-8'))
                        self._extract_and_fix_filenames(zf, output_dir)
                else:
                    with zipfile.ZipFile(archive_path, 'r') as zf:
                        self._extract_and_fix_filenames(zf, output_dir)
                return  # 解压成功，退出循环
            except RuntimeError as e:
                err_str = str(e).lower()
                if 'password' in err_str or 'decrypt' in err_str or 'bad password' in err_str:
                    if first_try:
                        archive_name = os.path.basename(archive_path)
                        password = self._request_password(archive_name)
                        first_try = False
                        continue  # 用获取的密码重试一次
                    raise Exception(t('extract_wrong_password'))
                raise

    def _extract_and_fix_filenames(self, zf, output_dir):
        """解压ZIP并修复文件名编码"""
        # 先全部解压
        zf.extractall(output_dir)
        
        # 遍历解压后的文件，修复乱码文件名
        self._fix_extracted_filenames(output_dir)

    def _fix_extracted_filenames(self, directory):
        """递归修复目录中的乱码文件名"""
        import shutil
        
        # 收集需要重命名的项
        rename_list = []
        
        for root, dirs, files in os.walk(directory):
            for name in dirs + files:
                original_path = os.path.join(root, name)
                
                # 尝试修复文件名编码
                fixed_name = self._try_fix_encoding(name)
                
                if fixed_name != name:
                    fixed_path = os.path.join(root, fixed_name)
                    rename_list.append((original_path, fixed_path))
        
        # 执行重命名（从最深路径开始，避免父目录先被重命名）
        rename_list.sort(key=lambda x: x[0], reverse=True)
        
        for original_path, fixed_path in rename_list:
            if os.path.exists(original_path):
                # 确保目标目录存在
                os.makedirs(os.path.dirname(fixed_path), exist_ok=True)
                # 重命名
                if os.path.exists(fixed_path):
                    # 如果目标已存在，先删除
                    if os.path.isfile(fixed_path):
                        os.remove(fixed_path)
                    else:
                        shutil.rmtree(fixed_path)
                os.rename(original_path, fixed_path)

    @staticmethod
    def _try_fix_encoding(name):
        """尝试多种编码组合修复乱码文件名"""
        # 如果文件名已经是有效的UTF-8中文，不必修复
        import unicodedata
        has_cjk = any(
            '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf'
            for c in name
        )
        if has_cjk:
            return name
        
        # 如果全是ASCII，不必修复
        if all(ord(c) < 128 for c in name):
            return name
        
        # 按优先级尝试编码组合
        # 常见乱码来源：ZIP中文件名以CP437存储，但实际上是GBK/UTF-8/Big5编码
        encoding_pairs = [
            ('cp437', 'gbk'),      # GBK中文（最常见）
            ('cp437', 'utf-8'),    # UTF-8中文
            ('cp437', 'big5'),     # 繁体中文
            ('cp437', 'shift_jis'),# 日文
            ('cp437', 'cp949'),    # 韩文
            ('utf-8', 'gbk'),      # UTF-8读了当作GBK
            ('utf-8', 'big5'),     # UTF-8读了当作Big5
            ('latin-1', 'gbk'),    # Latin-1读了当作GBK
            ('latin-1', 'utf-8'),  # Latin-1读了当作UTF-8
        ]
        
        for src_enc, dst_enc in encoding_pairs:
            try:
                fixed = name.encode(src_enc).decode(dst_enc)
                # 验证修复结果是否合理（包含有效中文或字母数字）
                if any('\u4e00' <= c <= '\u9fff' for c in fixed) or \
                   any(c.isalnum() for c in fixed):
                    return fixed
            except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
                continue
        
        # 尝试单个编码方案：zigzag - 可能是正确的编码但没有中间转换
        for enc in ['gbk', 'big5', 'shift_jis', 'utf-8']:
            try:
                # 尝试用该编码重新解码原始字节
                raw = name.encode('latin-1', errors='replace')
                fixed = raw.decode(enc, errors='replace')
                if any('\u4e00' <= c <= '\u9fff' for c in fixed) or \
                   any(c.isalnum() for c in fixed):
                    return fixed
            except Exception:
                continue
        
        return name  # 所有尝试都失败，保持原样

    def _extract_7z(self, archive_path, output_dir):
        """解压7z文件（密码对话框只在需要时弹出一次）"""
        if not HAS_PY7ZR:
            raise Exception("需要安装 py7zr 库才能解压7z文件\n请运行: pip install py7zr")
        
        os.makedirs(output_dir, exist_ok=True)
        
        password = None
        first_try = True
        
        while True:
            try:
                with py7zr.SevenZipFile(archive_path, 'r', password=password) as archive:
                    archive.extractall(output_dir)
                return  # 解压成功
            except py7zr.exceptions.PasswordRequired:
                if first_try:
                    archive_name = os.path.basename(archive_path)
                    password = self._request_password(archive_name)
                    first_try = False
                    continue  # 用获取的密码重试一次
                raise Exception(t('extract_wrong_password'))
            except Exception as e:
                if 'password' in str(e).lower() or 'decrypt' in str(e).lower():
                    raise Exception(t('extract_wrong_password'))
                raise

    def _extract_tar(self, archive_path, output_dir):
        """解压TAR文件"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 规范化路径
        archive_path = os.path.normpath(archive_path)
        output_dir = os.path.normpath(output_dir)
        
        # 确定压缩模式
        if archive_path.lower().endswith('.tar.gz') or archive_path.lower().endswith('.tgz'):
            mode = 'r:gz'
        elif archive_path.lower().endswith('.tar.bz2'):
            mode = 'r:bz2'
        else:
            mode = 'r'
        
        with tarfile.open(archive_path, mode) as tf:
            tf.extractall(output_dir)


class PasswordDialog(QDialog):
    """密码输入对话框"""

    def __init__(self, parent=None, archive_name=None):
        super().__init__(parent)
        self.archive_name = archive_name
        self.setWindowTitle(t('extract_password_title'))
        # 根据是否有文件名调整对话框高度
        if archive_name:
            self.setFixedSize(350, 210)
        else:
            self.setFixedSize(300, 170)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel(t('extract_password_title'))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
            }
        """)
        layout.addWidget(title_label)

        # 文件名提示（如果有）
        if self.archive_name:
            archive_label = QLabel(f"文件：{self.archive_name}")
            archive_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #868e96;
                    padding: 4px 0;
                }
            """)
            layout.addWidget(archive_label)

        # 密码输入框
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(t('extract_password_placeholder'))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #4dabf7;
            }
        """)
        self.password_input.textChanged.connect(self._on_password_changed)
        layout.addWidget(self.password_input)

        # 确认按钮（默认禁用，输入密码后才可点击）
        self.confirm_btn = AnimatedButton(t('extract_confirm'))
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #adb5bd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #868e96;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #dee2e6;
                color: #adb5bd;
            }
        """)
        self.confirm_btn.clicked.connect(self.accept)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)

    def _on_password_changed(self, text):
        """密码框内容变化时更新确认按钮状态"""
        has_text = bool(text.strip())
        self.confirm_btn.setEnabled(has_text)
        if has_text:
            self.confirm_btn.setStyleSheet("""
                QPushButton {
                    background-color: #51cf66;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #40c057;
                }
                QPushButton:pressed {
                    background-color: #37b24d;
                }
                QPushButton:disabled {
                    background-color: #dee2e6;
                    color: #adb5bd;
                }
            """)
        else:
            self.confirm_btn.setStyleSheet("""
                QPushButton {
                    background-color: #adb5bd;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #868e96;
                }
                QPushButton:pressed {
                    background-color: #495057;
                }
                QPushButton:disabled {
                    background-color: #dee2e6;
                    color: #adb5bd;
                }
            """)

    def get_password(self):
        """获取输入的密码"""
        return self.password_input.text()