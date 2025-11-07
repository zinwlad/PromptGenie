import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def cleanup_previous_build(script_dir):
    """Remove previous build directories and files"""
    dirs_to_remove = [
        script_dir / "build",
        script_dir / "dist",
        script_dir / "PromptGenie.spec"
    ]
    
    print("Cleaning up previous build...")
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            if dir_path.is_dir():
                shutil.rmtree(dir_path, ignore_errors=True)
                print(f"Removed directory: {dir_path}")
            else:
                try:
                    os.remove(dir_path)
                    print(f"Removed file: {dir_path}")
                except Exception as e:
                    print(f"Error removing {dir_path}: {e}")
    
    # Small delay to ensure all file handles are released
    time.sleep(1)

def main():
    # Set paths
    script_dir = Path(__file__).parent.absolute()
    build_dir = script_dir / "dist" / "PromptGenie"
    
    # Clean up previous build
    cleanup_previous_build(script_dir)
    
    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)
    
    # Install/upgrade required packages
    print("Installing/updating required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "pyinstaller", "pyqt6", "pyperclip"])
    
    # Create a data directory in both build and dist folders
    build_data_dir = build_dir / "data"
    dist_data_dir = script_dir / "dist" / "data"
    
    # Create directories if they don't exist
    os.makedirs(build_data_dir, exist_ok=True)
    os.makedirs(dist_data_dir, exist_ok=True)
    
    # Copy data files to both locations
    data_files = ["theme_prompts.json", "keyword_library.json"]
    for file in data_files:
        src = script_dir / file
        if src.exists():
            # Copy to build directory
            shutil.copy2(src, build_data_dir / file)
            print(f"Copied {file} to {build_data_dir}")
            
            # Also copy to dist/data directory
            shutil.copy2(src, dist_data_dir / file)
            print(f"Copied {file} to {dist_data_dir}")
    
    # Prepare PyInstaller command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name", "PromptGenie",
        "--windowed",
        "--onefile",
        "--icon=NONE",
        f"--add-data={script_dir}/theme_prompts.json;.",
        f"--add-data={script_dir}/keyword_library.json;.",
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "pyperclip",
        "--clean",
        "--distpath", str(build_dir.parent),  # Output to dist/PromptGenie
        str(script_dir / "PromptGenie_qt.py")
    ]
    
    # Run PyInstaller
    print("Building PromptGenie executable...")
    subprocess.check_call(pyinstaller_cmd)
    
    # Create logs directory
    logs_dir = build_dir / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Copy additional files
    for file in ["theme_prompts.json", "keyword_library.json"]:
        src = script_dir / file
        if src.exists():
            shutil.copy2(src, build_dir / file)
    
    print(f"\nBuild complete! Executable is in: {build_dir}")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
