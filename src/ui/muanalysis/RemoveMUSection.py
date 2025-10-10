from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from ui.components import ActionButton
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.CleanTheme import \
    CleanTheme as AnalysisTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.SubsectionTitle import SubsectionTitle


class RemoveMUSection(QWidget):
    """Widget section for removing motor units from EMG data.

    Provides functionality to remove specific motor units by number/range
    and to remove empty motor units that contain no pulse data.
    """

    def __init__(self, mu_analysis_func, analysis_plot, colors, parent=None):
        """Initialize the Remove MU Section widget.

        Args:
            mu_analysis_func: Instance of MU analysis functionality handler
            analysis_plot: Plot widget for displaying updated analysis results
            colors: Color scheme dictionary for UI styling
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.mu_analysis_func = mu_analysis_func
        self.analysis_plot = analysis_plot
        self.colors = colors
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface components.

        Creates the layout with input field for MU numbers, confirm button,
        and button for removing empty MUs. Applies appropriate styling and
        connects button signals to their respective handlers.
        """
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)

        title_label = SubsectionTitle("MU EDITING")
        container_layout.addWidget(title_label)

        remove_mu_layout = QHBoxLayout()
        remove_mu_layout.setSpacing(10)
        remove_mu_layout.setContentsMargins(0, 0, 0, 0)

        self.mu_remove_input = AnalysisInput(placeholder="Remove MUs")
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

        self.remove_empty_mus_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e5e5e5;
                border-radius: 5px;
                font-size: 1em;
                height: 100px;
                width: 200px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
            """
        )

        container_layout.addWidget(self.remove_empty_mus_btn)

        container_layout.addLayout(remove_mu_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(container)

    def remove_specified_mus(self):
        """Remove motor units specified by user input.

        Parses the input text for MU numbers and ranges (e.g., "1,3-5,7"),
        validates that the specified MUs exist in the loaded data,
        and removes them if valid. Updates the plot after successful removal.

        Input format supports:
        - Single numbers: "1,3,7"
        - Ranges: "3-5" (removes MUs 3,4,5)
        - Mixed: "1,3-5,8"
        """
        input_text = self.mu_remove_input.get()
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
            self.mu_remove_input.set("")
        except ValueError as e:
            ErrorDialog(
                "Invalid format:\n Expected format: '1 or 3-5'.",
                "Invalid Input",
            ).exec_()

    def remove_empty_mus(self):
        """Remove all motor units that contain no pulse data.

        Identifies motor units with empty MUPULSES arrays and removes them
        from the EMG data. Shows info dialog if no empty MUs are found.
        Updates the plot after successful removal.
        """
        if not self.mu_analysis_func.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        emgfile = self.mu_analysis_func.file
        empty_mu_indices = [
            i for i, pulses in enumerate(
                emgfile["MUPULSES"]) if len(pulses) == 0]
        if not empty_mu_indices:
            ErrorDialog("No empty MUs to remove.", "Info").exec_()
            return

        input_text = ",".join(str(i + 1) for i in empty_mu_indices)
        self.mu_analysis_func.remove_mus_by_range(input_text)
        self.mu_analysis_func.plot_idr(
            self.mu_analysis_func.file, self.analysis_plot)
        self.mu_remove_input.set("")
