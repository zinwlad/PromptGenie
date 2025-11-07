# ui_components.py — КРАСОТА КАЗАХСТАНА
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIcon, QPainter, QLinearGradient, QColor
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer


class TooltipCheckBox(QCheckBox):
    
    def __init__(self, word, trans, effect, type_="positive"):
        super().__init__(word)
        self.trans = trans or ""
        self.effect = effect or ""
        self.type = type_
        
        # БАЗОВЫЙ СТИЛЬ
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QCheckBox {
                padding: 10px 12px;
                font-size: 12pt;
                font-weight: 500;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d2d2d, stop:1 #353535);
                border: 1.5px solid #444;
                color: #e0e0e0;
                spacing: 12px;
            }
            QCheckBox:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3a3a3a, stop:1 #444444);
                border: 1.5px solid #007acc;
                padding-top: 8px;
                padding-bottom: 12px;
            }
            QCheckBox:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #007acc, stop:1 #005a99);
                color: white;
                font-weight: 600;
            }
        """)
        
        if type_ == "negative":
            self.setStyleSheet(self.styleSheet().replace(
                "color: #e0e0e0", "color: #ff6b6b"
            ).replace(
                "border: 1.5px solid #444", "border: 1.5px solid #ff4444"
            ))

    def enterEvent(self, event):
        word = self.text()
        trans = self.trans
        effect = self.effect

        tip = f"""
        <div style="
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e1e1e, stop:1 #0a0a0a);
                border: 2px solid #007acc;
                border-radius: 16px;
                padding: 16px;
                font-family: 'Segoe UI', sans-serif;
                max-width: 460px;
        ">
            <div style="
                font-size: 15pt;
                font-weight: 700;
                color: #00ddff;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                margin-bottom: 8px;
            ">✦ {word}</div>
            
            <div style="
                font-style: italic;
                color: #64b5f6;
                font-size: 12pt;
                margin: 8px 0;
                opacity: 0.9;
            ">➤ {trans}</div>
            
            <div style="
                background: rgba(0,122,204,0.15);
                padding: 12px;
                border-radius: 10px;
                border-left: 4px solid #007acc;
                color: #bbdefb;
                font-size: 11pt;
                line-height: 1.5;
            ">
                <b>Эффект:</b> {effect}
            </div>
            
            <div style="
                margin-top: 12px;
                font-size: 9pt;
                color: #666;
                text-align: right;
            ">Kazakh AI Design 2025</div>
        </div>
        """
        
        QToolTip.setFont(QFont('Segoe UI', 11))
        QToolTip.showText(
            event.globalPosition().toPoint(),
            tip,
            self,
            msecShowTime=15000
        )


class StyledTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabWidget::pane {
                background: #1e1e1e;
                border: 2px solid #007acc;
                border-radius: 16px;
                margin: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                padding: 16px 40px;
                margin: 0 4px;
                border-radius: 14px 14px 0 0;
                font-weight: 600;
                font-size: 13pt;
                min-width: 160px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a, stop:1 #333333);
                color: #aaaaaa;
                border: 2px solid transparent;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007acc, stop:1 #005a99);
                color: white;
                border-bottom: none;
                box-shadow: 0 4px 15px rgba(0,122,204,0.4);
            }
            QTabBar::tab:hover:!selected {
                background: #3a3a3a;
                color: #00ddff;
            }
        """)


class GradientButton(QPushButton):
    """КНОПКИ С ГРАДИЕНТОМ И АНИМАЦИЕЙ"""
    def __init__(self, text, color="#007acc"):
        super().__init__(text)
        self.color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self.darken(color)});
                border: 2px solid {color};
                border-radius: 22px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                padding: 0 30px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.lighten(color)}, stop:1 {color});
                padding-top: -3px;
                padding-bottom: 3px;
            }}
            QPushButton:pressed {{
                padding-top: 2px;
                padding-bottom: -2px;
            }}
        """)
        
        # Анимация при наведении
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def darken(self, hex_color):
        c = QColor(hex_color)
        c.setHsv(c.hue(), c.saturation(), max(0, c.value() - 40))
        return c.name()

    def lighten(self, hex_color):
        c = QColor(hex_color)
        c.setHsv(c.hue(), c.saturation(), min(255, c.value() + 50))
        return c.name()


class GlassPanel(QFrame):
    """СТЕКЛЯННАЯ ПАНЕЛЬ — КАК В MACOS"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: rgba(30, 30, 30, 0.7);
                border: 1px solid rgba(0, 122, 204, 0.3);
                border-radius: 18px;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
            }
        """)


class SearchBox(QLineEdit):
    """ПОИСК С АНИМАЦИЕЙ"""
    def __init__(self, placeholder="Поиск..."):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(48)
        self.setStyleSheet("""
            QLineEdit {
                padding: 0 50px;
                font-size: 13pt;
                border: 2px solid #444;
                border-radius: 24px;
                background: #2a2a2a;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
                background: #333;
                box-shadow: 0 0 20px rgba(0,122,204,0.3);
            }
        """)
        
        # Иконка поиска
        self.setTextMargins(40, 0, 0, 0)
        icon = QLabel(self)
        icon.setPixmap(QIcon.fromTheme("edit-find").pixmap(20, 20))
        icon.move(15, 14)


class StatusLabel(QLabel):
    """СТАТУС-БАР С АНИМАЦИЕЙ"""
    def __init__(self):
        super().__init__("Готов к работе")
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007acc, stop:1 #005a99);
                color: white;
                padding: 12px 20px;
                border-radius: 0 0 16px 16px;
                font-weight: 600;
            }
        """)


class TemplateDescriptionEdit(QTextEdit):
    """Стилизованное поле для описания шаблона"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background: #252526;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                min-height: 80px;
                max-height: 120px;
                color: #e0e0e0;
                selection-background-color: #007acc;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        self.setPlaceholderText("Введите описание шаблона...")


class TemplatePreviewEdit(QTextEdit):
    """Стилизованное поле для предпросмотра шаблона"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background: #252526;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                color: #e0e0e0;
                selection-background-color: #007acc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        self.setReadOnly(True)
        self.setPlaceholderText("Предпросмотр шаблона...")
        
        # Пульсация
        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse)
        self.timer.start(3000)
        self.opacity = 1.0

    def pulse(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(1000)
        anim.setStartValue(1.0)
        anim.setEndValue(0.7)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        QTimer.singleShot(1000, lambda: self.setWindowOpacity(1.0))