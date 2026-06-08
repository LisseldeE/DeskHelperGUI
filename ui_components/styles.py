# -*- coding: utf-8 -*-
"""
DeskHelperGUI 样式模块
包含全局样式表和颜色定义
"""

# 颜色定义
COLORS = {
    'primary': '#339af0',           # 主色调（蓝色）
    'primary_hover': '#228be6',      # 主色调悬停
    'success': '#51cf66',           # 确认色（绿色）
    'success_hover': '#40c057',      # 确认色悬停
    'danger': '#ff6b6b',            # 危险色（红色）
    'danger_hover': '#fa5252',       # 危险色悬停
    'background': '#f8f9fa',         # 主窗口背景
    'card_background': 'white',      # 卡片背景
    'border': '#dee2e6',             # 边框色
    'disabled': '#adb5bd',           # 禁用色
    'text_primary': '#495057',       # 主文字色
    'text_secondary': '#868e96',     # 次文字色
    'input_focus': '#4dabf7',        # 输入框焦点
}

# 全局样式表
STYLESHEET = """
/* 主窗口背景 */
QMainWindow {
    background-color: #f8f9fa;
}

/* 全局字体设置 */
* {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}

/* 分组框 */
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #495057;
}

/* 输入框 */
QLineEdit {
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: white;
    font-size: 13px;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    min-height: 20px;
}
QLineEdit:focus {
    border: 2px solid #4dabf7;
}

/* 默认按钮 */
QPushButton {
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #ced4da;
}
QPushButton:hover {
    background-color: #dee2e6;
}
QPushButton:disabled {
    background-color: #adb5bd;
    color: #868e96;
}

/* 主要操作按钮（蓝色） */
QPushButton#primaryBtn {
    background-color: #339af0;
    color: white;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #228be6;
}
QPushButton#primaryBtn:disabled {
    background-color: #adb5bd;
}

/* 确认按钮（绿色） */
QPushButton#successBtn {
    background-color: #51cf66;
    color: white;
    border: none;
}
QPushButton#successBtn:hover {
    background-color: #40c057;
}
QPushButton#successBtn:disabled {
    background-color: #adb5bd;
}

/* 危险按钮（红色） */
QPushButton#dangerBtn {
    background-color: #ff6b6b;
    color: white;
    border: none;
}
QPushButton#dangerBtn:hover {
    background-color: #fa5252;
}
QPushButton#dangerBtn:disabled {
    background-color: #adb5bd;
}

/* 下拉框 */
QComboBox {
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}
QComboBox:hover {
    background-color: #dee2e6;
    border: 1px solid #adb5bd;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #495057;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #ced4da;
    selection-background-color: #339af0;
    selection-color: white;
}

/* 列表控件 */
QListWidget {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background-color: white;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #e9ecef;
    color: #495057;
}
QListWidget::item:selected {
    background-color: #e7f5ff;
    color: #339af0;
}
QListWidget::item:hover:!selected {
    background-color: #f8f9fa;
    color: #495057;
}

/* 表格 */
QTableWidget {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background-color: white;
    gridline-color: #e9ecef;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}
QTableWidget::item {
    padding: 8px;
}
QHeaderView::section {
    background-color: #f1f3f5;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
    color: #495057;
}

/* 复选框 */
QCheckBox {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    color: #495057;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ced4da;
    border-radius: 4px;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #339af0;
    border-color: #339af0;
}
QCheckBox::indicator:hover {
    border-color: #339af0;
}

/* 滚动条 */
QScrollBar:vertical {
    border: none;
    background-color: #f1f3f5;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #ced4da;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background-color: #adb5bd;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #f1f3f5;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #ced4da;
    min-width: 30px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #adb5bd;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* 进度条 */
QProgressBar {
    border: 1px solid #dee2e6;
    border-radius: 6px;
    text-align: center;
    background-color: #e9ecef;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}
QProgressBar::chunk {
    background-color: #339af0;
    border-radius: 5px;
}

/* 滑动条 */
QSlider::groove:horizontal {
    border: 1px solid #dee2e6;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: #339af0;
    border: 1px solid #228be6;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #228be6;
}
"""

# 侧边栏按钮样式
SIDEBAR_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #495057;
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    padding: 12px 15px;
    font-size: 13px;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}
QPushButton:hover {
    background-color: #e9ecef;
}
"""

# 侧边栏按钮激活样式
SIDEBAR_BUTTON_ACTIVE_STYLE = """
QPushButton {
    background-color: #e9ecef;
    color: #339af0;
    border: none;
    border-left: 3px solid #339af0;
    text-align: left;
    padding: 12px 15px;
    font-size: 13px;
    font-weight: 600;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}
"""