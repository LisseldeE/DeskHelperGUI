# -*- coding: utf-8 -*-
"""
DeskHelperGUI 文件加密功能模块
提供文件加密、解密功能
使用AES-256-GCM加密算法
"""

import os
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QFrame, QListWidget, QListWidgetItem,
    QAbstractItemView, QSizePolicy, QFileDialog, QApplication, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t
from ui_components import AnimatedButton

# cryptography延迟导入
HAS_CRYPTOGRAPHY = None

# 盐值大小（字节）
SALT_SIZE = 16


class FileListItemWidget(QFrame):
    """文件列表项widget，包含文件名和删除按钮"""

    delete_requested = pyqtSignal(int)  # (行号)

    def __init__(self, file_path, row_index, is_encrypted=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.row_index = row_index
        self.is_encrypted = is_encrypted
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

        # 加密状态图标
        status_label = QLabel()
        if self.is_encrypted:
            status_label.setText("🔒")
            status_label.setStyleSheet("color: #fa5252; font-size: 12px;")
        else:
            status_label.setText("📄")
            status_label.setStyleSheet("color: #495057; font-size: 12px;")
        status_label.setFixedWidth(20)
        layout.addWidget(status_label)

        # 文件名标签
        file_name = os.path.basename(self.file_path)
        self.name_label = QLabel(file_name)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                background-color: transparent;
                padding: 0px 4px;
            }
        """)
        self.name_label.setToolTip(self.file_path)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_label.setFixedHeight(24)
        layout.addWidget(self.name_label)

        # 删除按钮
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
        self.delete_requested.emit(self.row_index)

    def update_row_index(self, new_index):
        self.row_index = new_index


class DragDropListWidget(QListWidget):
    """支持拖拽导入的文件列表widget"""

    files_dropped = pyqtSignal(list)  # (文件列表)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        if files:
            self.files_dropped.emit(files)


class FileEncryptWidget(QWidget):
    """文件加密功能界面"""

    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)
    # 成功信号（用于显示成功横幅）
    success_requested = pyqtSignal(str)
    
    # 进度更新信号
    progress_updated = pyqtSignal(int)
    # UI重置信号（用于子线程完成后通知主线程重置UI）
    reset_ui_requested = pyqtSignal()

    @staticmethod
    def _check_cryptography():
        """延迟检测cryptography库"""
        global HAS_CRYPTOGRAPHY
        if HAS_CRYPTOGRAPHY is None:
            try:
                from cryptography.fernet import Fernet
                HAS_CRYPTOGRAPHY = True
            except ImportError:
                HAS_CRYPTOGRAPHY = False
        return HAS_CRYPTOGRAPHY

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.file_list = []  # 文件列表 [(path, is_encrypted)]
        self.is_processing = False
        self._cancel_requested = False  # 取消标志
        self._loading_config = False
        self.list_item_widgets = {}
        self._password_visible = False
        self._confirm_visible = False

        set_language(lang)
        self._init_ui()
        self._load_config()
        self.progress_updated.connect(self.progress_bar.setValue)
        self.reset_ui_requested.connect(self._reset_ui)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 左右分割布局
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：文件列表
        left_panel = self._create_file_list_panel()
        left_panel.setMinimumWidth(300)
        splitter.addWidget(left_panel)
        
        # 右侧：密码输入
        right_panel = self._create_password_panel()
        right_panel.setMinimumWidth(260)
        right_panel.setMaximumWidth(400)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter, 1)

        # 按钮区域
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_file_list_panel(self):
        """创建文件列表面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # 标题和按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        self.list_label = QLabel(t('encrypt_file_list'))
        self.list_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(self.list_label)
        
        header_layout.addStretch()
        
        # 浏览按钮
        self.browse_btn = AnimatedButton(t('encrypt_browse'))
        self.browse_btn.setMinimumWidth(75)
        self.browse_btn.setFixedHeight(32)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
            QPushButton:pressed {
                background-color: #1c7ed6;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        header_layout.addWidget(self.browse_btn)

        # 清空按钮
        self.clear_btn = AnimatedButton(t('encrypt_clear'))
        self.clear_btn.setMinimumWidth(75)
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 12px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_list)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)

        # 提示文本
        self.tip_label = QLabel(t('encrypt_import_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        layout.addWidget(self.tip_label)

        # 文件列表
        self.file_list_widget = DragDropListWidget()
        self.file_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
            }
        """)
        self.file_list_widget.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.file_list_widget, 1)

        # 文件数量和输出路径
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        self.file_count_label = QLabel(t('encrypt_file_count', 0))
        self.file_count_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.file_count_label)
        
        info_layout.addStretch()
        
        self.save_path_label = QLabel(t('encrypt_output_path', ''))
        self.save_path_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.save_path_label)
        
        layout.addLayout(info_layout)

        panel.setLayout(layout)
        return panel

    def _create_password_panel(self):
        """创建密码输入面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setAlignment(Qt.AlignTop)  # 内容由上至下布局

        # 空状态提示（无文件时显示）
        self.empty_hint_label = QLabel(t('encrypt_hint_no_file'))
        self.empty_hint_label.setStyleSheet("color: #868e96; font-size: 13px; background: transparent;")
        self.empty_hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_hint_label)

        # 密码输入区域容器（有文件时显示）
        self.password_content_widget = QFrame()
        self.password_content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        self.title_label = QLabel(t('encrypt_password_title'))
        self.title_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.title_label)

        # 密码输入行
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)
        
        self.pwd_label = QLabel(t('encrypt_password'))
        self.pwd_label.setStyleSheet("color: #495057; font-size: 12px; background: transparent;")
        self.pwd_label.setFixedWidth(50)
        pwd_row.addWidget(self.pwd_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(t('encrypt_password_placeholder'))
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self._on_password_changed)
        pwd_row.addWidget(self.password_input)
        
        # 小眼睛按钮
        self.eye_btn = AnimatedButton("👁")
        self.eye_btn.setFixedSize(28, 28)
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #868e96;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                color: #495057;
            }
        """)
        self.eye_btn.clicked.connect(self._toggle_password_visibility)
        pwd_row.addWidget(self.eye_btn)
        
        content_layout.addLayout(pwd_row)

        # 确认密码行（初始隐藏）
        self.confirm_row_widget = QFrame()
        self.confirm_row_widget.setStyleSheet("background: transparent; border: none;")
        confirm_row = QHBoxLayout()
        confirm_row.setSpacing(8)
        confirm_row.setContentsMargins(0, 0, 0, 0)
        
        self.confirm_label = QLabel(t('encrypt_confirm_password'))
        self.confirm_label.setStyleSheet("color: #495057; font-size: 12px; background: transparent;")
        self.confirm_label.setFixedWidth(50)
        confirm_row.addWidget(self.confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(t('encrypt_confirm_placeholder'))
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.textChanged.connect(self._on_confirm_changed)
        confirm_row.addWidget(self.confirm_input)
        
        self.confirm_row_widget.setLayout(confirm_row)
        self.confirm_row_widget.setVisible(False)
        content_layout.addWidget(self.confirm_row_widget)

        # 提示信息
        self.password_hint_label = QLabel()
        self.password_hint_label.setStyleSheet("color: #868e96; font-size: 11px; background: transparent;")
        self.password_hint_label.setAlignment(Qt.AlignCenter)
        self.password_hint_label.setWordWrap(True)
        content_layout.addWidget(self.password_hint_label)

        self.password_content_widget.setLayout(content_layout)
        self.password_content_widget.setVisible(False)
        layout.addWidget(self.password_content_widget)

        layout.addStretch()
        
        panel.setLayout(layout)
        return panel

    def _create_buttons(self, parent_layout):
        """创建底部按钮区域"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # 进度条容器（固定高度占位，防止进度条显隐时布局跳动）
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
        self.process_btn = AnimatedButton(t('encrypt_encrypt'))
        self.process_btn.setFixedSize(120, 34)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #adb5bd;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #868e96;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.process_btn)

        parent_layout.addLayout(btn_layout)

    def _load_config(self):
        """加载配置"""
        if self._loading_config:
            return
        self._loading_config = True
        
        try:
            if self.config:
                save_path = self.config.get_save_path()
                if save_path:
                    self.save_path_label.setText(t('encrypt_output_path', save_path.replace('\\', '/')))
        finally:
            self._loading_config = False

    def _browse_file(self):
        """浏览选择文件"""
        file_paths = QFileDialog.getOpenFileNames(
            self,
            t('encrypt_select_file'),
            "",
            f"{t('encrypt_all_files')} (*.*)"
        )[0]
        
        if file_paths:
            self._add_files(file_paths)

    def _on_files_dropped(self, files):
        """拖拽导入文件"""
        self._add_files(files)

    def _add_files(self, files):
        """添加文件到列表"""
        for file_path in files:
            # 检查是否已存在
            if not any(f[0] == file_path for f in self.file_list):
                # 检测是否为加密文件（.enc后缀）
                is_encrypted = file_path.endswith('.enc')
                self.file_list.append((file_path, is_encrypted))
        
        self._update_file_list()
        self._update_ui_state()

    def _update_file_list(self):
        """更新文件列表显示"""
        self.file_list_widget.clear()
        self.list_item_widgets.clear()

        for i, (file_path, is_encrypted) in enumerate(self.file_list):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 28))
            self.file_list_widget.addItem(item)
            
            item_widget = FileListItemWidget(file_path, i, is_encrypted)
            item_widget.delete_requested.connect(self._on_delete_item)
            self.file_list_widget.setItemWidget(item, item_widget)
            self.list_item_widgets[i] = item_widget

        # 更新文件数量
        self.file_count_label.setText(t('encrypt_file_count', len(self.file_list)))

    def _on_delete_item(self, row_index):
        """删除文件项"""
        if row_index < len(self.file_list):
            self.file_list.pop(row_index)
            self._update_file_list()
            self._update_ui_state()

    def _clear_list(self):
        """清空文件列表"""
        self.file_list.clear()
        self._update_file_list()
        self._update_ui_state()

    def _update_ui_state(self):
        """更新UI状态"""
        if not self.file_list:
            # 无文件：显示空状态提示，隐藏密码输入区域
            self.empty_hint_label.setVisible(True)
            self.password_content_widget.setVisible(False)
            self.process_btn.setEnabled(False)
            self.process_btn.setText(t('encrypt_encrypt'))
            self.process_btn.setStyleSheet("""
                QPushButton {
                    background-color: #adb5bd;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                }
            """)
            return

        # 有文件：隐藏空状态提示，显示密码输入区域
        self.empty_hint_label.setVisible(False)
        self.password_content_widget.setVisible(True)

        # 检查所有文件是否都是加密文件
        all_encrypted = all(f[1] for f in self.file_list)
        all_normal = all(not f[1] for f in self.file_list)

        if all_encrypted:
            # 解密模式
            self.confirm_row_widget.setVisible(False)
            self.password_hint_label.setText(t('encrypt_hint_decrypt'))
            self.process_btn.setText(t('encrypt_decrypt'))
            self.process_btn.setStyleSheet("""
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
            """)
            # 解密模式：有密码即可
            self.process_btn.setEnabled(len(self.password_input.text()) > 0)
        elif all_normal:
            # 加密模式
            self.process_btn.setText(t('encrypt_encrypt'))
            
            password = self.password_input.text()
            confirm = self.confirm_input.text()
            
            # 显示/隐藏确认密码框
            if password:
                if not self.confirm_row_widget.isVisible():
                    self.confirm_row_widget.setVisible(True)
                    self._animate_confirm_show()
                self.password_hint_label.setText(t('encrypt_hint_encrypt'))
            else:
                if self.confirm_row_widget.isVisible():
                    self._animate_confirm_hide()
                self.password_hint_label.setText(t('encrypt_hint_enter_password'))
            
            # 检查密码是否一致
            if password and confirm and password == confirm:
                self.process_btn.setEnabled(True)
                self.process_btn.setStyleSheet("""
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
                """)
                self.password_hint_label.setText(t('encrypt_hint_ready'))
            elif password and confirm and password != confirm:
                self.process_btn.setEnabled(False)
                self.process_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #adb5bd;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 13px;
                        font-weight: 500;
                    }
                """)
                self.password_hint_label.setText(t('encrypt_hint_password_mismatch'))
            else:
                self.process_btn.setEnabled(False)
                self.process_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #adb5bd;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 13px;
                        font-weight: 500;
                    }
                """)
        else:
            # 混合文件（加密和普通文件混合）
            self.confirm_row_widget.setVisible(False)
            self.password_hint_label.setText(t('encrypt_mixed_files'))
            self.process_btn.setEnabled(False)
            self.process_btn.setText(t('encrypt_encrypt'))
            self.warning_requested.emit(t('encrypt_mixed_files'))

    def _animate_confirm_show(self):
        """确认密码框显示动画"""
        self.confirm_row_widget.setFixedHeight(0)
        target_height = 36
        
        def animate_step():
            current = self.confirm_row_widget.height()
            if current < target_height:
                self.confirm_row_widget.setFixedHeight(current + 4)
                QTimer.singleShot(10, animate_step)
        
        animate_step()

    def _animate_confirm_hide(self):
        """确认密码框隐藏动画"""
        target_height = 0
        
        def animate_step():
            current = self.confirm_row_widget.height()
            if current > target_height:
                self.confirm_row_widget.setFixedHeight(current - 4)
                QTimer.singleShot(10, animate_step)
            else:
                self.confirm_row_widget.setVisible(False)
        
        animate_step()

    def _toggle_password_visibility(self):
        """切换密码可见性"""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🔒")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁")

    def _on_password_changed(self):
        """密码输入变化"""
        self._update_ui_state()

    def _on_confirm_changed(self):
        """确认密码变化"""
        self._update_ui_state()

    def _start_processing(self):
        """开始处理或取消操作"""
        if self.is_processing:
            # 取消操作
            self._cancel_requested = True
            self.process_btn.setEnabled(False)
            self.process_btn.setText(t('encrypt_canceling'))
            return

        if not self.file_list:
            return

        # 检查cryptography库
        if not self._check_cryptography():
            self.warning_requested.emit(t('encrypt_no_library'))
            return

        password = self.password_input.text()
        if not password:
            self.warning_requested.emit(t('encrypt_no_password'))
            return

        self.is_processing = True
        self._cancel_requested = False
        self.process_btn.setText(t('encrypt_cancel'))
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 获取保存路径
        save_path = self.config.get_save_path() if self.config else ''

        # 在线程中执行
        thread = threading.Thread(
            target=self._process_files,
            args=(password, save_path)
        )
        thread.start()

    def _process_files(self, password, save_path):
        """处理文件（加密/解密）- 支持大文件和取消操作"""
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        import base64
        import struct

        CHUNK_SIZE = 64 * 1024 * 1024  # 64MB 分块大小
        LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB 大文件阈值

        # 计算总字节数用于进度
        total_bytes = 0
        for file_path, _ in self.file_list:
            try:
                total_bytes += os.path.getsize(file_path)
            except:
                pass
        
        if total_bytes == 0:
            total_bytes = 1  # 防止除零
        
        processed_bytes = 0
        success_count = 0
        error_msg = ''
        temp_files = []  # 临时文件列表，用于取消时清理

        try:
            for i, (file_path, is_encrypted) in enumerate(self.file_list):
                if self._cancel_requested:
                    error_msg = t('encrypt_cancelled')
                    break

                try:
                    file_size = os.path.getsize(file_path)
                    
                    # 生成输出文件名
                    base_name = os.path.basename(file_path)
                    if is_encrypted:
                        if base_name.endswith('.enc'):
                            output_name = base_name[:-4]
                        else:
                            output_name = base_name + '_decrypted'
                    else:
                        output_name = base_name + '.enc'
                    
                    output_path = os.path.join(save_path, output_name).replace('\\', '/')
                    output_path = self._get_unique_filepath(output_path)
                    
                    # 对于大文件，使用 AES-CTR 分块加密
                    use_chunked = file_size > LARGE_FILE_THRESHOLD
                    
                    if use_chunked:
                        # AES-CTR 分块加密/解密
                        result = self._process_large_file(
                            file_path, output_path, password, is_encrypted,
                            CHUNK_SIZE, processed_bytes, total_bytes, temp_files
                        )
                        if result is None:  # 取消
                            error_msg = t('encrypt_cancelled')
                            break
                        elif result is False:  # 错误
                            error_msg = t('encrypt_error', '处理失败')
                            break
                        processed_bytes = result
                    else:
                        # Fernet 加密（小文件）
                        with open(file_path, 'rb') as f:
                            data = f.read()

                        if is_encrypted:
                            if len(data) < SALT_SIZE:
                                error_msg = t('encrypt_invalid_format')
                                break
                            
                            salt = data[:SALT_SIZE]
                            encrypted_data = data[SALT_SIZE:]
                            
                            kdf = PBKDF2HMAC(
                                algorithm=hashes.SHA256(),
                                length=32,
                                salt=salt,
                                iterations=100000,
                            )
                            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                            fernet = Fernet(key)
                            
                            decrypted = fernet.decrypt(encrypted_data)
                            
                            with open(output_path, 'wb') as f:
                                f.write(decrypted)
                        else:
                            salt = os.urandom(SALT_SIZE)
                            
                            kdf = PBKDF2HMAC(
                                algorithm=hashes.SHA256(),
                                length=32,
                                salt=salt,
                                iterations=100000,
                            )
                            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                            fernet = Fernet(key)
                            
                            encrypted_data = fernet.encrypt(data)
                            
                            with open(output_path, 'wb') as f:
                                f.write(salt)
                                f.write(encrypted_data)
                        
                        processed_bytes += file_size
                        progress = int(processed_bytes / total_bytes * 100)
                        self.progress_updated.emit(progress)

                    success_count += 1
                    
                except InvalidToken:
                    error_msg = t('encrypt_wrong_password')
                    break
                except PermissionError:
                    error_msg = t('encrypt_permission_error', os.path.basename(file_path))
                    break
                except FileNotFoundError:
                    error_msg = t('encrypt_file_not_found', os.path.basename(file_path))
                    break
                except Exception as e:
                    error_msg = t('encrypt_error', str(e))
                    break

            # 完成
            if self._cancel_requested:
                # 清理临时文件
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
                self.warning_requested.emit(error_msg)
            elif success_count == len(self.file_list):
                self.success_requested.emit(t('encrypt_success', success_count, save_path.replace('\\', '/')))
            else:
                self.warning_requested.emit(error_msg)

        finally:
            self.is_processing = False
            self.reset_ui_requested.emit()

    def _process_large_file(self, file_path, output_path, password, is_encrypted, 
                            chunk_size, processed_bytes, total_bytes, temp_files):
        """处理大文件（AES-CTR 分块加密）"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        import struct

        temp_output = output_path + '.tmp'
        temp_files.append(temp_output)

        try:
            if is_encrypted:
                # 解密大文件
                with open(file_path, 'rb') as f_in:
                    # 读取头部：salt(16) + nonce(16) + chunk_size(8)
                    header = f_in.read(SALT_SIZE + 16 + 8)
                    if len(header) < SALT_SIZE + 16 + 8:
                        return False
                    
                    salt = header[:SALT_SIZE]
                    nonce = header[SALT_SIZE:SALT_SIZE + 16]
                    
                    # 派生密钥
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=100000,
                    )
                    key = kdf.derive(password.encode())
                    
                    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                    decryptor = cipher.decryptor()
                    
                    with open(temp_output, 'wb') as f_out:
                        while True:
                            if self._cancel_requested:
                                return None
                            
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            
                            decrypted_chunk = decryptor.update(chunk)
                            f_out.write(decrypted_chunk)
                            
                            processed_bytes += len(chunk)
                            progress = int(processed_bytes / total_bytes * 100)
                            self.progress_updated.emit(progress)
                        
                        # 最终处理
                        final_data = decryptor.finalize()
                        if final_data:
                            f_out.write(final_data)
            else:
                # 加密大文件
                salt = os.urandom(SALT_SIZE)
                nonce = os.urandom(16)  # CTR 模式 nonce
                
                # 派生密钥
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode())
                
                cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                encryptor = cipher.encryptor()
                
                with open(temp_output, 'wb') as f_out:
                    # 写入头部
                    f_out.write(salt)
                    f_out.write(nonce)
                    f_out.write(struct.pack('>Q', chunk_size))
                    
                    with open(file_path, 'rb') as f_in:
                        while True:
                            if self._cancel_requested:
                                return None
                            
                            chunk = f_in.read(chunk_size)
                            if not chunk:
                                break
                            
                            encrypted_chunk = encryptor.update(chunk)
                            f_out.write(encrypted_chunk)
                            
                            processed_bytes += len(chunk)
                            progress = int(processed_bytes / total_bytes * 100)
                            self.progress_updated.emit(progress)
                        
                        # 最终处理
                        final_data = encryptor.finalize()
                        if final_data:
                            f_out.write(final_data)
            
            # 重命名临时文件为最终文件
            os.rename(temp_output, output_path)
            temp_files.remove(temp_output)
            
            return processed_bytes
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
            raise e

    def _get_unique_filepath(self, filepath):
        """获取唯一文件路径"""
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(f"{base} ({counter}){ext}"):
            counter += 1
        return f"{base} ({counter}){ext}"

    def _reset_ui(self):
        """重置UI"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        # 清除密码输入框
        self.password_input.clear()
        self.confirm_input.clear()
        self.confirm_row_widget.setVisible(False)
        # 清空文件列表
        self.file_list.clear()
        self._update_file_list()
        self.process_btn.setEnabled(True)
        self._update_ui_state()

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        if files:
            self._add_files(files)

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)
        self._update_ui_text()

    def _update_ui_text(self):
        """更新UI文本"""
        self.list_label.setText(t('encrypt_file_list'))
        self.tip_label.setText(t('encrypt_import_tip'))
        self.file_count_label.setText(t('encrypt_file_count', len(self.file_list)))
        
        if self.config:
            save_path = self.config.get_save_path()
            if save_path:
                self.save_path_label.setText(t('encrypt_output_path', save_path.replace('\\', '/')))
        
        self.browse_btn.setText(t('encrypt_browse'))
        self.clear_btn.setText(t('encrypt_clear'))
        
        # 更新密码面板文本
        self.title_label.setText(t('encrypt_password_title'))
        self.pwd_label.setText(t('encrypt_password'))
        self.password_input.setPlaceholderText(t('encrypt_password_placeholder'))
        self.confirm_label.setText(t('encrypt_confirm_password'))
        self.confirm_input.setPlaceholderText(t('encrypt_confirm_placeholder'))
        
        # 更新空状态提示
        self.empty_hint_label.setText(t('encrypt_hint_no_file'))
        
        # 更新密码提示（根据当前状态）
        if self.file_list:
            # 有文件时，调用 _on_password_changed 更新提示
            self._on_password_changed()
        else:
            # 无文件时，显示空状态提示
            self.password_hint_label.setText(t('encrypt_hint_no_file'))
        
        # 更新按钮文本
        if self.file_list and all(f[1] for f in self.file_list):
            self.process_btn.setText(t('encrypt_decrypt'))
        else:
            self.process_btn.setText(t('encrypt_encrypt'))