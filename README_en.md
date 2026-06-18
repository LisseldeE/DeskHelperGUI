# DeskHelperGUI - Desktop Office Assistant

## Project Overview

DeskHelperGUI is a desktop office assistant tool that provides various quick and practical features to make daily office work more efficient.

## Project Information

- **Project Name**: DeskHelperGUI
- **Version**: R5
- **Author**: Lisselde_E
- **Email**: Lisselde.E@outlook.com
- **Repository**: https://github.com/LisseldeE/DeskHelperGUI

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
- **PDF Split**: Split PDF into single-page or multi-page files
- **PDF Merge**: Merge multiple PDF files into one
- **PDF Compress**: Compress PDF file size to reduce storage space

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

### 2026.6.18 R5
**#01**
- Added feature - File Processing
- Merged file name extraction module, added batch rename and batch create sub-features
- Fixed issue where some control text displayed abnormally after switching language in all modules
- Fixed program crash caused by switching language
- Fixed occasional crash on program startup

**#02**
- Updated content of two introduction files
- Released R5 build version

### 2026.6.13 R4
**#01**
- Fixed issue where duplicate files in export path would directly replace target files
- Fixed issue where top notification banner message was too long
- Unified information style displayed in top notification banner for all modules
- Added feature - File hash verification
- Added dynamic transition animation to main interface

**#02**
- Added feature - QR Code Tool
- Support text, URL, WiFi, business card, contact information conversion
- Added QR code decoding mode
- Added custom QR code style (color and background color)
- Optimized interface layout display logic

**#03**
- Added feature - File Encryption
- Support file encryption and encrypted file decryption
- Optimized logic for large file encryption/decryption
- Optimized memory logic for large file encryption/decryption
- Fixed issue where duplicate name saving logic caused some modules to crash
- Optimized program memory stack, increased stability

**#04**
- Updated content of two introduction files

### 2026.6.8 R1
**#01**
- Initial software interface construction
- Added compression functionality
- Adapted multi-language display

**#02**
- Optimized interface DPI adaptation
- Optimized information notification style
- Added button animation and transition styles
- Optimized button text display logic
- Completed compression functionality construction
- Built program icon

### 2026.6.9
**#03**
- Added feature - File name extraction
- Fixed global path save/read issues
- Completed file name extraction functionality construction

**#04**
- Added feature - Image processing
- Optimized image processing logic
- Fixed button jumping issue when adjusting window size

### 2026.6.10 R2
**#01**
- Added global settings button
- Changed save path to global save path, removed individual configuration in modules
- Added save path configuration dialog on startup
- Optimized program startup speed

**#02**
- Added feature - Format conversion
- Added PDF to JPG, PNG format options
- Optimized interface notification banner style
- Optimized output path display in other modules

### 2026.6.11 R3
**#01**
- Added feature - PDF Processing
- Added PDF file split, merge and compress
- Optimized progress bar display rendering logic for all modules
- Optimized and unified interface layout logic for all modules

**#02**
- Added feature - Image Processing - ID Photo Layout
- Added multiple layout presets and paper size presets
- Layout can freely adjust photo arrangement
- In ID photo layout mode, other processing methods are temporarily disabled

**#03**
- Added default user desktop settings path
- Added domestic download source, intelligent switching to optimize download update experience

## Technology Stack

- Python 3.x
- PyQt5 (GUI Framework)
- Pillow (Image Processing)
- Pandas + OpenPyXL (Excel Export)
- cryptography (File Encryption)
- qrcode (QR Code Generation)

## Installation and Running

### System Requirements
- Python 3.6 or higher
- Windows / macOS / Linux

### Install Dependencies
```bash
pip install PyQt5 Pillow pandas openpyxl PyMuPDF cryptography qrcode[pil]
```

### Run Program
```bash
python DeskHelperGUI.py
```

## Open Source License

This project uses the MIT open source license, see [LICENSE](LICENSE) file for details.

## Contact and Feedback

**This application is under development. If you have any questions or new ideas, please feel free to contact me!**

- 📧 Email: Lisselde.E@outlook.com
- 🐙 GitHub: https://github.com/LisseldeE/DeskHelperGUI

Issues and Pull Requests are welcome!