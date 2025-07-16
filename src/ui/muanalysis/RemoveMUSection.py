from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QLabel,
    QFrame,
)
from ui.components import ActionButton, CleanTheme
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme as AnalysisTheme
from PyQt5.QtCore import Qt


class RemoveMUSection(QWidget):
    def __init__(self, mu_analysis_func, analysis_plot, colors, parent=None):
        super().__init__(parent)
        self.mu_analysis_func = mu_analysis_func
        self.analysis_plot = analysis_plot
        self.colors = colors
        self.init_ui()

    def init_ui(self):
        # Use a container QFrame for consistent sidebar alignment
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)  # 10px left/right to match sidebar
        container_layout.setSpacing(8)

        # Update heading to 'MU EDITING' and match sidebar heading formatting
        title_label = QLabel("MU EDITING")
        title_label.setStyleSheet(
            f"""
            color: {AnalysisTheme.ANALYSIS_TEXT_TERTIARY};
            font-size: 10px;
            font-weight: 700;
            font-family: Arial;
            letter-spacing: 1px;
            margin-bottom: 2px;
            text-transform: uppercase;
            """
        )
        container_layout.addWidget(title_label)

        remove_mu_layout = QHBoxLayout()
        remove_mu_layout.setSpacing(10)
        remove_mu_layout.setContentsMargins(0, 0, 0, 0)

        self.mu_remove_input = QLineEdit()
        self.mu_remove_input.setPlaceholderText("Remove MUs")
        self.mu_remove_input.setStyleSheet(
            f"""
            QLineEdit {{
                color: {self.colors['text_primary']};
                background-color: {AnalysisTheme.ANALYSIS_BG_CARD};
                border: 1px solid {AnalysisTheme.BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            """
        )
        self.mu_remove_input.setMinimumWidth(0)
        self.mu_remove_input.setMaximumWidth(16777215)
        remove_mu_layout.addWidget(self.mu_remove_input)

        self.remove_mu_confirm_btn = ActionButton("\u2713", primary=False)
        self.remove_mu_confirm_btn.setToolTip("Remove specified MUs")
        self.remove_mu_confirm_btn.clicked.connect(self.remove_specified_mus)
        self.remove_mu_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_mu_confirm_btn.setFixedWidth(36)
        self.remove_mu_confirm_btn.setFixedHeight(36)
        self.remove_mu_confirm_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {AnalysisTheme.ANALYSIS_BG_BUTTON};
                color: {AnalysisTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 5px;
                padding: 0px;
                text-align: center;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {AnalysisTheme.ANALYSIS_TEXT_BUTTON};
                color: {AnalysisTheme.ANALYSIS_BG_BUTTON};
            }}
            """
        )
        remove_mu_layout.addWidget(self.remove_mu_confirm_btn)

        container_layout.addLayout(remove_mu_layout)

        # Clear the main layout and add the container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(container)

    def remove_specified_mus(self):
        input_text = self.mu_remove_input.text()
        if not self.mu_analysis_func.data_loaded():
            QMessageBox.warning(self, "No Data", "Please load a file first.")
            return

        if not input_text:
            return

        try:
            self.mu_analysis_func.remove_mus_by_range(input_text)
            # After removing, replot the data to reflect the changes
            self.mu_analysis_func.plot_idr(
                self.mu_analysis_func.file, self.analysis_plot
            )
            QMessageBox.information(
                self,
                "Success",
                "Specified MUs have been removed and the plot has been updated.",
            )
            self.mu_remove_input.clear()
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Invalid Input",
                f"Invalid format: {e}\nPlease use comma-separated 'mu' or 'start-end' pairs, e.g., '1, 3-5'.",
            )
