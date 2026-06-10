# -*- coding: utf-8 -*-
"""
DeskHelperGUI - 桌面助手GUI
基于 Python PyQt5 的桌面助手，提供各种便捷功能

项目信息：
- 项目名称：DeskHelperGUI
- 项目作者：Lisselde_E
- 项目邮箱：Lisselde.E@outlook.com
- 项目仓库：https://github.com/LisseldeE/DeskHelperGUI
"""

import sys
import ctypes
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from ui_components import (
    STYLESHEET, SIDEBAR_BUTTON_STYLE, SIDEBAR_BUTTON_ACTIVE_STYLE,
    AboutDialog, AnimatedButton, NotificationBanner, SettingsDialog
)
from config_manager import ConfigManager
from i18n import set_language, t, get_i18n

# 延迟导入功能模块（优化启动速度）
# from features import QuickCompressWidget, FileNameExtractorWidget, ImageProcessorWidget

# 项目信息
APP_NAME = "DeskHelperGUI"
APP_VERSION = "R1"
APP_AUTHOR = "Lisselde_E"
APP_EMAIL = "Lisselde.E@outlook.com"
APP_REPO = "LisseldeE/DeskHelperGUI"


def get_resource_path(relative_path):
    """获取资源文件路径，兼容打包和未打包"""
    try:
        base_path = sys._MEIPASS  # PyInstaller打包后的临时目录
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def setup_dpi_scaling():
    """设置DPI缩放适配（解决高DPI显示问题）"""
    # Windows高DPI适配 - 启用Per-Monitor DPI感知
    if sys.platform == 'win32':
        try:
            # 设置为 Per Monitor Aware V1 (1)，让程序自己处理DPI缩放
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            # 如果失败，尝试使用旧版本API
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass

    # Qt高DPI设置 - 启用自动缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 适配125%、150%等非整数倍缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager

        # 从配置加载语言
        self.lang = self.config.get_language()
        set_language(self.lang)

        self.current_feature = None  # 当前功能
        self.feature_buttons = {}  # 功能按钮字典
        self.feature_widgets = {}  # 功能界面字典

        self._init_window()
        self._init_ui()

        # 从配置加载上次使用的功能
        last_feature = self.config.get_last_feature()
        self._switch_feature(last_feature)

    def _init_window(self):
        """初始化窗口"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(700, 500)

        # 使用默认窗口大小
        self.resize(900, 600)

        # 设置窗口图标
        icon_path = get_resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _init_ui(self):
        """初始化UI"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶栏
        self._create_top_bar(main_layout)

        # 内容区域（左侧栏 + 右侧功能区）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧栏
        self._create_sidebar(content_layout)

        # 右侧功能区
        self._create_feature_area(content_layout)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        # 通知横幅（浮动在顶部，不挤压内容）
        self.notification_banner = NotificationBanner(central_widget)

    def _create_top_bar(self, parent_layout):
        """创建顶栏"""
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #dee2e6;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 0, 20, 0)

        # 左侧：程序名称
        title_label = QLabel(APP_NAME)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #339af0;
            }
        """)
        layout.addWidget(title_label)

        layout.addStretch()

        # 右侧：语言切换按钮
        self.lang_btn = AnimatedButton(t('lang_switch'))
        self.lang_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.lang_btn.setFixedHeight(32)
        self.lang_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.lang_btn.clicked.connect(self._toggle_language)
        layout.addWidget(self.lang_btn)

        layout.addSpacing(10)

        # 右侧：设置按钮（齿轮图标）
        self.settings_btn = AnimatedButton("⚙")
        self.settings_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: black;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
                color: black;
            }
        """)
        self.settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(self.settings_btn)

        layout.addSpacing(10)

        # 右侧：关于按钮（i图标）
        self.about_btn = AnimatedButton("i")
        self.about_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.about_btn.setFixedSize(32, 32)
        self.about_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.about_btn.clicked.connect(self._show_about)
        layout.addWidget(self.about_btn)

        top_bar.setLayout(layout)
        parent_layout.addWidget(top_bar)

    def _create_sidebar(self, parent_layout):
        """创建左侧栏"""
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-right: 1px solid #dee2e6;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 15, 10, 15)

        # 功能按钮列表
        features = [
            ('quick_compress', t('feature_quick_compress')),
            ('image_processor', t('feature_image_processor')),
            ('file_extractor', t('feature_file_extractor')),
        ]

        for feature_id, feature_name in features:
            btn = AnimatedButton(feature_name)
            btn.setObjectName(f"sidebar_{feature_id}")
            btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, fid=feature_id: self._switch_feature(fid))
            layout.addWidget(btn)
            self.feature_buttons[feature_id] = btn

        layout.addStretch()

        sidebar.setLayout(layout)
        parent_layout.addWidget(sidebar)

    def _create_feature_area(self, parent_layout):
        """创建右侧功能区"""
        self.feature_stack = QStackedWidget()
        self.feature_stack.setStyleSheet("background-color: #f8f9fa;")

        # 只创建默认功能界面（快捷压缩），其他界面延迟创建
        self._create_quick_compress_widget()

        parent_layout.addWidget(self.feature_stack)

    def _create_quick_compress_widget(self):
        """创建快捷压缩界面"""
        if 'quick_compress' in self.feature_widgets:
            return
        from features import QuickCompressWidget
        quick_compress_widget = QuickCompressWidget(self.lang, self.config)
        quick_compress_widget.compress_finished.connect(self._on_compress_finished)
        quick_compress_widget.extract_finished.connect(self._on_extract_finished)
        self.feature_widgets['quick_compress'] = quick_compress_widget
        self.feature_stack.addWidget(quick_compress_widget)

    def _create_file_extractor_widget(self):
        """创建文件名提取界面"""
        if 'file_extractor' in self.feature_widgets:
            return
        from features import FileNameExtractorWidget
        file_extractor_widget = FileNameExtractorWidget(self.lang, self.config)
        file_extractor_widget.export_finished.connect(self._on_extractor_finished)
        file_extractor_widget.warning_requested.connect(self._on_extractor_warning)
        self.feature_widgets['file_extractor'] = file_extractor_widget
        self.feature_stack.addWidget(file_extractor_widget)

    def _create_image_processor_widget(self):
        """创建图片处理界面"""
        if 'image_processor' in self.feature_widgets:
            return
        from features import ImageProcessorWidget
        image_processor_widget = ImageProcessorWidget(self.lang, self.config)
        image_processor_widget.process_finished.connect(self._on_image_finished)
        image_processor_widget.warning_requested.connect(self._on_image_warning)
        self.feature_widgets['image_processor'] = image_processor_widget
        self.feature_stack.addWidget(image_processor_widget)

    def _switch_feature(self, feature_id):
        """切换功能界面"""
        if feature_id == self.current_feature:
            return

        # 更新按钮样式
        for fid, btn in self.feature_buttons.items():
            if fid == feature_id:
                btn.setStyleSheet(SIDEBAR_BUTTON_ACTIVE_STYLE)
            else:
                btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)

        # 延迟创建界面（如果尚未创建）
        if feature_id == 'file_extractor' and feature_id not in self.feature_widgets:
            self._create_file_extractor_widget()
        elif feature_id == 'image_processor' and feature_id not in self.feature_widgets:
            self._create_image_processor_widget()

        # 切换界面
        if feature_id in self.feature_widgets:
            widget = self.feature_widgets[feature_id]
            self.feature_stack.setCurrentWidget(widget)
            self.current_feature = feature_id
            
            # 重新加载配置（确保全局路径同步）
            # 使用 try 防止加载过程中的异常影响切换
            try:
                if hasattr(widget, '_load_config'):
                    widget._load_config()
            except Exception:
                pass

            # 保存到配置
            self.config.set_last_feature(feature_id)

    def _toggle_language(self):
        """切换语言"""
        if self.lang == 'zh':
            self.lang = 'en'
        else:
            self.lang = 'zh'

        # 更新全局语言
        set_language(self.lang)

        # 保存到配置
        self.config.set_language(self.lang)

        # 更新界面文本
        self._update_ui_text()

    def _update_ui_text(self):
        """更新界面文本"""
        # 更新顶栏按钮
        self.lang_btn.setText(t('lang_switch'))
        # 设置按钮和关于按钮使用图标，不需要更新文本

        # 更新功能按钮文本
        features_text = {
            'quick_compress': t('feature_quick_compress'),
            'file_extractor': t('feature_file_extractor'),
            'image_processor': t('feature_image_processor'),
        }
        for feature_id, text in features_text.items():
            if feature_id in self.feature_buttons:
                self.feature_buttons[feature_id].setText(text)

        # 更新功能界面
        for widget in self.feature_widgets.values():
            widget.update_language(self.lang)

    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self.lang, self)
        dialog.exec_()

    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.lang, self.config, self)
        if dialog.exec_():
            # 设置保存后，重新加载各模块的配置
            for widget in self.feature_widgets.values():
                try:
                    if hasattr(widget, '_load_config'):
                        widget._load_config()
                except Exception:
                    pass

    def _on_compress_finished(self, success, message):
        """压缩完成回调 - 显示顶部通知横幅"""
        if success:
            self.notification_banner.show_message(
                t('msg_compress_done', os.path.basename(message)),
                type='success', duration=4000
            )
        else:
            self.notification_banner.show_message(
                t('msg_compress_failed', message),
                type='error', duration=5000
            )

    def _on_extract_finished(self, success, message):
        """解压完成回调 - 显示顶部通知横幅"""
        if success:
            self.notification_banner.show_message(
                t('extract_done', message),
                type='success', duration=4000
            )
        else:
            self.notification_banner.show_message(
                t('extract_failed', message),
                type='error', duration=5000
            )

    def _on_extractor_finished(self, success, message):
        """文件名提取导出完成回调 - 显示顶部通知横幅"""
        if success:
            self.notification_banner.show_message(
                t('extractor_export_done', message),
                type='success', duration=4000
            )
        else:
            self.notification_banner.show_message(
                t('extractor_export_failed', message),
                type='error', duration=5000
            )

    def _on_image_finished(self, success, message):
        """图片处理完成回调 - 显示顶部通知横幅"""
        if success:
            self.notification_banner.show_message(
                t('image_done', message),
                type='success', duration=4000
            )
        else:
            self.notification_banner.show_message(
                t('image_failed', message),
                type='error', duration=5000
            )

    def _on_image_warning(self, message):
        """图片处理警告回调 - 显示顶部通知横幅"""
        self.notification_banner.show_message(
            message,
            type='warning', duration=3000
        )

    def _on_extractor_warning(self, message):
        """文件名提取警告回调 - 显示顶部通知横幅"""
        self.notification_banner.show_message(
            message,
            type='warning', duration=3000
        )

    def resizeEvent(self, event):
        """主窗口大小变化时重新定位通知横幅"""
        super().resizeEvent(event)
        if hasattr(self, 'notification_banner') and self.notification_banner.isVisible():
            self.notification_banner._reposition()

    def closeEvent(self, event):
        """窗口关闭事件"""
        event.accept()


def main():
    """主函数"""
    # 设置DPI缩放（必须在QApplication创建之前）
    setup_dpi_scaling()

    # 设置AppUserModelID（必须在QApplication创建之前）
    if sys.platform == 'win32':
        app_id = f"LisseldeE.{APP_NAME}.{APP_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_AUTHOR)

    # 设置全局样式表
    app.setStyleSheet(STYLESHEET)

    # 设置窗口图标
    icon_path = get_resource_path('icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 加载配置
    config = ConfigManager()

    # 设置语言（用于启动时的对话框）
    set_language(config.get_language())

    # 检查保存路径是否为空，若为空则弹出配置对话框
    if not config.get_save_path():
        startup_dialog = SettingsDialog(config.get_language(), config, None, is_startup=True)
        if not startup_dialog.exec_():
            # 用户取消配置，使用默认路径（桌面）
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            if os.path.exists(desktop_path):
                config.set_save_path(desktop_path.replace('\\', '/'))

    # 创建并显示主窗口
    window = MainWindow(config)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    # Windows任务栏图标设置（必须在窗口显示后）
    if sys.platform == 'win32' and os.path.exists(icon_path):
        try:
            hwnd = int(window.winId())
            hicon = ctypes.windll.user32.LoadImageW(
                None, icon_path, 1,  # IMAGE_ICON
                0, 0, 0x10  # LR_LOADFROMFILE
            )
            if hicon:
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hicon)  # WM_SETICON, ICON_SMALL
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hicon)  # WM_SETICON, ICON_BIG
        except Exception:
            pass

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()