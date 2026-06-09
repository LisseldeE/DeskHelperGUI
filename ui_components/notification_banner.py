# -*- coding: utf-8 -*-
"""
DeskHelperGUI 通知横幅组件
浮动置顶重叠显示，不挤压界面内容
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QByteArray


class NotificationBanner(QFrame):
    """
    顶部浮动通知横幅 - 置顶重叠显示，不挤压上方元素

    支持类型:
        success (绿色) / error (红色) / warning (黄色) / info (蓝色)

    用法:
        banner.show_message('操作成功', type='success')
        banner.show_message('出错了', type='error', duration=5000)
    """

    # 类型常量
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._start_hide_animation)

        self._fade_animation = None
        self._opacity_effect = None
        self._is_animating = False
        self._is_showing = False  # 防止重复显示

        self.setVisible(False)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setFixedHeight(42)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(10)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)

        # 消息文本
        self.msg_label = QLabel()
        self.msg_label.setWordWrap(False)
        self.msg_label.setAlignment(Qt.AlignVCenter)
        self.msg_label.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self.msg_label, 1)

        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: inherit;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.close_btn.clicked.connect(self._on_close_clicked)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    # ---- 公开接口 ----

    def show_message(self, message, type='success', duration=3500):
        """
        显示通知横幅

        Args:
            message: 通知文本
            type: success / error / warning / info
            duration: 自动隐藏毫秒（0 表示不自动隐藏）
        """
        # 防止重复显示
        if self._is_showing:
            return
        self._is_showing = True
        
        # 如果正在动画中，先停止
        self._stop_animations()

        # 定义各类型的颜色和图标
        configs = {
            self.SUCCESS: ('#d3f9d8', '#2b8a3e', '#b2f2bb', '✓'),
            self.ERROR:   ('#ffe3e3', '#c92a2a', '#ffc9c9', '✕'),
            self.WARNING: ('#fff3bf', '#e67700', '#ffe066', '⚠'),
            self.INFO:    ('#d0ebff', '#1971c2', '#a5d8ff', 'ℹ'),
        }

        bg_color, fg_color, border_color, icon = configs.get(type, configs[self.INFO])

        # 整体框架样式（圆角 + 精致边框）
        self.setStyleSheet(f"""
            NotificationBanner {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)

        # 图标和文字颜色
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {fg_color}; background: transparent;"
        )
        self.msg_label.setText(message)
        self.msg_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {fg_color}; background: transparent;"
        )
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {fg_color};
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """)

        # 重置位置到顶部
        self._reposition()

        # 淡入动画
        self._start_show_animation()

        # 定时自动隐藏
        if duration > 0:
            self._timeout_timer.stop()
            self._timeout_timer.start(duration)

    def dismiss(self):
        """立即关闭通知"""
        self._timeout_timer.stop()
        self._start_hide_animation()

    # ---- 内部方法 ----

    def _reposition(self):
        """调整位置到父窗口顶部居中"""
        parent = self.parent()
        if parent:
            parent_width = parent.width()
            margin = 16
            self.setFixedWidth(min(parent_width - margin * 2, 420))
            self.move((parent_width - self.width()) // 2, 4)
            self.raise_()

    def _start_show_animation(self):
        """淡入显示"""
        # 停止旧的动画
        if self._fade_animation:
            try:
                self._fade_animation.finished.disconnect()
            except:
                pass
            self._fade_animation.stop()
            self._fade_animation.deleteLater()
            self._fade_animation = None

        self._is_animating = True

        # 创建/获取透明度效果
        if not self._opacity_effect:
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)

        self._opacity_effect.setOpacity(0.0)
        self.setVisible(True)

        anim = QPropertyAnimation(self._opacity_effect, QByteArray(b"opacity"))
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        self._fade_animation = anim
        anim.finished.connect(self._on_show_finished)
        anim.start()

    def _on_show_finished(self):
        """淡入完成"""
        self._is_animating = False
        self._fade_animation = None

    def _start_hide_animation(self):
        """淡出隐藏"""
        if self._is_animating or not self.isVisible():
            return

        # 停止旧的动画
        if self._fade_animation:
            try:
                self._fade_animation.finished.disconnect()
            except:
                pass
            self._fade_animation.stop()
            self._fade_animation.deleteLater()
            self._fade_animation = None

        self._is_animating = True
        self._timeout_timer.stop()

        if not self._opacity_effect:
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)

        anim = QPropertyAnimation(self._opacity_effect, QByteArray(b"opacity"))
        anim.setDuration(250)
        anim.setStartValue(self._opacity_effect.opacity())
        anim.setEndValue(0.0)
        self._fade_animation = anim
        anim.finished.connect(self._on_hide_finished)
        anim.start()

    def _on_hide_finished(self):
        """淡出完成"""
        self._is_animating = False
        self._fade_animation = None
        self._is_showing = False  # 重置显示标志
        self.setVisible(False)

    def _on_close_clicked(self):
        """点击关闭按钮"""
        self.dismiss()

    def _stop_animations(self):
        """停止所有正在执行的动画"""
        if self._fade_animation:
            try:
                self._fade_animation.finished.disconnect()
            except:
                pass
            self._fade_animation.stop()
            self._fade_animation.deleteLater()
            self._fade_animation = None
        self._timeout_timer.stop()
        self._is_animating = False
        self._is_showing = False  # 重置显示标志

    # ---- 事件重写 ----

    def resizeEvent(self, event):
        """父窗口大小变化时重新定位"""
        super().resizeEvent(event)
        if self.isVisible():
            self._reposition()

    def mousePressEvent(self, event):
        """点击通知可以提前关闭"""
        self.dismiss()
        super().mousePressEvent(event)