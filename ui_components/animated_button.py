# -*- coding: utf-8 -*-
"""
DeskHelperGUI 动画按钮组件
包含带点击动画效果的按钮类
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QPoint


class AnimatedButton(QPushButton):
    """
    带动画效果的按钮类
    - 点击时有按下效果（向下移动1px模拟下沉）
    - 释放时恢复原始位置
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._original_pos = None
        self._is_pressed = False

    def setStyleSheet(self, style):
        """重写setStyleSheet，保存原始位置"""
        if not self._is_pressed:
            self._original_pos = None  # 样式变化后重新获取位置
        super().setStyleSheet(style)

    def showEvent(self, event):
        """控件显示时保存初始位置"""
        super().showEvent(event)
        if self._original_pos is None:
            self._original_pos = self.pos()

    def moveEvent(self, event):
        """布局移动控件时同步更新原始位置"""
        super().moveEvent(event)
        if not self._is_pressed:
            self._original_pos = self.pos()

    def mousePressEvent(self, event):
        """鼠标按下 - 向下移动1px模拟按下效果"""
        if self._original_pos is None:
            self._original_pos = self.pos()

        self._is_pressed = True
        self.move(QPoint(self._original_pos.x(), self._original_pos.y() + 1))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 恢复原始位置"""
        self._is_pressed = False
        if self._original_pos is not None:
            self.move(self._original_pos)
        super().mouseReleaseEvent(event)
