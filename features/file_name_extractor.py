# -*- coding: utf-8 -*-
"""
DeskHelperGUI 文件名提取功能模块
提取文件夹中的文件名并导出到Excel
"""

import os
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QMessageBox, QGroupBox,
    QCheckBox, QListWidget, QListWidgetItem, QSizePolicy, QScrollArea,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t, get_i18n
from ui_components import AnimatedButton

# pandas延迟导入（优化启动速度）
HAS_PANDAS = None  # 延迟检测


class FileNameExtractorWidget(QWidget):
    """文件名提取功能界面"""

    # 导出完成信号
    export_finished = pyqtSignal(bool, str)  # (成功, 消息)
    
    # 警告信号（用于显示横幅通知）
    warning_requested = pyqtSignal(str)  # (警告消息)

    def __init__(self, lang='zh', config=None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.config = config
        self.selected_folder = ""
        self.file_list = []
        self.is_exporting = False

        # 设置语言
        set_language(lang)

        self._init_ui()
        self._load_config()
        # 连接导出完成信号
        self.export_finished.connect(self.on_export_finished)
        self.setAcceptDrops(True)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 文件夹选择区域
        self.folder_group = QGroupBox(t('extractor_folder'))
        folder_layout = QVBoxLayout()
        folder_layout.setSpacing(10)
        folder_layout.setContentsMargins(10, 15, 10, 15)

        # 文件夹路径输入行
        path_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText(t('extractor_folder_placeholder'))
        self.folder_input.setReadOnly(True)
        self.folder_input.setStyleSheet("""
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
        path_layout.addWidget(self.folder_input, 1)

        self.browse_btn = AnimatedButton(t('extractor_browse'))
        self.browse_btn.setFixedSize(100, 36)
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
        self.browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.browse_btn)

        folder_layout.addLayout(path_layout)

        # 提示标签
        self.tip_label = QLabel(t('extractor_tip'))
        self.tip_label.setStyleSheet("color: #868e96; font-size: 12px;")
        self.tip_label.setAlignment(Qt.AlignCenter)
        folder_layout.addWidget(self.tip_label)

        self.folder_group.setLayout(folder_layout)
        layout.addWidget(self.folder_group)

        # 预览区域
        self.preview_group = QGroupBox(t('extractor_preview'))
        preview_main_layout = QVBoxLayout()
        preview_main_layout.setSpacing(6)
        preview_main_layout.setContentsMargins(10, 15, 10, 15)

        # 预览标题行（刷新按钮靠右侧边框）
        preview_header = QHBoxLayout()
        preview_header.setContentsMargins(0, 0, 0, 0)
        
        # 空标签占位（标题已由QGroupBox显示，这里仅放刷新按钮）
        preview_header.addStretch()
        
        # 刷新预览按钮
        self.preview_btn = AnimatedButton(t('extractor_preview_btn'))
        self.preview_btn.setFixedHeight(28)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
            QPushButton:pressed {
                background-color: #37b24d;
            }
        """)
        self.preview_btn.clicked.connect(self._preview_files)
        preview_header.addWidget(self.preview_btn)
        
        preview_main_layout.addLayout(preview_header)

        # 文件列表
        self.file_listbox = QListWidget()
        self.file_listbox.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
                color: #495057;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
                color: #339af0;
            }
            QListWidget::item:hover {
                background-color: #f1f3f5;
            }
        """)
        preview_main_layout.addWidget(self.file_listbox, 1)

        # 状态标签
        self.status_label = QLabel(t('extractor_status_ready'))
        self.status_label.setStyleSheet("color: #868e96; font-size: 12px;")
        preview_main_layout.addWidget(self.status_label)

        # 包含扩展名选项（放在状态标签下方）
        self.include_ext_check = QCheckBox(t('extractor_include_ext'))
        self.include_ext_check.setChecked(True)
        self.include_ext_check.setStyleSheet("""
            QCheckBox {
                color: #495057;
                font-size: 13px;
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
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
            }
            QCheckBox::indicator:hover {
                border-color: #339af0;
            }
        """)
        self.include_ext_check.stateChanged.connect(self._auto_refresh_preview)
        preview_main_layout.addWidget(self.include_ext_check)
        
        # 输出路径显示（右下角）
        output_path_layout = QHBoxLayout()
        output_path_layout.addStretch()
        self.output_path_label = QLabel(t('extractor_output_path', ''))
        self.output_path_label.setStyleSheet("color: #868e96; font-size: 12px;")
        output_path_layout.addWidget(self.output_path_label)
        preview_main_layout.addLayout(output_path_layout)

        self.preview_group.setLayout(preview_main_layout)
        layout.addWidget(self.preview_group, 1)  # 让预览区域占据剩余空间

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 进度条容器（填充导出按钮左侧空白，防止进度条显隐时布局跳动）
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

        # 导出按钮
        self.export_btn = AnimatedButton(t('extractor_export'))
        self.export_btn.setFixedSize(130, 34)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #51cf66;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #40c057;
            }
            QPushButton:pressed {
                background-color: #37b24d;
            }
        """)
        self.export_btn.clicked.connect(self._export_to_excel)
        btn_layout.addWidget(self.export_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)
        
        # 防止递归加载配置
        self._loading_config = False

    def _load_config(self):
        """加载配置"""
        # 防止递归调用
        if self._loading_config:
            return
        self._loading_config = True
        
        try:
            # 加载输出路径
            if self.config:
                save_path = self.config.get_save_path()
                if save_path:
                    self.output_path_label.setText(t('extractor_output_path', save_path.replace('\\', '/')))
        finally:
            self._loading_config = False

    def _save_config(self):
        """保存配置"""
        # 不需要保存保存路径，使用全局配置
        pass

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.selected_folder = path
                self.folder_input.setText(path)
                self._auto_refresh_preview()  # 自动刷新预览

    def _browse_folder(self):
        """浏览选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, t('extractor_select_folder'), ""
        )
        if folder:
            self.selected_folder = folder
            self.folder_input.setText(folder)
            self._auto_refresh_preview()  # 自动刷新预览

    def _auto_refresh_preview(self):
        """自动刷新预览（当文件夹已选择时）"""
        if self.selected_folder:
            self._preview_files()

    def _clear_preview(self):
        """清空预览"""
        self.file_listbox.clear()
        self.status_label.setText(t('extractor_status_ready'))

    def _get_files_list(self):
        """获取文件列表"""
        if not self.selected_folder or not os.path.exists(self.selected_folder):
            return []

        files = []
        try:
            for item in os.listdir(self.selected_folder):
                item_path = os.path.join(self.selected_folder, item)
                if os.path.isfile(item_path):
                    if self.include_ext_check.isChecked():
                        files.append(item)
                    else:
                        name, ext = os.path.splitext(item)
                        files.append(name)
            return sorted(files)
        except Exception as e:
            return []

    def _preview_files(self):
        """预览文件列表"""
        if not self.selected_folder:
            self.warning_requested.emit(t('extractor_no_folder'))
            return

        self.file_listbox.clear()
        files = self._get_files_list()

        if not files:
            self.status_label.setText(t('extractor_no_files'))
            return

        for filename in files:
            self.file_listbox.addItem(filename)

        self.status_label.setText(t('extractor_status_found', len(files)))

    def _export_to_excel(self):
        """导出到Excel"""
        # 延迟检测pandas（优化启动速度）
        global HAS_PANDAS
        if HAS_PANDAS is None:
            try:
                import pandas as pd
                HAS_PANDAS = True
            except ImportError:
                HAS_PANDAS = False
        
        if not HAS_PANDAS:
            self.warning_requested.emit(t('extractor_need_pandas'))
            return

        if not self.selected_folder:
            self.warning_requested.emit(t('extractor_no_folder'))
            return

        files = self._get_files_list()
        if not files:
            self.warning_requested.emit(t('extractor_no_files'))
            return

        # 使用全局保存路径
        save_path = self.config.get_save_path() if self.config else ""
        
        # 获取文件夹名称作为文件名
        folder_name = os.path.basename(self.selected_folder)
        default_filename = f"{folder_name}_文件名列表.xlsx"
        
        if not save_path:
            # 使用默认文件名（保存到源文件夹）
            save_path = os.path.join(self.selected_folder, default_filename)
        elif os.path.isdir(save_path):
            # 如果是目录路径，在该目录下创建文件
            save_path = os.path.join(save_path, default_filename)
        elif not save_path.endswith('.xlsx'):
            # 如果没有扩展名，添加扩展名
            save_path += '.xlsx'

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.export_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.is_exporting = True

        # 在线程中执行导出
        def do_export():
            try:
                import pandas as pd  # 在线程中导入
                
                # 创建DataFrame，序号从1开始
                df = pd.DataFrame({
                    '序号': range(1, len(files) + 1),
                    '文件名': files
                })

                # 导出到Excel
                with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='文件列表', index=False)

                    # 获取工作表并设置格式
                    worksheet = writer.sheets['文件列表']
                    worksheet.column_dimensions['A'].width = 8   # 序号列
                    worksheet.column_dimensions['B'].width = 50  # 文件名列

                self.export_finished.emit(True, save_path)
            except Exception as e:
                self.export_finished.emit(False, str(e))

        thread = threading.Thread(target=do_export, daemon=True)
        thread.start()

    def on_export_finished(self, success, message):
        """导出完成回调"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.is_exporting = False
        
        # 导出成功后清空文件夹和列表
        if success:
            self.selected_folder = None
            self.folder_input.clear()
            self.file_listbox.clear()
            self.status_label.setText(t('extractor_status_ready'))
        
        # 通知横幅会在主窗口中显示，这里不需要弹窗

    def update_language(self, lang):
        """更新语言"""
        self.lang = lang
        set_language(lang)

        # 更新界面文本
        self.folder_group.setTitle(t('extractor_folder'))
        self.tip_label.setText(t('extractor_tip'))
        self.browse_btn.setText(t('extractor_browse'))
        self.preview_group.setTitle(t('extractor_preview'))
        self.include_ext_check.setText(t('extractor_include_ext'))
        self.status_label.setText(t('extractor_status_ready'))
        self.preview_btn.setText(t('extractor_preview_btn'))
        self.export_btn.setText(t('extractor_export'))
        
        # 重新加载输出路径
        self._load_config()