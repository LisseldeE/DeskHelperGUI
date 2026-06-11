# -*- coding: utf-8 -*-
"""
DeskHelperGUI 图片处理功能模块
提供图片旋转、裁剪、压缩等功能
"""

import os
import io
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QMessageBox, QGroupBox,
    QComboBox, QSlider, QSpinBox, QScrollArea, QFrame, QSizePolicy,
    QCheckBox, QRadioButton, QButtonGroup, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton

# PIL延迟导入（优化启动速度）
HAS_PIL = None  # 延迟检测


# 预设尺寸配置（单位：像素，按照300DPI标准）
PRESET_SIZES = {
    'zh': {
        '1_inch': ('1寸证件照 (25×35mm)', 295, 413),
        '2_inch': ('2寸证件照 (35×49mm)', 413, 579),
        'small_2_inch': ('小2寸证件照 (35×45mm)', 413, 531),
        'passport': ('护照/签证照 (35×45mm)', 413, 531),
        'id_card': ('身份证照 (26×32mm)', 307, 378),
        'driver_license': ('驾驶证照 (21×26mm)', 248, 307),
    },
    'en': {
        '1_inch': ('1-inch ID Photo (25×35mm)', 295, 413),
        '2_inch': ('2-inch ID Photo (35×49mm)', 413, 579),
        'small_2_inch': ('Small 2-inch ID Photo (35×45mm)', 413, 531),
        'passport': ('Passport/Visa Photo (35×45mm)', 413, 531),
        'id_card': ('ID Card Photo (26×32mm)', 307, 378),
        'driver_license': ('Driver License Photo (21×26mm)', 248, 307),
    }
}

# 证件照排版 - 证件照尺寸配置（单位：像素，300DPI）
ID_PHOTO_SIZES = {
    'zh': {
        '1_inch': ('1寸 (25×35mm)', 295, 413),
        '2_inch': ('2寸 (35×49mm)', 413, 579),
        'small_2_inch': ('小2寸 (35×45mm)', 413, 531),
        'passport': ('护照/签证 (35×45mm)', 413, 531),
    },
    'en': {
        '1_inch': ('1-inch (25×35mm)', 295, 413),
        '2_inch': ('2-inch (35×49mm)', 413, 579),
        'small_2_inch': ('Small 2-inch (35×45mm)', 413, 531),
        'passport': ('Passport/Visa (35×45mm)', 413, 531),
    }
}

# 证件照排版 - 相纸尺寸配置（单位：像素，300DPI）
PAPER_SIZES = {
    'zh': {
        '3r': ('3R (89×127mm)', 1051, 1500),
        '4r': ('4R (102×152mm)', 1205, 1795),
        '5r': ('5R (127×178mm)', 1500, 2102),
        '6r': ('6R (152×203mm)', 1795, 2400),
        'a4': ('A4 (210×297mm)', 2480, 3508),
    },
    'en': {
        '3r': ('3R (89×127mm)', 1051, 1500),
        '4r': ('4R (102×152mm)', 1205, 1795),
        '5r': ('5R (127×178mm)', 1500, 2102),
        '6r': ('6R (152×203mm)', 1795, 2400),
        'a4': ('A4 (210×297mm)', 2480, 3508),
    }
}


class ImageProcessorWidget(QWidget):
    """图片处理功能界面"""

    # 处理完成信号
    process_finished = pyqtSignal(bool, str)  # (成功, 消息)
    
    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)  # (警告消息)
    
    # 进度更新信号（用于线程安全更新进度条）
    progress_updated = pyqtSignal(int)  # (进度值)

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.original_image = None  # 原始PIL图片
        self.original_file_path = ""  # 原始文件路径
        self.original_file_ext = ""  # 原始文件扩展名
        self.original_file_size = 0  # 原始文件大小
        self.max_jpeg_size = 0  # 最高质量JPEG大小
        self.original_ratio = 1.0  # 原始图片宽高比
        self.is_processing = False
        self._updating_size = False  # 防止尺寸联动递归
        self._updating_preset = False  # 防止预设更新递归
        self._loading_image = False  # 正在加载图片标志

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        self.process_finished.connect(self.on_process_finished)
        self.progress_updated.connect(self.progress_bar.setValue)
        self.setAcceptDrops(True)
        
        # 创建预览刷新定时器（延迟刷新，避免频繁更新）
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._auto_preview)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 图片导入区域
        self._create_import_area(main_layout)

        # 处理方式和预览区域（左右分割）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：处理方式选择（带滚动）
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f1f3f5;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                min-height: 30px;
                border-radius: 4px;
            }
        """)
        left_panel = self._create_processing_panel()
        left_scroll.setWidget(left_panel)
        left_scroll.setMinimumWidth(260)
        left_scroll.setMaximumWidth(400)
        splitter.addWidget(left_scroll)
        
        # 右侧：图片预览
        right_panel = self._create_preview_panel()
        right_panel.setMinimumWidth(300)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter, 1)

        # 按钮区域
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_import_area(self, parent_layout):
        """创建图片导入区域"""
        self.import_group = QGroupBox(t('image_import'))
        import_layout = QVBoxLayout()
        import_layout.setSpacing(6)
        import_layout.setContentsMargins(8, 10, 8, 10)

        # 文件路径输入行
        path_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText(t('image_import_placeholder'))
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

        self.browse_btn = AnimatedButton(t('image_browse'))
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
        self.browse_btn.clicked.connect(self._browse_image)
        path_layout.addWidget(self.browse_btn)

        import_layout.addLayout(path_layout)

        # 提示和文件信息合并为一行
        info_layout = QHBoxLayout()
        self.tip_label = QLabel(t('image_import_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        info_layout.addWidget(self.tip_label)
        
        info_layout.addStretch()
        
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #495057; font-size: 12px;")
        info_layout.addWidget(self.file_info_label)
        import_layout.addLayout(info_layout)

        self.import_group.setLayout(import_layout)
        parent_layout.addWidget(self.import_group)

    def _create_processing_panel(self):
        """创建处理方式面板"""
        panel = QFrame()
        panel.setMinimumWidth(240)
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # 处理方式选择（单选按钮切换显示）
        self.process_group = QGroupBox(t('image_process_mode'))
        process_layout = QVBoxLayout()
        process_layout.setSpacing(6)
        process_layout.setContentsMargins(8, 10, 8, 10)

        # 单选按钮组
        self.mode_group = QButtonGroup(self)
        
        # 旋转选项
        self.rotate_radio = QRadioButton(t('image_rotate'))
        self.rotate_radio.setChecked(True)
        self.rotate_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 8px; }")
        self.mode_group.addButton(self.rotate_radio, 0)
        process_layout.addWidget(self.rotate_radio)

        # 裁剪选项
        self.crop_radio = QRadioButton(t('image_crop'))
        self.crop_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 8px; }")
        self.mode_group.addButton(self.crop_radio, 1)
        process_layout.addWidget(self.crop_radio)

        # 压缩选项
        self.compress_radio = QRadioButton(t('image_compress'))
        self.compress_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 8px; }")
        self.mode_group.addButton(self.compress_radio, 2)
        process_layout.addWidget(self.compress_radio)

        # 证件照排版选项
        self.id_photo_radio = QRadioButton(t('image_id_photo_layout'))
        self.id_photo_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 8px; }")
        self.mode_group.addButton(self.id_photo_radio, 3)
        process_layout.addWidget(self.id_photo_radio)

        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        self.process_group.setLayout(process_layout)
        layout.addWidget(self.process_group)

        # ========== 旋转设置区域 ==========
        self.rotate_group = QGroupBox("")
        rotate_layout = QVBoxLayout()
        rotate_layout.setSpacing(6)
        rotate_layout.setContentsMargins(8, 8, 8, 8)

        # 启用复选框
        self.rotate_enable_check = QCheckBox(t('image_enable'))
        self.rotate_enable_check.setChecked(False)
        self.rotate_enable_check.setStyleSheet("""
            QCheckBox {
                color: #339af0;
                font-size: 13px;
                font-weight: 600;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
            QCheckBox::indicator:hover {
                border-color: #339af0;
            }
        """)
        self.rotate_enable_check.stateChanged.connect(self._schedule_preview)
        rotate_layout.addWidget(self.rotate_enable_check)

        # 角度选择
        angle_layout = QHBoxLayout()
        angle_label = QLabel(t('image_angle'))
        angle_label.setStyleSheet("color: #495057; font-size: 13px;")
        angle_layout.addWidget(angle_label)

        self.angle_combo = QComboBox()
        self.angle_combo.addItems(['90°', '180°', '270°', t('image_angle_custom')])
        self.angle_combo.setFixedHeight(30)
        self.angle_combo.setStyleSheet("""
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
        self.angle_combo.currentIndexChanged.connect(self._on_angle_changed)
        angle_layout.addWidget(self.angle_combo, 1)
        rotate_layout.addLayout(angle_layout)

        # 自定义角度输入
        self.custom_angle_layout = QHBoxLayout()
        self.custom_angle_label = QLabel(t('image_custom_angle'))
        self.custom_angle_label.setStyleSheet("color: #495057; font-size: 13px;")
        self.custom_angle_layout.addWidget(self.custom_angle_label)

        self.custom_angle_spin = QSpinBox()
        self.custom_angle_spin.setRange(1, 359)
        self.custom_angle_spin.setValue(45)
        self.custom_angle_spin.setSuffix('°')
        self.custom_angle_spin.setFixedHeight(30)
        self.custom_angle_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #339af0;
            }
        """)
        self.custom_angle_spin.valueChanged.connect(self._schedule_preview)
        self.custom_angle_layout.addWidget(self.custom_angle_spin, 1)
        rotate_layout.addLayout(self.custom_angle_layout)
        self.custom_angle_label.setVisible(False)
        self.custom_angle_spin.setVisible(False)

        self.rotate_group.setLayout(rotate_layout)
        self.rotate_group.setStyleSheet("""
            QGroupBox {
                font-weight: normal;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 0px;
                background-color: white;
            }
        """)
        layout.addWidget(self.rotate_group)

        # ========== 裁剪设置区域 ==========
        self.crop_group = QGroupBox("")
        crop_layout = QVBoxLayout()
        crop_layout.setSpacing(6)
        crop_layout.setContentsMargins(8, 8, 8, 8)

        # 启用复选框
        self.crop_enable_check = QCheckBox(t('image_enable'))
        self.crop_enable_check.setChecked(False)
        self.crop_enable_check.setStyleSheet("""
            QCheckBox {
                color: #339af0;
                font-size: 13px;
                font-weight: 600;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
            QCheckBox::indicator:hover {
                border-color: #339af0;
            }
        """)
        self.crop_enable_check.stateChanged.connect(self._schedule_preview)
        crop_layout.addWidget(self.crop_enable_check)

        # 预设尺寸选择
        preset_label = QLabel(t('image_preset_size'))
        preset_label.setStyleSheet("color: #495057; font-size: 13px;")
        crop_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self._update_preset_sizes()
        self.preset_combo.setFixedHeight(30)
        self.preset_combo.setStyleSheet("""
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
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        crop_layout.addWidget(self.preset_combo)

        # 自定义尺寸
        custom_size_label = QLabel(t('image_custom_size'))
        custom_size_label.setStyleSheet("color: #495057; font-size: 13px;")
        crop_layout.addWidget(custom_size_label)

        size_input_layout = QHBoxLayout()
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(' px')
        self.width_spin.setFixedHeight(30)
        self.width_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #339af0;
            }
        """)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        size_input_layout.addWidget(self.width_spin)

        size_x_label = QLabel('×')
        size_x_label.setStyleSheet("color: #868e96; font-size: 14px;")
        size_x_label.setAlignment(Qt.AlignCenter)
        size_x_label.setFixedWidth(20)
        size_input_layout.addWidget(size_x_label)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(600)
        self.height_spin.setSuffix(' px')
        self.height_spin.setFixedHeight(30)
        self.height_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #339af0;
            }
        """)
        self.height_spin.valueChanged.connect(self._on_height_changed)
        size_input_layout.addWidget(self.height_spin)
        crop_layout.addLayout(size_input_layout)

        # 保持纵横比复选框
        self.keep_ratio_checkbox = QCheckBox(t('image_keep_ratio'))
        self.keep_ratio_checkbox.setStyleSheet("""
            QCheckBox {
                color: #339af0;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
            QCheckBox::indicator:hover {
                border-color: #339af0;
            }
        """)
        self.keep_ratio_checkbox.setChecked(False)
        self.keep_ratio_checkbox.stateChanged.connect(self._schedule_preview)
        crop_layout.addWidget(self.keep_ratio_checkbox)

        self.crop_group.setLayout(crop_layout)
        self.crop_group.setStyleSheet("""
            QGroupBox {
                font-weight: normal;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 0px;
                background-color: white;
            }
        """)
        self.crop_group.setVisible(False)
        layout.addWidget(self.crop_group)

        # ========== 压缩设置区域 ==========
        self.compress_group = QGroupBox("")
        compress_layout = QVBoxLayout()
        compress_layout.setSpacing(6)
        compress_layout.setContentsMargins(8, 8, 8, 8)

        # 启用复选框
        self.compress_enable_check = QCheckBox(t('image_enable'))
        self.compress_enable_check.setChecked(False)
        self.compress_enable_check.setStyleSheet("""
            QCheckBox {
                color: #339af0;
                font-size: 13px;
                font-weight: 600;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #339af0;
                border-color: #339af0;
            }
            QCheckBox::indicator:hover {
                border-color: #339af0;
            }
        """)
        self.compress_enable_check.stateChanged.connect(self._schedule_preview)
        compress_layout.addWidget(self.compress_enable_check)

        # 目标大小
        size_label = QLabel(t('image_target_size'))
        size_label.setStyleSheet("color: #495057; font-size: 13px;")
        compress_layout.addWidget(size_label)

        # 滑块和数值
        slider_layout = QHBoxLayout()
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 100)  # 1% - 100%
        self.size_slider.setValue(100)  # 默认100%
        self.size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #dee2e6;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #339af0;
                border: 1px solid #228be6;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #228be6;
            }
        """)
        self.size_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.size_slider, 1)

        self.size_value_label = QLabel('100%')
        self.size_value_label.setStyleSheet("""
            QLabel {
                color: #339af0;
                font-size: 13px;
                font-weight: 600;
                min-width: 70px;
            }
        """)
        self.size_value_label.setAlignment(Qt.AlignCenter)
        slider_layout.addWidget(self.size_value_label)
        compress_layout.addLayout(slider_layout)

        # 预估大小提示
        self.estimate_label = QLabel("")
        self.estimate_label.setStyleSheet("color: #868e96; font-size: 12px;")
        self.estimate_label.setAlignment(Qt.AlignCenter)
        compress_layout.addWidget(self.estimate_label)

        self.compress_group.setLayout(compress_layout)
        self.compress_group.setStyleSheet("""
            QGroupBox {
                font-weight: normal;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 0px;
                background-color: white;
            }
        """)
        self.compress_group.setVisible(False)
        layout.addWidget(self.compress_group)

        # ========== 证件照排版设置区域 ==========
        self.id_photo_group = QGroupBox("")
        id_photo_layout = QVBoxLayout()
        id_photo_layout.setSpacing(6)
        id_photo_layout.setContentsMargins(8, 8, 8, 8)

        # 证件照尺寸选择
        photo_size_label = QLabel(t('id_photo_size'))
        photo_size_label.setStyleSheet("color: #495057; font-size: 13px;")
        id_photo_layout.addWidget(photo_size_label)

        self.id_photo_size_combo = QComboBox()
        self._update_id_photo_sizes()
        self.id_photo_size_combo.setFixedHeight(30)
        self.id_photo_size_combo.setStyleSheet("""
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
        self.id_photo_size_combo.currentIndexChanged.connect(self._schedule_preview)
        id_photo_layout.addWidget(self.id_photo_size_combo)

        # 相纸尺寸选择
        paper_size_label = QLabel(t('id_photo_paper_size'))
        paper_size_label.setStyleSheet("color: #495057; font-size: 13px;")
        id_photo_layout.addWidget(paper_size_label)

        self.paper_size_combo = QComboBox()
        self._update_paper_sizes()
        self.paper_size_combo.setFixedHeight(30)
        self.paper_size_combo.setStyleSheet("""
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
        self.paper_size_combo.currentIndexChanged.connect(self._schedule_preview)
        id_photo_layout.addWidget(self.paper_size_combo)

        # 排版方式选择
        layout_mode_label = QLabel(t('id_photo_layout_mode'))
        layout_mode_label.setStyleSheet("color: #495057; font-size: 13px;")
        id_photo_layout.addWidget(layout_mode_label)

        layout_mode_container = QHBoxLayout()
        self.layout_horizontal_radio = QRadioButton(t('id_photo_layout_horizontal'))
        self.layout_horizontal_radio.setChecked(True)
        self.layout_horizontal_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 6px; }")
        self.layout_horizontal_radio.toggled.connect(self._schedule_preview)
        layout_mode_container.addWidget(self.layout_horizontal_radio)

        self.layout_vertical_radio = QRadioButton(t('id_photo_layout_vertical'))
        self.layout_vertical_radio.setStyleSheet("QRadioButton { color: #495057; font-size: 13px; spacing: 6px; }")
        self.layout_vertical_radio.toggled.connect(self._schedule_preview)
        layout_mode_container.addWidget(self.layout_vertical_radio)

        self.layout_mode_group = QButtonGroup(self)
        self.layout_mode_group.addButton(self.layout_horizontal_radio, 0)
        self.layout_mode_group.addButton(self.layout_vertical_radio, 1)
        id_photo_layout.addLayout(layout_mode_container)

        # 可排版数量提示
        self.id_photo_count_label = QLabel("")
        self.id_photo_count_label.setStyleSheet("color: #339af0; font-size: 12px; font-weight: 600;")
        self.id_photo_count_label.setAlignment(Qt.AlignCenter)
        id_photo_layout.addWidget(self.id_photo_count_label)

        self.id_photo_group.setLayout(id_photo_layout)
        self.id_photo_group.setStyleSheet("""
            QGroupBox {
                font-weight: normal;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 0px;
                background-color: white;
            }
        """)
        self.id_photo_group.setVisible(False)
        layout.addWidget(self.id_photo_group)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_preview_panel(self):
        """创建预览面板"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # 预览标题
        preview_title = QLabel(t('image_preview'))
        preview_title.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        layout.addWidget(preview_title)

        # 预览区域（带滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #adb5bd;
                font-size: 14px;
            }
        """)
        self.preview_label.setText(t('image_preview_placeholder'))
        self.preview_label.setMinimumSize(200, 150)
        scroll_area.setWidget(self.preview_label)
        layout.addWidget(scroll_area, 1)

        # 预览信息
        self.preview_info_label = QLabel("")
        self.preview_info_label.setStyleSheet("color: #868e96; font-size: 12px;")
        self.preview_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_info_label)

        # 输出路径显示（右下角）
        output_path_layout = QHBoxLayout()
        output_path_layout.addStretch()
        self.output_path_label = QLabel(t('image_output_path', ''))
        self.output_path_label.setStyleSheet("color: #868e96; font-size: 12px;")
        output_path_layout.addWidget(self.output_path_label)
        layout.addLayout(output_path_layout)

        panel.setLayout(layout)
        return panel

    def _create_buttons(self, parent_layout):
        """创建按钮区域（进度条嵌入按钮行右侧）"""
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

        # 重置按钮
        self.reset_btn = AnimatedButton(t('image_reset'))
        self.reset_btn.setFixedSize(90, 36)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #ced4da;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_image)
        btn_layout.addWidget(self.reset_btn)

        # 保存按钮
        self.save_btn = AnimatedButton(t('image_save'))
        self.save_btn.setFixedSize(130, 36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
            QPushButton:pressed {
                background-color: #37b24d;
            }
        """)
        self.save_btn.clicked.connect(self._process_and_save)
        btn_layout.addWidget(self.save_btn)

        parent_layout.addLayout(btn_layout)

    def _load_config(self):
        """加载配置"""
        # 加载输出路径
        if self.config:
            save_path = self.config.get_save_path()
            if save_path:
                self.output_path_label.setText(t('image_output_path', save_path.replace('\\', '/')))

    def _update_preset_sizes(self):
        """更新预设尺寸列表"""
        self.preset_combo.clear()
        presets = PRESET_SIZES.get(self.lang, PRESET_SIZES['zh'])
        self.preset_combo.addItem(t('image_custom'))
        for key, (name, w, h) in presets.items():
            self.preset_combo.addItem(name, (w, h))

    def _update_id_photo_sizes(self):
        """更新证件照尺寸列表"""
        self.id_photo_size_combo.clear()
        sizes = ID_PHOTO_SIZES.get(self.lang, ID_PHOTO_SIZES['zh'])
        for key, (name, w, h) in sizes.items():
            self.id_photo_size_combo.addItem(name, (w, h))

    def _update_paper_sizes(self):
        """更新相纸尺寸列表"""
        self.paper_size_combo.clear()
        sizes = PAPER_SIZES.get(self.lang, PAPER_SIZES['zh'])
        for key, (name, w, h) in sizes.items():
            self.paper_size_combo.addItem(name, (w, h))

    def _on_mode_changed(self, button):
        """处理模式改变 - 切换显示对应设置区域"""
        mode_id = self.mode_group.id(button)
        
        self.rotate_group.setVisible(mode_id == 0)
        self.crop_group.setVisible(mode_id == 1)
        self.compress_group.setVisible(mode_id == 2)
        self.id_photo_group.setVisible(mode_id == 3)
        
        # 证件照排版模式下，触发预览更新
        if mode_id == 3 and self.original_image is not None:
            self._schedule_preview()

    def _on_angle_changed(self, index):
        """角度选择改变"""
        is_custom = index == 3  # 自定义角度
        self.custom_angle_label.setVisible(is_custom)
        self.custom_angle_spin.setVisible(is_custom)
        self._schedule_preview()

    def _on_preset_changed(self, index):
        """预设尺寸改变"""
        if index == 0:  # 自定义
            return
        
        data = self.preset_combo.currentData()
        if data:
            w, h = data
            self._updating_size = True
            self._updating_preset = True
            self.width_spin.setValue(w)
            self.height_spin.setValue(h)
            self._updating_preset = False
            self._updating_size = False
            self._schedule_preview()

    def _on_width_changed(self, value):
        """宽度改变时联动高度"""
        if self._updating_size or self._loading_image:
            return
        
        # 修改自定义尺寸时，预设自动变为自定义
        if not self._updating_preset:
            self._updating_preset = True
            self.preset_combo.setCurrentIndex(0)
            self._updating_preset = False
        
        if self.keep_ratio_checkbox.isChecked() and self.original_ratio > 0:
            self._updating_size = True
            try:
                new_height = int(value / self.original_ratio)
                self.height_spin.blockSignals(True)
                self.height_spin.setValue(new_height)
                self.height_spin.blockSignals(False)
            finally:
                self._updating_size = False
        
        self._schedule_preview()

    def _on_height_changed(self, value):
        """高度改变时联动宽度"""
        if self._updating_size or self._loading_image:
            return
        
        # 修改自定义尺寸时，预设自动变为自定义
        if not self._updating_preset:
            self._updating_preset = True
            self.preset_combo.setCurrentIndex(0)
            self._updating_preset = False
        
        if self.keep_ratio_checkbox.isChecked() and self.original_ratio > 0:
            self._updating_size = True
            try:
                new_width = int(value * self.original_ratio)
                self.width_spin.blockSignals(True)
                self.width_spin.setValue(new_width)
                self.width_spin.blockSignals(False)
            finally:
                self._updating_size = False
        
        self._schedule_preview()

    def _on_slider_changed(self, value):
        """滑块值改变（百分比）"""
        # 显示百分比
        self.size_value_label.setText(f'{value}%')
        
        # 更新预估大小提示（基于最高质量JPEG大小）
        if self.max_jpeg_size > 0:
            # 计算目标大小（基于最高质量JPEG大小）
            target_bytes = int(self.max_jpeg_size * value / 100)
            target_kb = target_bytes / 1024
            
            if target_kb >= 1024:
                size_str = f'{target_kb / 1024:.1f} MB'
            else:
                size_str = f'{target_kb:.1f} KB'
            
            # 显示最高质量JPEG大小作为参考
            max_kb = self.max_jpeg_size / 1024
            if max_kb >= 1024:
                max_str = f'{max_kb / 1024:.1f} MB'
            else:
                max_str = f'{max_kb:.1f} KB'
            
            self.estimate_label.setText(f'预估大小: {size_str} (最高质量: {max_str})')
        
        self._schedule_preview()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                self._load_image(path)

    def _browse_image(self):
        """浏览选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, t('image_select_file'), "",
            f"{t('image_files')} (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            self._load_image(file_path)

    def _load_image(self, file_path):
        """加载图片"""
        # 延迟检测PIL（优化启动速度）
        global HAS_PIL
        if HAS_PIL is None:
            try:
                from PIL import Image
                HAS_PIL = True
            except ImportError:
                HAS_PIL = False
        
        if not HAS_PIL:
            QMessageBox.critical(self, t('msg_error'), t('image_need_pil'))
            return

        # 设置加载标志，防止加载过程中触发预览
        self._loading_image = True
        
        try:
            from PIL import Image  # 在方法中导入
            
            # 显示文件路径
            self.file_input.setText(file_path)
            
            # 获取文件大小
            self.original_file_size = os.path.getsize(file_path)
            
            # 加载原始图片
            try:
                self.original_image = Image.open(file_path)
                self.original_file_path = file_path
                
                # 保存原始文件扩展名
                self.original_file_ext = os.path.splitext(file_path)[1].lower()
                
                print(f"[DEBUG] Original file extension: {self.original_file_ext}")
                
                # 计算原始宽高比
                width, height = self.original_image.size
                self.original_ratio = width / height if height > 0 else 1.0
                
                # 计算最高质量JPEG的大小（用于压缩参考）
                if self.original_image.mode == 'RGBA':
                    background = Image.new('RGB', self.original_image.size, (255, 255, 255))
                    background.paste(self.original_image, mask=self.original_image.split()[3])
                    temp_image = background
                elif self.original_image.mode != 'RGB':
                    temp_image = self.original_image.convert('RGB')
                else:
                    temp_image = self.original_image
                
                buffer = io.BytesIO()
                temp_image.save(buffer, format='JPEG', quality=95, optimize=True)
                self.max_jpeg_size = buffer.tell()
                
                print(f"[DEBUG] Loaded image: {file_path}")
                print(f"[DEBUG] Original file size: {self.original_file_size} bytes ({self.original_file_size/1024:.1f} KB)")
                print(f"[DEBUG] Max JPEG size (quality 95): {self.max_jpeg_size} bytes ({self.max_jpeg_size/1024:.1f} KB)")
                
                # 显示文件信息
                size_str = self._format_file_size(self.original_file_size)
                self.file_info_label.setText(t('image_file_info', width, height, size_str))
                
                # 设置默认裁剪尺寸为原图尺寸
                self._updating_size = True
                self.width_spin.setValue(width)
                self.height_spin.setValue(height)
                self._updating_size = False
                
            except Exception as img_error:
                QMessageBox.critical(self, t('msg_error'), f"无法加载图片: {img_error}")
                return
            
            # 更新预估大小提示
            self._update_slider_range()
            
        except Exception as e:
            QMessageBox.critical(self, t('msg_error'), t('image_load_failed', str(e)))
        finally:
            # 加载完成，清除标志
            self._loading_image = False
        
        # 显示预览（根据当前模式，在清除标志后执行）
        try:
            if self.id_photo_radio.isChecked():
                # 证件照排版模式下，显示排版后的预览
                self._auto_preview()
            else:
                # 其他模式下，显示原始图片预览
                self._display_preview_from_file(file_path)
        except Exception as preview_error:
            print(f"预览显示失败: {preview_error}")
    
    def _display_preview_from_file(self, file_path):
        """从文件直接显示预览图片（避免转换）"""
        try:
            # 直接使用 QPixmap 加载文件
            pixmap = QPixmap(file_path)
            
            if pixmap.isNull():
                print("无法从文件加载图片")
                return
            
            # 缩放以适应预览区域
            label_size = self.preview_label.size()
            if label_size.width() < 100:
                label_size = QSize(300, 200)
            
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
            # 更新预览信息
            if self.original_image:
                w, h = self.original_image.size
                self.preview_info_label.setText(t('image_preview_size', w, h))
            
        except Exception as e:
            print(f"预览显示错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_slider_range(self):
        """更新预估大小提示"""
        if self.max_jpeg_size > 0:
            # 获取当前百分比
            current_percent = self.size_slider.value()
            
            # 计算目标大小（基于最高质量JPEG大小）
            target_bytes = int(self.max_jpeg_size * current_percent / 100)
            target_kb = target_bytes / 1024
            
            if target_kb >= 1024:
                size_str = f'{target_kb / 1024:.1f} MB'
            else:
                size_str = f'{target_kb:.1f} KB'
            
            # 显示最高质量JPEG大小作为参考
            max_kb = self.max_jpeg_size / 1024
            if max_kb >= 1024:
                max_str = f'{max_kb / 1024:.1f} MB'
            else:
                max_str = f'{max_kb:.1f} KB'
            
            self.estimate_label.setText(f'预估大小: {size_str} (最高质量: {max_str})')

    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes >= 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.2f} MB'
        elif size_bytes >= 1024:
            return f'{size_bytes / 1024:.1f} KB'
        else:
            return f'{size_bytes} B'

    def _display_preview(self, image):
        """显示预览图片（用于处理后的图片）"""
        if image is None:
            return
        
        try:
            import tempfile
            
            # 使用系统临时目录创建临时文件（更安全）
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"_temp_preview_{id(self)}.jpg")
            
            # 根据模式选择保存格式
            if image.mode == 'RGBA':
                temp_path = os.path.join(temp_dir, f"_temp_preview_{id(self)}.png")
                image.save(temp_path, format='PNG')
            else:
                # 转换为RGB模式（JPEG不支持RGBA）
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(temp_path, format='JPEG', quality=95)
            
            # 从临时文件加载
            pixmap = QPixmap(temp_path)
            
            if not pixmap.isNull():
                # 缩放以适应预览区域
                label_size = self.preview_label.size()
                if label_size.width() < 100:
                    label_size = QSize(300, 200)
                
                scaled_pixmap = pixmap.scaled(
                    label_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 更新预览信息
                w, h = image.size
                self.preview_info_label.setText(t('image_preview_size', w, h))
            
            # 删除临时文件
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"Preview error: {e}")
            import traceback
            traceback.print_exc()

    def _schedule_preview(self):
        """安排预览刷新（延迟200ms，避免频繁刷新）"""
        if self._loading_image:
            return
        if self.original_image is not None:
            self.preview_timer.start(200)
    
    def _auto_preview(self):
        """自动预览处理效果"""
        if self.original_image is None or self._loading_image:
            return
        
        try:
            processed, compressed_data = self._apply_all_effects(self.original_image)
            self._display_preview(processed)
        except Exception as e:
            print(f"Auto preview error: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_all_effects(self, image):
        """应用所有启用的效果"""
        from PIL import Image
        
        result = image.copy()
        compressed_data = None
        
        # 证件照排版模式（单独处理）
        if self.id_photo_radio.isChecked():
            return self._create_id_photo_layout(image), None
        
        # 旋转
        if self.rotate_enable_check.isChecked():
            angle_index = self.angle_combo.currentIndex()
            if angle_index == 3:  # 自定义角度
                angle = self.custom_angle_spin.value()
            else:
                angles = [90, 180, 270]
                angle = angles[angle_index]
            result = result.rotate(-angle, expand=True)
        
        # 裁剪
        if self.crop_enable_check.isChecked():
            target_w = self.width_spin.value()
            target_h = self.height_spin.value()
            result = self._resize_image(result, target_w, target_h)
        
        # 压缩（仅对JPEG格式有效）
        if self.compress_enable_check.isChecked() and self.original_file_ext in ['.jpg', '.jpeg']:
            print(f"[DEBUG] Compression enabled for JPEG format")
            
            # 先转换为RGB模式（JPEG不支持RGBA）
            if result.mode == 'RGBA':
                background = Image.new('RGB', result.size, (255, 255, 255))
                background.paste(result, mask=result.split()[3])
                result_for_compress = background
            elif result.mode != 'RGB':
                result_for_compress = result.convert('RGB')
            else:
                result_for_compress = result
            
            # 先计算最高质量JPEG的大小
            buffer = io.BytesIO()
            result_for_compress.save(buffer, format='JPEG', quality=95, optimize=True)
            max_jpeg_size = buffer.tell()
            
            print(f"[DEBUG] Original file size: {self.original_file_size} bytes ({self.original_file_size/1024:.1f} KB)")
            print(f"[DEBUG] Max JPEG size (quality 95): {max_jpeg_size} bytes ({max_jpeg_size/1024:.1f} KB)")
            
            # 使用百分比计算目标大小（基于最高质量JPEG大小）
            percent = self.size_slider.value()
            target_bytes = int(max_jpeg_size * percent / 100)
            target_kb = target_bytes / 1024
            
            print(f"[DEBUG] Target size: {target_bytes} bytes ({target_kb:.1f} KB) at {percent}%")
            
            # 如果目标大小等于或超过最高质量JPEG能达到的大小，使用最高质量
            if target_bytes >= max_jpeg_size:
                print(f"[DEBUG] Target size ({target_bytes} bytes) >= max JPEG size ({max_jpeg_size} bytes)")
                print(f"[DEBUG] Using max quality JPEG: {max_jpeg_size} bytes")
                compressed_data = buffer.getvalue()
            else:
                print(f"[DEBUG] Target size ({target_bytes} bytes) < max JPEG size ({max_jpeg_size} bytes)")
                print(f"[DEBUG] Calling _compress_image to compress to {target_kb:.1f} KB")
                compressed_data = self._compress_image(result_for_compress, target_kb)
                print(f"[DEBUG] Compressed result: {len(compressed_data)} bytes ({len(compressed_data)/1024:.1f} KB)")
        elif self.compress_enable_check.isChecked():
            print(f"[DEBUG] Compression enabled but file format is {self.original_file_ext} (not JPEG)")
            print(f"[DEBUG] Compression will not be applied for non-JPEG formats")
        else:
            print(f"[DEBUG] Compression NOT enabled")
        
        return result, compressed_data

    def _create_id_photo_layout(self, image):
        """创建证件照排版图片"""
        from PIL import Image
        
        # 获取证件照尺寸
        photo_data = self.id_photo_size_combo.currentData()
        if not photo_data:
            photo_w, photo_h = 295, 413  # 默认1寸
        else:
            photo_w, photo_h = photo_data
        
        # 获取相纸尺寸
        paper_data = self.paper_size_combo.currentData()
        if not paper_data:
            paper_w, paper_h = 1205, 1795  # 默认4R
        else:
            paper_w, paper_h = paper_data
        
        # 获取排版方式
        is_horizontal = self.layout_horizontal_radio.isChecked()
        
        # 计算可排版数量
        margin = 20  # 边距（像素）
        spacing = 10  # 间距（像素）
        
        if is_horizontal:
            # 横向排布：证件照横向排列
            cols = (paper_w - 2 * margin + spacing) // (photo_w + spacing)
            rows = (paper_h - 2 * margin + spacing) // (photo_h + spacing)
        else:
            # 纵向排布：证件照纵向排列（旋转90度放置）
            cols = (paper_w - 2 * margin + spacing) // (photo_h + spacing)
            rows = (paper_h - 2 * margin + spacing) // (photo_w + spacing)
        
        cols = max(1, cols)
        rows = max(1, rows)
        count = cols * rows
        
        # 更新可排版数量提示
        self.id_photo_count_label.setText(t('id_photo_count', count))
        
        # 裁剪证件照
        cropped_photo = self._resize_image(image, photo_w, photo_h)
        
        # 如果是纵向排布，需要旋转证件照
        if not is_horizontal:
            cropped_photo = cropped_photo.rotate(-90, expand=True)
        
        # 创建相纸背景（白色）
        paper = Image.new('RGB', (paper_w, paper_h), (255, 255, 255))
        
        # 计算起始位置（居中排版）
        if is_horizontal:
            total_width = cols * photo_w + (cols - 1) * spacing
            total_height = rows * photo_h + (rows - 1) * spacing
        else:
            total_width = cols * photo_h + (cols - 1) * spacing
            total_height = rows * photo_w + (rows - 1) * spacing
        
        start_x = (paper_w - total_width) // 2
        start_y = (paper_h - total_height) // 2
        
        # 排版证件照
        for row in range(rows):
            for col in range(cols):
                if is_horizontal:
                    x = start_x + col * (photo_w + spacing)
                    y = start_y + row * (photo_h + spacing)
                else:
                    x = start_x + col * (photo_h + spacing)
                    y = start_y + row * (photo_w + spacing)
                
                paper.paste(cropped_photo, (x, y))
        
        return paper

    def _resize_image(self, image, target_w, target_h):
        """调整图片尺寸（保持比例居中裁剪）"""
        from PIL import Image
        
        w, h = image.size
        
        # 计算缩放比例
        ratio_w = target_w / w
        ratio_h = target_h / h
        ratio = max(ratio_w, ratio_h)
        
        # 缩放图片
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        scaled = image.resize((new_w, new_h), Image.LANCZOS)
        
        # 居中裁剪
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        
        return scaled.crop((left, top, right, bottom))

    def _compress_image(self, image, target_kb):
        """压缩图片到目标大小，返回压缩后的 bytes 数据"""
        from PIL import Image
        
        target_bytes = int(target_kb * 1024)
        
        print(f"[DEBUG] Target size: {target_bytes} bytes ({target_kb:.1f} KB)")
        
        # 转换为RGB模式（去除alpha通道）
        if image.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 先尝试最高质量，看看是否能达到目标大小
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95, optimize=True)
        max_size = buffer.tell()
        
        print(f"[DEBUG] Max quality size: {max_size} bytes")
        
        # 如果最高质量的大小已经小于目标，直接返回
        if max_size <= target_bytes:
            print(f"[DEBUG] No compression needed, size = {max_size} bytes")
            return buffer.getvalue()
        
        # 二分查找合适的质量
        min_quality = 1
        max_quality = 95
        
        best_buffer = None
        best_quality = min_quality
        best_size = 0  # 初始化为0，而不是inf
        
        # 先尝试最低质量，看看是否能达到目标大小
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=min_quality, optimize=True)
        min_size = buffer.tell()
        
        print(f"[DEBUG] Min quality size: {min_size} bytes")
        
        # 如果最低质量的大小仍然大于目标，返回最低质量的结果
        if min_size > target_bytes:
            print(f"[DEBUG] Cannot compress to target size, min size = {min_size} bytes")
            return buffer.getvalue()
        
        # 二分查找 - 寻找最接近目标大小但不超过的质量
        iteration = 0
        while min_quality <= max_quality:
            iteration += 1
            quality = (min_quality + max_quality) // 2
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            size = buffer.tell()
            
            print(f"[DEBUG] Iteration {iteration}: Quality {quality}, size {size} bytes, target {target_bytes} bytes")
            
            if size <= target_bytes:
                # 这个质量可以接受，记录下来
                current_buffer = buffer.getvalue()
                # 如果这个结果更接近目标大小（更大），更新最佳结果
                if size > best_size:
                    best_buffer = current_buffer
                    best_quality = quality
                    best_size = size
                # 尝试提高质量（寻找更大的文件）
                min_quality = quality + 1
            else:
                # 文件太大，降低质量
                max_quality = quality - 1
        
        # 如果找到了合适的结果，返回
        if best_buffer is not None:
            print(f"[DEBUG] Compressed to {len(best_buffer)} bytes with quality {best_quality}")
            return best_buffer
        
        # 如果没有找到，使用最低质量
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=1, optimize=True)
        print(f"[DEBUG] Fallback to quality 1, size = {buffer.tell()} bytes")
        return buffer.getvalue()

    def _reset_image(self):
        """重置为原始图片"""
        if self.original_image:
            # 切换至旋转图片模式
            self.rotate_radio.setChecked(True)
            self._on_mode_changed(self.rotate_radio)
            # 显示原始图片预览
            self._display_preview(self.original_image)
            # 重置裁剪尺寸为原图尺寸
            w, h = self.original_image.size
            self._updating_size = True
            self.width_spin.setValue(w)
            self.height_spin.setValue(h)
            self._updating_size = False

    def _clear_all(self):
        """清除所有设置项，回到默认状态"""
        # 清除图片数据
        self.original_image = None
        self.original_file_path = ''
        self.original_file_ext = ''
        self.original_file_size = 0
        self.max_jpeg_size = 0
        self.original_ratio = 1.0
        
        # 清除文件输入框
        self.file_input.clear()
        
        # 清除文件信息标签
        self.file_info_label.setText('')
        
        # 清除预览图片
        self.preview_label.clear()
        self.preview_label.setText(t('image_preview_placeholder'))
        self.preview_info_label.setText('')
        
        # 重置旋转设置
        self.rotate_enable_check.setChecked(False)
        self.angle_combo.setCurrentIndex(0)  # 90度
        self.custom_angle_spin.setValue(0)
        self.custom_angle_label.setVisible(False)
        self.custom_angle_spin.setVisible(False)
        
        # 重置裁剪设置
        self.crop_enable_check.setChecked(False)
        self.preset_combo.setCurrentIndex(0)  # 自定义
        self._updating_size = True
        self.width_spin.setValue(800)
        self.height_spin.setValue(600)
        self._updating_size = False
        self.keep_ratio_checkbox.setChecked(False)
        
        # 重置压缩设置
        self.compress_enable_check.setChecked(False)
        self.size_slider.setValue(100)  # 100%
        self.size_value_label.setText('100%')
        self.estimate_label.setText('')
        
        # 重置证件照排版设置
        self.id_photo_size_combo.setCurrentIndex(0)
        self.paper_size_combo.setCurrentIndex(0)
        self.layout_horizontal_radio.setChecked(True)
        self.id_photo_count_label.setText('')
        
        # 不清除保存路径输入框，保留用户设置的路径

    def _process_and_save(self):
        """处理并保存图片"""
        # 延迟检测PIL（优化启动速度）
        global HAS_PIL
        if HAS_PIL is None:
            try:
                from PIL import Image
                HAS_PIL = True
            except ImportError:
                HAS_PIL = False
        
        if not HAS_PIL:
            QMessageBox.critical(self, t('msg_error'), t('image_need_pil'))
            return

        if self.original_image is None:
            self.warning_requested.emit(t('image_no_image'))
            return

        # 证件照排版模式不需要检查启用功能
        if not self.id_photo_radio.isChecked():
            # 检查是否有启用的功能
            if not (self.rotate_enable_check.isChecked() or 
                    self.crop_enable_check.isChecked() or 
                    self.compress_enable_check.isChecked()):
                self.warning_requested.emit(t('image_no_effect'))
                return

        # 使用全局保存路径
        save_path = self.config.get_save_path() if self.config else ""
        if not save_path:
            self.warning_requested.emit(t('msg_select_path'))
            return

        # 显示进度条，禁用按钮
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.is_processing = True
        
        def do_process():
            try:
                from PIL import Image  # 在线程中导入
                
                # 使用信号更新进度条（线程安全）
                self.progress_updated.emit(20)
                
                processed, compressed_data = self._apply_all_effects(self.original_image)
                
                self.progress_updated.emit(60)
                
                # 生成输出文件名
                if self.original_file_path:
                    base_name = os.path.splitext(os.path.basename(self.original_file_path))[0]
                    if self.id_photo_radio.isChecked():
                        # 证件照排版使用 JPEG 格式
                        default_name = f"{base_name}_id_photo_layout.jpg"
                    else:
                        default_name = f"{base_name}_processed{self.original_file_ext}"
                else:
                    if self.id_photo_radio.isChecked():
                        default_name = f"id_photo_layout.jpg"
                    else:
                        default_name = f"processed_image{self.original_file_ext or '.png'}"
                
                # 使用全局保存路径（目录）+ 文件名
                final_save_path = os.path.join(save_path, default_name)
                
                print(f"[DEBUG] Saving to: {final_save_path}")
                print(f"[DEBUG] Original format: {self.original_file_ext}")
                
                # 证件照排版模式 - 保存为高质量 JPEG
                if self.id_photo_radio.isChecked():
                    if processed.mode == 'RGBA':
                        background = Image.new('RGB', processed.size, (255, 255, 255))
                        background.paste(processed, mask=processed.split()[3])
                        processed = background
                    elif processed.mode != 'RGB':
                        processed = processed.convert('RGB')
                    processed.save(final_save_path, format='JPEG', quality=95)
                    print(f"[DEBUG] Saved ID photo layout JPEG to {final_save_path}")
                # 如果有压缩数据，直接写入（仅适用于JPEG）
                elif compressed_data is not None and self.original_file_ext in ['.jpg', '.jpeg']:
                    with open(final_save_path, 'wb') as f:
                        f.write(compressed_data)
                    print(f"[DEBUG] Saved compressed JPEG to {final_save_path}, size = {len(compressed_data)} bytes ({len(compressed_data)/1024:.1f} KB)")
                else:
                    # 根据原始格式保存
                    if self.original_file_ext in ['.jpg', '.jpeg']:
                        # JPEG格式
                        if processed.mode == 'RGBA':
                            background = Image.new('RGB', processed.size, (255, 255, 255))
                            background.paste(processed, mask=processed.split()[3])
                            processed = background
                        elif processed.mode != 'RGB':
                            processed = processed.convert('RGB')
                        processed.save(final_save_path, format='JPEG', quality=100)
                        print(f"[DEBUG] Saved JPEG to {final_save_path}")
                    elif self.original_file_ext == '.png':
                        # PNG格式（保持透明通道）
                        processed.save(final_save_path, format='PNG')
                        print(f"[DEBUG] Saved PNG to {final_save_path}")
                    elif self.original_file_ext in ['.bmp', '.webp', '.gif']:
                        # 其他格式
                        format_name = self.original_file_ext[1:].upper()
                        if format_name == 'GIF':
                            processed.save(final_save_path, format='GIF', save_all=True)
                        else:
                            processed.save(final_save_path, format=format_name)
                        print(f"[DEBUG] Saved {format_name} to {final_save_path}")
                    else:
                        # 默认保存为PNG
                        processed.save(final_save_path, format='PNG')
                        print(f"[DEBUG] Saved PNG (default) to {final_save_path}")
                
                self.progress_updated.emit(100)
                self.process_finished.emit(True, final_save_path)
                
            except Exception as e:
                print(f"[DEBUG] Save error: {e}")
                import traceback
                traceback.print_exc()
                self.process_finished.emit(False, str(e))

        thread = threading.Thread(target=do_process, daemon=True)
        thread.start()

    def on_process_finished(self, success, message):
        """处理完成回调"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.save_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.is_processing = False
        
        if success:
            # 清除已选择的图片，重置设置项
            self._clear_all()
        else:
            # 显示错误消息
            QMessageBox.critical(self, t('msg_error'), t('image_failed', message))

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)

        # 更新界面文本
        self.import_group.setTitle(t('image_import'))
        self.file_input.setPlaceholderText(t('image_import_placeholder'))
        self.tip_label.setText(t('image_import_tip'))
        self.browse_btn.setText(t('image_browse'))
        
        self.process_group.setTitle(t('image_process_mode'))
        self.rotate_radio.setText(t('image_rotate'))
        self.crop_radio.setText(t('image_crop'))
        self.compress_radio.setText(t('image_compress'))
        self.id_photo_radio.setText(t('image_id_photo_layout'))
        
        self.rotate_enable_check.setText(t('image_enable'))
        self.angle_combo.setItemText(3, t('image_angle_custom'))
        self.custom_angle_label.setText(t('image_custom_angle'))
        
        self.crop_enable_check.setText(t('image_enable'))
        self._update_preset_sizes()
        self.keep_ratio_checkbox.setText(t('image_keep_ratio'))
        
        self.compress_enable_check.setText(t('image_enable'))
        self.estimate_label.setText("")
        
        # 更新证件照排版相关文本
        self._update_id_photo_sizes()
        self._update_paper_sizes()
        self.layout_horizontal_radio.setText(t('id_photo_layout_horizontal'))
        self.layout_vertical_radio.setText(t('id_photo_layout_vertical'))
        
        self.reset_btn.setText(t('image_reset'))
        self.save_btn.setText(t('image_save'))
        
        if self.original_image is None:
            self.preview_label.setText(t('image_preview_placeholder'))
        
        # 重新加载输出路径
        self._load_config()