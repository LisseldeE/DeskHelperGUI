# -*- coding: utf-8 -*-
"""
DeskHelperGUI 可点击标签组件
支持悬浮效果和下划线显示
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ClickableLabel(QLabel):
    """可点击标签类 - 支持悬浮效果和下划线"""

    def __init__(self, text="", parent=None,
                 normal_color="#339af0", hover_color="#228be6",
                 underline_on_hover=True):
        super().__init__(text, parent)

        self._normal_color = normal_color
        self._hover_color = hover_color
        self._underline_on_hover = underline_on_hover
        self._is_hovering = False
        self._click_callback = None

        # 设置默认样式
        self.setStyleSheet(f"QLabel {{ font-size: 11px; color: {self._normal_color}; }}")
        self.setAlignment(Qt.AlignCenter)

        # 保存原始字体
        self._original_font = self.font()

    def enterEvent(self, event):
        """鼠标进入 - 应用 hover 样式"""
        self._is_hovering = True
        self._apply_hover_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开 - 恢复正常样式"""
        self._is_hovering = False
        self._apply_normal_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击 - 执行回调"""
        if event.button() == Qt.LeftButton and self._click_callback:
            self._click_callback(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 保持 hover 状态"""
        if self._is_hovering:
            self._apply_hover_style()

    def set_click_callback(self, callback):
        """设置点击回调函数"""
        self._click_callback = callback
        self.setCursor(Qt.PointingHandCursor)

    def _apply_hover_style(self):
        """应用 hover 样式"""
        self.setStyleSheet(f"QLabel {{ font-size: 11px; color: {self._hover_color}; }}")

        if self._underline_on_hover:
            font = QFont(self._original_font)
            font.setUnderline(True)
            self.setFont(font)

    def _apply_normal_style(self):
        """应用正常样式"""
        self.setStyleSheet(f"QLabel {{ font-size: 11px; color: {self._normal_color}; }}")

        if self._underline_on_hover:
            font = QFont(self._original_font)
            font.setUnderline(False)
            self.setFont(font)