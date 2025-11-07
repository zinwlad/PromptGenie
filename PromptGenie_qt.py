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


class TooltipCheckBox(QCheckBox):
    def __init__(self, word, trans, effect, type_="positive"):
        super().__init__(word)
        self.trans = trans
        self.effect = effect
        self.type = type_
        self.setStyleSheet("padding: 6px; font-size: 11pt;")
        if type_ == "negative":
            self.setStyleSheet(self.styleSheet() + "color: #d9534f; font-weight: bold;")

    def enterEvent(self, event):
        tip = f"<b>{self.text()}</b><br><i>{self.trans}</i><hr><small>{self.effect}</small>"
        QToolTip.showText(event.globalPosition().toPoint(), tip)


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

            # Создаем вкладки
            tabs = QTabWidget()
            tabs.setStyleSheet("""
                QTabBar::tab {
                    padding: 12px 30px;
                    background: #2d2d2d;
                    border: 1px solid #444;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #007acc;
                    color: white;
                }
                QTabWidget::pane {
                    border: 1px solid #444;
                    border-top: none;
                    top: -1px;
                    background: #252526;
                }
            """)
            
            # Добавляем вкладки
            templates_tab = self.templates_tab()
            builder_tab = self.builder_tab()
            
            tabs.addTab(templates_tab, "Шаблоны")
            tabs.addTab(builder_tab, "Конструктор")
            
            layout.addWidget(tabs)
            
            # Статус бар
            self.statusBar().showMessage("Готов к работе")
            
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
            
            # Инициализируем атрибуты, которые будут использоваться в других методах
            self.temp_title = None
            self.temp_desc = None
            self.temp_preview = None
            
            # Основной виджет вкладки
            w = QWidget()
            lay = QHBoxLayout(w)
            lay.setSpacing(15)
            lay.setContentsMargins(5, 5, 5, 5)

            # Левая панель - список шаблонов
            left = QGroupBox("Список шаблонов")
            left.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 10px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            l = QVBoxLayout(left)
            l.setSpacing(10)
            
            # Поле поиска
            self.search_temp = QLineEdit()
            self.search_temp.setPlaceholderText("Поиск по названию или описанию")
            self.search_temp.textChanged.connect(self.filter_templates)
            l.addWidget(self.search_temp)
            
            # Кнопка добавления шаблона
            btn_add = QPushButton("Добавить шаблон")
            btn_add.clicked.connect(lambda: self.open_template_dialog())
            l.addWidget(btn_add)
            
            # Список шаблонов
            self.tlist = QListWidget()
            self.tlist.itemClicked.connect(self.show_temp)
            l.addWidget(self.tlist)
            
            # Проверка загруженных данных
            if not self.themes:
                self.tlist.addItem("Шаблоны не загружены")
                logger.warning("Список шаблонов пуст при инициализации UI")
            else:
                # Обновляем список шаблонов, если данные загружены
                self.refresh_template_list()
            
            # Правая панель - просмотр шаблона
            right = QGroupBox("Просмотр шаблона")
            right.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 10px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            r = QVBoxLayout(right)
            
            # Заголовок шаблона
            self.temp_title = QLabel("Выберите шаблон")
            self.temp_title.setStyleSheet("font-size:13pt; font-weight:bold;")
            r.addWidget(self.temp_title)
            
            # Описание шаблона
            self.temp_desc = QTextEdit()
            self.temp_desc.setReadOnly(True)
            self.temp_desc.setMaximumHeight(80)
            r.addWidget(self.temp_desc)
            
            # Превью шаблона
            self.temp_preview = QTextEdit()
            self.temp_preview.setReadOnly(True)
            self.temp_preview.setStyleSheet("""
                QTextEdit {
                    background-color: #252526;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
            r.addWidget(self.temp_preview)
            
            # Кнопки управления
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            self.btn_edit = QPushButton("Редактировать")
            self.btn_edit.clicked.connect(self.edit_current_template)
            self.btn_edit.setEnabled(False)
            
            self.btn_delete = QPushButton("Удалить")
            self.btn_delete.clicked.connect(self.delete_current_template)
            self.btn_delete.setEnabled(False)
            
            self.btn_copy = QPushButton("Копировать")
            self.btn_copy.clicked.connect(self.copy_template_prompt)
            self.btn_copy.setEnabled(False)
            
            btn_layout.addWidget(self.btn_edit)
            btn_layout.addWidget(self.btn_delete)
            btn_layout.addWidget(self.btn_copy)
            
            r.addWidget(btn_frame)
            
            # Добавляем панели в основной макет
            lay.addWidget(left, 1)
            lay.addWidget(right, 2)
            
            logger.debug("Вкладка шаблонов успешно инициализирована")
            return w
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации вкладки шаблонов: {str(e)}", exc_info=True)
            raise
        return w

    def refresh_template_list(self):
        self.tlist.clear()
        for t in self.themes:
            item = QListWidgetItem(t.get("title_ru", "Без названия"))
            item.setData(Qt.ItemDataRole.UserRole, t)  # Store the theme data with the item
            self.tlist.addItem(item)

    def filter_templates(self, text):
        text = text.lower()
        self.tlist.clear()
        for t in self.themes:
            if text in t.get("title_ru", "").lower() or text in t.get("description_ru", "").lower():
                item = QListWidgetItem(t.get("title_ru", "Без названия"))
                item.setData(Qt.ItemDataRole.UserRole, t)
                self.tlist.addItem(item)

    def validate_template_data(self, title: str, prompt: str) -> tuple[bool, str]:
        """Валидация данных шаблона."""
        if not title.strip():
            return False, "Название шаблона не может быть пустым"
        if not prompt.strip():
            return False, "Промпт не может быть пустым"
        if len(title) > 100:
            return False, "Слишком длинное название (макс. 100 символов)"
        if len(prompt) > 10000:
            return False, "Слишком длинный промпт (макс. 10000 символов)"
        return True, ""

    def save_themes(self) -> bool:
        """Сохранение тем в файл с обработкой ошибок."""
        logger.info("Сохранение тем в файл")
        
        try:
            themes_count = len(self.themes)
            logger.debug(f"Сохранение {themes_count} тем")
            
            # Определяем пути к файлам
            themes_path = self.data_dir / "theme_prompts.json"
            temp_path = self.data_dir / "theme_prompts.json.tmp"
            
            # Создаем резервную копию перед сохранением
            if themes_path.exists():
                logger.debug("Создание резервной копии файла тем")
                self.create_backup(str(themes_path))
            
            # Сохраняем во временный файл, затем переименовываем
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump({"themes": self.themes}, f, ensure_ascii=False, indent=2, sort_keys=True)
                
                # Атомарная операция замены файла
                if sys.platform == 'win32':
                    # На Windows сначала удаляем старый файл, если он существует
                    if themes_path.exists():
                        themes_path.unlink()
                    temp_path.rename(themes_path)
                else:
                    # На Unix-подобных системах replace атомарный
                    temp_path.replace(themes_path)
                
                logger.info(f"Успешно сохранено {themes_count} тем в {themes_path}")
                return True
                
            except Exception as e:
                # Удаляем временный файл в случае ошибки
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception as cleanup_error:
                        logger.error(f"Ошибка при удалении временного файла: {cleanup_error}")
                raise
            
        except Exception as e:
            error_msg = f"Ошибка при сохранении тем: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить темы.\n\n"
                f"Ошибка: {str(e)}\n\n"
                "Проверьте права доступа к файлу и наличие свободного места на диске."
            )
            return False

    def open_template_dialog(self, edit_mode: bool = False, theme: Optional[Dict] = None) -> None:
        """Открытие диалога редактирования шаблона."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование шаблона" if edit_mode else "Новый шаблон")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        # Название
        title_label = QLabel("Название (RU): *")
        title_edit = QLineEdit(theme.get("title_ru", "") if edit_mode else "")
        title_edit.setPlaceholderText("Введите название шаблона")
        title_edit.setMaxLength(100)
        
        # Описание
        desc_label = QLabel("Описание (RU):")
        desc_edit = QTextEdit()
        desc_edit.setPlainText(theme.get("description_ru", "") if edit_mode else "")
        desc_edit.setPlaceholderText("Введите описание шаблона")
        desc_edit.setMaximumHeight(90)
        
        # Промпт
        prompt_label = QLabel("Промпт (EN): *")
        prompt_edit = QTextEdit()
        prompt_edit.setPlainText(theme.get("prompt_combined_en", "") if edit_mode else "")
        prompt_edit.setPlaceholderText("Введите текст промпта")
        
        # Счетчики символов
        title_counter = QLabel(f"{len(title_edit.text())}/100")
        prompt_counter = QLabel(f"{len(prompt_edit.toPlainText())}/10000")
        
        # Обновление счетчиков
        def update_title_counter(text):
            title_counter.setText(f"{len(text)}/100")
            
        def update_prompt_counter():
            text = prompt_edit.toPlainText()
            prompt_counter.setText(f"{len(text)}/10000")
        
        title_edit.textChanged.connect(update_title_counter)
        prompt_edit.textChanged.connect(update_prompt_counter)
        
        # Компоновка
        form_layout = QFormLayout()
        form_layout.addRow(title_label, title_edit)
        form_layout.addRow("", title_counter)
        form_layout.addRow(desc_label, desc_edit)
        form_layout.addRow(prompt_label, prompt_edit)
        form_layout.addRow("", prompt_counter)
        
        layout.addLayout(form_layout)

        # Кнопки
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            desc = desc_edit.toPlainText().strip()
            prompt = prompt_edit.toPlainText().strip()

            # Валидация
            is_valid, error_msg = self.validate_template_data(title, prompt)
            if not is_valid:
                QMessageBox.warning(self, "Ошибка валидации", error_msg)
                return self.open_template_dialog(edit_mode, theme)  # Повторно открываем диалог

            # Подготовка данных
            data = {
                "title_ru": title,
                "description_ru": desc or "Без описания",
                "prompt_combined_en": prompt,
                "last_modified": datetime.now().isoformat()
            }

            # Сохранение
            if edit_mode and theme:
                theme.update(data)
                action = "обновлён"
            else:
                data["created_at"] = datetime.now().isoformat()
                self.themes.append(data)
                action = "добавлен"

            if self.save_themes():
                self.refresh_template_list()
                self.statusBar().showMessage(f"Шаблон успешно {action}", 3000)
                logger.info(f"Шаблон '{title}' {action}")

    def edit_current_template(self):
        item = self.tlist.currentItem()
        if not item:
            return
        theme = item.data(Qt.ItemDataRole.UserRole)
        self.open_template_dialog(edit_mode=True, theme=theme)

    def delete_current_template(self):
        item = self.tlist.currentItem()
        if not item:
            return
        theme = item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Удалить", f"Удалить шаблон «{theme.get('title_ru')}»?") == QMessageBox.StandardButton.Yes:
            self.themes.remove(theme)
            self.save_themes()
            self.refresh_template_list()
            self.clear_template_preview()
            self.statusBar().showMessage("Шаблон удалён")

    def clear_template_preview(self):
        self.temp_title.setText("Выберите шаблон")
        self.temp_desc.clear()
        self.temp_preview.clear()

    def show_temp(self, item):
        """Показывает выбранный шаблон в интерфейсе.
        
        Args:
            item: QListWidgetItem, содержащий данные шаблона
        """
        theme = item.data(Qt.ItemDataRole.UserRole)
        if theme:
            self.temp_title.setText(theme.get("title_ru", ""))
            self.temp_desc.setPlainText(theme.get("description_ru", ""))
            self.temp_preview.setPlainText(theme.get("prompt_combined_en", ""))
            
            # Включаем кнопки действий при выборе шаблона
            self.btn_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)
            self.btn_copy.setEnabled(True)
        else:
            # Отключаем кнопки, если шаблон не выбран
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_copy.setEnabled(False)

    def copy_template_prompt(self):
        txt = self.temp_preview.toPlainText()
        if txt.strip():
            pyperclip.copy(txt)
            self.statusBar().showMessage("Промпт скопирован")


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

        btn_copy = QPushButton("Копировать")
        btn_copy.clicked.connect(self.copy_prompt)
        btn_clear = QPushButton("Очистить")
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
            self.statusBar().showMessage("Промпт скопирован")

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