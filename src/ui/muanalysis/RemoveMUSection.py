from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QFrame,
)
from ui.components import ActionButton
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme as AnalysisTheme
from PyQt5.QtCore import Qt

from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton


class RemoveMUSection(QWidget):
    def __init__(self, mu_analysis_func, analysis_plot, colors, parent=None):
        super().__init__(parent)
        self.mu_analysis_func = mu_analysis_func
        self.analysis_plot = analysis_plot
        self.colors = colors
        self.init_ui()

    def init_ui(self):
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)

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
            """
        )
        remove_mu_layout.addWidget(self.remove_mu_confirm_btn)

        self.remove_empty_mus_btn = GeneralButton(
            "Remove empty MUs", lambda: self.remove_empty_mus(), parent=self
        )
        self.remove_empty_mus_btn.setToolTip("Remove all empty MUs")
        container_layout.addWidget(self.remove_empty_mus_btn)

        container_layout.addLayout(remove_mu_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(container)

    def remove_specified_mus(self):
        input_text = self.mu_remove_input.text()
        if not self.mu_analysis_func.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        if not input_text:
            return

        try:
            file = self.mu_analysis_func.file
            total_mus = file.get("NUMBER_OF_MUS", 0) if file else 0

            mus_to_check = []
            parts = input_text.split(",")
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                sub_parts = [p.strip() for p in part.split("-")]

                if len(sub_parts) == 1:
                    mu_num = int(sub_parts[0])
                    mus_to_check.append(mu_num)
                elif len(sub_parts) == 2:
                    start_num = int(sub_parts[0])
                    end_num = int(sub_parts[1])
                    mus_to_check.extend(range(start_num, end_num + 1))

            invalid_mus = [mu for mu in mus_to_check if mu > total_mus]
            if invalid_mus:
                ErrorDialog(
                    f"Invalid MU numbers: {', '.join(map(str, invalid_mus))}\nAvailable MUs: 1-{total_mus}",
                    "Invalid Input",
                ).exec_()
                return

            self.mu_analysis_func.remove_mus_by_range(input_text)
            self.mu_analysis_func.plot_idr(
                self.mu_analysis_func.file, self.analysis_plot
            )
            self.mu_remove_input.clear()
        except ValueError as e:
            ErrorDialog(
                "Invalid format:\n Expected format: '1 or 3-5'.",
                "Invalid Input",
            ).exec_()

    def remove_empty_mus(self):
        if not self.mu_analysis_func.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        emgfile = self.mu_analysis_func.file
        empty_mu_indices = [
            i for i, pulses in enumerate(emgfile["MUPULSES"]) if len(pulses) == 0
        ]
        if not empty_mu_indices:
            ErrorDialog("No empty MUs to remove.", "Info").exec_()
            return

        input_text = ",".join(str(i + 1) for i in empty_mu_indices)
        self.mu_analysis_func.remove_mus_by_range(input_text)
        self.mu_analysis_func.plot_idr(self.mu_analysis_func.file, self.analysis_plot)
        self.mu_remove_input.clear()
