# -*- coding: utf-8 -*-
"""
DeskHelperGUI 关于对话框
包含项目信息和检查更新功能
"""

import urllib.request
import json
import re
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import set_language, t
from ui_components.animated_button import AnimatedButton

# 项目信息
APP_NAME = "DeskHelperGUI"
APP_VERSION = "R3"
APP_AUTHOR = "Lisselde_E"
APP_EMAIL = "Lisselde.E@outlook.com"
APP_REPO = "LisseldeE/DeskHelperGUI"


class AboutDialog(QDialog):
    """关于弹窗"""

    def __init__(self, lang='zh', parent=None):
        super().__init__(parent)
        self.lang = lang
        set_language(lang)
        self.setWindowTitle(t('about_title'))
        # 移除右上角的问号按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(400, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(25, 20, 25, 20)

        # 标题
        title_label = QLabel(APP_NAME)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #339af0;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本信息
        version_label = QLabel(t('about_version'))
        version_label.setStyleSheet("font-size: 13px; color: #495057;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 描述
        desc_label = QLabel(t('about_desc'))
        desc_label.setStyleSheet("font-size: 12px; color: #868e96;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 作者信息
        author_label = QLabel(t('about_author'))
        author_label.setStyleSheet("font-size: 12px; color: #495057;")
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        # GitHub链接（可点击）
        github_label = QLabel(f"GitHub: {APP_REPO}")
        github_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #339af0;
            }
            QLabel:hover {
                color: #228be6;
                text-decoration: underline;
            }
        """)
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setCursor(Qt.PointingHandCursor)
        github_label.mousePressEvent = lambda event: self._open_github()
        layout.addWidget(github_label)

        # 邮箱（可点击复制）
        email_label = QLabel(f"Email: {APP_EMAIL}")
        email_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #495057;
            }
            QLabel:hover {
                color: #339af0;
            }
        """)
        email_label.setAlignment(Qt.AlignCenter)
        email_label.setCursor(Qt.PointingHandCursor)
        email_label.mousePressEvent = lambda event: self._copy_email()
        layout.addWidget(email_label)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 检查更新按钮
        check_update_btn = AnimatedButton(t('about_check_update'))
        check_update_btn.setMinimumWidth(120)
        check_update_btn.setFixedHeight(36)
        check_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #339af0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #228be6;
            }
        """)
        check_update_btn.clicked.connect(self._check_update)
        btn_layout.addWidget(check_update_btn)

        btn_layout.addSpacing(10)

        # 关闭按钮
        close_btn = AnimatedButton(t('about_close'))
        close_btn.setFixedSize(100, 36)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _open_github(self):
        """打开GitHub链接"""
        QDesktopServices.openUrl(QUrl(f"https://github.com/{APP_REPO}"))

    def _copy_email(self):
        """复制邮箱到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(APP_EMAIL)
        QMessageBox.information(self, t('about_info'), t('about_email_copied'))

    def _check_update(self):
        """检查更新"""
        checking_text = t('about_check_update')
        try:
            # 获取GitHub仓库的tags列表
            url = f"https://api.github.com/repos/{APP_REPO}/tags"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', APP_NAME)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            if not data:
                QMessageBox.information(self, checking_text, t('about_no_tags'))
                return

            # 获取最新tag
            latest_tag = data[0]['name']

            # 解析当前版本号
            current_version_match = re.search(r'R(\d+)', APP_VERSION)
            if not current_version_match:
                QMessageBox.warning(self, checking_text, t('about_parse_error'))
                return
            current_version = int(current_version_match.group(1))

            # 解析远程版本号
            latest_version_match = re.search(r'R(\d+)', latest_tag)
            if not latest_version_match:
                QMessageBox.warning(self, checking_text, t('about_remote_parse_error'))
                return
            latest_version = int(latest_version_match.group(1))

            # 比较版本号
            if latest_version > current_version:
                # 发现新版本
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(checking_text)
                msg_box.setText(t('about_new_version', latest_tag))
                msg_box.setIcon(QMessageBox.NoIcon)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        font-size: 11px;
                    }
                    QMessageBox QLabel {
                        color: #495057;
                        font-size: 11px;
                        padding: 10px;
                    }
                """)

                # 自定义按钮
                yes_btn = msg_box.addButton(t('about_yes'), QMessageBox.YesRole)
                no_btn = msg_box.addButton(t('about_no'), QMessageBox.NoRole)

                # 绿色"是"按钮
                yes_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #51cf66;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 24px;
                        min-width: 80px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #40c057;
                    }
                """)

                # 红色"否"按钮
                no_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff6b6b;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 24px;
                        min-width: 80px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #fa5252;
                    }
                """)

                msg_box.exec_()

                if msg_box.clickedButton() == yes_btn:
                    QDesktopServices.openUrl(QUrl(f"https://github.com/{APP_REPO}/releases"))
            else:
                # 已是最新版本
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(checking_text)
                msg_box.setText(t('about_latest'))
                msg_box.setIcon(QMessageBox.NoIcon)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        font-size: 11px;
                    }
                    QMessageBox QLabel {
                        color: #495057;
                        font-size: 11px;
                        padding: 10px;
                    }
                """)
                msg_box.exec_()

        except urllib.error.URLError as e:
            QMessageBox.warning(self, checking_text, t('about_network_error', str(e)))
        except Exception as e:
            QMessageBox.warning(self, checking_text, t('about_check_failed', str(e)))
