from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from ui.components import ActionButton
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.CleanTheme import \
    CleanTheme as AnalysisTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.SubsectionTitle import SubsectionTitle

import openhdemg.library as emg

class RemoveMUSection(QWidget):
    """Widget section for removing motor units from EMG data.

    Provides functionality to remove specific motor units by number/range
    and to remove empty motor units that contain no pulse data.
    """

    def __init__(self, mu, analysis_plot, colors, parent=None):
        """Initialize the Remove MU Section widget.

        Args:
            mu: Instance of MU file functionality handler
            analysis_plot: Plot widget for displaying updated analysis results
            colors: Color scheme dictionary for UI styling
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.mu = mu
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
        container_layout.setContentsMargins(10, 10, 10, 0)
        container_layout.setSpacing(8)

        remove_mu_layout = QHBoxLayout()
        remove_mu_layout.setSpacing(10)
        remove_mu_layout.setContentsMargins(0, 0, 0, 0)

        self.mu_remove_input = AnalysisInput(placeholder="Remove MUs")
        remove_mu_layout.addWidget(self.mu_remove_input)

        self.remove_mu_confirm_btn = ActionButton("\u2713")
        self.remove_mu_confirm_btn.setToolTip("Remove specified MUs")
        self.remove_mu_confirm_btn.clicked.connect(self.remove_specified_mus)
        self.remove_mu_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_mu_confirm_btn.setFixedWidth(36)
        self.remove_mu_confirm_btn.setFixedHeight(36)
        remove_mu_layout.addWidget(self.remove_mu_confirm_btn)
        self.remove_mu_confirm_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #333333;
                color: {AnalysisTheme.ANALYSIS_TEXT_BUTTON};
                border-radius: 5px;
                padding: 0px;
                text-align: center;
                font-size: 14px;
            }}
            """
        )

        self.remove_empty_mus_btn = ActionButton("Remove empty MUs", parent=self)
        self.remove_empty_mus_btn.clicked.connect(lambda: self.remove_empty_mus())
        self.remove_empty_mus_btn.setMinimumHeight(40)

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
        if not self.mu.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        if not input_text:
            return

        try:
            file = self.mu.file
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

            self.remove_mus_by_range(file, input_text)
            self.mu.plot_idr(
                self.mu.file, self.analysis_plot
            )
            self.mu_remove_input.set("")
        except ValueError as e:
            ErrorDialog(
                "Invalid format:\n Expected format: '1 or 3-5'.",
                "Invalid Input",
            ).exec_()

    def remove_mus_by_range(self, emgfile, input_text):
        """Remove motor units specified by input text from the loaded EMG file.

        Args:
            input_text: String specifying MUs to remove in format:
                       - Single MU: "5" (removes MU 5)
                       - Range: "3-7" (removes MUs 3,4,5,6,7)
                       - Multiple: "1,3-5,8" (removes MUs 1,3,4,5,8)

        Updates all related data structures including BINARY_MUS_FIRING, IPTS,
        MUPULSES, ACCURACY, and NUMBER_OF_MUS. Indices are 1-based in input
        but converted to 0-based internally for array operations.

        Raises:
            ValueError: If no file is loaded or input format is invalid
        """
        if not self.mu.data_loaded():
            raise ValueError("No file loaded.")
        mus_to_remove = []
        parts = input_text.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            sub_parts = [p.strip() for p in part.split("-")]

            # In MU Analysis, we don't have arrays, so we expect 'mu' or 'start-end'
            if len(sub_parts) == 1:  # Single MU
                mu_idx = int(sub_parts[0])
                if mu_idx < 0:
                    raise ValueError("Indices must be positive.")
                mus_to_remove.append(mu_idx)
            elif len(sub_parts) == 2:  # MU range: start-end
                mu_start_idx = int(sub_parts[0])
                mu_end_idx = int(sub_parts[1])
                if mu_start_idx < 0 or mu_end_idx < 0:
                    raise ValueError("Indices must be positive.")
                if mu_end_idx < mu_start_idx:
                    raise ValueError("End of range cannot be smaller than start.")
                for mu_idx in range(mu_start_idx, mu_end_idx + 1):
                    mus_to_remove.append(mu_idx)
            else:
                raise ValueError("Each part must be in 'mu' or 'start-end' format.")

        mus_to_remove = sorted(list(set(mus_to_remove)))

        self.mu.set_file(emg.delete_mus(emgfile, mus_to_remove))

    def remove_empty_mus(self):
        """Remove all motor units that contain no pulse data.

        Identifies motor units with empty MUPULSES arrays and removes them
        from the EMG data. Shows info dialog if no empty MUs are found.
        Updates the plot after successful removal.
        """
        if not self.mu.data_loaded():
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        emgfile = self.mu.file

        empty_mu_indices = [
            i for i, pulses in enumerate(
                emgfile["MUPULSES"]) if len(pulses) == 0]
        if not empty_mu_indices:
            ErrorDialog("No empty MUs to remove.", "Info").exec_()
            return

        self.mu.set_file(emg.delete_empty_mus(emgfile))
        self.mu.plot_idr(
            self.mu.file, self.analysis_plot)
        self.mu_remove_input.set("")
