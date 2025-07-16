from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QLabel
from ui.components import ActionButton, CleanTheme
from PyQt5.QtGui import QFont

class RemoveMUSection(QWidget):
    def __init__(self, mu_analysis_func, analysis_plot, parent=None):
        super().__init__(parent)
        self.mu_analysis_func = mu_analysis_func
        self.analysis_plot = analysis_plot
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(8)

        title_label = QLabel("Remove Specified MUs")
        title_label.setStyleSheet(f"""
            color: "{CleanTheme.TEXT_SECONDARY}";
            font-size: 9pt;
            font-weight: bold;
            padding-left: 2px;
        """)
        layout.addWidget(title_label)

        remove_mu_layout = QHBoxLayout()
        remove_mu_layout.setSpacing(10)
        remove_mu_layout.setContentsMargins(0, 0, 0, 0)

        self.mu_remove_input = QLineEdit()
        self.mu_remove_input.setPlaceholderText("e.g., 1, 3-5")
        self.mu_remove_input.setStyleSheet(
            f"""
            QLineEdit {{
                color: {CleanTheme.TEXT_PRIMARY};
                background-color: {CleanTheme.BG_CARD};
                border: 1px solid {CleanTheme.BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            """
        )
        remove_mu_layout.addWidget(self.mu_remove_input)

        self.remove_mu_confirm_btn = ActionButton("✓", primary=True)
        self.remove_mu_confirm_btn.setToolTip("Remove specified MUs")
        self.remove_mu_confirm_btn.clicked.connect(self.remove_specified_mus)
        
        # Set a fixed width to match other buttons
        self.remove_mu_confirm_btn.setFixedWidth(36)

        remove_mu_layout.addWidget(self.remove_mu_confirm_btn)
        
        layout.addLayout(remove_mu_layout)

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
            self.mu_analysis_func.plot_idr(self.mu_analysis_func.file, self.analysis_plot)
            QMessageBox.information(self, "Success", "Specified MUs have been removed and the plot has been updated.")
            self.mu_remove_input.clear()
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Invalid format: {e}\nPlease use comma-separated 'mu' or 'start-end' pairs, e.g., '1, 3-5'.")

