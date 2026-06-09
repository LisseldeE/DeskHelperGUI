# DeskHelperGUI - 桌面办公小助手

## 项目简介

DeskHelperGUI 是一款桌面办公辅助工具，提供多种快捷实用功能，让日常办公更高效。

## 项目信息

- **项目名称**: DeskHelperGUI
- **项目版本**: R1
- **项目作者**: Lisselde_E
- **联系邮箱**: Lisselde.E@outlook.com
- **项目仓库**: https://github.com/LisseldeE/DeskHelperGUI

## 功能特性

### 快捷压缩
- **文件压缩**: 可选择压缩格式、压缩级别、是否加密，以全局路径保存压缩文件
- **快捷解压**: 自动识别压缩包，支持加密文件解密，以全局路径保存解压文件

### 文件名提取
- 选择要提取文件名的文件夹
- 可选择是否需要扩展名
- 提取后显示文件名列表
- 导出为 Excel 文件

### 图片处理
- 导入图片文件
- **旋转图片**: 可选择旋转角度
- **裁剪图片**: 提供预设尺寸选项（如证件照尺寸）
- **压缩图片**: 提供压缩大小调整滑块，实时预览压缩后大小

## 更新日志

### 2026.6.8 R1
**#01**
- 初步构建软件界面
- 新增压缩功能
- 适配多语言显示

**#02**
- 优化界面 DPI 适配
- 优化信息通知样式
- 添加按钮动画与过渡样式
- 优化按钮文字显示逻辑
- 完成压缩功能构建
- 构建程序图标

### 2026.6.9
**#03**
- 新增功能 - 文件名提取
- 修复全局路径保存读取问题
- 完成文件名提取功能构建

**#04**
- 新增功能 - 图片处理
- 优化图片处理逻辑
- 修复窗口大小调整时的按钮跳动问题

## 技术栈

- Python 3.x
- PyQt5 (GUI框架)
- Pillow (图片处理)
- Pandas + OpenPyXL (Excel导出)

## 安装与运行

### 系统要求
- Python 3.6 或更高版本
- Windows / macOS / Linux

### 安装依赖
```bash
pip install PyQt5 Pillow pandas openpyxl
```

### 运行程序
```bash
python DeskHelperGUI.py
```

## 开源声明

本项目采用 MIT 开源协议，详见 [LICENSE](LICENSE) 文件。

## 联系与反馈

**开发中应用，如有问题或新的创意欢迎和我联系！**

- 📧 邮箱: Lisselde.E@outlook.com
- 🐙 GitHub: https://github.com/LisseldeE/DeskHelperGUI

欢迎提交 Issue 和 Pull Request！