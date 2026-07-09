# -*- coding: utf-8 -*-
"""
DeskHelperGUI PDF工具功能模块
提供PDF文件合并、拆分、压缩功能
"""

import os
import threading
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QGroupBox, QComboBox, QCheckBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame, QSpinBox,
    QListWidget, QMessageBox, QFileDialog, QSplitter, QListWidgetItem,
    QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDrag

# pdf2docx延迟导入标志
PDF2DOCX_AVAILABLE = None

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton
from .utils import get_unique_filepath

# PyMuPDF延迟导入
HAS_PYMUPDF = None


class FileListItemWidget(QFrame):
    """文件列表项widget，包含文件名和删除按钮"""

    # 删除信号
    delete_requested = pyqtSignal(int)  # (行号)

    def __init__(self, file_path, row_index, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.row_index = row_index
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
        self.name_label.setToolTip(self.file_path)  # 鼠标悬停显示完整路径
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_label.setFixedHeight(24)
        layout.addWidget(self.name_label)

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
        self.delete_requested.emit(self.row_index)

    def update_row_index(self, new_index):
        """更新行号"""
        self.row_index = new_index


class DragDropListWidget(QListWidget):
    """支持拖拽排序的文件列表widget"""

    # 文件顺序改变信号
    order_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        """拖拽放下事件"""
        super().dropEvent(event)
        # 触发顺序改变信号
        self.order_changed.emit()


class PDFToolWidget(QWidget):
    """PDF工具功能界面"""

    # 操作完成信号
    operation_finished = pyqtSignal(bool, str)  # (成功, 消息)
    
    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)  # (警告消息)
    
    # 进度更新信号
    progress_updated = pyqtSignal(int)  # (进度值)

    @staticmethod
    def _check_pymupdf():
        """延迟检测PyMuPDF库"""
        global HAS_PYMUPDF
        if HAS_PYMUPDF is None:
            try:
                import fitz
                HAS_PYMUPDF = True
            except ImportError:
                HAS_PYMUPDF = False
        return HAS_PYMUPDF

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.file_list = []  # 文件列表
        self.is_processing = False
        self._loading_config = False
        self.list_item_widgets = {}  # 存储列表项widget的字典 {row: widget}

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        self.operation_finished.connect(self.on_operation_finished)
        self.progress_updated.connect(self.progress_bar.setValue)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 文件列表和操作设置区域（左右分割）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：文件列表
        left_panel = self._create_file_list_panel()
        left_panel.setMinimumWidth(300)
        splitter.addWidget(left_panel)
        
        # 右侧：操作设置
        right_panel = self._create_settings_panel()
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

        # 文件列表标题和浏览按钮（水平布局）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # 文件列表标题
        list_label = QLabel(t('pdf_file_list'))
        list_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(list_label)
        
        header_layout.addStretch()
        
        # 浏览按钮（放在标题右侧）
        self.browse_btn = AnimatedButton(t('pdf_browse'))
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

        # 清空列表按钮（放在浏览按钮右侧）
        self.clear_btn = AnimatedButton(t('pdf_clear'))
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
        self.tip_label = QLabel(t('pdf_import_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        layout.addWidget(self.tip_label)

        # 文件列表（使用支持拖拽排序的QListWidget）
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
        self.file_list_widget.order_changed.connect(self._on_order_changed)
        layout.addWidget(self.file_list_widget, 1)

        # 文件数量和输出路径显示（水平布局）
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        # 文件数量显示（左侧）
        self.file_count_label = QLabel(t('pdf_file_count', 0))
        self.file_count_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.file_count_label)
        
        info_layout.addStretch()
        
        # 输出路径显示（右侧）
        self.save_path_label = QLabel(t('pdf_output_path', ''))
        self.save_path_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.save_path_label)
        
        layout.addLayout(info_layout)

        panel.setLayout(layout)
        return panel

    def _create_settings_panel(self):
        """创建操作设置面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # 操作模式选择区域
        self.mode_group = QGroupBox(t('pdf_operation_mode'))
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(6)
        mode_layout.setContentsMargins(8, 10, 8, 10)

        # 创建单选按钮组
        self.operation_group = QButtonGroup(self)
        
        # 合并PDF
        self.merge_radio = QRadioButton(t('pdf_merge'))
        self.merge_radio.setChecked(True)
        self.merge_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.operation_group.addButton(self.merge_radio, 0)
        mode_layout.addWidget(self.merge_radio)

        # 拆分PDF
        self.split_radio = QRadioButton(t('pdf_split'))
        self.split_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.operation_group.addButton(self.split_radio, 1)
        mode_layout.addWidget(self.split_radio)

        # 压缩PDF
        self.compress_radio = QRadioButton(t('pdf_compress'))
        self.compress_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.operation_group.addButton(self.compress_radio, 2)
        mode_layout.addWidget(self.compress_radio)

        # 转Word
        self.word_radio = QRadioButton(t('pdf_to_word'))
        self.word_radio.setStyleSheet("""
            QRadioButton {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.operation_group.addButton(self.word_radio, 3)
        mode_layout.addWidget(self.word_radio)

        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)

        # 压缩设置区域（仅压缩模式时显示）
        self.compress_settings_group = QGroupBox(t('pdf_compress_settings'))
        compress_layout = QVBoxLayout()
        compress_layout.setSpacing(6)
        compress_layout.setContentsMargins(8, 10, 8, 10)

        # 压缩质量选择
        quality_label = QLabel(t('pdf_compress_quality'))
        quality_label.setStyleSheet("color: #495057; font-size: 13px;")
        compress_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            t('pdf_quality_high'),
            t('pdf_quality_medium'),
            t('pdf_quality_low')
        ])
        self.quality_combo.setFixedHeight(30)
        self.quality_combo.setStyleSheet("""
            QComboBox {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
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
            }
        """)
        compress_layout.addWidget(self.quality_combo)

        self.compress_settings_group.setLayout(compress_layout)
        self.compress_settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }
        """)
        self.compress_settings_group.setVisible(False)  # 默认隐藏
        layout.addWidget(self.compress_settings_group)

        # Word转换设置区域(仅转Word模式时显示)
        self.word_settings_group = QGroupBox(t('pdf_word_settings'))
        word_layout = QVBoxLayout()
        word_layout.setSpacing(6)
        word_layout.setContentsMargins(8, 10, 8, 10)

        # 页面范围选择
        page_range_label = QLabel(t('pdf_page_range'))
        page_range_label.setStyleSheet("color: #495057; font-size: 13px;")
        word_layout.addWidget(page_range_label)

        # 页面范围单选按钮组
        self.page_range_group = QButtonGroup(self)
        
        # 全部页面
        self.page_all_radio = QRadioButton(t('pdf_page_range_all'))
        self.page_all_radio.setChecked(True)
        self.page_all_radio.setStyleSheet("""
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
        self.page_range_group.addButton(self.page_all_radio, 0)
        word_layout.addWidget(self.page_all_radio)

        # 自定义范围
        self.page_custom_radio = QRadioButton(t('pdf_page_range_custom'))
        self.page_custom_radio.setStyleSheet("""
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
        self.page_range_group.addButton(self.page_custom_radio, 1)
        word_layout.addWidget(self.page_custom_radio)

        # 自定义范围输入框
        self.page_range_input = QLineEdit()
        self.page_range_input.setPlaceholderText(t('pdf_page_range_placeholder'))
        self.page_range_input.setFixedHeight(28)
        self.page_range_input.setStyleSheet("""
            QLineEdit {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
                background-color: white;
            }
        """)
        self.page_range_input.setEnabled(False)  # 默认禁用
        word_layout.addWidget(self.page_range_input)

        # 连接页面范围单选按钮变化信号
        self.page_range_group.buttonClicked.connect(self._on_page_range_changed)

        # 格式说明
        self.format_label = QLabel(t('pdf_format_quality'))
        self.format_label.setStyleSheet("color: #495057; font-size: 13px; margin-top: 6px;")
        word_layout.addWidget(self.format_label)

        # 格式说明文本
        self.format_desc = QLabel(t('pdf_format_desc'))
        self.format_desc.setStyleSheet("color: #868e96; font-size: 12px; padding: 0px 4px;")
        self.format_desc.setWordWrap(True)
        word_layout.addWidget(self.format_desc)

        self.word_settings_group.setLayout(word_layout)
        self.word_settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }
        """)
        self.word_settings_group.setVisible(False)  # 默认隐藏
        layout.addWidget(self.word_settings_group)

        # 连接单选按钮变化信号
        self.operation_group.buttonClicked.connect(self._on_operation_changed)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_buttons(self, parent_layout):
        """创建操作按钮和进度条"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

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

        # 开始处理按钮
        self.process_btn = AnimatedButton(t('pdf_start'))
        self.process_btn.setFixedSize(120, 34)
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
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        self.process_btn.clicked.connect(self._start_processing)
        btn_layout.addWidget(self.process_btn)

        parent_layout.addLayout(btn_layout)

    def _load_config(self):
        """加载配置"""
        if self._loading_config:
            return
        self._loading_config = True
        
        try:
            # 加载全局保存路径
            if self.config:
                save_path = self.config.get_save_path()
                if save_path:
                    # 使用 "/" 作为路径分隔符
                    self.save_path_label.setText(t('pdf_output_path', save_path.replace('\\', '/')))
        finally:
            self._loading_config = False

    def _browse_file(self):
        """浏览选择PDF文件"""
        file_paths = QFileDialog.getOpenFileNames(
            self,
            t('pdf_select_file'),
            "",
            f"{t('pdf_files')} (*.pdf);;{t('pdf_all_files')} (*.*)"
        )[0]
        
        if file_paths:
            self.file_list.extend(file_paths)
            self._update_file_list()

    def _on_operation_changed(self, button):
        """操作模式变化"""
        # 压缩模式时显示压缩设置
        if button == self.compress_radio:
            self.compress_settings_group.setVisible(True)
            self.word_settings_group.setVisible(False)
        # 转Word模式时显示Word设置
        elif button == self.word_radio:
            self.compress_settings_group.setVisible(False)
            self.word_settings_group.setVisible(True)
        else:
            self.compress_settings_group.setVisible(False)
            self.word_settings_group.setVisible(False)

    def _on_page_range_changed(self, button):
        """页面范围选择变化"""
        # 自定义范围时启用输入框
        if button == self.page_custom_radio:
            self.page_range_input.setEnabled(True)
        else:
            self.page_range_input.setEnabled(False)

    def _update_file_list(self):
        """更新文件列表显示"""
        # 清空旧的列表项
        self.file_list_widget.clear()
        self.list_item_widgets.clear()

        # 创建新的列表项
        for i, file_path in enumerate(self.file_list):
            # 创建QListWidgetItem
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 28))  # 设置item高度
            self.file_list_widget.addItem(item)
            
            # 创建自定义widget
            item_widget = FileListItemWidget(file_path, i)
            item_widget.delete_requested.connect(self._on_delete_item)
            
            # 将widget嵌入到item中
            self.file_list_widget.setItemWidget(item, item_widget)
            self.list_item_widgets[i] = item_widget
        
        # 更新文件数量
        self.file_count_label.setText(t('pdf_file_count', len(self.file_list)))

    def _on_order_changed(self):
        """文件顺序改变回调"""
        # 更新file_list的顺序
        new_file_list = []
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            widget = self.file_list_widget.itemWidget(item)
            if widget:
                new_file_list.append(widget.file_path)
                widget.update_row_index(i)
        
        self.file_list = new_file_list

    def _on_delete_item(self, row_index):
        """删除文件项"""
        if row_index >= 0 and row_index < len(self.file_list):
            del self.file_list[row_index]
            self._update_file_list()

    def _clear_list(self):
        """清空文件列表"""
        self.file_list = []
        self._update_file_list()

    def _start_processing(self):
        """开始处理"""
        # 检查所需库
        operation = self.operation_group.checkedId()
        
        # 合并、拆分、压缩需要PyMuPDF
        if operation in [0, 1, 2]:
            if not self._check_pymupdf():
                self.warning_requested.emit(t('pdf_need_pymupdf'))
                return
        
        # 转Word需要pdf2docx
        if operation == 3:
            try:
                import pdf2docx
            except ImportError:
                self.warning_requested.emit(t('pdf_need_docx_lib'))
                return

        # 验证文件列表
        if not self.file_list:
            self.warning_requested.emit(t('pdf_no_files'))
            return
        
        # 获取全局保存路径
        save_path = self.config.get_save_path() if self.config else ""
        if not save_path:
            self.warning_requested.emit(t('pdf_no_save_path'))
            return
        
        # 确保保存路径存在
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                self.warning_requested.emit(t('pdf_create_path_failed', str(e)))
                return

        # 获取操作参数
        quality_index = self.quality_combo.currentIndex()
        page_range_type = self.page_range_group.checkedId()
        page_range_text = self.page_range_input.text() if page_range_type == 1 else ""

        # 禁用按钮,显示进度条
        self.process_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.is_processing = True

        # 在新线程中执行操作
        thread = threading.Thread(
            target=self._process_thread,
            args=(operation, save_path, quality_index, page_range_type, page_range_text),
            daemon=True
        )
        thread.start()

    def _process_thread(self, operation, save_path, quality_index, page_range_type=0, page_range_text=""):
        """处理线程"""
        try:
            import fitz  # PyMuPDF
            
            if operation == 0:  # 合并PDF
                self._merge_pdfs(save_path)
            elif operation == 1:  # 拆分PDF
                self._split_pdfs(save_path)
            elif operation == 2:  # 压缩PDF
                self._compress_pdfs(save_path, quality_index)
            elif operation == 3:  # 转Word
                self._pdf_to_word(save_path, page_range_type, page_range_text)
        except Exception as e:
            self.operation_finished.emit(False, str(e))
        finally:
            # 恢复UI
            self.is_processing = False

    def _merge_pdfs(self, save_path):
        """合并PDF文件"""
        import fitz
        
        try:
            # 创建合并后的PDF
            merged_pdf = fitz.open()
            
            total_files = len(self.file_list)
            for i, file_path in enumerate(self.file_list):
                try:
                    pdf = fitz.open(file_path)
                    merged_pdf.insert_pdf(pdf)
                    pdf.close()
                    
                    # 更新进度
                    progress = int((i + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                except Exception as e:
                    # 跳过无法处理的文件
                    continue
            
            # 保存合并后的PDF
            output_name = "merged.pdf"
            output_path = os.path.join(save_path, output_name)
            
            # 处理文件名冲突（Windows风格：文件名（1））
            output_path = get_unique_filepath(output_path)
            
            merged_pdf.save(output_path)
            merged_pdf.close()
            
            self.operation_finished.emit(True, t('pdf_merge_done', os.path.basename(output_path)))
            
        except Exception as e:
            self.operation_finished.emit(False, t('pdf_merge_failed', str(e)))

    def _split_pdfs(self, save_path):
        """拆分PDF文件"""
        import fitz
        
        try:
            total_files = len(self.file_list)
            processed_files = 0
            
            for file_idx, file_path in enumerate(self.file_list):
                try:
                    pdf = fitz.open(file_path)
                    file_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 创建导出文件夹
                    export_folder = os.path.join(save_path, f"{file_name}_导出")
                    if not os.path.exists(export_folder):
                        os.makedirs(export_folder)
                    
                    # 拆分每一页
                    page_count = len(pdf)
                    for page_num in range(page_count):
                        new_pdf = fitz.open()
                        new_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)
                        
                        # 命名为"文件名_页X.pdf"（简化命名）
                        output_name = f"{file_name}_页{page_num + 1}.pdf"
                        output_path = os.path.join(export_folder, output_name)
                        
                        new_pdf.save(output_path)
                        new_pdf.close()
                    
                    pdf.close()
                    processed_files += 1
                    
                    # 更新进度
                    progress = int((file_idx + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    # 跳过无法处理的文件
                    continue
            
            self.operation_finished.emit(True, t('pdf_split_done', os.path.basename(save_path)))
            
        except Exception as e:
            self.operation_finished.emit(False, t('pdf_split_failed', str(e)))

    def _compress_pdfs(self, save_path, quality_index):
        """压缩PDF文件"""
        import fitz
        
        try:
            # 压缩质量映射
            quality_map = {
                0: 80,   # 高质量
                1: 60,   # 中等质量
                2: 40,   # 低质量
            }
            quality = quality_map.get(quality_index, 60)
            
            total_files = len(self.file_list)
            processed_files = 0
            
            for file_idx, file_path in enumerate(self.file_list):
                try:
                    pdf = fitz.open(file_path)
                    file_name = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(file_name)[0]
                    
                    # 输出文件名
                    output_name = f"{name_without_ext}_compressed.pdf"
                    output_path = os.path.join(save_path, output_name)
                    
                    # 处理文件名冲突（Windows风格：文件名（1））
                    output_path = get_unique_filepath(output_path)
                    
                    # 压缩PDF
                    pdf.save(output_path, garbage=4, deflate=True)
                    pdf.close()
                    
                    processed_files += 1
                    
                    # 更新进度
                    progress = int((file_idx + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    # 跳过无法处理的文件
                    continue
            
            if processed_files == total_files:
                self.operation_finished.emit(True, t('pdf_compress_done', os.path.basename(save_path)))
            else:
                self.operation_finished.emit(True, t('pdf_compress_partial', processed_files, total_files, os.path.basename(save_path)))
            
        except Exception as e:
            self.operation_finished.emit(False, t('pdf_compress_failed', str(e)))

    def _pdf_to_word(self, save_path, page_range_type, page_range_text):
        """PDF转Word - 使用pdf2docx库"""
        import fitz  # PyMuPDF - 用于检测扫描PDF
        
        # 延迟导入pdf2docx库
        global PDF2DOCX_AVAILABLE
        if PDF2DOCX_AVAILABLE is None:
            try:
                from pdf2docx import parse, Converter
                PDF2DOCX_AVAILABLE = True
            except ImportError:
                PDF2DOCX_AVAILABLE = False
        
        try:
            total_files = len(self.file_list)
            processed_files = 0
            
            for file_idx, file_path in enumerate(self.file_list):
                try:
                    # 检查是否为扫描PDF(图片PDF)
                    pdf_doc = fitz.open(file_path)
                    is_scanned = self._check_scanned_pdf(pdf_doc)
                    pdf_doc.close()
                    
                    if is_scanned:
                        # 扫描PDF,跳过并记录警告
                        self.warning_requested.emit(t('pdf_scanned_warning'))
                        continue
                    
                    # 解析页面范围
                    pages_to_convert, error_msg = self._parse_page_range(page_range_type, page_range_text, file_path)
                    if error_msg:
                        # 页面范围解析失败
                        self.operation_finished.emit(False, error_msg)
                        return
                    
                    # 输出文件路径
                    file_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_name = f"{file_name}.docx"
                    output_path = os.path.join(save_path, output_name)
                    
                    # 处理文件名冲突
                    output_path = get_unique_filepath(output_path)
                    
                    # 检查pdf2docx库是否可用
                    if not PDF2DOCX_AVAILABLE:
                        raise Exception(t('pdf_need_docx_lib'))
                    
                    # 根据页面范围类型选择转换方式
                    try:
                        if pages_to_convert is None:
                            # 全部页面: 使用parse()函数
                            parse(file_path, output_path)
                        else:
                            # 自定义范围: 使用Converter类和pages参数(支持离散页面)
                            from pdf2docx import Converter
                            cv = Converter(file_path)
                            try:
                                cv.convert(output_path, pages=pages_to_convert)
                            finally:
                                cv.close()
                        
                        # 验证文件是否正确生成
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            # 验证DOCX文件格式
                            try:
                                import zipfile
                                with zipfile.ZipFile(output_path, 'r') as zip_ref:
                                    # DOCX文件必须包含这些核心文件
                                    required_files = ['[Content_Types].xml', 'word/document.xml']
                                    missing_files = [f for f in required_files if f not in zip_ref.namelist()]
                                    if missing_files:
                                        raise Exception(f"生成的DOCX文件缺少核心文件: {missing_files}")
                            except zipfile.BadZipFile:
                                raise Exception("生成的文件不是有效的DOCX格式")
                        else:
                            raise Exception("转换后的文件无效或大小为0")
                            
                    except Exception as conv_error:
                        # 向用户显示错误信息
                        error_msg = f"PDF转换失败: {os.path.basename(file_path)}\n错误: {str(conv_error)}"
                        self.warning_requested.emit(error_msg)
                        print(f"详细错误信息:\n{traceback.format_exc()}")
                        raise
                    
                    processed_files += 1
                    
                    # 更新进度
                    progress = int((file_idx + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    # 向用户显示错误信息
                    error_msg = t('pdf_file_process_failed', os.path.basename(file_path), str(e))
                    self.warning_requested.emit(error_msg)
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    continue
            
            if processed_files == total_files:
                self.operation_finished.emit(True, t('pdf_word_done', os.path.basename(save_path)))
            else:
                self.operation_finished.emit(True, t('pdf_word_partial', processed_files, total_files, os.path.basename(save_path)))
            
        except Exception as e:
            self.operation_finished.emit(False, t('pdf_word_failed', str(e)))
    
    def _check_scanned_pdf(self, pdf_doc):
        """检查PDF是否为扫描版(图片PDF)
        
        Args:
            pdf_doc: PyMuPDF打开的PDF文档对象
        
        Returns:
            True=扫描PDF, False=文本PDF
        """
        # 检查前几页的文字数量
        max_pages_to_check = min(5, len(pdf_doc))
        
        for page_idx in range(max_pages_to_check):
            page = pdf_doc[page_idx]
            text = page.get_text()
            
            # 如果找到文字,则不是扫描PDF
            if len(text.strip()) > 50:  # 至少50个字符
                return False
        
        # 如果前几页都没有文字,可能是扫描PDF
        return True

    def _parse_page_range(self, page_range_type, page_range_text, pdf_path):
        """解析页面范围
        
        Args:
            page_range_type: 0=全部页面, 1=自定义范围
            page_range_text: 页面范围文本,如"1-5, 8, 10-12"
            pdf_path: PDF文件路径
        
        Returns:
            (pages_to_convert, error_msg)
            - pages_to_convert: None表示全部页面,list表示指定页面,空list表示解析失败
            - error_msg: 错误消息,None表示成功
        """
        import pdfplumber
        
        if page_range_type == 0:
            # 全部页面,返回None表示使用全部
            return (None, None)
        
        # 获取PDF总页数
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
        
        # 解析自定义范围
        pages = []
        try:
            # 分割范围字符串
            parts = page_range_text.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 范围: "1-5"
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    # 转换为0-based索引
                    for page_num in range(start - 1, end):
                        if 0 <= page_num < total_pages:
                            pages.append(page_num)
                else:
                    # 单页: "8"
                    page_num = int(part) - 1
                    if 0 <= page_num < total_pages:
                        pages.append(page_num)
            
            if not pages:
                return ([], t('pdf_page_range_invalid'))
            
            # 去重并排序
            pages = sorted(set(pages))
            return (pages, None)
            
        except Exception:
            return ([], t('pdf_page_range_invalid'))

    def on_operation_finished(self, success, message):
        """操作完成回调"""
        # 恢复按钮状态，隐藏进度条
        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.is_processing = False

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)
        
        # 更新界面文本
        self.tip_label.setText(t('pdf_import_tip'))
        self.browse_btn.setText(t('pdf_browse'))
        self.clear_btn.setText(t('pdf_clear'))
        self.mode_group.setTitle(t('pdf_operation_mode'))
        self.merge_radio.setText(t('pdf_merge'))
        self.split_radio.setText(t('pdf_split'))
        self.compress_radio.setText(t('pdf_compress'))
        self.word_radio.setText(t('pdf_to_word'))
        self.compress_settings_group.setTitle(t('pdf_compress_settings'))
        self.quality_combo.setItemText(0, t('pdf_quality_high'))
        self.quality_combo.setItemText(1, t('pdf_quality_medium'))
        self.quality_combo.setItemText(2, t('pdf_quality_low'))
        self.word_settings_group.setTitle(t('pdf_word_settings'))
        self.page_all_radio.setText(t('pdf_page_range_all'))
        self.page_custom_radio.setText(t('pdf_page_range_custom'))
        self.page_range_input.setPlaceholderText(t('pdf_page_range_placeholder'))
        self.format_label.setText(t('pdf_format_quality'))
        self.format_desc.setText(t('pdf_format_desc'))
        self.file_count_label.setText(t('pdf_file_count', len(self.file_list)))
        self.process_btn.setText(t('pdf_start'))
        
        # 重新加载配置以更新保存路径显示
        self._load_config()

    # 拖放支持
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and file_path.lower().endswith('.pdf'):
                files.append(file_path)
        
        if files:
            self.file_list.extend(files)
            self._update_file_list()