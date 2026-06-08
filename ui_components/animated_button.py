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
    - 点击时有按下效果（向下移动1px）
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_pos = None
        self.is_pressed = False

    def mousePressEvent(self, event):
        """鼠标按下事件 - 触发点击动画"""
        if self.original_pos is None:
            self.original_pos = self.pos()

        self.is_pressed = True
        # 向下移动1px，模拟按下效果
        self.move(QPoint(self.original_pos.x(), self.original_pos.y() + 1))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 恢复位置"""
        self.is_pressed = False
        if self.original_pos is not None:
            self.move(self.original_pos)
        super().mouseReleaseEvent(event)