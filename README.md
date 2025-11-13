# PromptGenie

A powerful PyQt6-based application for generating and managing AI prompts with a modern, user-friendly interface.

![PromptGenie Screenshot](screenshot.png)

## 🌟 Features

- 🎨 Modern, responsive UI with dark theme
- 📋 Copy generated prompts to clipboard with one click
- 🔍 Search and filter templates
- 🎭 Multiple prompt generation modes
- 📁 Save and load prompt templates
- 🎨 Built-in theme editor
- 🖼️ Image generation API integration
- 🚀 Built with PyQt6 for cross-platform compatibility
- 🛠️ Easy deployment with PyInstaller

## 📋 Requirements

- Python 3.8+
- PyQt6
- pyperclip
- pyinstaller (for building standalone executable)
- requests (for API integration)

## 🚀 Installation

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/zinwlad/PromptGenie.git
   cd PromptGenie
   
   # Switch to the latest development branch
   git checkout feature/theme-editor
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Building Standalone Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the application:
   ```bash
   python build_exe.py
   ```

   The executable will be created in the `dist` directory.

## 🎮 Usage

1. Launch the application:
   ```bash
   python PromptGenie_qt.py
   ```
   or run the executable from the `dist` directory.

2. Browse and select prompt templates from the left panel.
3. Customize the prompt using the available options.
4. Click "Copy to Clipboard" to copy the generated prompt.
5. Use the theme editor to create and manage your own prompt templates.

## 🛠️ Features in Detail

### Theme Editor
- Create, edit, and delete prompt templates
- Organize templates by categories
- Support for both positive and negative prompts

### API Integration
- Configure API settings for image generation
- Save and load API configurations
- Easy-to-use interface for generating images from prompts

### Keyword Library
- Predefined keywords for common prompt elements
- Categorized for easy access
- Tooltips with descriptions and effects

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

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
