import traceback

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from app.muAnalysisFunctions.MUAPFunc import (extract_delsys_muaps,
                                              muaps_from_sta, sta)
from app.muAnalysisFunctions.PlotEMGFunc import (diff, double_diff,
                                                 parse_channel_input,
                                                 plot_differentials,
                                                 plot_emgsig, plot_idr,
                                                 plot_ipts, plot_mupulses,
                                                 plot_refsig, sort_rawemg)
from ui.components.muAnalysisComponents.AnalysisCheckbox import AnalysisCheckbox
from ui.components.muAnalysisComponents.AnalysisCheckboxDark import AnalysisCheckboxDark
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisDropdownDialog import AnalysisDropdownDialog
from ui.components.muAnalysisComponents.AnalysisLabeledDropdownDialog import AnalysisLabeledDropdownDialog
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.PropertiesInnerDialogButton import PropertiesInnerDialogButton
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot


class PlotEMGToolDialog(QDialog):

    """Dialog containing options for plotting"""

    def __init__(self, analysis_plot, parent=None):
        super().__init__(parent)
        self.analysis_plot = analysis_plot
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Plot EMG Tool")
        self.setMinimumWidth(700)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setStyleSheet(
            f"background-color: {CleanTheme.ANALYSIS_DIALOG_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title_label = AnalysisText.create_title_dark("Plot Emg Tool")
        layout.addWidget(title_label)

        # --- Filter Section Layout ---
        filter_row = QWidget()
        filter_row_layout = QHBoxLayout(filter_row)
        filter_row_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Checkboxes (vertical)
        checkboxes = QWidget()
        checkbox_col = QVBoxLayout(checkboxes)
        checkbox_col.setContentsMargins(0, 0, 0, 0)

        # reference signal checkbox
        self.ref_signal_checkbox = AnalysisCheckboxDark("Reference signal")
        checkbox_col.addWidget(self.ref_signal_checkbox)

        # time in seconds checkbox
        self.time_seconds_checkbox = AnalysisCheckboxDark("Time in seconds")
        checkbox_col.addWidget(self.time_seconds_checkbox)
        filter_row_layout.addWidget(checkboxes, stretch=1)

        checkbox_col.addStretch(1)

        # Right: Dropdowns (vertical)
        dropdowns = QWidget()
        dropdown_col = QVBoxLayout(dropdowns)
        dropdown_col.setContentsMargins(0, 0, 0, 0)

        # matrix code dropdown
        self.matrix_code_dropdown = AnalysisDropdownDialog(
            "Matrix Code",
            items=["GR08MM1305", "GR04MM1305", "GR10MM0808"],
            parent=self
        )
        dropdown_col.addWidget(self.matrix_code_dropdown)

        # orientation dropdown
        self.orientation_dropdown = AnalysisDropdownDialog(
            "Orientation",
            items=["0", "180"],
            parent=self
        )
        dropdown_col.addWidget(self.orientation_dropdown)
        filter_row_layout.addWidget(dropdowns, stretch=1)

        layout.addWidget(filter_row)
        # layout.addSpacing(5)

        # --- Plot EMGsig, REFsig, IDR, and MUPulses Buttons with Inputs (each in their own row, aligned) ---

        # layout for the middle of the dialog
        mid = QWidget()
        mid_layout = QHBoxLayout(mid)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(mid)

        # left half
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.addWidget(left, stretch=1)

        # right half
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.addWidget(right, stretch=1)

        # figuring out button and input widths
        def dummy_action(): return None
        button_width = max(
            GeneralButton("Plot EMGsig", dummy_action).sizeHint().width(),
            GeneralButton("Plot REFsig", dummy_action).sizeHint().width(),
            GeneralButton("Plot IDR", dummy_action).sizeHint().width(),
            GeneralButton("Plot MUPulses", dummy_action).sizeHint().width(),
        ) + 40  # Add extra width for longer text
        textbox_width = 230

        # left row 1 : Plot EMGsig + Channel Number
        emsig = QWidget()
        emgsig_row = QHBoxLayout(emsig)
        emgsig_row.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(emsig)

        # the input
        self.channel_input = AnalysisInput(
            placeholder="Channel Number (e.g. 1-3,5,7)")
        self.channel_input.set_width(textbox_width)
        emgsig_row.addWidget(self.channel_input)

        # the button
        emgsig_btn = GeneralButton(
            "Plot EMGsig",
            self.handle_emgsig_clicked,
            parent=self)
        emgsig_btn.setFixedWidth(button_width)
        emgsig_row.addWidget(emgsig_btn)

        # left row 2: Plot IDR + MU number
        idr = QWidget()
        idr_row = QHBoxLayout(idr)
        idr_row.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(idr)

        # the input
        self.mu_input = AnalysisInput(placeholder="MU number (e.g. 1-3,5)")
        self.mu_input.set_width(textbox_width)
        idr_row.addWidget(self.mu_input)

        # the button
        idr_btn = GeneralButton(
            "Plot IDR",
            self.handle_idr_clicked,
            parent=self)
        idr_btn.setFixedWidth(button_width)
        idr_row.addWidget(idr_btn)

        # left row 3: Plot Source + MU number
        source = QWidget()
        source_row = QHBoxLayout(source)
        source_row.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(source)

        # the dropdown
        self.source_mu_input = AnalysisInput(
            placeholder="MU Number (e.g. 1-3,5)")
        self.source_mu_input.set_width(textbox_width)
        source_row.addWidget(self.source_mu_input)

        # the button
        source_btn = GeneralButton(
            "Plot Source",
            self.handle_source_clicked,
            parent=self)
        source_btn.setFixedWidth(button_width)
        source_row.addWidget(source_btn)

        # right row 1: Plot MUPulses + line width
        mupulses = QWidget()
        mupulses_row = QHBoxLayout(mupulses)
        mupulses_row.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(mupulses)

        # the input
        self.linewidth_input = AnalysisInput(placeholder="Line Width")
        self.linewidth_input.set_width(textbox_width)
        mupulses_row.addWidget(self.linewidth_input)

        # the button
        mupulses_btn = GeneralButton(
            "Plot MUPulses",
            self.handle_mupulses_clicked,
            parent=self)
        mupulses_btn.setFixedWidth(button_width)
        mupulses_row.addWidget(mupulses_btn)

       # right row 2: Plot REFsig (no input)
        refsig = QWidget()
        refsig_row = QHBoxLayout(refsig)
        refsig_row.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(refsig)

        # the button
        refsig_row.addStretch(1)
        refsig_btn = GeneralButton(
            "Plot REFsig",
            self.handle_refsig_clicked,
            parent=self)
        refsig_btn.setFixedWidth(button_width)
        refsig_row.addWidget(refsig_btn)

        right_layout.addStretch(1)

        # bottom row 1: Derivation + Matrix Column + Config Dropdown
        derivation = QWidget()
        derivation_row = QHBoxLayout(derivation)
        derivation_row.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(derivation)

        # the input
        self.matrix_col_input = AnalysisInput(
            placeholder="Matrix Column ('0' or 'col0' etc.)")
        self.matrix_col_input.set_width(textbox_width)
        derivation_row.addWidget(self.matrix_col_input)

        # Configuration dropdown using custom AnalysisDropdown
        self.derivation_config_dropdown = AnalysisDropdownDialog(
            "Configuration",
            items=["Single Differential", "Double Differential"],
            parent=self
        )
        derivation_row.addWidget(self.derivation_config_dropdown)

        # the button
        derivation_btn = GeneralButton(
            "Derivation",
            self.handle_derivation_clicked,
            parent=self)
        derivation_btn.setFixedWidth(button_width)
        derivation_row.addWidget(derivation_btn)

        # bottom row 2: plot muap
        muap = QWidget()
        muap_row = QHBoxLayout(muap)
        muap_row.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(muap)

        # mu number dropdown
        mu_number_input = AnalysisInput(placeholder="MU Number (e.g. '0')")
        muap_row.addWidget(mu_number_input, stretch=1)
        self.mu_number_input = mu_number_input

        # configuration dropdown
        configuration_items = [
            "Monopolar",
            "Single differential",
            "Double differential"]
        configuration_dropdown = AnalysisDropdownDialog(
            "Configuration", configuration_items, parent=self)
        muap_row.addWidget(configuration_dropdown, stretch=1)
        self.configuration_dropdown = configuration_dropdown

        # timewindow dropdown
        timewindow_items = ["25", "50", "100", "200"]
        timewindow_dropdown = AnalysisDropdownDialog(
            "Timewindow (ms)", timewindow_items, parent=self)
        muap_row.addWidget(timewindow_dropdown, stretch=1)
        self.timewindow_dropdown = timewindow_dropdown

        # the button
        muap_btn = GeneralButton("Plot MUAPs", self.plot_muaps, parent=self)
        muap_btn.setFixedWidth(button_width)
        muap_row.addWidget(muap_btn)

    def handle_emgsig_clicked(self):
        raw_text = self.channel_input.get()
        emgfile = FileUploadFunc.file

        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return

        try:
            # Get the checkbox states for filter options
            time_in_seconds = self.time_seconds_checkbox.isChecked()
            add_ref_signal = self.ref_signal_checkbox.isChecked()

            # Pass the raw text string directly to plot_emgsig for validation
            plot_emgsig(
                emgfile=emgfile,
                analysis_plot=self.analysis_plot,
                channels=raw_text,  # Pass as string for validation
                manual_offset=0,
                addrefsig=add_ref_signal,  # Use checkbox state
                timeinseconds=time_in_seconds,  # Use checkbox state
                figsize=[20, 15],
                tight_layout=True,
                showimmediately=False,
            )
        except ValueError as e:
            ErrorDialog('Invalid channel input', 'Error').exec_()
        except Exception as e:
            ErrorDialog('Error plotting EMG', 'Error').exec_()

    def handle_refsig_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        try:
            fig = plot_refsig(
                emgfile=emgfile,
                analysis_plot=self.analysis_plot,
                timeinseconds=self.time_seconds_checkbox.isChecked()
            )
            canvas = SaveablePlot(fig)
            self.analysis_plot.display_fig(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting REFsig', 'Error').exec_()

    def handle_idr_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        mu_text = self.mu_input.get()
        try:
            munumber = self.parse_mu_input(mu_text)
        except Exception:
            ErrorDialog('invalid plot inputs', 'Error').exec_()
            return
        try:
            fig = plot_idr(
                emgfile=emgfile,
                munumber=munumber,
                addrefsig=self.ref_signal_checkbox.isChecked(),
                timeinseconds=self.time_seconds_checkbox.isChecked(),
                showimmediately=False
            )
            canvas = SaveablePlot(fig)
            self.analysis_plot.display_fig(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting IDR', 'Error').exec_()

    def handle_mupulses_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        lw_text = self.linewidth_input.get()
        try:
            linewidth = float(lw_text)
            if linewidth <= 0:
                raise ValueError()
        except Exception:
            ErrorDialog('invalid plot inputs', 'Error').exec_()
            return
        try:
            fig = plot_mupulses(
                emgfile=emgfile,
                linewidths=linewidth,
                addrefsig=self.ref_signal_checkbox.isChecked(),
                timeinseconds=self.time_seconds_checkbox.isChecked(),
                tight_layout=True,
                showimmediately=False
            )
            canvas = SaveablePlot(fig)
            self.analysis_plot.display_fig(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting MUPulses', 'Error').exec_()

    def parse_mu_input(self, raw_text):
        # Accepts comma-separated and dash ranges, e.g. '1,3,5-7'
        mus = []
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("Empty input")
        parts = raw_text.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start_end = part.split('-')
                if len(start_end) != 2:
                    raise ValueError("Invalid range format")
                start, end = start_end
                start = int(start)
                end = int(end)
                if start > end:
                    raise ValueError("Range start must be <= end")
                mus.extend(range(start, end + 1))
            else:
                mus.append(int(part))
        return sorted(set(mus))

    def handle_source_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        mu_text = self.source_mu_input.get()
        try:
            munumber = self.parse_mu_input(mu_text)
        except Exception:
            ErrorDialog('invalid plot inputs', 'Error').exec_()
            return
        try:
            fig = plot_ipts(
                emgfile=emgfile,
                munumber=munumber,
                timeinseconds=self.time_seconds_checkbox.isChecked(),
                addrefsig=self.ref_signal_checkbox.isChecked(),
                tight_layout=True,
            )
            canvas = SaveablePlot(fig)
            self.analysis_plot.display_fig(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting Source', 'Error').exec_()

    def handle_derivation_clicked(self):
        emgfile = FileUploadFunc.file

        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return

        matrix_col_text = self.matrix_col_input.get().strip()
        if self.derivation_config_dropdown.currentIndex() < 0:
            ErrorDialog(
                'invalid plot inputs (no differential selected)',
                'Error').exec_()
            return

        if matrix_col_text == "":
            ErrorDialog(
                'invalid plot inputs (no column name given)',
                'Error').exec_()
            return

        try:
            if matrix_col_text.isdigit():
                num = int(matrix_col_text)
                if num < 0:
                    raise ValueError()
                column_name = f"col{num}"
            else:
                column_name = matrix_col_text
        except Exception:
            ErrorDialog(
                'invalid plot inputs (invalid column input)',
                'Error').exec_()
            return

        derivation_type = self.derivation_config_dropdown.currentText().lower().replace(" ", "_")

        try:
            if self.matrix_code_dropdown.currentText() != "":
                code = self.matrix_code_dropdown.currentText()
            else:
                code = "GR08MM1305"

            if self.orientation_dropdown.currentText() != "":
                orientation = int(self.orientation_dropdown.currentText())
            else:
                orientation = 180

            sorted_rawemg = sort_rawemg(
                emgfile=emgfile,
                code=code,
                orientation=orientation,
            )

            if derivation_type == "single_differential":
                differential_data = diff(sorted_rawemg=sorted_rawemg)
            elif derivation_type == "double_differential":
                differential_data = double_diff(sorted_rawemg=sorted_rawemg)
            else:
                ErrorDialog(
                    'Invalid derivation type selected',
                    'Error').exec_()
                return

            fig = plot_differentials(
                emgfile=emgfile,
                differential=differential_data,
                column=column_name,
                timeinseconds=self.time_seconds_checkbox.isChecked(),
                addrefsig=self.ref_signal_checkbox.isChecked(),
                tight_layout=True,
                showimmediately=False
            )

            canvas = SaveablePlot(fig)
            self.analysis_plot.display_fig(canvas)
            plt.close(fig)

        except Exception as e:
            print("Full traceback:")
            traceback.print_exc()
            ErrorDialog(
                f'Error plotting Derivation:\n{str(e)}',
                'Error').exec_()

    def plot_muaps(self):
        """Function that plots MUAPs as long as the correct inputs are defined 
        in the modal. 
        Params: None
        Returns: None
        """
        try:
            try:
                max_mu = FileUploadFunc.file["NUMBER_OF_MUS"]
                mu_num = int(self.mu_number_input.get())

                if (mu_num < 0 or mu_num >= max_mu):
                    raise ValueError()
            except ValueError as e:
                ErrorDialog(
                    "Please enter a valid MU number from 0 to " + str(max_mu - 1)).exec_()
                return
            except KeyError as e:
                ErrorDialog(
                    "Your file isn't formatted properly. Include the NUMBER_OF_MUS").exec_()
                return

            # DELSYS requires different MUAPS plot
            if FileUploadFunc.file["SOURCE"] == "DELSYS":
                muaps_dict = extract_delsys_muaps(FileUploadFunc.file)
                muaps_from_sta(self.analysis_plot, muaps_dict[mu_num])

            else:
                try:
                    sorted_file = sort_rawemg(
                        emgfile=FileUploadFunc.file,
                        code=self.matrix_code_dropdown.currentText(),
                        orientation=int(self.orientation_dropdown.currentText()),
                    )
                except ValueError as e:
                    if (self.matrix_code_dropdown.currentText() == ""):
                        ErrorDialog(
                            "Please select a matrix code",
                            "Invalid Input").exec_()
                    elif (self.orientation_dropdown.currentText() == ""):
                        ErrorDialog(
                            "Please select an orientation",
                            "Invalid Input").exec_()
                    else:
                        print(e)
                    return

                if self.configuration_dropdown.currentText() == "Single differential":
                    diff_file = diff(sorted_rawemg=sorted_file)
                elif self.configuration_dropdown.currentText() == "Double differential":
                    diff_file = double_diff(sorted_rawemg=sorted_file)
                elif self.configuration_dropdown.currentText() == "Monopolar":
                    diff_file = sorted_file

                sta_dict = sta(
                    emgfile=FileUploadFunc.file,
                    sorted_rawemg=diff_file,
                    firings="all",
                    timewindow=int(self.timewindow_dropdown.currentText()),
                )

                # Plotting
                muaps_from_sta(self.analysis_plot, sta_dict[mu_num])
        except ValueError as e:
            if (self.configuration_dropdown.currentText() == ""):
                ErrorDialog(
                    "Please select a muap configuration",
                    "Invalid Input").exec_()
            elif (self.timewindow_dropdown.currentText() == ""):
                ErrorDialog(
                    "Please select a timewindow",
                    "Invalid Input").exec_()
        except UnboundLocalError as e:
            ErrorDialog(
                "Please enter a valid configuration",
                "Invalid Input").exec_()
        except KeyError as e:
            ErrorDialog(
                "Please enter a valid Matrix Column",
                "Invalid Input").exec_()


# general class for any inner inputs inside dialog
class PropertiesInnerDialogText(QLineEdit):
    def __init__(self, text):
        super().__init__()
        self.setMinimumHeight(32)
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", 11))
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                border: 2px solid {CleanTheme.BORDER};
                border-radius: 6px;
                background-color: {CleanTheme.ANALYSIS_BG_CARD};
                color: {CleanTheme.TEXT_PRIMARY};
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border-color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """)


class PlotEMGButton(QWidget):
    """Button widget for opening Motor Unit Properties dialog"""

    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated

    def __init__(self, analysis_plot, parent=None):
        super().__init__(parent)
        self.analysis_plot = analysis_plot
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Subtitle
        subtitle_label = AnalysisText.create_subtitle("PLOT EMG")
        subtitle_label.setObjectName("motorUnitAnalysisSubTitle")
        layout.addWidget(subtitle_label)

        plot_emg_btn = GeneralButton(
            "Plot EMG", lambda: self.open_plot_emg_btn())
        layout.addWidget(plot_emg_btn)
        layout.setAlignment(plot_emg_btn, Qt.AlignmentFlag.AlignTop)

    def open_plot_emg_btn(self):
        if FileUploadFunc.file is None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        # Open the Motor Unit Properties dialog
        dialog = PlotEMGToolDialog(self.analysis_plot)
        dialog.exec_()
