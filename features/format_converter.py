# -*- coding: utf-8 -*-
"""
DeskHelperGUI 格式转换功能模块
提供图片格式转换功能，包括ICO转换
"""

import os
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QGroupBox, QComboBox, QCheckBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame, QSpinBox,
    QListWidget, QMessageBox, QFileDialog, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton
from .utils import get_unique_filepath

# PIL延迟导入
HAS_PIL = None

# PyMuPDF延迟导入
HAS_PYMUPDF = None


# ICO尺寸选项
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


class FormatConverterWidget(QWidget):
    """格式转换功能界面"""

    # 转换完成信号
    convert_finished = pyqtSignal(bool, str)  # (成功, 消息)
    
    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)  # (警告消息)
    
    # 进度更新信号
    progress_updated = pyqtSignal(int)  # (进度值)

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.file_list = []  # 文件列表
        self.is_converting = False
        self._loading_config = False

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        self.convert_finished.connect(self.on_convert_finished)
        self.progress_updated.connect(self.progress_bar.setValue)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 文件导入区域
        self._create_import_area(main_layout)

        # 转换设置和预览区域（左右分割）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：转换设置
        left_panel = self._create_settings_panel()
        left_panel.setMinimumWidth(260)
        left_panel.setMaximumWidth(400)
        splitter.addWidget(left_panel)
        
        # 右侧：文件列表
        right_panel = self._create_file_list_panel()
        right_panel.setMinimumWidth(300)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter, 1)

        # 按钮区域
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_import_area(self, parent_layout):
        """创建文件导入区域"""
        self.import_group = QGroupBox(t('converter_import'))
        import_layout = QVBoxLayout()
        import_layout.setSpacing(6)
        import_layout.setContentsMargins(8, 10, 8, 10)

        # 导入模式选择
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        
        self.single_file_radio = QRadioButton(t('converter_single_file'))
        self.single_file_radio.setChecked(True)
        self.single_file_radio.setStyleSheet("""
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
        self.mode_group.addButton(self.single_file_radio, 0)
        mode_layout.addWidget(self.single_file_radio)

        self.folder_radio = QRadioButton(t('converter_folder'))
        self.folder_radio.setStyleSheet("""
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
        self.mode_group.addButton(self.folder_radio, 1)
        mode_layout.addWidget(self.folder_radio)
        
        mode_layout.addStretch()
        import_layout.addLayout(mode_layout)

        # 文件路径输入行
        path_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText(t('converter_import_placeholder'))
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

        self.browse_btn = AnimatedButton(t('converter_browse'))
        self.browse_btn.setFixedSize(90, 34)
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
            QPushButton:pressed {
                background-color: #1c7ed6;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(self.browse_btn)

        import_layout.addLayout(path_layout)

        # 提示文本
        self.tip_label = QLabel(t('converter_import_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        import_layout.addWidget(self.tip_label)

        self.import_group.setLayout(import_layout)
        parent_layout.addWidget(self.import_group)

    def _create_settings_panel(self):
        """创建转换设置面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # 格式选择区域
        self.format_group = QGroupBox(t('converter_format_settings'))
        format_layout = QVBoxLayout()
        format_layout.setSpacing(6)
        format_layout.setContentsMargins(8, 10, 8, 10)

        # 目标格式选择
        self.format_label = QLabel(t('converter_target_format'))
        self.format_label.setStyleSheet("color: #495057; font-size: 13px;")
        format_layout.addWidget(self.format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPG', 'PNG', 'ICO', 'BMP', 'GIF', 'WebP', 'PDF→JPG', 'PDF→PNG'])
        self.format_combo.setFixedHeight(30)
        self.format_combo.setStyleSheet("""
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
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)

        self.format_group.setLayout(format_layout)
        layout.addWidget(self.format_group)

        # ICO特殊设置区域
        self.ico_group = QGroupBox(t('converter_ico_settings'))
        ico_layout = QVBoxLayout()
        ico_layout.setSpacing(6)
        ico_layout.setContentsMargins(8, 10, 8, 10)

        # ICO尺寸选择
        self.size_label = QLabel(t('converter_ico_size'))
        self.size_label.setStyleSheet("color: #495057; font-size: 13px;")
        ico_layout.addWidget(self.size_label)

        # ICO尺寸单选按钮（竖向布局）
        self.ico_size_group = QButtonGroup(self)
        size_layout = QVBoxLayout()
        size_layout.setSpacing(4)
        
        # 创建尺寸选项
        sizes_display = [
            ('16×16', 16),
            ('32×32', 32),
            ('48×48', 48),
            ('64×64', 64),
            ('128×128', 128),
            ('256×256', 256),
        ]
        
        for text, size in sizes_display:
            rb = QRadioButton(text)
            rb.setStyleSheet("""
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
            self.ico_size_group.addButton(rb, size)
            size_layout.addWidget(rb)
            if size == 64:
                rb.setChecked(True)  # 默认64x64
        
        ico_layout.addLayout(size_layout)

        # ICO尺寸提示
        self.ico_size_tip = QLabel(t('converter_ico_size_tip'))
        self.ico_size_tip.setStyleSheet("color: #868e96; font-size: 11px;")
        ico_layout.addWidget(self.ico_size_tip)

        self.ico_group.setLayout(ico_layout)
        self.ico_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: white;
            }
        """)
        self.ico_group.setVisible(False)  # 默认隐藏，选择ICO时显示
        layout.addWidget(self.ico_group)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_file_list_panel(self):
        """创建文件列表面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # 文件列表标题行（清空按钮靠右侧边框）
        list_header = QHBoxLayout()
        self.list_label = QLabel(t('converter_file_list'))
        self.list_label.setStyleSheet("color: #495057; font-size: 13px; font-weight: bold;")
        list_header.addWidget(self.list_label)
        
        list_header.addStretch()
        
        # 清空按钮在标题行最右侧
        self.list_clear_btn = AnimatedButton(t('converter_clear'))
        self.list_clear_btn.setFixedHeight(26)
        self.list_clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.list_clear_btn.clicked.connect(self._clear_list)
        list_header.addWidget(self.list_clear_btn)
        
        layout.addLayout(list_header)

        # 文件列表
        self.file_list_widget = QListWidget()
        self.file_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #339af0;
                color: white;
            }
        """)
        layout.addWidget(self.file_list_widget, 1)

        # 文件数量和输出路径显示（水平布局）
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        # 文件数量显示（左侧）
        self.file_count_label = QLabel(t('converter_file_count', 0))
        self.file_count_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.file_count_label)
        
        info_layout.addStretch()
        
        # 输出路径显示（右侧）
        self.save_path_label = QLabel(t('converter_output_path', ''))
        self.save_path_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.save_path_label)
        
        layout.addLayout(info_layout)

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

        # 开始转换按钮
        self.convert_btn = AnimatedButton(t('converter_start'))
        self.convert_btn.setFixedSize(120, 34)
        self.convert_btn.setStyleSheet("""
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
        self.convert_btn.clicked.connect(self._start_conversion)
        btn_layout.addWidget(self.convert_btn)

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
                    self.save_path_label.setText(t('converter_output_path', save_path.replace('\\', '/')))
        finally:
            self._loading_config = False

    def _browse_file(self):
        """浏览选择文件或文件夹"""
        if self.single_file_radio.isChecked():
            # 选择单个文件
            file_path = QFileDialog.getOpenFileName(
                self,
                t('converter_select_file'),
                "",
                f"{t('converter_image_files')} (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.ico *.pdf);;{t('converter_all_files')} (*.*)"
            )[0]
            if file_path:
                self.file_input.setText(file_path)
                self.file_list = [file_path]
                self._update_file_list()
        else:
            # 选择文件夹
            folder_path = QFileDialog.getExistingDirectory(
                self,
                t('converter_select_folder'),
                ""
            )
            if folder_path:
                self.file_input.setText(folder_path)
                # 扫描文件夹中的图片文件
                self._scan_folder(folder_path)

    def _scan_folder(self, folder_path):
        """扫描文件夹中的图片文件"""
        self.file_list = []
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.ico', '.pdf']
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions:
                    self.file_list.append(os.path.join(root, file))
        
        self._update_file_list()

    def _on_format_changed(self, format_text):
        """格式选择变化"""
        # ICO格式显示特殊设置
        if format_text == 'ICO':
            self.ico_group.setVisible(True)
        else:
            self.ico_group.setVisible(False)

    def _update_file_list(self):
        """更新文件列表显示"""
        self.file_list_widget.clear()
        for file_path in self.file_list:
            # 只显示文件名，不显示完整路径
            file_name = os.path.basename(file_path)
            self.file_list_widget.addItem(file_name)
        
        self.file_count_label.setText(t('converter_file_count', len(self.file_list)))
        
        # 检测是否只有PDF文件，动态调整格式选项
        self._update_format_options()

    def _update_format_options(self):
        """根据文件类型动态更新格式选项"""
        # 检测文件类型
        has_pdf = False
        only_pdf = False
        
        if self.file_list:
            pdf_files = [f for f in self.file_list if os.path.splitext(f)[1].lower() == '.pdf']
            has_pdf = len(pdf_files) > 0
            only_pdf = len(pdf_files) == len(self.file_list)
        
        # 保存当前选择
        current_format = self.format_combo.currentText()
        
        # 清空并重新添加选项
        self.format_combo.clear()
        
        if only_pdf:
            # 只有PDF文件时，只显示PDF转换选项
            self.format_combo.addItems(['PDF→JPG', 'PDF→PNG'])
        elif has_pdf:
            # 有PDF也有其他文件，显示所有选项
            self.format_combo.addItems(['JPG', 'PNG', 'ICO', 'BMP', 'GIF', 'WebP', 'PDF→JPG', 'PDF→PNG'])
        else:
            # 没有PDF文件时，隐藏PDF转换选项
            self.format_combo.addItems(['JPG', 'PNG', 'ICO', 'BMP', 'GIF', 'WebP'])
        
        # 尝试恢复之前的选择（如果仍然有效）
        index = self.format_combo.findText(current_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        else:
            # 默认选择第一个
            self.format_combo.setCurrentIndex(0)
        
        # 触发格式变化事件
        self._on_format_changed(self.format_combo.currentText())

    def _clear_list(self):
        """清空文件列表"""
        self.file_list = []
        self.file_input.setText("")
        self._update_file_list()  # 这会自动调用_update_format_options恢复所有选项
        # 清空后设置默认格式为JPG
        self.format_combo.setCurrentIndex(0)  # JPG是第一个选项

    def _start_conversion(self):
        """开始转换"""
        # 获取目标格式
        target_format = self.format_combo.currentText().lower()
        
        # PDF转换需要检查PyMuPDF库
        if 'pdf' in target_format:
            global HAS_PYMUPDF
            if HAS_PYMUPDF is None:
                try:
                    import fitz
                    HAS_PYMUPDF = True
                except ImportError:
                    HAS_PYMUPDF = False
            
            if not HAS_PYMUPDF:
                self.warning_requested.emit(t('converter_need_pymupdf'))
                return
        else:
            # 图片转换需要检查PIL库
            global HAS_PIL
            if HAS_PIL is None:
                try:
                    from PIL import Image
                    HAS_PIL = True
                except ImportError:
                    HAS_PIL = False
            
            if not HAS_PIL:
                self.warning_requested.emit(t('converter_need_pil'))
                return

        # 验证文件列表
        if not self.file_list:
            self.warning_requested.emit(t('converter_no_files'))
            return
        
        # 获取全局保存路径
        save_path = self.config.get_save_path() if self.config else ""
        if not save_path:
            self.warning_requested.emit(t('converter_no_save_path'))
            return
        
        # 确保保存路径存在
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                self.warning_requested.emit(t('converter_create_path_failed', str(e)))
                return

        # ICO格式获取尺寸
        ico_size = None
        if target_format == 'ico':
            checked_btn = self.ico_size_group.checkedButton()
            if checked_btn:
                ico_size = self.ico_size_group.id(checked_btn)
            else:
                ico_size = 64  # 默认64x64

        # 禁用按钮，显示进度条（list_clear_btn已在文件列表标题区）
        self.convert_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.list_clear_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.file_list))
        self.progress_bar.setValue(0)
        self.is_converting = True

        # 在新线程中执行转换
        thread = threading.Thread(
            target=self._convert_files,
            args=(self.file_list, target_format, save_path, ico_size)
        )
        thread.daemon = True
        thread.start()

    def _convert_files(self, file_list, target_format, save_path, ico_size):
        """执行文件转换（在线程中运行）"""
        success_count = 0
        error_messages = []
        
        # 判断是否为PDF转换
        is_pdf_conversion = 'pdf' in target_format
        
        if is_pdf_conversion:
            # PDF转图片
            import fitz  # PyMuPDF
            
            # 获取目标图片格式
            image_format = target_format.split('→')[1] if '→' in target_format else 'jpg'
            
            for i, file_path in enumerate(file_list):
                try:
                    # 检查是否为PDF文件
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext != '.pdf':
                        error_messages.append(f"{os.path.basename(file_path)}: 不是PDF文件")
                        continue
                    
                    # 获取原始文件名（不带扩展名）
                    original_name = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 转换PDF
                    page_count = self._convert_pdf_to_image(file_path, save_path, original_name, image_format)
                    success_count += 1
                    
                except Exception as e:
                    error_messages.append(f"{os.path.basename(file_path)}: {str(e)}")
                
                # 更新进度
                self.progress_updated.emit(i + 1)
        else:
            # 图片格式转换
            from PIL import Image
            
            for i, file_path in enumerate(file_list):
                try:
                    # 打开图片
                    with Image.open(file_path) as img:
                        # 获取原始文件名（不带扩展名）
                        original_name = os.path.splitext(os.path.basename(file_path))[0]
                        
                        # 根据目标格式处理
                        if target_format == 'ico':
                            # ICO格式：强制1:1比例
                            self._convert_to_ico(img, save_path, original_name, ico_size)
                        else:
                            # 其他格式：保留原始比例
                            self._convert_to_other(img, save_path, original_name, target_format)
                        
                        success_count += 1
                except Exception as e:
                    error_messages.append(f"{os.path.basename(file_path)}: {str(e)}")
                
                # 更新进度
                self.progress_updated.emit(i + 1)
        
        # 转换完成（简化消息，只显示路径）
        if success_count == len(file_list):
            self.convert_finished.emit(True, save_path)
        elif success_count > 0:
            self.convert_finished.emit(True, save_path)
        else:
            message = t('converter_failed', ', '.join(error_messages[:3]))
            self.convert_finished.emit(False, message)

    def _convert_to_ico(self, img, save_path, original_name, size):
        """转换为ICO格式（参考功能参照.py的逻辑）"""
        from PIL import Image
        
        # 转换为RGBA模式（ICO需要透明度支持）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 调整到指定尺寸（强制1:1）
        resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # 保存ICO文件
        output_path = os.path.join(save_path, f"{original_name}.ico")
        # 处理文件名冲突（Windows风格：文件名（1））
        output_path = get_unique_filepath(output_path)
        resized_img.save(
            output_path,
            format='ICO',
            sizes=[(size, size)]
        )

    def _convert_to_other(self, img, save_path, original_name, target_format):
        """转换为其他格式（保留原始比例）"""
        from PIL import Image
        
        # 格式映射
        format_map = {
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'bmp': 'BMP',
            'gif': 'GIF',
            'webp': 'WebP'
        }
        
        pil_format = format_map.get(target_format, target_format.upper())
        
        # 处理特殊格式要求
        if pil_format == 'JPEG':
            # JPEG不支持透明度，转换为RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
        
        # 保存文件
        output_path = os.path.join(save_path, f"{original_name}.{target_format}")
        
        # 处理文件名冲突（Windows风格：文件名（1））
        output_path = get_unique_filepath(output_path)
        
        # 保存参数
        save_kwargs = {}
        if pil_format == 'JPEG':
            save_kwargs['quality'] = 95
        elif pil_format == 'PNG':
            save_kwargs['optimize'] = True
        
        img.save(output_path, format=pil_format, **save_kwargs)

    def _convert_pdf_to_image(self, pdf_path, save_path, original_name, image_format):
        """将PDF转换为图片"""
        import fitz  # PyMuPDF
        
        # 打开PDF文件
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        # 遍历每一页
        for page_num in range(page_count):
            page = doc[page_num]
            
            # 设置渲染参数（高分辨率）
            zoom = 2.0  # 缩放因子，提高分辨率
            mat = fitz.Matrix(zoom, zoom)
            
            # 渲染页面为图片
            pix = page.get_pixmap(matrix=mat)
            
            # 生成输出文件名（多页时添加页码）
            if page_count == 1:
                output_name = original_name
            else:
                output_name = f"{original_name}_page{page_num + 1}"
            
            # 保存图片
            output_path = os.path.join(save_path, f"{output_name}.{image_format}")
            
            # 处理文件名冲突（Windows风格：文件名（1））
            output_path = get_unique_filepath(output_path)
            
            if image_format.lower() == 'jpg' or image_format.lower() == 'jpeg':
                pix.save(output_path, "jpeg")
            else:
                pix.save(output_path, image_format.lower())
        
        doc.close()
        return page_count

    def on_convert_finished(self, success, message):
        """转换完成回调"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.list_clear_btn.setEnabled(True)
        self.is_converting = False
        
        # 转换成功后自动清空列表
        if success:
            self._clear_list()

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
        
        # 检查是文件还是文件夹
        first_path = urls[0].toLocalFile()
        if os.path.isfile(first_path):
            # 单文件模式
            self.single_file_radio.setChecked(True)
            self.file_input.setText(first_path)
            self.file_list = [first_path]
            self._update_file_list()
        elif os.path.isdir(first_path):
            # 文件夹模式
            self.folder_radio.setChecked(True)
            self.file_input.setText(first_path)
            self._scan_folder(first_path)

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)
        
        # 更新界面文本
        self.import_group.setTitle(t('converter_import'))
        self.single_file_radio.setText(t('converter_single_file'))
        self.folder_radio.setText(t('converter_folder'))
        self.file_input.setPlaceholderText(t('converter_import_placeholder'))
        self.tip_label.setText(t('converter_import_tip'))
        self.browse_btn.setText(t('converter_browse'))
        
        self.format_group.setTitle(t('converter_format_settings'))
        self.format_label.setText(t('converter_target_format'))
        # 格式选项保持不变
        
        self.ico_group.setTitle(t('converter_ico_settings'))
        self.size_label.setText(t('converter_ico_size'))
        self.ico_size_tip.setText(t('converter_ico_size_tip'))
        
        self.list_label.setText(t('converter_file_list'))
        self.file_count_label.setText(t('converter_file_count', len(self.file_list)))
        
        self.list_clear_btn.setText(t('converter_clear'))
        self.convert_btn.setText(t('converter_start'))
 
        # 重新加载配置（更新输出路径显示）
        self._load_config()