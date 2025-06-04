# DiskEater

![DiskEater Banner](https://i.imgur.com/Gd4ajOi.png)

## 📝 Description

DiskEater is an optimized file encryption tool that allows encrypting and decrypting files in parallel, offering high performance and security.

## ✨ Features

- 🔒 Secure encryption using Fernet (symmetric encryption)
- ⚡ Parallel processing using all available CPU cores
- 🚀 Optimized I/O operations with memory mapping
- 🔑 Mystery key system for additional security
- 📊 Progress tracking and detailed logging
- 🎨 Colorful and user-friendly interface

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/Br3noAraujo/diskeater.git
cd diskeater
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

### Basic Usage

```bash
# Encrypt files in a folder
python diskeater.py ./my_files

# Decrypt files
python diskeater.py ./my_files --decrypt --key "your_mystery_key"
```

### Available Options

- `target_folder`: Folder containing files to be processed
- `--decrypt`: Decrypt files instead of encrypting
- `--key`: Mystery key required for decryption

## 📋 Important Notes

- Always keep backups of your important files
- Store your mystery key in a safe place
- The tool will create the target directory if it doesn't exist
- All operations are logged in 'diskeater.log'
- Files are processed in parallel for maximum speed
- Original files are removed after processing

## ⚠️ Warning

This tool is for educational purposes only.
Use at your own risk.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

- **Br3noAraujo** - [GitHub](https://github.com/Br3noAraujo)