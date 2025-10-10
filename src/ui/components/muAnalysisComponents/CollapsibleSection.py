from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton
from PyQt5.QtCore import Qt

class CollapsibleSection(QWidget):
    def __init__(self, title, content_widget, parent=None, expanded=False):
        super().__init__(parent)
        self.content_widget = content_widget
        self.expanded = expanded

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # header of dropdown
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(5, 5, 5, 5)
        self.header_layout.setSpacing(5)

        # dropdown chevron icon and styling
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.chevron_btn = QToolButton()
        self.chevron_btn.setStyleSheet("border: none;")
        self.chevron_btn.setArrowType(Qt.DownArrow if self.expanded else Qt.RightArrow)
        self.chevron_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.chevron_btn.setAutoRaise(True)
        self.chevron_btn.clicked.connect(self.toggle)

        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch(1)
        self.header_layout.addWidget(self.chevron_btn)
        self.main_layout.addWidget(self.header)

        # display contents of dropdown
        self.content_widget.setVisible(self.expanded)
        self.main_layout.addWidget(self.content_widget)

        # make header clickable
        self.header.mousePressEvent = self.toggle

    # toggle for dropdowns
    def toggle(self, event=None):
        self.expanded = not self.expanded
        self.content_widget.setVisible(self.expanded)
        self.chevron_btn.setArrowType(Qt.DownArrow if self.expanded else Qt.RightArrow)
