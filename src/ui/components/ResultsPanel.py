import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStyle,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QTableView
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from .ResultsTable import ResultsTable
from .CleanTheme import CleanTheme

class ResultsPanel(QFrame):
    def __init__(self, parent = None, model = {}):
        super().__init__(parent)
        
        self.model = model
        
        self.colors = {
            "bg_main": "#f8f9fa",
            "bg_card": "#ffffff",
            "bg_sidebar": "#f8f9fa",
            "bg_topbar": "#ffffff",
            "border_light": "#e9ecef",
            "shadow": QColor(0, 0, 0, 25),
            "text_primary": "#212529",
            "text_secondary": "#6c757d",
            "text_title": "#343a40",
            "button_dark_bg": "#343a40",
            "button_dark_hover": "#495057",
            "button_grey_bg": "#e9ecee",
            "checkbox_bg": "#f1f3f5",
        }
        
        self.setObjectName("ResultsPanel")
        self.setStyleSheet(
            f"""
            #rightSidebar {{
                background-color: {self.colors['bg_card']};
                border-bottom: 1px solid {self.colors['border_light']};
            }}
        """
        )    
        
        # save results button
        save_button = QPushButton("Save Results")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['button_dark_hover']};
                color: {self.colors['button_grey_bg']};
                border: none;
                height: 40%;
                max-width: 100%;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['button_grey_bg']};
                color: {self.colors['button_dark_hover']};
            }}
        """
        )
        
        # table
        # self.table = QTableWidget()
        # self.table.setStyleSheet(
        #     f"background-color: {self.colors['bg_main']}"
        # )
        
        # self.model = ResultsTable(self.df)
        table_view = QTableView()
        table_view.setModel(self.model)
        
        # title
        title = QLabel("Results")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        
        # layout
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 0, 5, 0)
        top_layout.addWidget(title, stretch=2)
        top_layout.addWidget(save_button, stretch=3)
        top_layout.addStretch(1)
        
        self.layout = QVBoxLayout(self)
        self.layout.addLayout(top_layout, stretch=1)
        # self.layout.addWidget(self.table, stretch=3)
        self.layout.addWidget(table_view, stretch = 3)
        
    def tableUpdate(self, model):
        self.model = model
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.layout.addWidget(self.table_view)
        