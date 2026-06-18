# -*- coding: utf-8 -*-
"""
DeskHelperGUI 文件处理功能模块
包含文件名提取、批量重命名、批量创建功能
"""

import os
import re
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QGroupBox, QComboBox, QCheckBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame, QSpinBox,
    QListWidget, QMessageBox, QFileDialog, QSplitter, QListWidgetItem,
    QAbstractItemView, QSizePolicy, QStackedWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDrag, QColor, QFont

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton
from .utils import get_unique_filepath

# pandas延迟导入（优化启动速度）
HAS_PANDAS = None


class FileProcessorWidget(QWidget):
    """文件处理功能界面"""

    # 信号
    warning_requested = pyqtSignal(str)
    success_requested = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    # 模式定义
    MODES = ['extract', 'rename', 'create']

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.current_mode = 'extract'
        self.is_processing = False
        
        # 文件名提取模式数据
        self.extract_folder = ""
        self.extract_files = []
        
        # 批量重命名模式数据
        self.rename_folder = ""
        self.rename_files = []  # [(原名, 新名)]
        self.rename_rule = 'prefix'  # prefix/suffix/number/replace/regex
        
        # 批量创建模式数据
        self.create_excel_path = ""
        self.create_folder = ""
        self.create_files = []  # 文件名列表
        self.create_mode = 'folder'  # folder/file
        self.create_ext = '.txt'
        self.skip_existing = False

        set_language(lang)
        self._init_ui()
        self._load_config()
        self.progress_updated.connect(self._set_progress)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部导航栏
        self._create_nav_bar(main_layout)

        # 主内容区域（使用StackedWidget切换不同模式）
        self.content_stack = QStackedWidget()

        # 文件名提取界面
        extract_widget = self._create_extract_panel()
        self.content_stack.addWidget(extract_widget)

        # 批量重命名界面
        rename_widget = self._create_rename_panel()
        self.content_stack.addWidget(rename_widget)

        # 批量创建界面
        create_widget = self._create_create_panel()
        self.content_stack.addWidget(create_widget)

        main_layout.addWidget(self.content_stack, 1)

        # 底部操作区域
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_nav_bar(self, parent_layout):
        """创建顶部导航栏"""
        nav_frame = QFrame()
        nav_frame.setFixedHeight(50)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(8)

        # 模式按钮
        self.mode_buttons = {}
        mode_labels = {
            'extract': t('fp_mode_extract'),
            'rename': t('fp_mode_rename'),
            'create': t('fp_mode_create')
        }

        for mode in self.MODES:
            btn = QPushButton(mode_labels[mode])
            btn.setCheckable(True)
            btn.setChecked(mode == self.current_mode)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(80)
            btn.setStyleSheet(self._get_mode_btn_style(mode == self.current_mode))
            btn.clicked.connect(lambda checked, m=mode: self._switch_mode(m))
            nav_layout.addWidget(btn)
            self.mode_buttons[mode] = btn

        nav_layout.addStretch()

        nav_frame.setLayout(nav_layout)
        parent_layout.addWidget(nav_frame)

    def _get_mode_btn_style(self, is_active):
        """获取模式按钮样式"""
        if is_active:
            return """
                QPushButton {
                    background-color: #339af0;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #228be6;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: transparent;
                    color: #495057;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """

    def _switch_mode(self, mode):
        """切换模式"""
        self.current_mode = mode

        # 更新按钮样式
        for m, btn in self.mode_buttons.items():
            btn.setChecked(m == mode)
            btn.setStyleSheet(self._get_mode_btn_style(m == mode))

        # 切换界面
        self.content_stack.setCurrentIndex(self.MODES.index(mode))

        # 重置对应模式的界面
        if mode == 'extract':
            self._reset_extract_mode()
        elif mode == 'rename':
            self._reset_rename_mode()
        elif mode == 'create':
            self._reset_create_mode()

        # 更新底部按钮文本
        if mode == 'extract':
            self.process_btn.setText(t('fp_export'))
            self.process_btn.setStyleSheet(self._get_success_btn_style())
        elif mode == 'rename':
            self.process_btn.setText(t('fp_rename_start'))
            self.process_btn.setStyleSheet(self._get_success_btn_style())
        elif mode == 'create':
            self.process_btn.setText(t('fp_create_start'))
            self.process_btn.setStyleSheet(self._get_success_btn_style())

    def _reset_extract_mode(self):
        """重置文件名提取模式"""
        self.extract_folder = ""
        self.extract_files = []
        self.extract_folder_input.clear()
        self.extract_listbox.clear()
        self.extract_status_label.setText(t('fp_extract_status_ready'))
        self.extract_include_ext_check.setChecked(True)

    def _reset_rename_mode(self):
        """重置批量重命名模式"""
        self.rename_folder = ""
        self.rename_files = []
        self.rename_folder_input.clear()
        self.rename_table.setRowCount(0)
        self.rename_status_label.setText(t('fp_rename_status_ready'))
        self.rename_rule_combo.setCurrentIndex(0)
        self.prefix_input.clear()
        self.suffix_input.clear()
        self.number_input.setText("001")
        self.replace_old_input.clear()
        self.replace_new_input.clear()
        self.regex_pattern_input.clear()
        self.regex_replace_input.clear()

    def _reset_create_mode(self):
        """重置批量创建模式"""
        self.create_excel_path = ""
        self.create_folder = ""
        self.create_files = []
        self.create_mode = 'folder'
        self.create_ext = '.txt'
        self.skip_existing = False
        self.create_excel_input.clear()
        self.create_folder_input.clear()
        self.create_listbox.clear()
        self.create_status_label.setText(t('fp_create_status_ready'))
        self.create_folder_radio.setChecked(True)
        self.create_ext_input.setText(".txt")
        self.skip_existing_check.setChecked(False)

    def _create_extract_panel(self):
        """创建文件名提取界面"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 左右分割布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：设置区域
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        # 文件夹选择
        self.extract_folder_label = QLabel(t('fp_extract_folder'))
        self.extract_folder_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.extract_folder_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.extract_folder_input = QLineEdit()
        self.extract_folder_input.setPlaceholderText(t('fp_extract_folder_placeholder'))
        self.extract_folder_input.setReadOnly(True)
        self.extract_folder_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
        """)
        path_row.addWidget(self.extract_folder_input, 1)

        self.extract_browse_btn = AnimatedButton(t('fp_browse'))
        self.extract_browse_btn.setFixedHeight(28)
        self.extract_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.extract_browse_btn.clicked.connect(self._browse_extract_folder)
        path_row.addWidget(self.extract_browse_btn)
        left_layout.addLayout(path_row)

        # 提示标签
        self.extract_tip_label = QLabel(t('fp_extract_tip'))
        self.extract_tip_label.setStyleSheet("color: #868e96; font-size: 11px;")
        left_layout.addWidget(self.extract_tip_label)

        # 分隔线
        left_layout.addSpacing(8)

        # 包含扩展名选项
        self.extract_include_ext_check = QCheckBox(t('fp_extract_include_ext'))
        self.extract_include_ext_check.setChecked(True)
        self.extract_include_ext_check.setStyleSheet("""
            QCheckBox {
                color: #495057;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
        """)
        self.extract_include_ext_check.stateChanged.connect(self._auto_refresh_extract_preview)
        left_layout.addWidget(self.extract_include_ext_check)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # 右侧：预览区域
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.extract_preview_label = QLabel(t('fp_extract_preview'))
        self.extract_preview_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        right_layout.addWidget(self.extract_preview_label)

        # 刷新预览按钮
        self.extract_preview_btn = AnimatedButton(t('fp_preview_btn'))
        self.extract_preview_btn.setFixedHeight(28)
        self.extract_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
        """)
        self.extract_preview_btn.clicked.connect(self._preview_extract_files)
        right_layout.addWidget(self.extract_preview_btn)

        # 文件列表
        self.extract_listbox = QListWidget()
        self.extract_listbox.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
            }
            QListWidget::item:hover {
                background-color: #f1f3f5;
            }
        """)
        right_layout.addWidget(self.extract_listbox, 1)

        # 状态标签
        self.extract_status_label = QLabel(t('fp_extract_status_ready'))
        self.extract_status_label.setStyleSheet("color: #868e96; font-size: 11px;")
        right_layout.addWidget(self.extract_status_label)

        # 输出路径显示（右下角）
        output_path_layout = QHBoxLayout()
        output_path_layout.addStretch()
        self.extract_output_path_label = QLabel(t('fp_extract_output_path', ''))
        self.extract_output_path_label.setStyleSheet("color: #868e96; font-size: 11px;")
        output_path_layout.addWidget(self.extract_output_path_label)
        right_layout.addLayout(output_path_layout)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        splitter.setSizes([280, 350])
        main_layout.addWidget(splitter, 1)

        panel.setLayout(main_layout)
        return panel

    def _create_rename_panel(self):
        """创建批量重命名界面"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 左右分割布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：设置区域
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        # 目标路径选择
        self.rename_path_label = QLabel(t('fp_rename_target'))
        self.rename_path_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.rename_path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.rename_folder_input = QLineEdit()
        self.rename_folder_input.setPlaceholderText(t('fp_rename_folder_placeholder'))
        self.rename_folder_input.setReadOnly(True)
        self.rename_folder_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
        """)
        path_row.addWidget(self.rename_folder_input, 1)

        self.rename_browse_btn = AnimatedButton(t('fp_browse'))
        self.rename_browse_btn.setFixedHeight(28)
        self.rename_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.rename_browse_btn.clicked.connect(self._browse_rename_folder)
        path_row.addWidget(self.rename_browse_btn)
        left_layout.addLayout(path_row)

        # 分隔线
        left_layout.addSpacing(8)

        # 重命名规则
        self.rename_rule_label = QLabel(t('fp_rename_rule'))
        self.rename_rule_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.rename_rule_label)

        self.rename_rule_combo = QComboBox()
        self.rename_rule_combo.addItems([
            t('fp_rename_rule_prefix'),
            t('fp_rename_rule_suffix'),
            t('fp_rename_rule_number'),
            t('fp_rename_rule_replace'),
            t('fp_rename_rule_regex')
        ])
        self.rename_rule_combo.setFixedHeight(28)
        self.rename_rule_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ced4da;
                selection-background-color: #339af0;
            }
        """)
        self.rename_rule_combo.currentIndexChanged.connect(self._on_rename_rule_changed)
        left_layout.addWidget(self.rename_rule_combo)

        # 规则输入区域
        self.rename_input_container = QWidget()
        self.rename_input_layout = QVBoxLayout()
        self.rename_input_layout.setContentsMargins(0, 0, 0, 0)
        self.rename_input_layout.setSpacing(6)

        # 前缀输入
        self.prefix_row = QWidget()
        prefix_layout = QHBoxLayout()
        prefix_layout.setContentsMargins(0, 0, 0, 0)
        prefix_layout.setSpacing(8)
        self.prefix_label = QLabel(t('fp_rename_prefix_label'))
        self.prefix_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.prefix_label.setFixedWidth(50)
        prefix_layout.addWidget(self.prefix_label)
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText(t('fp_rename_prefix_placeholder'))
        self.prefix_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.prefix_input.textChanged.connect(self._auto_refresh_rename_preview)
        prefix_layout.addWidget(self.prefix_input)
        self.prefix_row.setLayout(prefix_layout)
        self.rename_input_layout.addWidget(self.prefix_row)

        # 后缀输入
        self.suffix_row = QWidget()
        suffix_layout = QHBoxLayout()
        suffix_layout.setContentsMargins(0, 0, 0, 0)
        suffix_layout.setSpacing(8)
        self.suffix_label = QLabel(t('fp_rename_suffix_label'))
        self.suffix_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.suffix_label.setFixedWidth(50)
        suffix_layout.addWidget(self.suffix_label)
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText(t('fp_rename_suffix_placeholder'))
        self.suffix_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.suffix_input.textChanged.connect(self._auto_refresh_rename_preview)
        suffix_layout.addWidget(self.suffix_input)
        self.suffix_row.setLayout(suffix_layout)
        self.suffix_row.setVisible(False)
        self.rename_input_layout.addWidget(self.suffix_row)

        # 序号输入
        self.number_row = QWidget()
        number_layout = QHBoxLayout()
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(8)
        self.number_label = QLabel(t('fp_rename_number_label'))
        self.number_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.number_label.setFixedWidth(50)
        number_layout.addWidget(self.number_label)
        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText(t('fp_rename_number_placeholder'))
        self.number_input.setText("001")
        self.number_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.number_input.textChanged.connect(self._auto_refresh_rename_preview)
        number_layout.addWidget(self.number_input)
        self.number_row.setLayout(number_layout)
        self.number_row.setVisible(False)
        self.rename_input_layout.addWidget(self.number_row)

        # 替换输入
        self.replace_row = QWidget()
        replace_layout = QVBoxLayout()
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(6)
        
        replace_old_row = QHBoxLayout()
        replace_old_row.setSpacing(8)
        self.replace_old_label = QLabel(t('fp_rename_replace_old'))
        self.replace_old_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.replace_old_label.setFixedWidth(50)
        replace_old_row.addWidget(self.replace_old_label)
        self.replace_old_input = QLineEdit()
        self.replace_old_input.setPlaceholderText(t('fp_rename_replace_old_placeholder'))
        self.replace_old_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.replace_old_input.textChanged.connect(self._auto_refresh_rename_preview)
        replace_old_row.addWidget(self.replace_old_input)
        replace_layout.addLayout(replace_old_row)
        
        replace_new_row = QHBoxLayout()
        replace_new_row.setSpacing(8)
        self.replace_new_label = QLabel(t('fp_rename_replace_new'))
        self.replace_new_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.replace_new_label.setFixedWidth(50)
        replace_new_row.addWidget(self.replace_new_label)
        self.replace_new_input = QLineEdit()
        self.replace_new_input.setPlaceholderText(t('fp_rename_replace_new_placeholder'))
        self.replace_new_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.replace_new_input.textChanged.connect(self._auto_refresh_rename_preview)
        replace_new_row.addWidget(self.replace_new_input)
        replace_layout.addLayout(replace_new_row)
        
        self.replace_row.setLayout(replace_layout)
        self.replace_row.setVisible(False)
        self.rename_input_layout.addWidget(self.replace_row)

        # 正则替换输入
        self.regex_row = QWidget()
        regex_layout = QVBoxLayout()
        regex_layout.setContentsMargins(0, 0, 0, 0)
        regex_layout.setSpacing(6)
        
        regex_pattern_row = QHBoxLayout()
        regex_pattern_row.setSpacing(8)
        self.regex_pattern_label = QLabel(t('fp_rename_regex_pattern'))
        self.regex_pattern_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.regex_pattern_label.setFixedWidth(50)
        regex_pattern_row.addWidget(self.regex_pattern_label)
        self.regex_pattern_input = QLineEdit()
        self.regex_pattern_input.setPlaceholderText(t('fp_rename_regex_pattern_placeholder'))
        self.regex_pattern_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.regex_pattern_input.textChanged.connect(self._auto_refresh_rename_preview)
        regex_pattern_row.addWidget(self.regex_pattern_input)
        regex_layout.addLayout(regex_pattern_row)
        
        regex_replace_row = QHBoxLayout()
        regex_replace_row.setSpacing(8)
        self.regex_replace_label = QLabel(t('fp_rename_regex_replace'))
        self.regex_replace_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.regex_replace_label.setFixedWidth(50)
        regex_replace_row.addWidget(self.regex_replace_label)
        self.regex_replace_input = QLineEdit()
        self.regex_replace_input.setPlaceholderText(t('fp_rename_regex_replace_placeholder'))
        self.regex_replace_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.regex_replace_input.textChanged.connect(self._auto_refresh_rename_preview)
        regex_replace_row.addWidget(self.regex_replace_input)
        regex_layout.addLayout(regex_replace_row)
        
        self.regex_row.setLayout(regex_layout)
        self.regex_row.setVisible(False)
        self.rename_input_layout.addWidget(self.regex_row)

        self.rename_input_container.setLayout(self.rename_input_layout)
        left_layout.addWidget(self.rename_input_container)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # 右侧：预览区域
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.rename_preview_label = QLabel(t('fp_rename_preview'))
        self.rename_preview_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        right_layout.addWidget(self.rename_preview_label)

        # 预览表格
        self.rename_table = QTableWidget()
        self.rename_table.setColumnCount(2)
        self.rename_table.setHorizontalHeaderLabels([t('fp_rename_old_name'), t('fp_rename_new_name')])
        self.rename_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rename_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #e9ecef;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px 6px;
            }
            QHeaderView::section {
                background-color: #f1f3f5;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: 600;
                color: #495057;
                font-size: 11px;
            }
        """)
        right_layout.addWidget(self.rename_table, 1)

        # 状态标签
        self.rename_status_label = QLabel(t('fp_rename_status_ready'))
        self.rename_status_label.setStyleSheet("color: #868e96; font-size: 11px;")
        right_layout.addWidget(self.rename_status_label)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        splitter.setSizes([280, 350])
        main_layout.addWidget(splitter, 1)

        panel.setLayout(main_layout)
        return panel

    def _create_create_panel(self):
        """创建批量创建界面"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # 左右分割布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：设置区域
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 8, 8)

        # Excel导入
        self.create_excel_label = QLabel(t('fp_create_excel'))
        self.create_excel_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.create_excel_label)

        excel_row = QHBoxLayout()
        excel_row.setSpacing(8)
        self.create_excel_input = QLineEdit()
        self.create_excel_input.setPlaceholderText(t('fp_create_excel_placeholder'))
        self.create_excel_input.setReadOnly(True)
        self.create_excel_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
        """)
        excel_row.addWidget(self.create_excel_input, 1)

        self.create_excel_browse_btn = AnimatedButton(t('fp_browse'))
        self.create_excel_browse_btn.setFixedHeight(28)
        self.create_excel_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.create_excel_browse_btn.clicked.connect(self._browse_create_excel)
        excel_row.addWidget(self.create_excel_browse_btn)
        left_layout.addLayout(excel_row)

        # 提示标签
        self.create_excel_tip_label = QLabel(t('fp_create_excel_tip'))
        self.create_excel_tip_label.setStyleSheet("color: #868e96; font-size: 11px;")
        left_layout.addWidget(self.create_excel_tip_label)

        # 分隔线
        left_layout.addSpacing(8)

        # 目标路径
        self.create_path_label = QLabel(t('fp_create_target'))
        self.create_path_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.create_path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.create_folder_input = QLineEdit()
        self.create_folder_input.setPlaceholderText(t('fp_create_folder_placeholder'))
        self.create_folder_input.setReadOnly(True)
        self.create_folder_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
        """)
        path_row.addWidget(self.create_folder_input, 1)

        self.create_folder_browse_btn = AnimatedButton(t('fp_browse'))
        self.create_folder_browse_btn.setFixedHeight(28)
        self.create_folder_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.create_folder_browse_btn.clicked.connect(self._browse_create_folder)
        path_row.addWidget(self.create_folder_browse_btn)
        left_layout.addLayout(path_row)

        # 分隔线
        left_layout.addSpacing(8)

        # 创建类型
        self.create_type_label = QLabel(t('fp_create_type'))
        self.create_type_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(self.create_type_label)

        type_row = QHBoxLayout()
        type_row.setSpacing(16)

        self.create_type_group = QButtonGroup(self)
        
        self.create_folder_radio = QRadioButton(t('fp_create_type_folder'))
        self.create_folder_radio.setChecked(True)
        self.create_folder_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 12px;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        self.create_type_group.addButton(self.create_folder_radio, 0)
        type_row.addWidget(self.create_folder_radio)

        self.create_file_radio = QRadioButton(t('fp_create_type_file'))
        self.create_file_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 12px;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        self.create_type_group.addButton(self.create_file_radio, 1)
        type_row.addWidget(self.create_file_radio)

        type_row.addStretch()
        left_layout.addLayout(type_row)

        # 扩展名输入（文件模式时显示）
        self.ext_row_widget = QWidget()
        ext_row = QHBoxLayout()
        ext_row.setContentsMargins(0, 0, 0, 0)
        ext_row.setSpacing(8)

        self.create_ext_label = QLabel(t('fp_create_ext_label'))
        self.create_ext_label.setStyleSheet("color: #495057; font-size: 12px;")
        self.create_ext_label.setFixedWidth(50)
        ext_row.addWidget(self.create_ext_label)

        self.create_ext_input = QLineEdit()
        self.create_ext_input.setText(".txt")
        self.create_ext_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.create_ext_input.textChanged.connect(self._auto_refresh_create_preview)
        ext_row.addWidget(self.create_ext_input)

        self.ext_row_widget.setLayout(ext_row)
        self.ext_row_widget.setVisible(False)
        left_layout.addWidget(self.ext_row_widget)

        # 忽略已有文件选项
        self.skip_existing_check = QCheckBox(t('fp_create_skip_existing'))
        self.skip_existing_check.setStyleSheet("""
            QCheckBox {
                color: #495057;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
        """)
        self.skip_existing_check.stateChanged.connect(self._auto_refresh_create_preview)
        left_layout.addWidget(self.skip_existing_check)

        # 连接类型变化信号
        self.create_type_group.buttonClicked.connect(self._on_create_type_changed)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # 右侧：预览区域
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 6px; }")
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(8, 8, 8, 8)

        self.create_preview_label = QLabel(t('fp_create_preview'))
        self.create_preview_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        right_layout.addWidget(self.create_preview_label)

        # 预览列表
        self.create_listbox = QListWidget()
        self.create_listbox.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
            }
            QListWidget::item:hover {
                background-color: #f1f3f5;
            }
        """)
        right_layout.addWidget(self.create_listbox, 1)

        # 状态标签
        self.create_status_label = QLabel(t('fp_create_status_ready'))
        self.create_status_label.setStyleSheet("color: #868e96; font-size: 11px;")
        right_layout.addWidget(self.create_status_label)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        splitter.setSizes([280, 350])
        main_layout.addWidget(splitter, 1)

        panel.setLayout(main_layout)
        return panel

    def _create_buttons(self, parent_layout):
        """创建底部操作区域"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # 进度条容器
        self.progress_container = QWidget()
        self.progress_container.setFixedHeight(14)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.progress_container.setLayout(container_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e9ecef;
                border: none;
                border-radius: 4px;
                height: 14px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #339af0;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        container_layout.addWidget(self.progress_bar)
        btn_layout.addWidget(self.progress_container, 1)

        # 操作按钮
        self.process_btn = AnimatedButton(t('fp_export'))
        self.process_btn.setFixedSize(120, 34)
        self.process_btn.setStyleSheet(self._get_success_btn_style())
        self.process_btn.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.process_btn)

        parent_layout.addLayout(btn_layout)

    def _get_success_btn_style(self):
        """获取确认按钮样式"""
        return """
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
            QPushButton:pressed {
                background-color: #37b24d;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """

    def _load_config(self):
        """加载配置"""
        # 加载全局保存路径并显示
        if self.config:
            save_path = self.config.get_save_path()
            if save_path:
                self.extract_output_path_label.setText(t('fp_extract_output_path', save_path.replace('\\', '/')))

    def _set_progress(self, value):
        """设置进度条"""
        self.progress_bar.setValue(value)

    # ---- 文件名提取功能 ----

    def _browse_extract_folder(self):
        """浏览选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, t('fp_select_folder'), ""
        )
        if folder:
            self.extract_folder = folder
            self.extract_folder_input.setText(folder)
            self._auto_refresh_extract_preview()

    def _auto_refresh_extract_preview(self):
        """自动刷新预览"""
        if self.extract_folder:
            self._preview_extract_files()

    def _preview_extract_files(self):
        """预览文件列表"""
        if not self.extract_folder:
            self.warning_requested.emit(t('fp_extract_no_folder'))
            return

        self.extract_listbox.clear()
        files = self._get_extract_files_list()

        if not files:
            self.extract_status_label.setText(t('fp_extract_no_files'))
            return

        for filename in files:
            self.extract_listbox.addItem(filename)

        self.extract_status_label.setText(t('fp_extract_status_found', len(files)))

    def _get_extract_files_list(self):
        """获取文件列表"""
        if not self.extract_folder or not os.path.exists(self.extract_folder):
            return []

        files = []
        try:
            for item in os.listdir(self.extract_folder):
                item_path = os.path.join(self.extract_folder, item)
                if os.path.isfile(item_path):
                    if self.extract_include_ext_check.isChecked():
                        files.append(item)
                    else:
                        name, ext = os.path.splitext(item)
                        files.append(name)
            return sorted(files)
        except Exception as e:
            return []

    def _export_to_excel(self):
        """导出到Excel"""
        global HAS_PANDAS
        if HAS_PANDAS is None:
            try:
                import pandas as pd
                HAS_PANDAS = True
            except ImportError:
                HAS_PANDAS = False

        if not HAS_PANDAS:
            self.warning_requested.emit(t('fp_extract_need_pandas'))
            return

        if not self.extract_folder:
            self.warning_requested.emit(t('fp_extract_no_folder'))
            return

        files = self._get_extract_files_list()
        if not files:
            self.warning_requested.emit(t('fp_extract_no_files'))
            return

        # 使用全局保存路径
        save_path = self.config.get_save_path() if self.config else ""
        
        # 获取文件夹名称作为文件名
        folder_name = os.path.basename(self.extract_folder)
        default_filename = f"{folder_name}_文件名列表.xlsx"
        
        if not save_path:
            # 使用默认文件名（保存到源文件夹）
            save_path = os.path.join(self.extract_folder, default_filename)
        elif os.path.isdir(save_path):
            # 如果是目录路径，在该目录下创建文件
            save_path = os.path.join(save_path, default_filename)
        elif not save_path.endswith('.xlsx'):
            # 如果没有扩展名，添加扩展名
            save_path += '.xlsx'

        # 处理文件名冲突
        save_path = get_unique_filepath(save_path)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.is_processing = True

        def do_export():
            try:
                import pandas as pd

                df = pd.DataFrame({
                    '序号': range(1, len(files) + 1),
                    '文件名': files
                })

                with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='文件列表', index=False)
                    worksheet = writer.sheets['文件列表']
                    worksheet.column_dimensions['A'].width = 8
                    worksheet.column_dimensions['B'].width = 50

                self.progress_updated.emit(100)
                self.success_requested.emit(t('fp_extract_done', save_path.replace('\\', '/')))
                
                # 清空
                self.extract_folder = ""
                self.extract_folder_input.clear()
                self.extract_listbox.clear()
                self.extract_status_label.setText(t('fp_extract_status_ready'))
            except Exception as e:
                self.warning_requested.emit(t('fp_extract_failed', str(e)))
            finally:
                self._reset_ui()

        thread = threading.Thread(target=do_export, daemon=True)
        thread.start()

    # ---- 批量重命名功能 ----

    def _browse_rename_folder(self):
        """浏览选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, t('fp_select_folder'), ""
        )
        if folder:
            self.rename_folder = folder
            self.rename_folder_input.setText(folder)
            self._auto_refresh_rename_preview()

    def _on_rename_rule_changed(self, index):
        """重命名规则变化"""
        rules = ['prefix', 'suffix', 'number', 'replace', 'regex']
        self.rename_rule = rules[index]

        # 显示/隐藏对应的输入行
        self.prefix_row.setVisible(self.rename_rule == 'prefix')
        self.suffix_row.setVisible(self.rename_rule == 'suffix')
        self.number_row.setVisible(self.rename_rule == 'number')
        self.replace_row.setVisible(self.rename_rule == 'replace')
        self.regex_row.setVisible(self.rename_rule == 'regex')

        self._auto_refresh_rename_preview()

    def _auto_refresh_rename_preview(self):
        """自动刷新重命名预览"""
        if self.rename_folder:
            self._preview_rename_files()

    def _preview_rename_files(self):
        """预览重命名"""
        if not self.rename_folder:
            self.rename_table.setRowCount(0)
            self.rename_status_label.setText(t('fp_rename_status_ready'))
            return

        # 获取文件夹中的文件
        try:
            files = []
            for item in os.listdir(self.rename_folder):
                item_path = os.path.join(self.rename_folder, item)
                if os.path.isfile(item_path):
                    files.append(item)
            files = sorted(files)
        except Exception:
            self.rename_table.setRowCount(0)
            return

        self.rename_table.setRowCount(len(files))
        self.rename_files = []

        for i, old_name in enumerate(files):
            new_name = self._apply_rename_rule(old_name)
            self.rename_files.append((old_name, new_name))

            # 原名
            old_item = QTableWidgetItem(old_name)
            old_item.setForeground(QColor('#495057'))
            self.rename_table.setItem(i, 0, old_item)

            # 新名
            new_item = QTableWidgetItem(new_name)
            
            # 检查是否有重名
            new_path = os.path.join(self.rename_folder, new_name)
            old_path = os.path.join(self.rename_folder, old_name)
            
            # 重名检测（排除自身）
            is_duplicate = False
            for j, (oj, nj) in enumerate(self.rename_files):
                if j != i and nj == new_name:
                    is_duplicate = True
                    break
            
            # 或者新名与现有文件名冲突（排除自身）
            if not is_duplicate and os.path.exists(new_path) and new_path != old_path:
                is_duplicate = True
            
            if is_duplicate:
                new_item.setForeground(QColor('#ff6b6b'))  # 红色提示重名
            else:
                new_item.setForeground(QColor('#495057'))
            
            self.rename_table.setItem(i, 1, new_item)

        # 更新状态
        self.rename_status_label.setText(t('fp_rename_status_found', len(files)))

    def _apply_rename_rule(self, old_name):
        """应用重命名规则"""
        name, ext = os.path.splitext(old_name)

        if self.rename_rule == 'prefix':
            prefix = self.prefix_input.text()
            return f"{prefix}{old_name}"
        elif self.rename_rule == 'suffix':
            suffix = self.suffix_input.text()
            return f"{name}{suffix}{ext}"
        elif self.rename_rule == 'number':
            # 获取起始序号
            try:
                start_num = int(self.number_input.text())
            except ValueError:
                start_num = 1
            
            # 计算当前序号（基于文件在列表中的位置）
            idx = self.rename_files.index((old_name, '')) if (old_name, '') in self.rename_files else 0
            
            # 格式化序号（保持输入的位数）
            num_str = self.number_input.text()
            width = len(num_str)
            new_num = start_num + idx
            
            # 保持位数
            if width > 0:
                new_name = f"{str(new_num).zfill(width)}"
            else:
                new_name = str(new_num)
            
            return f"{new_name}{ext}"
        elif self.rename_rule == 'replace':
            old_text = self.replace_old_input.text()
            new_text = self.replace_new_input.text()
            if old_text:
                return old_name.replace(old_text, new_text)
            return old_name
        elif self.rename_rule == 'regex':
            pattern = self.regex_pattern_input.text()
            replace = self.regex_replace_input.text()
            if pattern:
                try:
                    return re.sub(pattern, replace, old_name)
                except re.error:
                    return old_name
            return old_name
        
        return old_name

    def _start_rename(self):
        """开始重命名"""
        if not self.rename_folder:
            self.warning_requested.emit(t('fp_rename_no_folder'))
            return

        if not self.rename_files:
            self.warning_requested.emit(t('fp_rename_no_files'))
            return

        # 检查是否有重名
        has_duplicate = False
        new_names = []
        for old_name, new_name in self.rename_files:
            if new_name in new_names:
                has_duplicate = True
                break
            new_names.append(new_name)
        
        if has_duplicate:
            self.warning_requested.emit(t('fp_rename_duplicate'))
            return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.is_processing = True

        def do_rename():
            success_count = 0
            total = len(self.rename_files)
            
            for i, (old_name, new_name) in enumerate(self.rename_files):
                try:
                    old_path = os.path.join(self.rename_folder, old_name)
                    new_path = os.path.join(self.rename_folder, new_name)
                    
                    if old_path != new_path:
                        os.rename(old_path, new_path)
                    success_count += 1
                except Exception as e:
                    pass
                
                self.progress_updated.emit(int((i + 1) / total * 100))
            
            self.success_requested.emit(t('fp_rename_done', success_count))
            self._reset_ui()
            
            # 清空
            self.rename_folder = ""
            self.rename_folder_input.clear()
            self.rename_table.setRowCount(0)
            self.rename_status_label.setText(t('fp_rename_status_ready'))

        thread = threading.Thread(target=do_rename, daemon=True)
        thread.start()

    # ---- 批量创建功能 ----

    def _browse_create_excel(self):
        """浏览选择Excel文件"""
        file_path = QFileDialog.getOpenFileName(
            self,
            t('fp_create_select_excel'),
            "",
            f"{t('fp_excel_files')} (*.xlsx *.xls);;{t('fp_all_files')} (*.*)"
        )[0]
        
        if file_path:
            self.create_excel_path = file_path
            self.create_excel_input.setText(file_path)
            self._auto_refresh_create_preview()

    def _browse_create_folder(self):
        """浏览选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, t('fp_select_folder'), ""
        )
        if folder:
            self.create_folder = folder
            self.create_folder_input.setText(folder)
            self._auto_refresh_create_preview()

    def _on_create_type_changed(self, button):
        """创建类型变化"""
        if button == self.create_file_radio:
            self.ext_row_widget.setVisible(True)
            self.create_mode = 'file'
        else:
            self.ext_row_widget.setVisible(False)
            self.create_mode = 'folder'
        
        self._auto_refresh_create_preview()

    def _auto_refresh_create_preview(self):
        """自动刷新创建预览"""
        if self.create_excel_path:
            self._preview_create_files()

    def _preview_create_files(self):
        """预览创建"""
        global HAS_PANDAS
        if HAS_PANDAS is None:
            try:
                import pandas as pd
                HAS_PANDAS = True
            except ImportError:
                HAS_PANDAS = False

        if not HAS_PANDAS:
            self.warning_requested.emit(t('fp_need_pandas'))
            return

        if not self.create_excel_path:
            self.create_listbox.clear()
            self.create_status_label.setText(t('fp_create_status_ready'))
            return

        try:
            import pandas as pd
            df = pd.read_excel(self.create_excel_path, header=None)  # 不忽略第一行
            
            # 获取第一列
            if len(df.columns) == 0:
                self.warning_requested.emit(t('fp_create_excel_empty'))
                return
            
            names = df.iloc[:, 0].dropna().astype(str).tolist()
            
            self.create_listbox.clear()
            self.create_files = []
            
            ext = self.create_ext_input.text() if self.create_mode == 'file' else ""
            skip_existing = self.skip_existing_check.isChecked()
            
            # 统计数量
            total_count = len(names)
            existing_count = 0
            
            for name in names:
                if self.create_mode == 'folder':
                    item_name = name
                else:
                    item_name = f"{name}{ext}"
                
                # 检查是否已存在
                exists = False
                if self.create_folder:
                    full_path = os.path.join(self.create_folder, item_name)
                    exists = os.path.exists(full_path)
                
                # 添加到列表
                item = QListWidgetItem(item_name)
                
                if exists:
                    existing_count += 1
                    if skip_existing:
                        item.setForeground(QColor('#fab005'))  # 黄色：将跳过
                    else:
                        item.setForeground(QColor('#fa5252'))  # 红色：将覆盖
                else:
                    item.setForeground(QColor('#495057'))  # 默认灰色
                
                self.create_listbox.addItem(item)
                self.create_files.append(item_name)
            
            # 更新状态标签，显示数量统计
            create_count = total_count - existing_count if skip_existing else total_count
            
            if existing_count > 0:
                if skip_existing:
                    status_text = t('fp_create_status_found_skip', create_count, existing_count)
                else:
                    status_text = t('fp_create_status_found_overwrite', create_count, existing_count)
            else:
                status_text = t('fp_create_status_found', total_count)
            
            self.create_status_label.setText(status_text)
        except Exception as e:
            self.warning_requested.emit(t('fp_create_excel_error', str(e)))

    def _start_create(self):
        """开始创建"""
        global HAS_PANDAS
        if HAS_PANDAS is None:
            try:
                import pandas as pd
                HAS_PANDAS = True
            except ImportError:
                HAS_PANDAS = False

        if not HAS_PANDAS:
            self.warning_requested.emit(t('fp_need_pandas'))
            return

        if not self.create_excel_path:
            self.warning_requested.emit(t('fp_create_no_excel'))
            return

        if not self.create_folder:
            self.warning_requested.emit(t('fp_create_no_folder'))
            return

        if not self.create_files:
            self.warning_requested.emit(t('fp_create_no_files'))
            return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.is_processing = True

        def do_create():
            success_count = 0
            total = len(self.create_files)
            skip_existing = self.skip_existing_check.isChecked()
            
            for i, name in enumerate(self.create_files):
                try:
                    full_path = os.path.join(self.create_folder, name)
                    
                    # 检查是否跳过
                    if skip_existing and os.path.exists(full_path):
                        continue
                    
                    if self.create_mode == 'folder':
                        os.makedirs(full_path, exist_ok=True)
                    else:
                        # 创建空文件
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write('')
                    
                    success_count += 1
                except Exception as e:
                    pass
                
                self.progress_updated.emit(int((i + 1) / total * 100))
            
            self.success_requested.emit(t('fp_create_done', success_count))
            self._reset_ui()
            
            # 清空
            self.create_excel_path = ""
            self.create_excel_input.clear()
            self.create_folder = ""
            self.create_folder_input.clear()
            self.create_listbox.clear()
            self.create_status_label.setText(t('fp_create_status_ready'))

        thread = threading.Thread(target=do_create, daemon=True)
        thread.start()

    # ---- 公共方法 ----

    def _start_processing(self):
        """开始处理"""
        if self.is_processing:
            return

        if self.current_mode == 'extract':
            self._export_to_excel()
        elif self.current_mode == 'rename':
            self._start_rename()
        elif self.current_mode == 'create':
            self._start_create()

    def _reset_ui(self):
        """重置UI"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(True)
        self.is_processing = False

    # ---- 拖拽导入功能 ----

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件 - 根据当前模式处理"""
        urls = event.mimeData().urls()
        if not urls:
            return

        if self.current_mode == 'extract':
            # 文件名提取模式：接受文件夹
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.extract_folder = path
                self.extract_folder_input.setText(path)
                self._auto_refresh_extract_preview()

        elif self.current_mode == 'rename':
            # 批量重命名模式：接受文件夹
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.rename_folder = path
                self.rename_folder_input.setText(path)
                self._auto_refresh_rename_preview()

        elif self.current_mode == 'create':
            # 批量创建模式：接受 Excel 文件和文件夹
            for url in urls:
                path = url.toLocalFile()
                if os.path.isfile(path) and path.endswith('.xlsx'):
                    self.create_excel_path = path
                    self.create_excel_input.setText(path)
                    self._auto_refresh_create_preview()
                elif os.path.isdir(path):
                    self.create_folder = path
                    self.create_folder_input.setText(path)
                    self._auto_refresh_create_preview()

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)

        # 更新导航按钮
        mode_labels = {
            'extract': t('fp_mode_extract'),
            'rename': t('fp_mode_rename'),
            'create': t('fp_mode_create')
        }
        for mode, btn in self.mode_buttons.items():
            btn.setText(mode_labels[mode])

        # 更新文件名提取界面
        self.extract_folder_label.setText(t('fp_extract_folder'))
        self.extract_folder_input.setPlaceholderText(t('fp_extract_folder_placeholder'))
        self.extract_browse_btn.setText(t('fp_browse'))
        self.extract_tip_label.setText(t('fp_extract_tip'))
        self.extract_preview_label.setText(t('fp_extract_preview'))
        self.extract_preview_btn.setText(t('fp_preview_btn'))
        self.extract_include_ext_check.setText(t('fp_extract_include_ext'))
        self.extract_status_label.setText(t('fp_extract_status_ready'))
        
        # 重新加载全局保存路径
        if self.config:
            save_path = self.config.get_save_path()
            if save_path:
                self.extract_output_path_label.setText(t('fp_extract_output_path', save_path.replace('\\', '/')))
            else:
                self.extract_output_path_label.setText(t('fp_extract_output_path', ''))

        # 更新批量重命名界面
        self.rename_path_label.setText(t('fp_rename_target'))
        self.rename_folder_input.setPlaceholderText(t('fp_rename_folder_placeholder'))
        self.rename_browse_btn.setText(t('fp_browse'))
        self.rename_rule_label.setText(t('fp_rename_rule'))
        self.rename_rule_combo.setItemText(0, t('fp_rename_rule_prefix'))
        self.rename_rule_combo.setItemText(1, t('fp_rename_rule_suffix'))
        self.rename_rule_combo.setItemText(2, t('fp_rename_rule_number'))
        self.rename_rule_combo.setItemText(3, t('fp_rename_rule_replace'))
        self.rename_rule_combo.setItemText(4, t('fp_rename_rule_regex'))
        self.prefix_label.setText(t('fp_rename_prefix_label'))
        self.prefix_input.setPlaceholderText(t('fp_rename_prefix_placeholder'))
        self.suffix_label.setText(t('fp_rename_suffix_label'))
        self.suffix_input.setPlaceholderText(t('fp_rename_suffix_placeholder'))
        self.number_label.setText(t('fp_rename_number_label'))
        self.number_input.setPlaceholderText(t('fp_rename_number_placeholder'))
        self.replace_old_label.setText(t('fp_rename_replace_old'))
        self.replace_old_input.setPlaceholderText(t('fp_rename_replace_old_placeholder'))
        self.replace_new_label.setText(t('fp_rename_replace_new'))
        self.replace_new_input.setPlaceholderText(t('fp_rename_replace_new_placeholder'))
        self.regex_pattern_label.setText(t('fp_rename_regex_pattern'))
        self.regex_pattern_input.setPlaceholderText(t('fp_rename_regex_pattern_placeholder'))
        self.regex_replace_label.setText(t('fp_rename_regex_replace'))
        self.regex_replace_input.setPlaceholderText(t('fp_rename_regex_replace_placeholder'))
        self.rename_preview_label.setText(t('fp_rename_preview'))
        self.rename_status_label.setText(t('fp_rename_status_ready'))

        # 更新批量创建界面
        self.create_excel_label.setText(t('fp_create_excel'))
        self.create_excel_input.setPlaceholderText(t('fp_create_excel_placeholder'))
        self.create_excel_browse_btn.setText(t('fp_browse'))
        self.create_excel_tip_label.setText(t('fp_create_excel_tip'))
        self.create_path_label.setText(t('fp_create_target'))
        self.create_folder_input.setPlaceholderText(t('fp_create_folder_placeholder'))
        self.create_folder_browse_btn.setText(t('fp_browse'))
        self.create_type_label.setText(t('fp_create_type'))
        self.create_folder_radio.setText(t('fp_create_type_folder'))
        self.create_file_radio.setText(t('fp_create_type_file'))
        self.create_ext_label.setText(t('fp_create_ext_label'))
        self.skip_existing_check.setText(t('fp_create_skip_existing'))
        self.create_preview_label.setText(t('fp_create_preview'))
        self.create_status_label.setText(t('fp_create_status_ready'))

        # 更新底部按钮文本（不触发模式切换）
        if self.current_mode == 'extract':
            self.process_btn.setText(t('fp_export'))
        elif self.current_mode == 'rename':
            self.process_btn.setText(t('fp_rename_start'))
        elif self.current_mode == 'create':
            self.process_btn.setText(t('fp_create_start'))