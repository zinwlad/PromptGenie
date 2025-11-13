"""
Theme Editor for PromptGenie
Provides a user interface for creating and editing prompt themes
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QComboBox, QPushButton,
                           QMessageBox, QFileDialog, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ThemeEditor(QDialog):
    """Dialog for editing prompt themes"""
    theme_saved = pyqtSignal(dict)  # Signal emitted when a theme is saved
    
    def __init__(self, parent=None, theme_data: Optional[Dict] = None, 
                 categories: Optional[List[str]] = None):
        super().__init__(parent)
        self.theme_data = theme_data if theme_data else {}
        self.categories = categories or ["Фэнтези", "Фотография", "3D Рендер", "Аниме"]
        self.setup_ui()
        self.setWindowTitle("Редактор тем" if not theme_data else "Редактировать тему")
        self.setMinimumSize(600, 700)
        
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QGroupBox()
        form_layout = QVBoxLayout(scroll_widget)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        if "category" in self.theme_data:
            idx = self.category_combo.findText(self.theme_data["category"])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.add_form_row(form_layout, "Категория:", self.category_combo)
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.theme_data.get("title_ru", ""))
        self.title_edit.setPlaceholderText("Название темы")
        self.add_form_row(form_layout, "Название:", self.title_edit)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.theme_data.get("description_ru", ""))
        self.desc_edit.setPlaceholderText("Описание темы")
        self.desc_edit.setMaximumHeight(100)
        form_layout.addWidget(QLabel("Описание:"))
        form_layout.addWidget(self.desc_edit)
        
        # Prompt
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.theme_data.get("prompt_combined_en", ""))
        self.prompt_edit.setPlaceholderText("Введите промпт (английский)")
        form_layout.addWidget(QLabel("Промпт (английский):"))
        form_layout.addWidget(self.prompt_edit)
        
        # Negative prompt
        self.negative_prompt_edit = QTextEdit()
        self.negative_prompt_edit.setPlainText(
            self.theme_data.get("negative_prompt", 
                              "worst quality, low quality, blurry, text, watermark")
        )
        self.negative_prompt_edit.setPlaceholderText("Нежелательные элементы (через запятую)")
        self.negative_prompt_edit.setMaximumHeight(80)
        form_layout.addWidget(QLabel("Исключения (negative prompt):"))
        form_layout.addWidget(self.negative_prompt_edit)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_theme)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
    def add_form_row(self, layout, label_text, widget):
        """Helper to add a form row with a label and widget"""
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(widget, 1)
        layout.addLayout(row)
    
    def get_theme_data(self) -> Dict[str, Any]:
        """Get the theme data from the form"""
        return {
            "category": self.category_combo.currentText(),
            "title_ru": self.title_edit.text().strip(),
            "description_ru": self.desc_edit.toPlainText().strip(),
            "prompt_combined_en": self.prompt_edit.toPlainText().strip(),
            "negative_prompt": self.negative_prompt_edit.toPlainText().strip()
        }
    
    def validate_inputs(self) -> bool:
        """Validate the form inputs"""
        data = self.get_theme_data()
        
        if not data["title_ru"]:
            self.show_error("Ошибка", "Пожалуйста, укажите название темы")
            self.title_edit.setFocus()
            return False
            
        if not data["prompt_combined_en"]:
            self.show_error("Ошибка", "Пожалуйста, введите промпт")
            self.prompt_edit.setFocus()
            return False
            
        return True
    
    def show_error(self, title: str, message: str):
        """Show an error message"""
        QMessageBox.critical(self, title, message)
    
    def save_theme(self):
        """Save the theme and close the dialog"""
        if not self.validate_inputs():
            return
            
        theme_data = self.get_theme_data()
        self.theme_saved.emit(theme_data)
        self.accept()


def show_theme_editor(parent=None, theme_data=None, categories=None) -> Optional[Dict]:
    """Show the theme editor dialog and return the result"""
    dialog = ThemeEditor(parent, theme_data, categories)
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        return dialog.get_theme_data()
    return None


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Example usage
    theme = show_theme_editor()
    if theme:
        print("Saved theme:", json.dumps(theme, ensure_ascii=False, indent=2))
    
    sys.exit(app.exec())
