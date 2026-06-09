# -*- coding: utf-8 -*-
"""
DeskHelperGUI 动画按钮组件
包含带点击动画效果的按钮类
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QPoint, Qt, QEvent


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

    def event(self, event):
        """处理所有事件，包括布局改变事件"""
        # 当布局改变时（窗口大小调整），清除保存的位置
        if event.type() == QEvent.LayoutRequest:
            if not self._is_pressed:
                self._original_pos = None
        return super().event(event)

    def mousePressEvent(self, event):
        """鼠标按下 - 向下移动1px模拟按下效果"""
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
            
        # 每次点击时重新获取当前位置
        self._original_pos = self.pos()

        self._is_pressed = True
        super().mousePressEvent(event)
        # 在事件处理后移动
        if self._original_pos:
            self.move(QPoint(self._original_pos.x(), self._original_pos.y() + 1))

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 恢复原始位置"""
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return
            
        self._is_pressed = False
        if self._original_pos is not None:
            self.move(self._original_pos)
        super().mouseReleaseEvent(event)
