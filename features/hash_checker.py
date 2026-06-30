# -*- coding: utf-8 -*-
"""
DeskHelperGUI 哈希校验功能模块
计算文件哈希值并支持校验比对
"""

import os
import hashlib
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t
from ui_components import AnimatedButton


class HashCheckerWidget(QWidget):
    """哈希校验功能界面"""

    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)

    # 哈希算法映射
    HASH_ALGORITHMS = {
        'MD5': hashlib.md5,
        'SHA-1': hashlib.sha1,
        'SHA-256': hashlib.sha256,
        'SHA-384': hashlib.sha384,
        'SHA-512': hashlib.sha512,
    }

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.selected_file = ""
        self.current_hash = ""
        self.is_calculating = False

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        self.setAcceptDrops(True)  # 启用拖拽

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 文件选择区域
        self._create_file_section(layout)

        # 哈希值显示区域
        self._create_hash_section(layout)

        # 校验区域（包含输入和比对结果）
        self._create_verify_section(layout)

        # 底部添加弹性空间
        layout.addStretch()

        # 底栏显示导出路径
        self._create_footer(layout)

        self.setLayout(layout)

    def _create_file_section(self, parent_layout):
        """创建文件选择区域"""
        self.file_group = QGroupBox(t('hash_file_group'))
        file_layout = QVBoxLayout()
        file_layout.setContentsMargins(10, 15, 10, 15)
        file_layout.setSpacing(10)

        # 文件路径输入行
        path_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText(t('hash_file_placeholder'))
        self.file_input.setReadOnly(True)
        self.file_input.setStyleSheet("""
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
        path_layout.addWidget(self.file_input, 1)

        # 浏览按钮
        self.browse_btn = AnimatedButton(t('hash_browse'))
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
            QPushButton:pressed {
                background-color: #1c7ed6;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(self.browse_btn)

        # 清空按钮
        self.clear_btn = AnimatedButton(t('hash_clear'))
        self.clear_btn.setMinimumWidth(50)
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #868e96;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
            QPushButton:pressed {
                background-color: #343a40;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_file)
        path_layout.addWidget(self.clear_btn)

        file_layout.addLayout(path_layout)

        # 提示标签
        self.tip_label = QLabel(t('hash_file_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        self.tip_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.tip_label)

        self.file_group.setLayout(file_layout)
        parent_layout.addWidget(self.file_group)

    def _create_hash_section(self, parent_layout):
        """创建哈希值显示区域"""
        self.hash_group = QGroupBox(t('hash_value_group'))
        hash_layout = QVBoxLayout()
        hash_layout.setContentsMargins(10, 15, 10, 15)
        hash_layout.setSpacing(10)

        # 哈希模式选择行
        mode_layout = QHBoxLayout()
        self.mode_label = QLabel(t('hash_mode_label'))
        self.mode_label.setStyleSheet("font-size: 13px; color: #495057;")
        mode_layout.addWidget(self.mode_label)

        self.hash_mode_combo = QComboBox()
        self.hash_mode_combo.addItems(list(self.HASH_ALGORITHMS.keys()))
        self.hash_mode_combo.setFixedHeight(30)
        self.hash_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
                min-width: 100px;
            }
            QComboBox:hover {
                background-color: #dee2e6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ced4da;
                selection-background-color: #339af0;
                selection-color: white;
            }
        """)
        self.hash_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.hash_mode_combo)
        mode_layout.addStretch()
        hash_layout.addLayout(mode_layout)

        # 哈希值显示行
        value_layout = QHBoxLayout()
        self.hash_value_input = QLineEdit()
        self.hash_value_input.setReadOnly(True)
        self.hash_value_input.setPlaceholderText(t('hash_value_placeholder'))
        self.hash_value_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        value_layout.addWidget(self.hash_value_input, 1)

        # 复制按钮
        self.copy_btn = AnimatedButton(t('hash_copy'))
        self.copy_btn.setMinimumWidth(50)
        self.copy_btn.setFixedHeight(36)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
            QPushButton:pressed {
                background-color: #37b24d;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_hash)
        value_layout.addWidget(self.copy_btn)

        hash_layout.addLayout(value_layout)
        self.hash_group.setLayout(hash_layout)
        parent_layout.addWidget(self.hash_group)

    def _create_verify_section(self, parent_layout):
        """创建校验区域（包含输入和比对结果）"""
        self.verify_group = QGroupBox(t('hash_verify_group'))
        verify_layout = QVBoxLayout()
        verify_layout.setContentsMargins(10, 15, 10, 15)
        verify_layout.setSpacing(10)

        # 校验输入框
        input_layout = QHBoxLayout()
        self.verify_input = QLineEdit()
        self.verify_input.setPlaceholderText(t('hash_verify_placeholder'))
        self.verify_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.verify_input.textChanged.connect(self._on_verify_changed)
        input_layout.addWidget(self.verify_input, 1)

        # 清空按钮
        self.verify_clear_btn = AnimatedButton(t('hash_clear'))
        self.verify_clear_btn.setMinimumWidth(50)
        self.verify_clear_btn.setFixedHeight(36)
        self.verify_clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #868e96;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
            QPushButton:pressed {
                background-color: #343a40;
            }
        """)
        self.verify_clear_btn.clicked.connect(lambda: self.verify_input.clear())
        input_layout.addWidget(self.verify_clear_btn)

        verify_layout.addLayout(input_layout)

        # 比对结果显示
        self.result_label = QLabel(t('hash_result_waiting'))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #868e96;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)
        verify_layout.addWidget(self.result_label)

        self.verify_group.setLayout(verify_layout)
        parent_layout.addWidget(self.verify_group)

    def _create_footer(self, parent_layout):
        """创建底栏"""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #adb5bd; font-size: 11px;")
        footer_layout.addWidget(self.path_label)

        parent_layout.addLayout(footer_layout)

    def _load_config(self):
        """加载配置"""
        if self.config:
            # 加载哈希模式
            hash_mode = self.config.get('hash_checker.mode', 'MD5')
            index = self.hash_mode_combo.findText(hash_mode)
            if index >= 0:
                self.hash_mode_combo.setCurrentIndex(index)

            # 加载全局保存路径显示
            save_path = self.config.get_save_path()
            if save_path:
                self.path_label.setText(f"{t('settings_save_path')}: {save_path}")
            else:
                self.path_label.setText(f"{t('settings_save_path')}: {t('settings_no_path')}")

    def _save_config(self):
        """保存配置"""
        if self.config:
            self.config.set('hash_checker.mode', self.hash_mode_combo.currentText())
            self.config.save_config()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if not urls:
            return

        # 获取第一个文件
        first_path = urls[0].toLocalFile()
        if os.path.isfile(first_path):
            # 清除上次计算的哈希值
            self.current_hash = ""
            self.hash_value_input.clear()
            self._update_result('waiting')
            
            self.selected_file = first_path
            self.file_input.setText(first_path)
            self._calculate_hash()
        else:
            # 不是文件，显示提示
            self.warning_requested.emit(t('hash_file_only'))

    def _browse_file(self):
        """浏览选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t('hash_select_file'),
            "",
            t('hash_all_files')
        )
        if file_path:
            # 清除上次计算的哈希值
            self.current_hash = ""
            self.hash_value_input.clear()
            self._update_result('waiting')
            
            self.selected_file = file_path
            self.file_input.setText(file_path)
            self._calculate_hash()

    def _clear_file(self):
        """清空文件选择"""
        self.selected_file = ""
        self.current_hash = ""
        self.file_input.clear()
        self.hash_value_input.clear()
        self.verify_input.clear()
        self._update_result('waiting')

    def _on_mode_changed(self, mode):
        """哈希模式改变"""
        self._save_config()
        if self.selected_file and not self.is_calculating:
            self._calculate_hash()

    def _calculate_hash(self):
        """计算文件哈希值"""
        if not self.selected_file or self.is_calculating:
            return

        self.is_calculating = True
        self.hash_value_input.setText(t('hash_calculating'))
        self.copy_btn.setEnabled(False)

        # 在线程中计算
        def calculate():
            try:
                algorithm = self.hash_mode_combo.currentText()
                hash_func = self.HASH_ALGORITHMS[algorithm]

                with open(self.selected_file, 'rb') as f:
                    hasher = hash_func()
                    while chunk := f.read(8192):
                        hasher.update(chunk)
                    self.current_hash = hasher.hexdigest()

                # 在主线程更新UI
                QApplication.processEvents()
                self.hash_value_input.setText(self.current_hash)
                self.copy_btn.setEnabled(True)

                # 重新校验
                self._on_verify_changed(self.verify_input.text())

            except Exception as e:
                self.hash_value_input.setText(t('hash_calc_error'))
                self.current_hash = ""

            finally:
                self.is_calculating = False

        thread = threading.Thread(target=calculate, daemon=True)
        thread.start()

    def _copy_hash(self):
        """复制哈希值到剪贴板"""
        if self.current_hash:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_hash)
            self.warning_requested.emit(t('hash_copied'))

    def _on_verify_changed(self, text):
        """校验输入改变"""
        if not text.strip():
            self._update_result('waiting')
        elif not self.current_hash:
            self._update_result('no_hash')
        else:
            # 比较哈希值（忽略大小写）
            if text.strip().lower() == self.current_hash.lower():
                self._update_result('match')
            else:
                self._update_result('mismatch')

    def _update_result(self, status):
        """更新比对结果"""
        styles = {
            'waiting': {
                'text': t('hash_result_waiting'),
                'color': '#868e96',
                'bg': '#f8f9fa'
            },
            'no_hash': {
                'text': t('hash_result_no_hash'),
                'color': '#f59f00',
                'bg': '#fff3bf'
            },
            'match': {
                'text': t('hash_result_match'),
                'color': '#2f9e44',
                'bg': '#d3f9d8'
            },
            'mismatch': {
                'text': t('hash_result_mismatch'),
                'color': '#e03131',
                'bg': '#ffe3e3'
            }
        }

        style = styles.get(status, styles['waiting'])
        self.result_label.setText(style['text'])
        self.result_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 500;
                color: {style['color']};
                padding: 15px;
                background-color: {style['bg']};
                border-radius: 6px;
            }}
        """)

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)

        # 更新GroupBox标题
        self.file_group.setTitle(t('hash_file_group'))
        self.hash_group.setTitle(t('hash_value_group'))
        self.verify_group.setTitle(t('hash_verify_group'))

        # 更新输入框提示
        self.file_input.setPlaceholderText(t('hash_file_placeholder'))
        self.hash_value_input.setPlaceholderText(t('hash_value_placeholder'))
        self.verify_input.setPlaceholderText(t('hash_verify_placeholder'))

        # 更新按钮文本
        self.browse_btn.setText(t('hash_browse'))
        self.clear_btn.setText(t('hash_clear'))
        self.copy_btn.setText(t('hash_copy'))
        self.verify_clear_btn.setText(t('hash_clear'))

        # 更新标签
        self.mode_label.setText(t('hash_mode_label'))
        self.tip_label.setText(t('hash_file_tip'))

        # 更新结果状态文字
        current_status = 'waiting'
        if '成功' in self.result_label.text() or 'passed' in self.result_label.text().lower():
            current_status = 'match'
        elif '失败' in self.result_label.text() and '不匹配' in self.result_label.text() or 'mismatch' in self.result_label.text().lower():
            current_status = 'mismatch'
        elif '请先' in self.result_label.text() or 'calculate' in self.result_label.text().lower():
            current_status = 'no_hash'
        self._update_result(current_status)

        # 更新底栏
        save_path = self.config.get_save_path() if self.config else ''
        if save_path:
            self.path_label.setText(f"{t('settings_save_path')}: {save_path}")
        else:
            self.path_label.setText(f"{t('settings_save_path')}: {t('settings_no_path')}")