# PromptGenie 3.0 — Профессиональный конструктор промптов
import sys
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prompt_genie.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, QSettings

# Constants
THEMES_FILE = Path(__file__).parent / "theme_prompts.json"
from PyQt6.QtGui import QAction, QIcon, QPixmap, QFont, QTextCursor, QPainter, QLinearGradient, QColor, QPen
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, QTextEdit, 
                           QComboBox, QWidget, QFileDialog, QMessageBox, QSplitter,
                           QInputDialog, QLineEdit, QScrollArea, QFrame, QCheckBox,
                           QProgressBar, QStatusBar, QMenu, QSystemTrayIcon, QStyle,
                           QDialog, QDialogButtonBox, QFormLayout, QTabWidget, QTabBar,
                           QToolButton, QGroupBox, QSpinBox, QSlider)

# Local imports
from ui_theme import Ui_MainWindow
import version
from utils import resource_path, load_json_schema, validate_json_schema, safe_json_load
from theme_editor import show_theme_editor

# API Integration
class APIIntegrationDialog(QDialog):
    """Dialog for API integration settings"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки API")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Введите ваш API ключ")
        
        form.addRow("API ключ:", self.api_key_edit)
        
        # API Selection
        self.api_combo = QComboBox()
        self.api_combo.addItems(["Stable Diffusion API", "OpenAI DALL-E", "Midjourney (если доступно)"])
        form.addRow("Сервис:", self.api_combo)
        
        # Settings group
        settings_group = QGroupBox("Настройки генерации")
        settings_layout = QFormLayout()
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 1024)
        self.width_spin.setValue(512)
        settings_layout.addRow("Ширина:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 1024)
        self.height_spin.setValue(512)
        settings_layout.addRow("Высота:", self.height_spin)
        
        self.steps_slider = QSlider(Qt.Orientation.Horizontal)
        self.steps_slider.setRange(10, 150)
        self.steps_slider.setValue(30)
        settings_layout.addRow("Шаги генерации:", self.steps_slider)
        
        settings_group.setLayout(settings_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(settings_group)
        layout.addWidget(buttons)
        
    def get_settings(self) -> dict:
        """Get the API settings"""
        return {
            "api_key": self.api_key_edit.text().strip(),
            "service": self.api_combo.currentText(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "steps": self.steps_slider.value()
        }

class TemplatePreviewEdit(QTextEdit):
    """A custom text edit for template previews with syntax highlighting and line numbers."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Предпросмотр шаблона...")
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                min-height: 200px;
            }
            QTextEdit:focus {
                border: 1px solid #4a9cff;
            }
        """)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setAcceptRichText(False)
        
        # Set up the document with a monospace font
        font = QFont('Consolas', 10)
        self.setFont(font)


class TemplateDescriptionEdit(QTextEdit):
    """A custom text edit for template descriptions with placeholder text and styling."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Введите описание шаблона...")
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 100px;
            }
            QTextEdit:focus {
                border: 1px solid #4a9cff;
            }
        """)
        self.setAcceptRichText(False)


class GradientButton(QPushButton):
    """A button with a gradient background."""
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setMinimumHeight(32)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:pressed {
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(self.color).lighter(120))
        gradient.setColorAt(1, QColor(self.color).darker(120))
        
        # Draw button background with gradient
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)
        
        # Draw text
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class SearchBox(QLineEdit):
    """A custom search box with a clear button."""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                background: #2d2d2d;
                color: #e0e0e0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4a9cff;
            }
        """)


class StatusLabel(QLabel):
    """A custom status label that shows messages with different styles."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                padding: 2px 8px;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setMinimumWidth(200)
        
    def set_message(self, message, message_type="info"):
        """Set the status message with optional type styling.
        
        Args:
            message (str): The message to display
            message_type (str): Type of message (info, success, warning, error)
        """
        # Remove any existing style classes
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                padding: 2px 8px;
                border-radius: 4px;
                margin: 2px;
        """)
        
        # Add style based on message type
        if message_type == "success":
            self.setStyleSheet(self.styleSheet() + """
                background-color: #2e7d32;
                color: #e8f5e9;
                border: 1px solid #1b5e20;
            """)
        elif message_type == "warning":
            self.setStyleSheet(self.styleSheet() + """
                background-color: #ff8f00;
                color: #fff3e0;
                border: 1px solid #e65100;
            """)
        elif message_type == "error":
            self.setStyleSheet(self.styleSheet() + """
                background-color: #c62828;
                color: #ffebee;
                border: 1px solid #b71c1c;
            """)
        else:  # info
            self.setStyleSheet(self.styleSheet() + """
                background-color: #1565c0;
                color: #e3f2fd;
                border: 1px solid #0d47a1;
            """)
            
        self.setText(message)


class TooltipCheckBox(QCheckBox):
    """A custom QCheckBox that shows a tooltip with the full text when hovered.
    
    Args:
        text (str): The text to display next to the checkbox
        tooltip (str, optional): The tooltip text to show on hover
        effect (str, optional): Additional effect information
        word_type (str, optional): Type of word ('positive' or 'negative') to style accordingly
        parent (QWidget, optional): Parent widget
    """
    def __init__(self, text, tooltip="", effect="", word_type="positive", parent=None):
        super().__init__(text, parent)
        # Combine tooltip and effect for the tooltip text
        full_tooltip = tooltip
        if effect:
            full_tooltip = f"{tooltip}\n\nEffect: {effect}" if tooltip else f"Effect: {effect}"
        self.setToolTip(full_tooltip)
        
        # Set styling based on word type
        if word_type.lower() == "negative":
            self.setStyleSheet("""
                QCheckBox {
                    color: #ff6b6b;
                    padding: 4px 0;
                    spacing: 8px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #ff6b6b;
                    background: #2d2d2d;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #ff6b6b;
                    background: #ff6b6b;
                    border-radius: 3px;
                }
                QCheckBox:hover {
                    color: #ff8e8e;
                }
            """)
        else:
            self.setStyleSheet("""
                QCheckBox {
                    color: #e0e0e0;
                    padding: 4px 0;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #4a4a4a;
                    background: #2d2d2d;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #4a9cff;
                    background: #4a9cff;
                    border-radius: 3px;
                }
                QCheckBox:hover {
                    color: #ffffff;
                }
            """)


class StyledTabWidget(QTabWidget):
    """A custom tab widget with styled tabs."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
                background: #2d2d2d;
                border-radius: 4px;
                margin: 1px;
            }
            QTabBar::tab {
                background: #3e3e3e;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #3e3e3e;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2d2d2d;
                border-bottom: 1px solid #2d2d2d;
                margin-bottom: -1px;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QTabBar::tab:hover {
                background: #4a4a4a;
            }
        """)


class PromptGenie(QMainWindow):
    def get_data_dir(self) -> Path:
        """Get the application data directory."""
        # Use local directory for now
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
        
    def get_config_path(self) -> Path:
        """Get the path to the config file."""
        return self.data_dir / "config.json"
        
    def load_config(self) -> dict:
        """Load the application configuration."""
        config_path = self.get_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return {}
        
    def save_config(self, config: dict) -> bool:
        """Save the application configuration."""
        try:
            config_path = self.get_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def __init__(self):
        super(QMainWindow, self).__init__()
        logger.info("Инициализация приложения PromptGenie")
        
        try:
            # Initialize variables
            self.themes = []
            self.kw_data = {}
            self.selected_words = {}
            self.data_dir = self.get_data_dir()
            self.config = self.load_config()
            
            # Load data
            logger.debug("Loading data...")
            self.load_data()
            
            # Initialize UI
            self.setWindowTitle("PromptGenie 3.0")
            self.setMinimumSize(1280, 720)
            self.setStyleSheet("background:#1e1e1e; color:#e0e0e0; font-family:Segoe UI;")
            
            # Initialize UI components
            self._init_ui_components()
            
            logger.info("Приложение успешно инициализировано")
            
        except Exception as e:
            logger.critical("Ошибка при инициализации приложения", exc_info=True)
            raise
            
    def load_data(self):
        """Load theme and keyword data."""
        try:
            # Load themes
            if THEMES_FILE.exists():
                with open(THEMES_FILE, 'r', encoding='utf-8') as f:
                    themes_data = json.load(f)
                    # Access the 'themes' key from the loaded data
                    self.themes = themes_data.get('themes', [])
                logger.info(f"Loaded {len(self.themes)} themes from {THEMES_FILE}")
            else:
                logger.warning(f"Themes file not found: {THEMES_FILE}")
                self.themes = []
                
            # Load keyword library
            keyword_file = Path(__file__).parent / "keyword_library.json"
            if keyword_file.exists():
                with open(keyword_file, 'r', encoding='utf-8') as f:
                    keyword_data = json.load(f)
                    # Access the 'keywords' key from the loaded data
                    self.kw_data = keyword_data.get('keywords', {})
                logger.info(f"Loaded keyword library from {keyword_file}")
            else:
                logger.warning(f"Keyword library not found: {keyword_file}")
                self.kw_data = {}
                
            # Initialize selected words
            for category in self.kw_data.keys():
                self.selected_words[category] = []
                
            logger.info("Data loading completed successfully")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            QMessageBox.critical(
                self,
                "Ошибка загрузки данных",
                f"Не удалось загрузить данные: {str(e)}"
            )
            raise
            raise
    
    def _init_ui_components(self):
        """Инициализация компонентов пользовательского интерфейса."""
        logger.debug("Инициализация компонентов UI")
        self.init_ui()

    def init_ui(self):
        """Инициализация главного окна приложения."""
        try:
            logger.debug("Инициализация главного окна")
            
            # Создаем центральный виджет и устанавливаем его
            central = QWidget()
            self.setCentralWidget(central)
            
            # Основной макет
            layout = QVBoxLayout(central)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)

            # Create styled tab widget
            tabs = StyledTabWidget()
            
            # Добавляем вкладки
            templates_tab = self.templates_tab()
            builder_tab = self.builder_tab()
            
            tabs.addTab(templates_tab, "Шаблоны")
            tabs.addTab(builder_tab, "Конструктор")
            
            layout.addWidget(tabs)
            
            # Статус бар
            self.status_label = StatusLabel()
            self.statusBar().addWidget(self.status_label)
            
            # Устанавливаем активную вкладку
            tabs.setCurrentIndex(0)
            
            logger.debug("Главное окно успешно инициализировано")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации интерфейса: {str(e)}", exc_info=True)
            raise

    def templates_tab(self):
        """Создает и возвращает вкладку с шаблонами."""
        try:
            logger.debug("Инициализация вкладки шаблонов")
            
            # Основной виджет вкладки
            w = QWidget()
            layout = QHBoxLayout(w)
            layout.setSpacing(15)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Левая панель - список шаблонов
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setSpacing(10)
            
            # Поле поиска
            self.search_edit = SearchBox("Поиск по названию или описанию...")
            self.search_edit.textChanged.connect(self.filter_templates)
            left_layout.addWidget(self.search_edit)
            
            # Выбор категории
            self.category_combo = QComboBox()
            self.category_combo.addItem("Все категории", "")
            self.category_combo.currentIndexChanged.connect(self.filter_templates)
            left_layout.addWidget(self.category_combo)
            
            # Список шаблонов
            self.template_list = QListWidget()
            self.template_list.itemClicked.connect(self.show_temp)
            left_layout.addWidget(self.template_list, 1)  # Растягиваем на все доступное пространство
            
            # Кнопки управления
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            
            self.btn_add = GradientButton("Добавить", "#007acc")
            self.btn_add.clicked.connect(lambda: self.open_template_dialog())
            
            self.btn_edit = GradientButton("Изменить", "#ff9800")
            self.btn_edit.clicked.connect(self.edit_current_template)
            self.btn_edit.setEnabled(False)
            
            self.btn_delete = GradientButton("Удалить", "#f44336")
            self.btn_delete.clicked.connect(self.delete_current_template)
            self.btn_delete.setEnabled(False)
            
            self.btn_copy = GradientButton("Копировать", "#4caf50")
            self.btn_copy.clicked.connect(self.copy_template_prompt)
            self.btn_copy.setEnabled(False)
            
            btn_layout.addWidget(self.btn_add)
            btn_layout.addWidget(self.btn_edit)
            btn_layout.addWidget(self.btn_delete)
            btn_layout.addWidget(self.btn_copy)
            
            left_layout.addWidget(btn_frame)
            
            # Правая панель - просмотр шаблона
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            right_layout.setSpacing(10)
            
            # Категория шаблона
            self.temp_category = QLabel()
            self.temp_category.setStyleSheet("font-size: 14px; color: #4fc3f7;")
            right_layout.addWidget(self.temp_category)
            
            # Заголовок шаблона
            self.temp_title = QLabel()
            self.temp_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            right_layout.addWidget(self.temp_title)
            
            # Описание шаблона
            self.temp_desc = TemplateDescriptionEdit(self)
            self.temp_desc.setReadOnly(True)
            right_layout.addWidget(self.temp_desc)
            
            # Просмотр шаблона
            self.temp_preview = TemplatePreviewEdit(self)
            self.temp_preview.setReadOnly(True)
            self.temp_preview.setStyleSheet("""
                QTextEdit {
                    background: #252526;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
            right_layout.addWidget(self.temp_preview, 1)  # Растягиваем на все доступное пространство
            
            # Кнопка копирования
            self.copy_btn = GradientButton("Копировать промпт", "#4caf50")
            self.copy_btn.clicked.connect(self.copy_template_prompt)
            right_layout.addWidget(self.copy_btn)
            
            # Добавляем панели в основной макет
            layout.addWidget(left_panel, 1)
            layout.addWidget(right_panel, 2)
            
            # Загружаем список шаблонов
            self.refresh_template_list()
            
            logger.debug("Вкладка шаблонов успешно инициализирована")
            return w
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации вкладки шаблонов: {str(e)}", exc_info=True)
            raise

    def clear_template_preview(self):
        """Очищает предпросмотр шаблона."""
        # Обработка старых имен атрибутов
        if hasattr(self, 'temp_preview'):
            self.temp_preview.clear()
        if hasattr(self, 'temp_desc'):
            self.temp_desc.clear()
        if hasattr(self, 'temp_category'):
            self.temp_category.clear()
        if hasattr(self, 'temp_title'):
            self.temp_title.clear()
            
        # Обработка новых имен атрибутов
        if hasattr(self, 'template_preview'):
            self.template_preview.clear()
        if hasattr(self, 'template_description'):
            self.template_description.clear()
        if hasattr(self, 'template_variables_list'):
            self.template_variables_list.clear()

    def refresh_template_list(self):
        """Обновляет список шаблонов и категорий."""
        self.template_list.clear()
        
        # Собираем все категории
        categories = set()
        for theme in self.themes:
            category = theme.get("category", "Без категории")
            categories.add(category)
            
            item = QListWidgetItem(f"{category} - {theme['title_ru']}")
            item.setData(Qt.ItemDataRole.UserRole, theme)
            self.template_list.addItem(item)
        
        # Обновляем список категорий
        current_category = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("Все категории", "")
        for category in sorted(categories):
            self.category_combo.addItem(category, category)
            
        # Восстанавливаем выбранную категорию, если она есть
        if current_category:
            index = self.category_combo.findData(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        # Применяем фильтры
        self.filter_templates()
        
        # Сбрасываем превью при обновлении списка
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)
            self.show_temp(self.template_list.currentItem())
        else:
            self.clear_template_preview()

    def filter_templates(self, text=None):
        """Фильтрует список шаблонов по категории и введенному тексту."""
        try:
            # Обработка текста для поиска
            search_text = ""
            if text is not None and not isinstance(text, int):
                search_text = str(text).lower()
            elif hasattr(self, 'search_edit'):
                search_text = self.search_edit.text().lower()
                
            # Получаем выбранную категорию
            selected_category = self.category_combo.currentData()
            
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if not item:
                    continue
                    
                theme = item.data(Qt.ItemDataRole.UserRole)
                if not theme:
                    continue
                
                # Проверяем категорию
                category_match = not selected_category or (theme.get("category") == selected_category)
                
                # Проверяем вхождение текста в название или описание, если текст задан
                text_match = True
                if search_text:
                    title = str(theme.get("title_ru", "")).lower()
                    desc = str(theme.get("description_ru", "")).lower()
                    text_match = (search_text in title) or (search_text in desc)
                
                item.setHidden(not (category_match and text_match))
                
        except Exception as e:
            logger.error(f"Ошибка при фильтрации шаблонов: {str(e)}", exc_info=True)
            
    def copy_template_prompt(self):
        """Копирует текст промпта выбранного шаблона в буфер обмена."""
        try:
            if not hasattr(self, 'temp_preview') or not self.temp_preview.toPlainText():
                QMessageBox.information(self, "Информация", "Нет активного шаблона для копирования")
                return
                
            # Получаем текст из превью
            prompt_text = self.temp_preview.toPlainText()
            
            # Копируем в буфер обмена
            clipboard = QApplication.clipboard()
            clipboard.setText(prompt_text)
            
            # Показываем уведомление
            QMessageBox.information(self, "Успех", "Промпт скопирован в буфер обмена")
            
        except Exception as e:
            logger.error(f"Ошибка при копировании промпта: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось скопировать промпт:\n{str(e)}"
            )
            
    def edit_current_template(self):
        """Открывает диалог редактирования выбранного шаблона."""
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Информация", "Выберите шаблон для редактирования")
            return
            
        theme_data = current_item.data(Qt.ItemDataRole.UserRole)
        self.open_template_dialog(edit_mode=True, theme=theme_data)
        
    def delete_current_template(self):
        """Удаляет выбранный шаблон."""
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Информация", "Выберите шаблон для удаления")
            return
            
        theme_data = current_item.data(Qt.ItemDataRole.UserRole)
        theme_title = theme_data.get('title_ru', 'Неизвестный шаблон')
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            'Подтверждение удаления',
            f'Вы уверены, что хотите удалить шаблон "{theme_title}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем шаблон из списка
                for i, theme in enumerate(self.themes):
                    if theme.get('title_ru') == theme_title:
                        del self.themes[i]
                        break
                
                # Обновляем список шаблонов
                self.refresh_template_list()
                self.clear_template_preview()
                
                # Сохраняем изменения
                self.save_themes()
                
                QMessageBox.information(self, "Успех", "Шаблон успешно удален")
                
            except Exception as e:
                logger.error(f"Ошибка при удалении шаблона: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить шаблон:\n{str(e)}"
                )

    def open_template_dialog(self, edit_mode=False, theme=None):
        """Открывает диалог редактирования шаблона.
        
        Args:
            edit_mode: Режим редактирования (True) или создания (False)
            theme: Словарь с данными шаблона для редактирования
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование шаблона" if edit_mode else "Новый шаблон")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        # Поля ввода
        form = QFormLayout()
        
        # Категория с подсказкой
        category_edit = QComboBox()
        category_edit.setEditable(True)
        category_edit.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
        
        # Добавляем существующие категории
        categories = set()
        for t in self.themes:
            if "category" in t:
                categories.add(t["category"])
        
        for category in sorted(categories):
            category_edit.addItem(category)
        
        # Если это новая категория, добавляем её в список
        if theme and "category" in theme and theme["category"] not in categories:
            category_edit.addItem(theme["category"])
        
        form.addRow("Категория:", category_edit)
        
        # Поля для ввода
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Название шаблона")
        form.addRow("Название:", title_edit)
        
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Описание шаблона")
        desc_edit.setMaximumHeight(100)
        form.addRow("Описание:", desc_edit)
        
        prompt_edit = QTextEdit()
        prompt_edit.setPlaceholderText("Промпт (можно использовать ||| для разделения позитивных и негативных подсказок)")
        form.addRow("Промпт:", prompt_edit)
        
        # Заполняем поля, если это редактирование
        if theme:
            category_edit.setCurrentText(theme.get("category", ""))
            title_edit.setText(theme.get("title_ru", ""))
            desc_edit.setText(theme.get("description_ru", ""))
            prompt_edit.setText(theme.get("prompt_combined_en", ""))
        
        layout.addLayout(form)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Собираем данные
            new_theme = {
                "category": category_edit.currentText().strip(),
                "title_ru": title_edit.text().strip(),
                "description_ru": desc_edit.toPlainText().strip(),
                "prompt_combined_en": prompt_edit.toPlainText().strip()
            }
            
            # Валидация
            if not self.validate_template_data(new_theme["title_ru"], new_theme["prompt_combined_en"]):
                return
                
            # Обновляем или добавляем шаблон
            if edit_mode and theme:
                theme.update(new_theme)
            else:
                self.themes.append(new_theme)
                
            # Сохраняем и обновляем интерфейс
            if self.save_themes():
                self.refresh_template_list()

    def show_temp(self, item):
        """Показывает выбранный шаблон в интерфейсе.
        
        Args:
            item: QListWidgetItem, содержащий данные шаблона
        """
        if not item:
            return
            
        theme = item.data(Qt.ItemDataRole.UserRole)
        self.temp_category.setText(theme.get("category", "Без категории"))
        self.temp_title.setText(theme["title_ru"])
        self.temp_desc.setText(theme["description_ru"])
        self.temp_preview.setText(theme["prompt_combined_en"])
        
        # Активируем кнопки
        if hasattr(self, 'btn_edit'):
            self.btn_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)
            self.btn_copy.setEnabled(True)
        else:
            # Отключаем кнопки, если шаблон не выбран
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_copy.setEnabled(False)

    def builder_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setSpacing(15)
        
        # Проверка загруженных категорий
        if not self.kw_data:
            error_label = QLabel("Категории ключевых слов не загружены")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            lay.addWidget(error_label)
            logger.warning("Категории ключевых слов не загружены при инициализации UI")
            return w

        # Категории
        cat_box = QGroupBox("Категории")
        cat_lay = QVBoxLayout(cat_box)
        self.cat_list = QListWidget()
        for cat in self.kw_data:
            name = cat.split(".", 1)[1] if "." in cat else cat
            self.cat_list.addItem(name)
        self.cat_list.currentRowChanged.connect(self.load_cat)
        cat_lay.addWidget(self.cat_list)

        # Ключевые слова
        kw_box = QGroupBox("Ключевые слова")
        kw_lay = QVBoxLayout(kw_box)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск...")
        self.search.textChanged.connect(self.filter_kw)
        kw_lay.addWidget(self.search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.kw_widget = QWidget()
        self.kw_layout = QVBoxLayout(self.kw_widget)
        scroll.setWidget(self.kw_widget)
        kw_lay.addWidget(scroll)

        # Превью
        prev_box = QGroupBox("Результат")
        prev_lay = QVBoxLayout(prev_box)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        prev_lay.addWidget(self.preview)

        btn_copy = GradientButton("Копировать", "#4caf50")
        btn_copy.clicked.connect(self.copy_prompt)
        btn_clear = GradientButton("Очистить", "#f44336")
        btn_clear.clicked.connect(self.clear_all)
        btns = QHBoxLayout()
        btns.addWidget(btn_copy)
        btns.addStretch()
        btns.addWidget(btn_clear)
        prev_lay.addLayout(btns)

        lay.addWidget(cat_box, 1)
        lay.addWidget(kw_box, 2)
        lay.addWidget(prev_box, 3)

        if self.cat_list.count():
            self.cat_list.setCurrentRow(0)
        return w

    def load_cat(self, row):
        if row < 0: 
            return
            
        logger.debug(f"Loading category at row {row}")
        cat_key = list(self.kw_data.keys())[row]
        logger.debug(f"Category key: {cat_key}")
        
        # Get the list of keyword dictionaries for this category
        keyword_items = self.kw_data[cat_key]
        logger.debug(f"Number of items in category: {len(keyword_items) if keyword_items else 0}")
        
        # Clear existing items
        for i in reversed(range(self.kw_layout.count())):
            w = self.kw_layout.itemAt(i).widget()
            if w: 
                w.setParent(None)
        
        # If there are no items, show a message
        if not keyword_items:
            label = QLabel("No keywords found in this category.")
            label.setStyleSheet("color: #888888; font-style: italic;")
            self.kw_layout.addWidget(label)
            return
            
        # Add new items
        for item in keyword_items:
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid item in category {cat_key}: {item}")
                continue
                
            word = item.get("word", "")
            if not word:
                logger.warning(f"Skipping item with missing 'word' key: {item}")
                continue
                
            logger.debug(f"Adding keyword: {word}")
            
            cb = TooltipCheckBox(
                word,
                item.get("translate", ""),
                item.get("effect", ""),
                "negative" if "негатив" in cat_key.lower() else "positive"
            )
            
            cb.stateChanged.connect(self.on_checkbox_changed)
            
            # Check if this word is in the selected_words dictionary
            if word in self.selected_words.get(cat_key, []):
                cb.setChecked(True)
                
            self.kw_layout.addWidget(cb)

        self.update_preview()

    def on_checkbox_changed(self, state):
        cb = self.sender()
        if not cb:
            return
            
        # Get the current category
        current_row = self.cat_list.currentRow()
        if current_row < 0:
            return
            
        cat_key = list(self.kw_data.keys())[current_row]
        
        # Initialize the category in selected_words if it doesn't exist
        if cat_key not in self.selected_words:
            self.selected_words[cat_key] = []
            
        # Get the word from the checkbox text
        word = cb.text()
        
        # Update the selected words list for this category
        if state == Qt.CheckState.Checked.value:
            if word not in self.selected_words[cat_key]:
                self.selected_words[cat_key].append(word)
        else:
            if word in self.selected_words[cat_key]:
                self.selected_words[cat_key].remove(word)
        
        logger.debug(f"Updated selected words for {cat_key}: {self.selected_words[cat_key]}")
        self.update_preview()

    def filter_kw(self, text):
        text = text.lower()
        for i in range(self.kw_layout.count()):
            cb = self.kw_layout.itemAt(i).widget()
            if isinstance(cb, QCheckBox):
                visible = text in cb.text().lower() or text in cb.trans.lower()
                cb.setVisible(visible or not text)

    def update_preview(self):
        pos = [w for w, c in self.selected_words.items() if c and self.is_positive(w)]
        neg = [w for w, c in self.selected_words.items() if c and not self.is_positive(w)]
        lines = []
        if pos: lines += ["Позитивные:", ", ".join(pos), ""]
        if neg: lines += ["Негативные:", ", ".join(neg)]
        self.preview.setPlainText("\n".join(lines).strip() or "Выберите ключевые слова")

    def is_positive(self, word):
        """Проверяет, является ли ключевое слово позитивным.
        
        Args:
            word: Ключевое слово для проверки.
            
        Returns:
            bool: True, если слово позитивное, иначе False.
        """
        category = self.word_to_category.get(word)
        if category is not None:
            return "негатив" not in category.lower()
        return True  # По умолчанию считаем слово позитивным

    def copy_prompt(self):
        txt = self.preview.toPlainText()
        if "Выберите" not in txt:
            pyperclip.copy(txt)
            self.status_label.setText("Промпт скопирован в буфер обмена")
            self.status_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00aa55, stop:1 #008844);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 0 0 16px 16px;
                    font-weight: 600;
                }
            """)

    def clear_all(self):
        self.selected_words.clear()
        for i in range(self.kw_layout.count()):
            cb = self.kw_layout.itemAt(i).widget()
            if isinstance(cb, QCheckBox):
                cb.setChecked(False)
        self.update_preview()


def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик исключений."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("Необработанное исключение", 
                   exc_info=(exc_type, exc_value, exc_traceback))
    
    # Показываем пользователю понятное сообщение об ошибке
    error_msg = (
        f"Произошла непредвиденная ошибка.\n\n"
        f"Тип: {exc_type.__name__}\n"
        f"Сообщение: {str(exc_value)}"
    )
    
    # Создаем простое окно для отображения ошибки
    app = QApplication.instance()
    if app is not None:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Критическая ошибка")
        error_box.setText("В приложении произошла ошибка")
        error_box.setInformativeText(
            "Приносим извинения за неудобства. "
            "Подробности ошибки записаны в лог-файл."
        )
        error_box.setDetailedText(error_msg)
        error_box.exec()

def main():
    """Основная функция запуска приложения."""
    try:
        logger.info("=" * 80)
        logger.info(f"Запуск PromptGenie v3.0")
        logger.info(f"Платформа: {sys.platform}")
        logger.info(f"Python: {sys.version}")
        
        # Enable high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        app = QApplication(sys.argv)
        
        # Set application information
        app.setApplicationName("PromptGenie")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("PromptGenie")
        
        # Create and show the main window
        logger.info("Application initialized")
        win = PromptGenie()
        
        # Ensure the window is properly sized and centered
        screen = QApplication.primaryScreen().availableGeometry()
        window_size = win.size()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        win.move(x, y)
        
        # Show and activate the window
        win.show()
        win.activateWindow()
        win.raise_()
        
        # Process events to ensure the window is fully initialized
        app.processEvents()
        
        logger.info("Application started successfully")
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        logger.critical("Critical error while starting the application", exc_info=True)
        
        # Create a simple error dialog
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Startup Error")
        error_box.setText("Failed to start the application")
        error_box.setInformativeText(
            f"Error: {str(e)}\n\n"
            "Please check the logs for more information."
        )
        error_box.exec()
        
        return 1

if __name__ == "__main__":
    # Запуск приложения
    sys.exit(main())