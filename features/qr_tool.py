# -*- coding: utf-8 -*-
"""
DeskHelperGUI 二维码工具功能模块
生成和识别二维码/条形码
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QStackedWidget, QFrame, QGridLayout,
    QApplication, QSplitter, QFileDialog, QTextEdit, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QColor

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t
from ui_components import AnimatedButton


class QRToolWidget(QWidget):
    """二维码工具功能界面"""

    # 信号
    warning_requested = pyqtSignal(str)
    success_requested = pyqtSignal(str)

    # 模式定义
    MODES = ['text', 'url', 'wifi', 'card', 'contact', 'decode']

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.current_mode = 'text'
        self.is_barcode = False
        self.generated_image = None
        self.decoded_file = None  # 解码模式：选中的文件
        self.decoded_result = None  # 解码结果
        
        # 颜色设置
        self.foreground_color = QColor(0, 0, 0)  # 默认黑色主体
        self.background_color = QColor(255, 255, 255)  # 默认白色背景
        self.transparent_background = False  # 是否透明背景

        set_language(lang)
        self._init_ui()
        self._load_config()
        self.setAcceptDrops(True)  # 启用拖拽

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部导航栏
        self._create_nav_bar(main_layout)

        # 主内容区域（左右分割）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：输入区域
        left_panel = self._create_input_panel()
        left_panel.setMinimumWidth(280)
        splitter.addWidget(left_panel)

        # 右侧：预览区域
        right_panel = self._create_preview_panel()
        right_panel.setMinimumWidth(250)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        # 底部操作区域
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_nav_bar(self, parent_layout):
        """创建顶部导航栏"""
        nav_frame = QFrame()
        nav_frame.setFixedHeight(50)  # 固定导航栏高度
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
            'text': t('qr_mode_text'),
            'url': t('qr_mode_url'),
            'wifi': t('qr_mode_wifi'),
            'card': t('qr_mode_card'),
            'contact': t('qr_mode_contact'),
            'decode': t('qr_mode_decode')
        }

        for mode in self.MODES:
            btn = QPushButton(mode_labels[mode])
            btn.setCheckable(True)
            btn.setChecked(mode == self.current_mode)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(70)  # 最小宽度，允许扩展
            btn.setStyleSheet(self._get_mode_btn_style(mode == self.current_mode))
            btn.clicked.connect(lambda checked, m=mode: self._switch_mode(m))
            nav_layout.addWidget(btn)
            self.mode_buttons[mode] = btn

        nav_layout.addStretch()

        # 二维码/条形码切换按钮
        self.type_toggle_btn = QPushButton(t('qr_type_barcode'))
        self.type_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.type_toggle_btn.setFixedWidth(80)  # 固定按钮宽度
        self.type_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.type_toggle_btn.clicked.connect(self._toggle_type)
        nav_layout.addWidget(self.type_toggle_btn)

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
        # 清除当前模式的输入内容
        self._clear_current_inputs()

        self.current_mode = mode

        # 更新按钮样式
        for m, btn in self.mode_buttons.items():
            btn.setChecked(m == mode)
            btn.setStyleSheet(self._get_mode_btn_style(m == mode))

        # 切换输入界面
        self.input_stack.setCurrentIndex(self.MODES.index(mode))

        # 解码模式特殊处理
        if mode == 'decode':
            # 隐藏备注输入框
            self.remark_container.setVisible(False)
            # 隐藏颜色选择区域
            self.color_frame.setVisible(False)
            # 隐藏导出选项
            self.options_frame.setVisible(False)
            # 显示解码结果文本区域
            self.preview_label.setVisible(False)
            self.result_text_edit.setVisible(True)
            # 隐藏二维码/条形码切换按钮
            self.type_toggle_btn.setVisible(False)
        else:
            # 显示备注输入框
            self.remark_container.setVisible(True)
            # 显示颜色选择区域
            self.color_frame.setVisible(True)
            # 显示导出选项
            self.options_frame.setVisible(True)
            # 显示预览图片区域
            self.preview_label.setVisible(True)
            self.result_text_edit.setVisible(False)
            # 显示二维码/条形码切换按钮
            self.type_toggle_btn.setVisible(True)

        # 实时生成预览
        self._generate_preview()

    def _clear_current_inputs(self):
        """清除当前模式的输入内容"""
        mode = self.current_mode

        if mode == 'text':
            self.text_input.clear()
        elif mode == 'url':
            self.url_input.clear()
        elif mode == 'wifi':
            self.wifi_ssid_input.clear()
            self.wifi_password_input.clear()
            self.wifi_type_combo.setCurrentIndex(0)
        elif mode == 'card':
            for input_field in self.card_inputs.values():
                input_field.clear()
        elif mode == 'contact':
            self.contact_name_input.clear()
            self.contact_phone_input.clear()
        elif mode == 'decode':
            self.decode_file_input.clear()
            self.decoded_file = None
            self.decoded_result = None
            self.result_text_edit.clear()
            self.preview_label.clear()

        # 清除备注
        self.remark_input.clear()

    def _toggle_type(self):
        """切换二维码/条形码"""
        self.is_barcode = not self.is_barcode
        if self.is_barcode:
            self.type_toggle_btn.setText(t('qr_type_qrcode'))
        else:
            self.type_toggle_btn.setText(t('qr_type_barcode'))

        self._generate_preview()

    def _create_input_panel(self):
        """创建左侧输入面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # 标题（无背景框）
        title_label = QLabel(t('qr_content'))
        title_label.setStyleSheet("color: #495057; font-size: 14px; font-weight: bold; background: transparent;")
        layout.addWidget(title_label)

        # 使用StackedWidget切换不同模式的输入界面
        self.input_stack = QStackedWidget()

        # 文本模式
        text_widget = self._create_text_input()
        self.input_stack.addWidget(text_widget)

        # URL模式
        url_widget = self._create_url_input()
        self.input_stack.addWidget(url_widget)

        # WiFi模式
        wifi_widget = self._create_wifi_input()
        self.input_stack.addWidget(wifi_widget)

        # 名片模式
        card_widget = self._create_card_input()
        self.input_stack.addWidget(card_widget)

        # 联系信息模式
        contact_widget = self._create_contact_input()
        self.input_stack.addWidget(contact_widget)

        # 解码模式
        decode_widget = self._create_decode_input()
        self.input_stack.addWidget(decode_widget)

        layout.addWidget(self.input_stack)

        # 备注输入框（解码模式下隐藏）
        self.remark_container = QWidget()
        remark_layout = QVBoxLayout()
        remark_layout.setContentsMargins(0, 0, 0, 0)
        remark_layout.setSpacing(0)

        remark_label = QLabel(t('qr_remark'))
        remark_label.setStyleSheet("color: #868e96; font-size: 12px; background: transparent;")
        remark_layout.addWidget(remark_label)

        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText(t('qr_remark_placeholder'))
        self.remark_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.remark_input.textChanged.connect(self._generate_preview)
        remark_layout.addWidget(self.remark_input)

        self.remark_container.setLayout(remark_layout)
        layout.addWidget(self.remark_container)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_text_input(self):
        """创建文本模式输入"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText(t('qr_text_placeholder'))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 8px 0px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.text_input.textChanged.connect(self._generate_preview)
        layout.addWidget(self.text_input)

        container.setLayout(layout)
        return container

    def _create_url_input(self):
        """创建URL模式输入"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(t('qr_url_placeholder'))
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 8px 0px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.url_input.textChanged.connect(self._generate_preview)
        layout.addWidget(self.url_input)

        container.setLayout(layout)
        return container

    def _create_wifi_input(self):
        """创建WiFi模式输入"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignTop)

        # 网络名称
        ssid_row = QHBoxLayout()
        ssid_row.setSpacing(8)
        self.wifi_ssid_label = QLabel(t('qr_wifi_ssid'))
        self.wifi_ssid_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        self.wifi_ssid_label.setFixedWidth(50)
        ssid_row.addWidget(self.wifi_ssid_label)

        self.wifi_ssid_input = QLineEdit()
        self.wifi_ssid_input.setPlaceholderText(t('qr_wifi_ssid_placeholder'))
        self.wifi_ssid_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.wifi_ssid_input.textChanged.connect(self._generate_preview)
        ssid_row.addWidget(self.wifi_ssid_input)
        main_layout.addLayout(ssid_row)

        # 密码
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)
        self.wifi_pwd_label = QLabel(t('qr_wifi_password'))
        self.wifi_pwd_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        self.wifi_pwd_label.setFixedWidth(50)
        pwd_row.addWidget(self.wifi_pwd_label)

        self.wifi_password_input = QLineEdit()
        self.wifi_password_input.setPlaceholderText(t('qr_wifi_password_placeholder'))
        self.wifi_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.wifi_password_input.textChanged.connect(self._generate_preview)
        pwd_row.addWidget(self.wifi_password_input)
        main_layout.addLayout(pwd_row)

        # 加密类型
        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        self.wifi_type_label = QLabel(t('qr_wifi_type'))
        self.wifi_type_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        self.wifi_type_label.setFixedWidth(50)
        type_row.addWidget(self.wifi_type_label)

        self.wifi_type_combo = QComboBox()
        self.wifi_type_combo.addItems(['WPA/WPA2', 'WEP', t('qr_wifi_no_encrypt')])
        self.wifi_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #dee2e6;
                selection-background-color: #339af0;
                selection-color: white;
            }
        """)
        self.wifi_type_combo.currentIndexChanged.connect(self._generate_preview)
        type_row.addWidget(self.wifi_type_combo)
        main_layout.addLayout(type_row)

        widget.setLayout(main_layout)
        return widget

    def _create_card_input(self):
        """创建名片模式输入（vCard格式）"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignTop)

        fields = [
            ('qr_card_name', 'qr_card_name_placeholder', 'card_name'),
            ('qr_card_phone', 'qr_card_phone_placeholder', 'card_phone'),
            ('qr_card_email', 'qr_card_email_placeholder', 'card_email'),
            ('qr_card_company', 'qr_card_company_placeholder', 'card_company'),
            ('qr_card_address', 'qr_card_address_placeholder', 'card_address'),
        ]

        self.card_inputs = {}
        self.card_labels = {}
        for label_key, placeholder_key, attr_name in fields:
            # 使用水平布局：标签在左，输入框在右
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            label = QLabel(t(label_key))
            label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
            label.setFixedWidth(50)
            row_layout.addWidget(label)
            self.card_labels[attr_name] = label

            input_field = QLineEdit()
            input_field.setPlaceholderText(t(placeholder_key))
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 1px solid #339af0;
                }
            """)
            input_field.textChanged.connect(self._generate_preview)
            row_layout.addWidget(input_field)
            self.card_inputs[attr_name] = input_field

            main_layout.addLayout(row_layout)

        widget.setLayout(main_layout)
        return widget

    def _create_contact_input(self):
        """创建联系信息模式输入"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignTop)

        # 姓名
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        self.contact_name_label = QLabel(t('qr_contact_name'))
        self.contact_name_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        self.contact_name_label.setFixedWidth(50)
        name_row.addWidget(self.contact_name_label)

        self.contact_name_input = QLineEdit()
        self.contact_name_input.setPlaceholderText(t('qr_contact_name_placeholder'))
        self.contact_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.contact_name_input.textChanged.connect(self._generate_preview)
        name_row.addWidget(self.contact_name_input)
        main_layout.addLayout(name_row)

        # 电话
        phone_row = QHBoxLayout()
        phone_row.setSpacing(8)
        self.contact_phone_label = QLabel(t('qr_contact_phone'))
        self.contact_phone_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        self.contact_phone_label.setFixedWidth(50)
        phone_row.addWidget(self.contact_phone_label)

        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setPlaceholderText(t('qr_contact_phone_placeholder'))
        self.contact_phone_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.contact_phone_input.textChanged.connect(self._generate_preview)
        phone_row.addWidget(self.contact_phone_input)
        main_layout.addLayout(phone_row)

        widget.setLayout(main_layout)
        return widget

    def _create_decode_input(self):
        """创建解码模式输入"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        # 文件选择区域
        self.decode_file_label = QLabel(t('qr_decode_file'))
        self.decode_file_label.setStyleSheet("color: #495057; font-size: 12px; background: transparent;")
        layout.addWidget(self.decode_file_label)

        # 文件路径输入框和按钮
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.decode_file_input = QLineEdit()
        self.decode_file_input.setPlaceholderText(t('qr_decode_file_placeholder'))
        self.decode_file_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #339af0;
            }
        """)
        self.decode_file_input.setReadOnly(True)
        file_row.addWidget(self.decode_file_input)

        # 浏览按钮
        self.decode_browse_btn = QPushButton(t('qr_decode_browse'))
        self.decode_browse_btn.setCursor(Qt.PointingHandCursor)
        self.decode_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        self.decode_browse_btn.clicked.connect(self._browse_decode_file)
        file_row.addWidget(self.decode_browse_btn)

        layout.addLayout(file_row)

        # 拖拽提示
        self.decode_drag_hint = QLabel(t('qr_decode_drag_hint'))
        self.decode_drag_hint.setStyleSheet("color: #868e96; font-size: 11px; background: transparent;")
        self.decode_drag_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.decode_drag_hint)

        widget.setLayout(layout)
        return widget

    def _browse_decode_file(self):
        """浏览选择解码文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t('qr_decode_select_file'),
            "",
            t('qr_decode_image_files')
        )
        if file_path:
            self.decoded_file = file_path
            self.decode_file_input.setText(file_path)
            self._decode_image()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if self.current_mode == 'decode' and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if self.current_mode != 'decode':
            return

        urls = event.mimeData().urls()
        if not urls:
            return

        # 获取第一个文件
        first_path = urls[0].toLocalFile()
        if os.path.isfile(first_path):
            # 检查是否是图片文件
            ext = os.path.splitext(first_path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
                self.decoded_file = first_path
                self.decode_file_input.setText(first_path)
                self._decode_image()
            else:
                self.warning_requested.emit(t('qr_decode_image_only'))
        else:
            self.warning_requested.emit(t('qr_decode_file_only'))

    def _decode_image(self):
        """解码图片中的二维码/条形码"""
        if not self.decoded_file:
            return

        try:
            from pyzbar.pyzbar import decode
            from PIL import Image

            # 加载图片
            img = Image.open(self.decoded_file)

            # 解码
            results = decode(img)

            if results:
                # 显示解码结果
                result_text = ""
                for i, result in enumerate(results):
                    result_text += f"{result.data.decode('utf-8', errors='ignore')}"
                    if i < len(results) - 1:
                        result_text += "\n"

                self.decoded_result = result_text
                self.result_text_edit.setText(result_text)

                # 显示图片预览
                self._show_decode_preview(img)

                self.success_requested.emit(t('qr_decode_success'))
            else:
                self.decoded_result = None
                self.result_text_edit.setText(t('qr_decode_no_result'))
                self.warning_requested.emit(t('qr_decode_no_result'))

        except Exception as e:
            self.decoded_result = None
            self.result_text_edit.setText(t('qr_decode_error'))
            self.warning_requested.emit(t('qr_decode_error'))

    def _show_decode_preview(self, img):
        """显示解码图片预览"""
        from io import BytesIO

        # 转换为RGB
        if hasattr(img, 'convert'):
            img = img.convert('RGB')

        # 使用 BytesIO 保存图像
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # 加载到 QImage
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        # 缩放显示
        max_size = 200
        if pixmap.width() > max_size or pixmap.height() > max_size:
            scaled_pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        else:
            self.preview_label.setPixmap(pixmap)

    def _create_preview_panel(self):
        """创建右侧预览面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # 标题
        self.preview_title_label = QLabel(t('qr_preview'))
        self.preview_title_label.setStyleSheet("color: #495057; font-size: 14px; font-weight: bold; background: transparent;")
        self.preview_title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_title_label)

        # 预览图片区域（生成模式）
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.preview_label, stretch=1)

        # 解码结果文本区域（解码模式）
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        self.result_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.result_text_edit.setVisible(False)  # 默认隐藏
        layout.addWidget(self.result_text_edit, stretch=1)

        # 备注预览
        self.remark_preview_label = QLabel()
        self.remark_preview_label.setAlignment(Qt.AlignCenter)
        self.remark_preview_label.setStyleSheet("color: #868e96; font-size: 11px; background: transparent;")
        self.remark_preview_label.setWordWrap(True)
        layout.addWidget(self.remark_preview_label)

        # 颜色选择区域
        self.color_frame = QFrame()
        self.color_frame.setStyleSheet("background: transparent;")
        color_layout = QGridLayout()
        color_layout.setSpacing(8)
        color_layout.setContentsMargins(0, 0, 0, 0)

        # 主体颜色
        self.fg_color_label = QLabel(t('qr_foreground_color'))
        self.fg_color_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        color_layout.addWidget(self.fg_color_label, 0, 0)

        self.fg_color_btn = QPushButton()
        self.fg_color_btn.setFixedSize(40, 24)
        self.fg_color_btn.setCursor(Qt.PointingHandCursor)
        self._update_color_button(self.fg_color_btn, self.foreground_color)
        self.fg_color_btn.clicked.connect(self._choose_foreground_color)
        color_layout.addWidget(self.fg_color_btn, 0, 1)

        # 背景颜色
        self.bg_color_label = QLabel(t('qr_background_color'))
        self.bg_color_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        color_layout.addWidget(self.bg_color_label, 0, 2)

        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(40, 24)
        self.bg_color_btn.setCursor(Qt.PointingHandCursor)
        self._update_color_button(self.bg_color_btn, self.background_color, self.transparent_background)
        self.bg_color_btn.clicked.connect(self._choose_background_color)
        color_layout.addWidget(self.bg_color_btn, 0, 3)

        # 透明背景复选框
        self.transparent_checkbox = QPushButton(t('qr_transparent'))
        self.transparent_checkbox.setCheckable(True)
        self.transparent_checkbox.setChecked(self.transparent_background)
        self.transparent_checkbox.setCursor(Qt.PointingHandCursor)
        self.transparent_checkbox.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #339af0;
                color: white;
                border: 1px solid #339af0;
            }
            QPushButton:hover {
                border: 1px solid #adb5bd;
            }
        """)
        self.transparent_checkbox.toggled.connect(self._on_transparent_toggled)
        color_layout.addWidget(self.transparent_checkbox, 0, 4)

        color_layout.setColumnStretch(5, 1)  # 最后一列拉伸
        self.color_frame.setLayout(color_layout)
        layout.addWidget(self.color_frame)

        # 导出选项
        self.options_frame = QFrame()
        self.options_frame.setStyleSheet("background: transparent;")
        options_layout = QGridLayout()
        options_layout.setSpacing(8)
        options_layout.setContentsMargins(0, 0, 0, 0)

        combo_style = """
            QComboBox {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 60px;
                max-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #dee2e6;
                selection-background-color: #339af0;
            }
        """

        # 第一行：尺寸 + 格式
        self.size_label = QLabel(t('qr_size'))
        self.size_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        options_layout.addWidget(self.size_label, 0, 0)

        self.size_combo = QComboBox()
        self.size_combo.addItems(['256', '512', '1024'])
        self.size_combo.setStyleSheet(combo_style)
        options_layout.addWidget(self.size_combo, 0, 1)

        self.format_label = QLabel(t('qr_format'))
        self.format_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        options_layout.addWidget(self.format_label, 0, 2)

        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'JPG'])
        self.format_combo.setStyleSheet(combo_style)
        options_layout.addWidget(self.format_combo, 0, 3)

        # 第二行：容错级别
        self.error_label = QLabel(t('qr_error_level'))
        self.error_label.setStyleSheet("color: #495057; font-size: 11px; background: transparent;")
        options_layout.addWidget(self.error_label, 1, 0)

        self.error_level_combo = QComboBox()
        self.error_level_combo.addItems(['L', 'M', 'Q', 'H'])
        self.error_level_combo.setStyleSheet(combo_style)
        options_layout.addWidget(self.error_level_combo, 1, 1)

        options_layout.setColumnStretch(4, 1)  # 最后一列拉伸

        self.options_frame.setLayout(options_layout)
        layout.addWidget(self.options_frame)

        # 导出路径显示
        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #adb5bd; font-size: 11px; background: transparent;")
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        panel.setLayout(layout)
        return panel

    def _create_buttons(self, parent_layout):
        """创建底部按钮区域"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_layout.addStretch()  # 添加弹性空间，让按钮靠右

        # 开始导出按钮
        self.export_btn = AnimatedButton(t('qr_export_start'))
        self.export_btn.setFixedSize(120, 34)
        self.export_btn.setStyleSheet("""
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
        self.export_btn.clicked.connect(self._export_image)
        btn_layout.addWidget(self.export_btn)

        parent_layout.addLayout(btn_layout)

    def _update_path_label(self):
        """更新路径标签"""
        if self.config:
            save_path = self.config.get_save_path()
            if save_path:
                self.path_label.setText(f"{t('save_path')}: {save_path}")
            else:
                self.path_label.setText(f"{t('save_path')}: {t('not_configured')}")
        else:
            self.path_label.setText(f"{t('save_path')}: {t('not_configured')}")

    def _load_config(self):
        """加载配置"""
        self._update_path_label()

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)
        self._update_ui_text()
        self._generate_preview()

    def _update_ui_text(self):
        """更新界面文本"""
        # 更新模式按钮
        mode_labels = {
            'text': t('qr_mode_text'),
            'url': t('qr_mode_url'),
            'wifi': t('qr_mode_wifi'),
            'card': t('qr_mode_card'),
            'contact': t('qr_mode_contact'),
            'decode': t('qr_mode_decode')
        }
        for mode, btn in self.mode_buttons.items():
            if mode in mode_labels:
                btn.setText(mode_labels[mode])

        # 更新类型切换按钮
        if self.is_barcode:
            self.type_toggle_btn.setText(t('qr_type_qrcode'))
        else:
            self.type_toggle_btn.setText(t('qr_type_barcode'))

        # 更新导出按钮
        self.export_btn.setText(t('qr_export_start'))
        self._update_path_label()

        # 更新文本模式占位符
        if hasattr(self, 'text_input'):
            self.text_input.setPlaceholderText(t('qr_text_placeholder'))

        # 更新URL模式占位符
        if hasattr(self, 'url_input'):
            self.url_input.setPlaceholderText(t('qr_url_placeholder'))

        # 更新WiFi模式标签和占位符
        if hasattr(self, 'wifi_ssid_label'):
            self.wifi_ssid_label.setText(t('qr_wifi_ssid'))
            self.wifi_ssid_input.setPlaceholderText(t('qr_wifi_ssid_placeholder'))
            self.wifi_pwd_label.setText(t('qr_wifi_password'))
            self.wifi_password_input.setPlaceholderText(t('qr_wifi_password_placeholder'))
            self.wifi_type_label.setText(t('qr_wifi_type'))
            # 更新下拉框选项
            self.wifi_type_combo.setItemText(2, t('qr_wifi_no_encrypt'))

        # 更新名片模式标签和占位符
        if hasattr(self, 'card_labels'):
            card_fields = [
                ('card_name', 'qr_card_name', 'qr_card_name_placeholder'),
                ('card_phone', 'qr_card_phone', 'qr_card_phone_placeholder'),
                ('card_email', 'qr_card_email', 'qr_card_email_placeholder'),
                ('card_company', 'qr_card_company', 'qr_card_company_placeholder'),
                ('card_address', 'qr_card_address', 'qr_card_address_placeholder'),
            ]
            for attr_name, label_key, placeholder_key in card_fields:
                if attr_name in self.card_labels:
                    self.card_labels[attr_name].setText(t(label_key))
                if attr_name in self.card_inputs:
                    self.card_inputs[attr_name].setPlaceholderText(t(placeholder_key))

        # 更新联系信息模式标签和占位符
        if hasattr(self, 'contact_name_label'):
            self.contact_name_label.setText(t('qr_contact_name'))
            self.contact_name_input.setPlaceholderText(t('qr_contact_name_placeholder'))
            self.contact_phone_label.setText(t('qr_contact_phone'))
            self.contact_phone_input.setPlaceholderText(t('qr_contact_phone_placeholder'))

        # 更新解码模式标签和占位符
        if hasattr(self, 'decode_file_label'):
            self.decode_file_label.setText(t('qr_decode_file'))
            self.decode_file_input.setPlaceholderText(t('qr_decode_file_placeholder'))
            self.decode_browse_btn.setText(t('qr_decode_browse'))
            self.decode_drag_hint.setText(t('qr_decode_drag_hint'))

        # 更新备注标签和占位符
        if hasattr(self, 'remark_input'):
            # 查找备注标签
            if hasattr(self, 'remark_container'):
                remark_layout = self.remark_container.layout()
                if remark_layout:
                    remark_label = remark_layout.itemAt(0)
                    if remark_label and remark_label.widget():
                        remark_label.widget().setText(t('qr_remark'))
            self.remark_input.setPlaceholderText(t('qr_remark_placeholder'))

        # 更新预览面板标签
        if hasattr(self, 'preview_title_label'):
            self.preview_title_label.setText(t('qr_preview'))
        if hasattr(self, 'size_label'):
            self.size_label.setText(t('qr_size'))
        if hasattr(self, 'format_label'):
            self.format_label.setText(t('qr_format'))
        if hasattr(self, 'error_label'):
            self.error_label.setText(t('qr_error_level'))
        
        # 更新颜色标签
        if hasattr(self, 'fg_color_label'):
            self.fg_color_label.setText(t('qr_foreground_color'))
        if hasattr(self, 'bg_color_label'):
            self.bg_color_label.setText(t('qr_background_color'))
        if hasattr(self, 'transparent_checkbox'):
            self.transparent_checkbox.setText(t('qr_transparent'))

    def _get_content(self):
        """获取当前模式的二维码内容"""
        mode = self.current_mode

        if mode == 'text':
            return self.text_input.text()

        elif mode == 'url':
            url = self.url_input.text()
            if url and not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url

        elif mode == 'wifi':
            ssid = self.wifi_ssid_input.text()
            password = self.wifi_password_input.text()
            type_idx = self.wifi_type_combo.currentIndex()
            type_map = ['WPA', 'WEP', 'nopass']
            wifi_type = type_map[type_idx]

            if not ssid:
                return ''

            content = f'WIFI:T:{wifi_type};S:{ssid};P:{password};;'
            return content

        elif mode == 'card':
            name = self.card_inputs['card_name'].text()
            phone = self.card_inputs['card_phone'].text()
            email = self.card_inputs['card_email'].text()
            company = self.card_inputs['card_company'].text()
            address = self.card_inputs['card_address'].text()

            if not name:
                return ''

            vcard = 'BEGIN:VCARD\nVERSION:3.0\n'
            vcard += f'N:{name}\nFN:{name}\n'
            if phone:
                vcard += f'TEL:{phone}\n'
            if email:
                vcard += f'EMAIL:{email}\n'
            if company:
                vcard += f'ORG:{company}\n'
            if address:
                vcard += f'ADR:;;{address}\n'
            vcard += 'END:VCARD'
            return vcard

        elif mode == 'contact':
            name = self.contact_name_input.text()
            phone = self.contact_phone_input.text()

            if self.is_barcode:
                return phone if phone else ''
            else:
                if name and phone:
                    return f'{name}\n{phone}'
                elif phone:
                    return phone
                elif name:
                    return name
                return ''

        return ''

    def _update_color_button(self, button, color, transparent=False):
        """更新颜色按钮显示"""
        if transparent:
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 2px dashed #adb5bd;
                    border-radius: 4px;
                }
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }}
            """)

    def _choose_foreground_color(self):
        """选择主体颜色"""
        color = QColorDialog.getColor(self.foreground_color, self, t('qr_foreground_color'))
        if color.isValid():
            self.foreground_color = color
            self._update_color_button(self.fg_color_btn, color)
            self._generate_preview()

    def _choose_background_color(self):
        """选择背景颜色"""
        if self.transparent_background:
            # 透明模式下不允许选择背景颜色
            return
        color = QColorDialog.getColor(self.background_color, self, t('qr_background_color'))
        if color.isValid():
            self.background_color = color
            self._update_color_button(self.bg_color_btn, color)
            self._generate_preview()

    def _on_transparent_toggled(self, checked):
        """透明背景切换"""
        self.transparent_background = checked
        self._update_color_button(self.bg_color_btn, self.background_color, checked)
        
        if checked:
            # 透明模式锁定PNG格式
            self.format_combo.setCurrentText('PNG')
            self.format_combo.setEnabled(False)
        else:
            self.format_combo.setEnabled(True)
        
        self._generate_preview()

    def _generate_preview(self):
        """生成预览"""
        # 解码模式不需要生成预览
        if self.current_mode == 'decode':
            return

        content = self._get_content()
        remark = self.remark_input.text()

        if not content:
            self.preview_label.clear()
            self.preview_label.setText(t('qr_no_content'))
            self.remark_preview_label.clear()
            self.generated_image = None
            return

        try:
            if self.is_barcode:
                self._generate_barcode_preview(content, remark)
            else:
                self._generate_qrcode_preview(content, remark)
        except Exception as e:
            self.preview_label.setText(t('qr_generate_error'))
            self.generated_image = None

    def _generate_qrcode_preview(self, content, remark):
        """生成二维码预览"""
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
        from io import BytesIO
        from PIL import Image

        error_map = {'L': ERROR_CORRECT_L, 'M': ERROR_CORRECT_M, 'Q': ERROR_CORRECT_Q, 'H': ERROR_CORRECT_H}
        error_level = error_map.get(self.error_level_combo.currentText(), ERROR_CORRECT_M)

        qr = qrcode.QRCode(
            version=1,
            error_correction=error_level,
            box_size=10,
            border=2,
        )
        qr.add_data(content)
        qr.make(fit=True)

        # 使用自定义颜色
        fill_color = self.foreground_color.name()
        if self.transparent_background:
            back_color = "transparent"
        else:
            back_color = self.background_color.name()

        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        # 确保转换为标准 PIL 图像
        if self.transparent_background:
            # 透明背景时保持 RGBA 模式
            if hasattr(img, 'convert'):
                img = img.convert('RGBA')
        else:
            # 非透明时转换为 RGB
            if hasattr(img, 'convert'):
                img = img.convert('RGB')

        # 使用 BytesIO 保存图像，避免内存引用问题
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # 使用 loadFromData 加载图像数据（数据会被复制到 QImage 内部）
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        # 缩放显示（保持比例）
        size = int(self.size_combo.currentText())
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.preview_label.setPixmap(scaled_pixmap)
        self.remark_preview_label.setText(remark)

        # 保存转换后的图像副本，确保是标准 PIL 图像
        buffer.seek(0)
        self.generated_image = Image.open(buffer).copy()

    def _generate_barcode_preview(self, content, remark):
        """生成条形码预览"""
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        from PIL import Image

        code128 = barcode.get('code128', content, writer=ImageWriter())

        img = code128.render()

        # 确保转换为标准 PIL RGB 图像
        if hasattr(img, 'convert'):
            img = img.convert('RGB')

        # 使用 BytesIO 保存图像，避免内存引用问题
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # 使用 loadFromData 加载图像数据
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        # 缩放显示
        height = 100
        scaled_pixmap = pixmap.scaledToHeight(height, Qt.SmoothTransformation)

        self.preview_label.setPixmap(scaled_pixmap)
        self.remark_preview_label.setText(remark)

        # 保存转换后的图像副本，确保是标准 PIL 图像
        buffer.seek(0)
        self.generated_image = Image.open(buffer).copy()

    def _export_image(self):
        """导出图片或解码结果"""
        # 解码模式：导出txt文件
        if self.current_mode == 'decode':
            if not self.decoded_result:
                self.warning_requested.emit(t('qr_decode_no_result'))
                return

            save_path = self.config.get_save_path() if self.config else ''
            if not save_path:
                self.warning_requested.emit(t('no_save_path'))
                return

            filename = 'decoded_result.txt'
            full_path = os.path.join(save_path, filename)

            # 检查文件是否存在，如果存在则添加序号
            if os.path.exists(full_path):
                counter = 1
                while True:
                    new_filename = f"decoded_result ({counter}).txt"
                    new_full_path = os.path.join(save_path, new_filename)
                    if not os.path.exists(new_full_path):
                        full_path = new_full_path
                        break
                    counter += 1
                    if counter > 100:
                        break

            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(self.decoded_result)

                filename = os.path.basename(full_path)
                self.success_requested.emit(f"{t('qr_export_success')}\n{t('file_saved_to')}: {filename}")
            except Exception as e:
                self.warning_requested.emit(t('qr_export_error'))

            return

        # 生成模式：导出图片
        if self.generated_image is None:
            self.warning_requested.emit(t('qr_no_content'))
            return

        save_path = self.config.get_save_path() if self.config else ''
        if not save_path:
            self.warning_requested.emit(t('no_save_path'))
            return

        if self.is_barcode:
            base_name = 'barcode'
        else:
            base_name = 'qrcode'

        format_ext = self.format_combo.currentText().lower()
        filename = f'{base_name}.{format_ext}'

        # 拼接路径
        full_path = os.path.join(save_path, filename)
        
        # 检查文件是否存在，如果存在则添加序号
        if os.path.exists(full_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while True:
                new_filename = f"{name} ({counter}){ext}"
                new_full_path = os.path.join(save_path, new_filename)
                if not os.path.exists(new_full_path):
                    full_path = new_full_path
                    break
                counter += 1
                if counter > 100:
                    break

        # 获取参数
        size = int(self.size_combo.currentText())
        format_ext = self.format_combo.currentText().lower()
        remark = self.remark_input.text()

        self.export_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            from PIL import Image, ImageDraw, ImageFont

            # 复制并调整图像大小
            export_img = self.generated_image.copy()

            if self.is_barcode:
                export_img = export_img.resize((size, int(size * 0.3)))
            else:
                export_img = export_img.resize((size, size))

            # 如果有备注，在图像下方添加文字
            if remark:
                # 计算文字区域高度
                text_height = 30
                # 创建新图像（二维码 + 文字区域）
                if self.transparent_background:
                    # 透明背景时使用 RGBA 模式
                    new_img = Image.new('RGBA', (export_img.width, export_img.height + text_height), (255, 255, 255, 0))
                else:
                    new_img = Image.new('RGB', (export_img.width, export_img.height + text_height), 'white')
                # 粘贴二维码
                new_img.paste(export_img, (0, 0))
                # 绘制文字
                draw = ImageDraw.Draw(new_img)
                # 使用支持中文的字体
                font = None
                font_paths = [
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                    "C:/Windows/Fonts/simhei.ttf",  # 黑体
                    "simsun.ttc",
                    "msyh.ttc",
                    "simhei.ttf",
                    "arial.ttf"
                ]
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, 12)
                        break
                    except:
                        continue
                if font is None:
                    font = ImageFont.load_default()
                # 计算文字位置（居中）
                text_width = len(remark) * 7  # 默认估算值
                try:
                    # 使用 getlength 方法（PIL 9.2+）
                    text_width = font.getlength(remark)
                except:
                    try:
                        # 使用 getsize 方法（旧版 PIL）
                        text_width = font.getsize(remark)[0]
                    except:
                        try:
                            # 使用 bbox 方法
                            bbox = draw.textbbox((0, 0), remark, font=font)
                            text_width = bbox[2] - bbox[0]
                        except:
                            pass  # 使用默认估算值
                x = (new_img.width - int(text_width)) // 2
                y = export_img.height + 8
                # 使用主体颜色绘制文字
                fill_color = self.foreground_color.name()
                draw.text((x, y), remark, fill=fill_color, font=font)
                export_img = new_img

            # 保存图像
            if format_ext == 'jpg':
                # JPG不支持透明，转换为RGB
                if self.transparent_background:
                    # 透明背景时创建白色背景
                    bg_img = Image.new('RGB', export_img.size, 'white')
                    bg_img.paste(export_img, mask=export_img.split()[-1] if export_img.mode == 'RGBA' else None)
                    export_img = bg_img
                else:
                    export_img = export_img.convert('RGB')
                export_img.save(full_path, 'JPEG', quality=95)
            else:
                # PNG支持透明
                if self.transparent_background:
                    export_img.save(full_path, 'PNG')
                else:
                    export_img.save(full_path, 'PNG')

            filename = os.path.basename(full_path)
            self.success_requested.emit(f"{t('qr_export_success')}\n{t('file_saved_to')}: {filename}")

        except Exception as e:
            self.warning_requested.emit(t('qr_export_error'))

        finally:
            self.export_btn.setEnabled(True)