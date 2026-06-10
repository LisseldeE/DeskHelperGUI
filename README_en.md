# DeskHelperGUI - Desktop Office Assistant

## Project Overview

DeskHelperGUI is a desktop office assistant tool that provides various quick and practical features to make daily office work more efficient.

## Project Information

- **Project Name**: DeskHelperGUI
- **Version**: R2
- **Author**: Lisselde_E
- **Email**: Lisselde.E@outlook.com
- **Repository**: https://github.com/LisseldeE/DeskHelperGUI

## Features

### Quick Compression
- **File Compression**: Choose compression format, compression level, and encryption options; save compressed files with global path
- **Quick Decompression**: Automatically identify compressed packages, support encrypted file decryption, save decompressed files with global path

### File Name Extraction
- Select folder to extract file names from
- Option to include or exclude file extensions
- Display extracted file name list
- Export to Excel file

### Image Processing
- Import image files
- **Rotate Image**: Choose rotation angle
- **Crop Image**: Provide preset size options (e.g., ID photo sizes)
- **Compress Image**: Provide compression size adjustment slider with real-time preview of compressed size

### Format Conversion
- Import single file or batch process folders
- **Image Format Conversion**: Support JPG, PNG, ICO, BMP, GIF, WebP format conversion
- **PDF to Image**: Convert PDF to JPG or PNG format
- **ICO Format**: Support 16×16 to 256×256 multiple size options, auto-adjust ratio
- Use global save path, support drag-and-drop import

## Update Log

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

## Technology Stack

- Python 3.x
- PyQt5 (GUI Framework)
- Pillow (Image Processing)
- Pandas + OpenPyXL (Excel Export)

## Installation and Running

### System Requirements
- Python 3.6 or higher
- Windows / macOS / Linux

### Install Dependencies
```bash
pip install PyQt5 Pillow pandas openpyxl PyMuPDF
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