# PromptGenie

A powerful PyQt6-based application for generating and managing AI prompts with a modern, user-friendly interface.

## 🌟 Features

- 🎨 Modern, responsive UI with dark theme
- 📋 Copy generated prompts to clipboard with one click
- 🔍 Search and filter templates
- 🎭 Multiple prompt generation modes
- 📁 Save and load prompt templates
- 🚀 Built with PyQt6 for cross-platform compatibility
- 🛠️ Easy deployment with PyInstaller

## 📋 Requirements

- Python 3.8+
- PyQt6
- pyperclip
- pyinstaller (for building standalone executable)

## 🚀 Installation

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/zinwlad/PromptGenie.git
   cd PromptGenie
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On macOS/Linux
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install them manually:
   ```bash
   pip install PyQt6 pyperclip pyinstaller
   ```

### Building Standalone Executable

1. Make sure you have all dependencies installed

2. Run the build script:
   ```bash
   python build_exe.py
   ```

3. The built application will be available in the `dist/PromptGenie` directory

## 🖥️ Usage

### Running from Source
```bash
python PromptGenie_qt.py
```

### Running Built Executable
1. Navigate to the `dist/PromptGenie` directory
2. Run `PromptGenie.exe` (Windows) or `PromptGenie` (macOS/Linux)

## 🛠️ Project Structure

- `PromptGenie_qt.py` - Main application file
- `ui_components.py` - Custom UI components and styling
- `build_exe.py` - Build script for creating standalone executable
- `theme_prompts.json` - Template prompts database
- `keyword_library.json` - Keywords and effects library

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Features in Detail

- **Prompt Generation**: Create AI prompts with various options and parameters
- **Clipboard Integration**: One-click copy functionality for generated prompts
- **Responsive UI**: Clean and modern interface built with PyQt6

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
