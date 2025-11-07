# PromptGenie 3.0 — Профессиональный конструктор промптов
import sys
import json
import os
import pyperclip
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QIcon

# Local UI components
from ui_components import (
    TooltipCheckBox, 
    StyledTabWidget,
    GradientButton,
    SearchBox,
    GlassPanel,
    StatusLabel,
    TemplateDescriptionEdit,
    TemplatePreviewEdit
)

def setup_logging():
    """Настройка системы логирования."""
    # Создаем директорию для логов, если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Основной логгер
    logger = logging.getLogger('PromptGenie')
    logger.setLevel(logging.DEBUG)
    
    # Обработчик для записи в файл
    log_file = log_dir / f"prompt_genie_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Удаляем существующие обработчики, если они есть
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Логирование необработанных исключений
    def handle_exception(exc_type, exc_value, exc_traceback):
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
        
        # Создаем окно для отображения ошибки, если приложение запущено
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
    
    sys.excepthook = handle_exception
    
    return logger

# Инициализация логгера
logger = setup_logging()

def log_method_call(func):
    """Декоратор для логирования вызовов методов.
    
    Args:
        func: Декорируемая функция или метод.
        
    Returns:
        Обертка вокруг функции, добавляющая логирование вызовов.
    """
    def wrapper(*args, **kwargs):
        if logger.level > logging.DEBUG:
            return func(*args, **kwargs)
            
        # Логируем вызов метода
        logger.debug(
            "Вызов %s с аргументами: %s, %s",
            func.__name__,
            args[1:],  # Пропускаем self
            kwargs
        )
        
        try:
            # Вызываем оригинальную функцию
            result = func(*args, **kwargs)
            
            # Логируем успешное завершение
            logger.debug("Завершение %s", func.__name__)
            return result
            
        except Exception as e:
            # Логируем исключение, если оно возникло
            logger.exception("Ошибка в методе %s: %s", func.__name__, str(e))
            raise
            
    # Копируем имя и документацию оригинальной функции
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    
    return wrapper


class PromptGenie(QMainWindow):
    def get_data_dir(self):
        """Возвращает путь к директории с данными приложения."""
        if getattr(sys, 'frozen', False):
            # Если приложение упаковано (например, в exe)
            return Path(sys.executable).parent
        else:
            # При запуске из исходников
            return Path(__file__).parent

    def __init__(self):
        super(QMainWindow, self).__init__()
        logger.info("Инициализация приложения PromptGenie")
        
        try:
            # Инициализация переменных
            self.themes = []
            self.kw_data = {}
            self.selected_words = {}
            self.data_dir = self.get_data_dir()
            
            # Сначала загружаем данные
            logger.debug("Загрузка данных...")
            self.load_data()
            
            # Затем инициализируем UI
            self.setWindowTitle("PromptGenie 3.0")
            self.setMinimumSize(1280, 720)
            self.setStyleSheet("background:#1e1e1e; color:#e0e0e0; font-family:Segoe UI;")
            self._init_ui_components()
            
            logger.info("Приложение успешно инициализировано")
            
        except Exception as e:
            logger.critical("Ошибка при инициализации приложения", exc_info=True)
            raise
    
    def _init_ui_components(self):
        """Инициализация компонентов пользовательского интерфейса."""
        logger.debug("Инициализация компонентов UI")
        self.init_ui()

    def validate_json_schema(self, data: Dict, schema: Dict, file_path: str) -> bool:
        """Валидация JSON по схеме."""
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            error_msg = f"Ошибка валидации {file_path}: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Ошибка валидации", 
                              f"Ошибка в файле {file_path}:\n{str(e)}\n\n"
                              "Проверьте структуру файла.")
            return False
        except ImportError:
            logger.warning("Модуль jsonschema не установлен, пропуск валидации схемы")
            return True

    def safe_json_load(self, file_path: str, default: Any = None, schema: Optional[Dict] = None) -> Any:
        """Безопасная загрузка JSON с обработкой ошибок.
        
        Args:
            file_path: Путь к файлу JSON (может быть строкой или объектом Path).
            default: Значение по умолчанию, возвращаемое при ошибке загрузки.
            schema: Схема для валидации JSON (опционально).
            
        Returns:
            Загруженные данные или значение по умолчанию в случае ошибки.
        """
        try:
            # Преобразуем в Path, если это строка
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            file_path = file_path.resolve()  # Получаем абсолютный путь
            
            # Проверяем существование файла
            if not file_path.exists():
                error_msg = f"Файл не найден: {file_path}"
                logger.warning(error_msg)
                if default is not None:
                    return default
                raise FileNotFoundError(error_msg)

            # Читаем и парсим JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Валидируем по схеме, если она предоставлена
                if schema and not self.validate_json_schema(data, schema, str(file_path)):
                    if default is not None:
                        return default
                    return {}
                    
                return data
                
            except json.JSONDecodeError as e:
                error_msg = f"Ошибка разбора JSON в файле {file_path}: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(
                    self, 
                    "Ошибка формата", 
                    f"Ошибка в файле {file_path}:\n{str(e)}\n\n"
                    "Проверьте правильность формата JSON."
                )
                return default if default is not None else {}

        except Exception as e:
            error_msg = f"Ошибка при загрузке файла {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить файл {file_path}:\n{str(e)}"
            )
            return default if default is not None else {}

    def create_backup(self, file_path: str) -> None:
        """Создание резервной копии файла.
        
        Args:
            file_path: Путь к файлу, для которого создается резервная копия.
        """
        try:
            from datetime import datetime
            file_path = Path(file_path)
            if not file_path.exists():
                logger.warning(f"Файл для резервного копирования не найден: {file_path}")
                return
                
            # Создаем имя резервной копии с временной меткой
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}.bak"
            
            # Копируем файл
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Создана резервная копия: {backup_path}")
            
        except Exception as e:
            error_msg = f"Не удалось создать резервную копию {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def load_data(self) -> None:
        """Загрузка данных из JSON файлов."""
        logger.info("Начало загрузки данных")
        
        # Словарь для быстрого поиска категории по слову
        self.word_to_category = {}
        
        # Схема для валидации keyword_library.json
        keyword_schema = {
            "type": "object",
            "required": ["keywords"],
            "properties": {
                "keywords": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["word", "effect"],
                            "properties": {
                                "word": {"type": "string"},
                                "trans": {"type": ["string", "null"]},
                                "translate": {"type": ["string", "null"]},
                                "effect": {"type": "string"},
                                "type": {"type": "string", "enum": ["positive", "negative"]},
                                "when": {"type": ["string", "null"]}
                            }
                        }
                    }
                }
            }
        }
        
        try:
            # Формируем пути к файлам
            themes_path = self.data_dir / "theme_prompts.json"
            keywords_path = self.data_dir / "keyword_library.json"
            
            logger.debug(f"Загрузка тем из {themes_path}")
            themes_data = self.safe_json_load(str(themes_path), {"themes": []})
            self.themes = themes_data.get("themes", [])
            logger.info(f"Загружено {len(self.themes)} тем")

            # Загрузка ключевых слов
            logger.debug(f"Загрузка ключевых слов из {keywords_path}")
            kw_data = self.safe_json_load(keywords_path, {"keywords": {}}, keyword_schema)
            self.kw_data = kw_data.get("keywords", {})
            
            # Создаем словарь для быстрого поиска категории по слову
            for category, words in self.kw_data.items():
                for word_info in words:
                    word = word_info.get("word")
                    if word:
                        self.word_to_category[word] = category
            
            logger.info(f"Загружено {sum(len(v) for v in self.kw_data.values())} ключевых слов в {len(self.kw_data)} категориях")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {str(e)}", exc_info=True)
            raise
        logger.info(f"Загружено категорий: {len(self.kw_data)}")
        
        # Логируем статистику по загруженным данным
        total_keywords = sum(len(keywords) for keywords in self.kw_data.values())
        logger.info(f"Загружено {total_keywords} ключевых слов в {len(self.kw_data)} категориях")

        if not self.themes:
            logger.warning("Список тем пуст или не загружен")
        if not self.kw_data:
            logger.warning("Библиотека ключевых слов пуста или не загружена")
            
        logger.debug("Загрузка данных завершена")

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
        if row < 0: return
        cat_key = list(self.kw_data.keys())[row]
        items = self.kw_data[cat_key]

        for i in reversed(range(self.kw_layout.count())):
            w = self.kw_layout.itemAt(i).widget()
            if w: w.setParent(None)

        for item in items:
            cb = TooltipCheckBox(
                item["word"],
                item.get("translate", ""),
                item.get("effect", ""),
                "negative" if "негатив" in cat_key.lower() else "positive"
            )
            cb.stateChanged.connect(self.on_checkbox_changed)
            if item["word"] in self.selected_words:
                cb.setChecked(self.selected_words[item["word"]])
            self.kw_layout.addWidget(cb)

        self.update_preview()

    def on_checkbox_changed(self, state):
        cb = self.sender()
        if cb:
            self.selected_words[cb.text()] = (state == Qt.CheckState.Checked.value)
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
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Инициализация приложения
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for consistent look
        
        # Set application information
        app.setApplicationName("PromptGenie")
        app.setApplicationVersion("3.0")
        app.setOrganizationName("PromptGenie")
        
        # Create and show the main window
        logger.info("Создание главного окна")
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
        
        logger.info("Приложение успешно запущено")
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        logger.critical("Критическая ошибка при запуске приложения", exc_info=True)
        
        # Создаем простое окно для отображения ошибки
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Ошибка запуска")
        error_box.setText("Не удалось запустить приложение")
        error_box.setInformativeText(
            f"Ошибка: {str(e)}\n\n"
            "Проверьте логи для получения дополнительной информации."
        )
        error_box.exec()
        
        return 1

if __name__ == "__main__":
    # Запуск приложения
    sys.exit(main())