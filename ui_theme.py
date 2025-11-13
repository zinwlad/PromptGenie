from PyQt6.QtCore import QMetaObject, QCoreApplication
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QTextEdit, QPushButton, QLabel,
    QSplitter, QMenuBar, QMenu, QStatusBar, QFileDialog,
    QMessageBox, QInputDialog, QLineEdit, QComboBox
)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1000, 700)
        
        # Central Widget
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        
        # Main Layout
        self.mainLayout = QHBoxLayout(self.centralwidget)
        self.mainLayout.setObjectName(u"mainLayout")
        
        # Left Panel
        self.leftPanel = QWidget(self.centralwidget)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftPanel.setMaximumWidth(300)
        
        # Left Panel Layout
        self.leftLayout = QVBoxLayout(self.leftPanel)
        self.leftLayout.setObjectName(u"leftLayout")
        
        # Theme List
        self.themeListLabel = QLabel("Темы:", self.leftPanel)
        self.themeList = QListWidget(self.leftPanel)
        self.leftLayout.addWidget(self.themeListLabel)
        self.leftLayout.addWidget(self.themeList)
        
        # Right Panel
        self.rightPanel = QWidget(self.centralwidget)
        self.rightPanel.setObjectName(u"rightPanel")
        
        # Right Panel Layout
        self.rightLayout = QVBoxLayout(self.rightPanel)
        self.rightLayout.setObjectName(u"rightLayout")
        
        # Prompt Edit
        self.promptLabel = QLabel("Промпт:", self.rightPanel)
        self.promptEdit = QTextEdit(self.rightPanel)
        self.rightLayout.addWidget(self.promptLabel)
        self.rightLayout.addWidget(self.promptEdit)
        
        # Add panels to main layout
        self.mainLayout.addWidget(self.leftPanel)
        self.mainLayout.addWidget(self.rightPanel)
        
        # Set central widget
        MainWindow.setCentralWidget(self.centralwidget)
        
        # Menu Bar
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(0, 0, 800, 22)
        
        # File Menu
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        
        # Edit Menu
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        
        # Help Menu
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        
        # Add menus to menubar
        MainWindow.setMenuBar(self.menubar)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        
        # Status Bar
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        # Set window title and menu text
        self.retranslateUi(MainWindow)
        
        # Connect signals and slots
        QMetaObject.connectSlotsByName(MainWindow)
    
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"PromptGenie", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"Файл", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Правка", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Справка", None))
