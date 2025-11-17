from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QCheckBox, QDialog, QFileDialog, QHBoxLayout,
                             QLabel, QPushButton, QSizePolicy, QSpacerItem,
                             QStyle, QToolButton, QVBoxLayout, QWidget)

from ui.components.ActionButtonedit import ActionButtonedit
from ui.components.ErrorDialog import ErrorDialog
from core.logger import logger

class PlotDialog(QDialog):
    def __init__(self, title):
        """
        Initialize a Plot Dialog

        Args:
            title (str): Dialog Title
        """
        super().__init__()
        self.setFont(QFont("Segoe UI"))
        self.mouse_pos = None
        self.reversePlot = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self.setStyleSheet("""
            PlotDialog {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
        """)

        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 0, 5, 5)
        self.layout.setSpacing(0)

        self.max_btn = ActionButtonedit(
            text="window_maximize",
            icon="window_maximize.png")
        self.res_btn = ActionButtonedit(
            text="window_restore",
            icon="window_restore.png")
        self.min_btn = ActionButtonedit(
            text="window_restore",
            icon="window_minimize.png")
        self.close_btn = ActionButtonedit(
            text="window_close", icon="window_close.png")
        self.save_btn = ActionButtonedit(
            text="window_close", icon="window_save.png")
        self.title = QLabel(title)

        self.spacer = QSpacerItem(20, 0)

        self.close_btn.clicked.connect(self.hide)
        self.close_btn.setIconSize(QSize(24, 24))

        self.max_btn.clicked.connect(self.showFullScreen)
        self.max_btn.clicked.connect(lambda: self.toggle_buttons(True))
        self.max_btn.setIconSize(QSize(24, 24))

        self.res_btn.clicked.connect(self.showNormal)
        self.res_btn.clicked.connect(lambda: self.toggle_buttons(False))
        self.res_btn.setIconSize(QSize(24, 24))
        self.res_btn.hide()

        self.min_btn.clicked.connect(self.showMinimized)
        self.min_btn.setIconSize(QSize(20, 20))

        self.save_btn.clicked.connect(self._save_btn_pushed)
        self.save_btn.setIconSize(QSize(28, 28))

        btn_row = QWidget()
        self.btn_layout = QHBoxLayout()
        btn_row.setLayout(self.btn_layout)

        self.btn_layout.addWidget(self.title, stretch=1)
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.save_btn)
        self.btn_layout.addWidget(self.min_btn)
        self.btn_layout.addWidget(self.max_btn)
        self.btn_layout.addWidget(self.res_btn)
        self.btn_layout.addWidget(self.close_btn)

        self.setLayout(self.layout)

        self.canvas = QWidget()
        self.center_layout = QVBoxLayout()
        self.center_layout.setSpacing(0)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.addItem(
            QSpacerItem(
                20,
                0,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding))
        self.center_layout.addWidget(self.canvas)
        self.center_layout.addItem(
            QSpacerItem(
                20,
                0,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding))

        center_row = QWidget()
        center_row.setLayout(self.center_layout)

        self.layout.addWidget(btn_row)
        self.layout.addWidget(center_row)
        self._set_style()

    def _set_style(self):
        self.max_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(200, 200, 200, 128);
            }}

            QPushButton:pressed {{
                background-color: rgba(100, 100, 100, 180);
            }}
            """
        )
        self.max_btn.setMinimumSize(48, 48)

        self.res_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(200, 200, 200, 128);
            }}

            QPushButton:pressed {{
                background-color: rgba(100, 100, 100, 180);
            }}
            """
        )
        self.res_btn.setMinimumSize(48, 48)

        self.min_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(200, 200, 200, 128);
            }}

            QPushButton:pressed {{
                background-color: rgba(100, 100, 100, 180);
            }}
            """
        )
        self.min_btn.setMinimumSize(48, 48)

        self.close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: #e74c3c;
            }}

            QPushButton:pressed {{
                background-color: #f19484;
            }}
            """
        )
        self.close_btn.setMinimumSize(48, 48)

        self.save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(200, 200, 200, 128);
            }}

            QPushButton:pressed {{
                background-color: rgba(100, 100, 100, 180);
            }}
            """
        )
        self.save_btn.setMinimumSize(48, 48)

        self.title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                padding: 8px;
            }
        """)

    def set_canvas(self, canvas):
        self.center_layout.removeWidget(self.canvas)
        self.canvas.setParent(None)
        self.canvas.deleteLater()
        self.center_layout.insertWidget(1, canvas)
        self.canvas = canvas

    def toggle_buttons(self, flag):
        self.max_btn.setVisible(not flag)
        self.res_btn.setVisible(flag)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mouse_pos:
            self.move(event.globalPos() - self.mouse_pos)
            event.accept()

    def set_title(self, text):
        self.title.setText(text)

    def _save_btn_pushed(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Plot As PNG", "", "PNG (*.png);; All Files (*)")
        if filepath:
            try:
                self.canvas.figure.savefig(
                    filepath, dpi=300, bbox_inches='tight')
                self.save_success()
            except Exception as e:
                logger.exception("Failed to save plot as PNG.")
                ErrorDialog(f"Failed to save the plot.\n\nDetails: {e}")

    def save_success(self):
        self.save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: #bbf795;
                color: #bbf795;
                border: none;
                border-radius: 4px;
                padding: 8px 0px;
            }}
            """
        )
        self.save_btn.setIcon("save_success.png")
        QTimer.singleShot(2000, lambda: (
            self._set_style(),
            self.save_btn.setIcon("window_save.png")
        ))
