# DeskHelperGUI - Desktop Office Assistant

## Project Overview

DeskHelperGUI is a desktop office assistant tool that provides various quick and practical features to make daily office work more efficient. Supports file compression, image processing, PDF operations, QR code generation, and many other practical functions with a simple and easy-to-use interface.

## Project Information

- **Project Name**: DeskHelperGUI
- **Author**: Lisselde_E
- **Email**: Lisselde.E@outlook.com
- **Repository**: https://github.com/LisseldeE/DeskHelperGUI

## Download

- **GitHub Releases**: https://github.com/LisseldeE/DeskHelperGUI/releases
- **Gitee Mirror**: https://gitee.com/Lisselde_E/DeskHelperGUI/releases (Recommended for users in China)

## Features

### Quick Compression
- **File Compression**: Choose compression format, compression level, and encryption options; save compressed files with global path
- **Quick Decompression**: Automatically identify compressed packages, support encrypted file decryption, save decompressed files with global path

### File Processing
- **File Name Extraction**: Select folder to extract file names, option to include or exclude extensions, export to Excel file
- **Batch Rename**: Support prefix/suffix, number sequence, text replacement, regex and other renaming rules
- **Batch Create**: Read list from Excel file, batch create folders or files
- Use global save path, support drag-and-drop import

### Image Processing
- Import image files
- **Rotate Image**: Choose rotation angle
- **Crop Image**: Provide preset size options (e.g., ID photo sizes)
- **Compress Image**: Provide compression size adjustment slider with real-time preview of compressed size
- **ID Photo Layout**: Support 1-inch, 2-inch and other ID photo size presets, choose paper size and layout direction, real-time preview of layout effect

### Format Conversion
- Import single file or batch process folders
- **Image Format Conversion**: Support JPG, PNG, ICO, BMP, GIF, WebP format conversion
- **PDF to Image**: Convert PDF to JPG or PNG format
- **ICO Format**: Support 16×16 to 256×256 multiple size options, auto-adjust ratio
- Use global save path, support drag-and-drop import

### PDF Processing
- Import PDF files
- **PDF Split**: Split PDF into single-page or multi-page files, support custom page range
- **PDF Merge**: Merge multiple PDF files into one
- **PDF Compress**: Compress PDF file size to reduce storage space
- **PDF to Word**: Convert PDF to Word document, preserving tables, images, and styles, with page range selection
  - Automatically preserves table structure and image positions
  - Support all pages or custom range conversion
  - Note: Space-based layouts may not convert well, scanned PDFs are not supported

### File Hash Verification
- Import files for hash calculation
- Support MD5, SHA-1, SHA-256, SHA-512 algorithms
- Compare with existing hash values for verification
- Export hash value results

### QR Code Tool
- **Generate QR Code**: Support text, URL, WiFi, business card, contact information conversion
- **Decode QR Code**: Recognize QR code image content
- **Custom Style**: Adjust QR code color and background color
- Support exporting QR code images

### File Encryption
- **File Encryption**: Encrypt files with password, support AES-256 encryption algorithm
- **File Decryption**: Decrypt encrypted files with password
- **Large File Optimization**: Use chunked encryption for large files, real-time progress display
- Support cancel operation, automatic cleanup of temporary files

## Update Log

### 2026.7.9 R6

**#01**
- Updated configuration file save path
- Fixed issue where hash verification old data remained when importing new files

**#02**
- Added PDF tool - PDF to Word feature
- Moved configuration file save path

See [Update Log](https://github.com/LisseldeE/DeskHelperGUI/blob/main/update.log)

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
- Python 3.6 or higher
- Windows / macOS / Linux

### Install Dependencies
```bash
pip install PyQt5 Pillow pandas openpyxl PyMuPDF pdf2docx cryptography qrcode[pil]
```

### Run Program
```bash
python DeskHelperGUI.py
```

## Open Source License

This project uses the MIT open source license, see [LICENSE](https://github.com/LisseldeE/DeskHelperGUI/blob/main/LICENSE) file for details.

## Privacy Policy

This project does not collect any user data. All configuration files are saved in the user's local directory. See relevant privacy statement for details.

## Contact and Feedback

**This application is under development. If you have any questions or new ideas, please feel free to contact me!**

- 📧 Email: Lisselde.E@outlook.com
- 🐙 GitHub: https://github.com/LisseldeE/DeskHelperGUI

Issues and Pull Requests are welcome!