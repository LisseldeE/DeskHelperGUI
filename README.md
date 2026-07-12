# DeskHelperGUI - 桌面办公小助手

## 项目简介

DeskHelperGUI 是一款桌面办公辅助工具，提供多种快捷实用功能，让日常办公更高效。支持文件压缩、图片处理、PDF操作、二维码生成等多种实用功能，界面简洁易用。

## 项目截图

![项目截图](https://lisseldee.github.io/images/webp/3-1.webp)

## 项目信息

- **项目名称**: DeskHelperGUI
- **项目作者**: Lisselde_E
- **项目主页**: https://lisseldee.github.io
- **项目仓库**: https://github.com/LisseldeE/DeskHelperGUI

## 下载

- **GitHub Releases**: https://github.com/LisseldeE/DeskHelperGUI/releases
- **Gitee 镜像下载**: https://gitee.com/Lisselde_E/DeskHelperGUI/releases （推荐国内用户使用）

## 功能特性

### 快捷压缩
- **文件压缩**: 可选择压缩格式、压缩级别、是否加密，以全局路径保存压缩文件
- **快捷解压**: 自动识别压缩包，支持加密文件解密，以全局路径保存解压文件

### 文件处理
- **文件名提取**: 选择文件夹提取文件名，可选择是否包含扩展名，导出为 Excel 文件
- **批量重命名**: 支持添加前缀/后缀、数字编号、替换文本、正则表达式等多种重命名规则
- **批量创建**: 从 Excel 文件读取列表，批量创建文件夹或文件
- 使用全局保存路径，支持拖拽导入

### 图片处理
- 导入图片文件
- **旋转图片**: 可选择旋转角度
- **裁剪图片**: 提供预设尺寸选项（如证件照尺寸）
- **压缩图片**: 提供压缩大小调整滑块，实时预览压缩后大小
- **证件照排版**: 支持1寸、2寸等多种证件照尺寸预设，可选择相纸大小和排布方式，实时预览排版效果

### 格式转换
- 导入单文件或文件夹批量处理
- **图片格式转换**: 支持 JPG、PNG、ICO、BMP、GIF、WebP 格式互转
- **PDF转图片**: 支持将 PDF 转换为 JPG 或 PNG 格式
- **ICO格式**: 支持 16×16 至 256×256 多种尺寸选择，自动调整比例
- 使用全局保存路径，支持拖拽导入

### PDF处理
- 导入 PDF 文件
- **PDF拆分**: 将 PDF 拆分为单页或多页文件，支持自定义页面范围
- **PDF合并**: 将多个 PDF 文件合并为一个
- **PDF压缩**: 压缩 PDF 文件大小，减小存储空间
- **PDF转Word**: 将 PDF 转换为 Word 文档，保留表格、图片、样式，支持页面范围选择
  - 自动保留表格结构和图片位置
  - 支持全部页面或自定义范围转换
  - 注意: 空格定位的布局转换效果较差，不支持扫描PDF

### 文件哈希校验
- 导入文件进行哈希值计算
- 支持 MD5、SHA-1、SHA-256、SHA-512 多种算法
- 可与已有哈希值进行比对校验
- 导出哈希值结果

### 二维码工具
- **生成二维码**: 支持文本、URL、WiFi、名片、联系信息等多种内容转换
- **解码二维码**: 识别二维码图片内容
- **自定义样式**: 可调整二维码颜色与背景色
- 支持导出二维码图片

### 文件加密
- **文件加密**: 使用密码加密文件，支持 AES-256 加密算法
- **文件解密**: 输入密码解密加密文件
- **大文件优化**: 对大文件采用分块加密，实时显示进度
- 支持取消操作，自动清理临时文件

## 更新日志

### 2026.6.24 R6

**#02**
- 新增PDF工具-转为word功能
- 移动了配置文件保存路径

详见 [更新日志](https://github.com/LisseldeE/DeskHelperGUI/blob/main/CHANGELOG.md)

## 技术栈

- Python 3.x
- PyQt5 (GUI框架)
- Pillow (图片处理)
- Pandas + OpenPyXL (Excel导出)
- PyMuPDF (PDF处理)
- pdf2docx (PDF转Word)
- cryptography (文件加密)
- qrcode (二维码生成)

## 安装与运行

### 系统要求
- Python 3.6 或更高版本
- Windows10/11

### 安装依赖
```bash
pip install PyQt5 Pillow pandas openpyxl PyMuPDF pdf2docx cryptography qrcode[pil]
```

### 运行程序
```bash
python DeskHelperGUI.py
```

## 开源声明

本项目采用 MIT 开源协议，详见 [LICENSE](https://github.com/LisseldeE/DeskHelperGUI/blob/main/LICENSE) 文件。

## 隐私政策

本项目不收集任何用户数据，所有配置文件保存在用户本地目录。详见相关隐私说明。

## 联系与反馈

**开发中应用，如有问题或新的创意欢迎和我联系！**

欢迎提交 Issue 和 Pull Request！