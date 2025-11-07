# PromptGenie 3.0 — Профессиональный конструктор промптов
import sys
import json
import pyperclip
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt


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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PromptGenie 3.0")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background:#1e1e1e; color:#e0e0e0; font-family:Segoe UI;")

        self.themes = []
        self.kw_data = {}
        self.selected_words = {}

        self.load_data()
        self.init_ui()

    def load_data(self):
        try:
            with open("theme_prompts.json", "r", encoding="utf-8") as f:
                self.themes = json.load(f).get("themes", [])
            with open("keyword_library.json", "r", encoding="utf-8") as f:
                self.kw_data = json.load(f)["keywords"]
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Ошибка", f"Файл не найден: {e.filename}")
            sys.exit()
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Ошибка", "Неверный формат JSON")
            sys.exit()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding:12px 30px; background:#2d2d2d; border-radius:6px; }"
                           "QTabBar::tab:selected { background:#007acc; }")
        layout.addWidget(tabs)

        tabs.addTab(self.templates_tab(), "Шаблоны")
        tabs.addTab(self.builder_tab(), "Конструктор")

        self.statusBar().showMessage("Готов к работе")

    def templates_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setSpacing(15)

        # Левая панель
        left = QGroupBox("Список шаблонов")
        left.setStyleSheet("QGroupBox { font-weight:bold; border:2px solid #007acc; border-radius:8px; padding:10px; }")
        l = QVBoxLayout(left)

        self.search_temp = QLineEdit()
        self.search_temp.setPlaceholderText("Поиск по названию или описанию")
        self.search_temp.textChanged.connect(self.filter_templates)
        l.addWidget(self.search_temp)

        btn_add = QPushButton("Добавить шаблон")
        btn_add.clicked.connect(lambda: self.open_template_dialog())
        l.addWidget(btn_add)

        self.tlist = QListWidget()
        self.tlist.itemClicked.connect(self.show_temp)
        self.refresh_template_list()
        l.addWidget(self.tlist)

        # Правая панель
        right = QGroupBox("Просмотр шаблона")
        right.setStyleSheet("QGroupBox { font-weight:bold; border:2px solid #00aa00; border-radius:8px; padding:10px; }")
        r = QVBoxLayout(right)

        self.temp_title = QLabel("Выберите шаблон")
        self.temp_title.setStyleSheet("font-size:13pt; font-weight:bold;")
        r.addWidget(self.temp_title)

        self.temp_desc = QTextEdit()
        self.temp_desc.setReadOnly(True)
        self.temp_desc.setMaximumHeight(80)
        r.addWidget(self.temp_desc)

        self.temp_preview = QTextEdit()
        self.temp_preview.setReadOnly(True)
        r.addWidget(self.temp_preview)

        btns = QHBoxLayout()
        btn_copy = QPushButton("Копировать")
        btn_copy.clicked.connect(self.copy_template_prompt)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.edit_current_template)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.delete_current_template)

        for btn in (btn_copy, btn_edit, btn_del):
            btn.setFixedHeight(36)
            btns.addWidget(btn)
        btns.addStretch()
        r.addLayout(btns)

        lay.addWidget(left, 1)
        lay.addWidget(right, 2)
        return w

    def refresh_template_list(self):
        self.tlist.clear()
        for t in self.themes:
            item = QListWidgetItem(t.get("title_ru", "Без названия"))
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.tlist.addItem(item)

    def filter_templates(self, text):
        text = text.lower()
        self.tlist.clear()
        for t in self.themes:
            if text in t.get("title_ru", "").lower() or text in t.get("description_ru", "").lower():
                item = QListWidgetItem(t.get("title_ru", "Без названия"))
                item.setData(Qt.ItemDataRole.UserRole, t)
                self.tlist.addItem(item)

    def open_template_dialog(self, edit_mode=False, theme=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование шаблона" if edit_mode else "Новый шаблон")
        dialog.resize(560, 460)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Название (RU):"))
        title_edit = QLineEdit(theme.get("title_ru", "") if edit_mode else "")
        layout.addWidget(title_edit)

        layout.addWidget(QLabel("Описание (RU):"))
        desc_edit = QTextEdit()
        desc_edit.setPlainText(theme.get("description_ru", "") if edit_mode else "")
        desc_edit.setMaximumHeight(90)
        layout.addWidget(desc_edit)

        layout.addWidget(QLabel("Промпт (EN):"))
        prompt_edit = QTextEdit()
        prompt_edit.setPlainText(theme.get("prompt_combined_en", "") if edit_mode else "")
        layout.addWidget(prompt_edit)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_edit.text().strip()
            desc = desc_edit.toPlainText().strip()
            prompt = prompt_edit.toPlainText().strip()

            if not title or not prompt:
                QMessageBox.warning(self, "Ошибка", "Заполните название и промпт")
                return

            data = {
                "title_ru": title,
                "description_ru": desc or "Без описания",
                "prompt_combined_en": prompt
            }

            if edit_mode:
                theme.update(data)
            else:
                self.themes.append(data)

            self.save_themes()
            self.refresh_template_list()
            self.statusBar().showMessage("Шаблон сохранён")

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
        theme = item.data(Qt.ItemDataRole.UserRole)
        self.temp_title.setText(theme.get("title_ru", ""))
        self.temp_desc.setPlainText(theme.get("description_ru", ""))
        self.temp_preview.setPlainText(theme.get("prompt_combined_en", ""))
        pyperclip.copy(theme.get("prompt_combined_en", ""))

    def copy_template_prompt(self):
        txt = self.temp_preview.toPlainText()
        if txt.strip():
            pyperclip.copy(txt)
            self.statusBar().showMessage("Промпт скопирован")

    def save_themes(self):
        try:
            with open("theme_prompts.json", "w", encoding="utf-8") as f:
                json.dump({"themes": self.themes}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def builder_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setSpacing(15)

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
        for cat, items in self.kw_data.items():
            if any(i["word"] == word for i in items):
                return "негатив" not in cat.lower()
        return True

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = PromptGenie()
    win.show()
    sys.exit(app.exec())