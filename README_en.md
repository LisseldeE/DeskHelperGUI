# DeskHelperGUI - Desktop Office Assistant

## Project Introduction

DeskHelperGUI is a desktop office auxiliary tool that provides various quick and practical features to make daily office work more efficient. It supports file compression, image processing, PDF operations, QR code generation and many other practical functions with a simple and easy-to-use interface.

## Project Screenshots

![Project Screenshots](https://lisseldee.github.io/images/webp/3-1.webp)

## Project Information

- **Project Name**: DeskHelperGUI
- **Project Author**: Lisselde_E
- **Project Homepage**: https://lisseldee.github.io
- **Project Repository**: https://github.com/LisseldeE/DeskHelperGUI

## Download

- **GitHub Releases**: https://github.com/LisseldeE/DeskHelperGUI/releases
- **Gitee Mirror Download**: https://gitee.com/Lisselde_E/DeskHelperGUI/releases (Recommended for users in China)

## Features

### Quick Compression
- **File Compression**: Select compression format, compression level, and whether to encrypt, save compressed files with global path
- **Quick Decompression**: Automatically identify compressed files, support encrypted file decryption, save decompressed files with global path

### File Processing
- **File Name Extraction**: Select folder to extract file names, optional include extension, export as Excel file
- **Batch Rename**: Support adding prefix/suffix, numeric numbering, text replacement, regular expression and other rename rules
- **Batch Create**: Read list from Excel file, batch create folders or files
- Use global save path, support drag and drop import

### Image Processing
- Import image files
- **Rotate Image**: Selectable rotation angle
- **Crop Image**: Provide preset size options (such as ID photo sizes)
- **Compress Image**: Provide compression size adjustment slider, real-time preview of compressed size
- **ID Photo Layout**: Support 1-inch, 2-inch and other ID photo size presets, select paper size and layout mode, real-time preview of layout effect

### Format Conversion
- Import single file or folder for batch processing
- **Image Format Conversion**: Support JPG, PNG, ICO, BMP, GIF, WebP format conversion
- **PDF to Image**: Support converting PDF to JPG or PNG format
- **ICO Format**: Support 16×16 to 256×256 multiple size options, automatically adjust ratio
- Use global save path, support drag and drop import

### PDF Processing
- Import PDF files
- **PDF Split**: Split PDF into single-page or multi-page files, support custom page range
- **PDF Merge**: Merge multiple PDF files into one
- **PDF Compress**: Compress PDF file size, reduce storage space
- **PDF to Word**: Convert PDF to Word document, preserve tables, images, styles, support page range selection
  - Automatically preserve table structure and image position
  - Support all pages or custom range conversion
  - Note: Space-based layout conversion quality is poor, scanned PDF not supported

### File Hash Verification
- Import files for hash value calculation
- Support MD5, SHA-1, SHA-256, SHA-512 algorithms
- Can compare with existing hash values for verification
- Export hash value results

### QR Code Tool
- **Generate QR Code**: Support text, URL, WiFi, business card, contact information and other content conversion
- **Decode QR Code**: Recognize QR code image content
- **Custom Style**: Adjust QR code foreground and background colors
- Support exporting QR code images

### File Encryption
- **File Encryption**: Use password to encrypt files, support AES-256 encryption algorithm
- **File Decryption**: Enter password to decrypt encrypted files
- **Large File Optimization**: Use block encryption for large files, real-time display progress
- Support cancel operation, automatically clean temporary files

## Changelog

### 2026.6.24 R6

**#02**
- Added PDF tool - Convert to Word function
- Moved configuration file save path

See [CHANGELOG.md](https://github.com/LisseldeE/DeskHelperGUI/blob/main/CHANGELOG.md) for details

## Technology Stack

- Python 3.x
- PyQt5 (GUI Framework)
- Pillow (Image Processing)
- Pandas + OpenPyXL (Excel Export)
- PyMuPDF (PDF Processing)
- pdf2docx (PDF to Word)
- cryptography (File Encryption)
- qrcode (QR Code Generation)

## Installation and Running

### System Requirements
- Python 3.6 or higher version
- Windows10/11

### Install Dependencies
```bash
pip install PyQt5 Pillow pandas openpyxl PyMuPDF pdf2docx cryptography qrcode[pil]
```

### Run Program
```bash
python DeskHelperGUI.py
```

## Open Source License

This project uses MIT open source license, see [LICENSE](https://github.com/LisseldeE/DeskHelperGUI/blob/main/LICENSE) file.

## Privacy Policy

This project does not collect any user data, all configuration files are saved in user local directory. See relevant privacy statement.

## Contact and Feedback

**Application in development, if you have any questions or new ideas, feel free to contact me!**

Welcome to submit Issues and Pull Requests!