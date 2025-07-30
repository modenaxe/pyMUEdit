from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout,
    QHBoxLayout, 
    QPushButton, 
    QLineEdit,
    QDialog,
    QMessageBox,
    QCheckBox,
    QComboBox,
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from app.muAnalysisFunctions.PlotEMGFunc import parse_channel_input, plot_emgsig, plot_idr, plot_mupulses, plot_ipts
from app.muAnalysisFunctions.PlotEMGFunc import plot_differentials, diff, double_diff, sort_rawemg
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.AnalysisCheckbox import AnalysisCheckbox 
from ui.components.muAnalysisComponents.PropertiesInnerDialogButton import PropertiesInnerDialogButton
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.SaveablePlot import SaveablePlot
from ui.muanalysis.PlotMUAP import PlotMUAP
import matplotlib.pyplot as plt
import traceback


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
        self.setStyleSheet(f"background-color: {CleanTheme.ANALYSIS_BG_SIDEBAR};")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title_label = AnalysisText.create_title("Plot Emg Tool") 
        layout.addWidget(title_label)
        
        # --- Filter Section Layout ---
        filter_row_layout = QHBoxLayout()
        filter_row_layout.setSpacing(20)

        # Left: Checkboxes (vertical)
        checkbox_col = QVBoxLayout()
        checkbox_col.setSpacing(10)

        # reference signal checkbox 
        self.ref_signal_checkbox = AnalysisCheckbox("Reference signal")
        checkbox_col.addWidget(self.ref_signal_checkbox)

        # time in seconds checkbox
        self.time_seconds_checkbox = AnalysisCheckbox("Time in seconds")
        checkbox_col.addWidget(self.time_seconds_checkbox)
        filter_row_layout.addLayout(checkbox_col)

        # Right: Dropdowns (vertical)
        dropdown_col = QVBoxLayout()
        dropdown_col.setSpacing(10)
        self.matrix_code_dropdown = AnalysisDropdown(
            "Matrix Code",
            items=["GR08MM1305", "GR04MM1305", "GR10MM0808"],
            parent=self
        )
        dropdown_col.addWidget(self.matrix_code_dropdown)
        self.orientation_dropdown = AnalysisDropdown(
            "Orientation",
            items=["0", "180"],
            parent=self
        )
        dropdown_col.addWidget(self.orientation_dropdown)
        filter_row_layout.addLayout(dropdown_col)
        layout.addLayout(filter_row_layout)

        # --- Plot EMGsig, REFsig, IDR, and MUPulses Buttons with Inputs (each in their own row, aligned) ---
        button_input_col = QVBoxLayout()
        button_input_col.setSpacing(12)
        dummy_action = lambda: None
        button_width = max(
            GeneralButton("Plot EMGsig", dummy_action).sizeHint().width(),
            GeneralButton("Plot REFsig", dummy_action).sizeHint().width(),
            GeneralButton("Plot IDR", dummy_action).sizeHint().width(),
            GeneralButton("Plot MUPulses", dummy_action).sizeHint().width(),
        ) + 40  # Add extra width for longer text
        textbox_width = 280
        button_height = 36

        # Row 1: Plot EMGsig + Channel Number
        emgsig_row = QHBoxLayout()
        emgsig_btn = GeneralButton("Plot EMGsig", self.handle_emgsig_clicked, parent=self)
        emgsig_btn.setFixedWidth(button_width)
        emgsig_btn.setFixedHeight(button_height)
        emgsig_row.addWidget(emgsig_btn)
        emgsig_row.addSpacing(8)
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel Number (e.g. 1-3,5,7)")
        self.channel_input.setFont(QFont("Arial", 11))
        self.channel_input.setMinimumHeight(button_height)
        self.channel_input.setFixedHeight(button_height)
        self.channel_input.setFixedWidth(textbox_width)
        self.channel_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        emgsig_row.addWidget(self.channel_input)
        emgsig_row.addStretch(1)
        button_input_col.addLayout(emgsig_row)

        # Row 2: Plot REFsig (no input)
        refsig_row = QHBoxLayout()
        refsig_btn = GeneralButton("Plot REFsig", self.handle_refsig_clicked, parent=self)
        refsig_btn.setFixedWidth(button_width)
        refsig_btn.setFixedHeight(button_height)
        refsig_row.addWidget(refsig_btn)
        refsig_row.addStretch(1)
        button_input_col.addLayout(refsig_row)

        # Row 3: Plot IDR + MU number
        idr_row = QHBoxLayout()
        idr_btn = GeneralButton("Plot IDR", self.handle_idr_clicked, parent=self)
        idr_btn.setFixedWidth(button_width)
        idr_btn.setFixedHeight(button_height)
        idr_row.addWidget(idr_btn)
        idr_row.addSpacing(8)
        self.mu_input = QLineEdit()
        self.mu_input.setPlaceholderText("MU number (e.g. 1-3,5)")
        self.mu_input.setFont(QFont("Arial", 11))
        self.mu_input.setMinimumHeight(button_height)
        self.mu_input.setFixedHeight(button_height)
        self.mu_input.setFixedWidth(textbox_width)
        self.mu_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        idr_row.addWidget(self.mu_input)
        idr_row.addStretch(1)
        button_input_col.addLayout(idr_row)

        # Row 4: Plot MUPulses + line width
        mupulses_row = QHBoxLayout()
        mupulses_btn = GeneralButton("Plot MUPulses", self.handle_mupulses_clicked, parent=self)
        mupulses_btn.setFixedWidth(button_width)
        mupulses_btn.setFixedHeight(button_height)
        mupulses_row.addWidget(mupulses_btn)
        mupulses_row.addSpacing(8)
        self.linewidth_input = QLineEdit()
        self.linewidth_input.setPlaceholderText("Line Width")
        self.linewidth_input.setFont(QFont("Arial", 11))
        self.linewidth_input.setMinimumHeight(button_height)
        self.linewidth_input.setFixedHeight(button_height)
        self.linewidth_input.setFixedWidth(textbox_width)
        self.linewidth_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        mupulses_row.addWidget(self.linewidth_input)
        mupulses_row.addStretch(1)
        button_input_col.addLayout(mupulses_row)

        layout.addLayout(button_input_col)
        
        # Row 5: Plot Source + MU number
        source_row = QHBoxLayout()
        source_btn = GeneralButton("Plot Source", self.handle_source_clicked, parent=self)
        source_btn.setFixedWidth(button_width)
        source_btn.setFixedHeight(button_height)
        source_row.addWidget(source_btn)
        source_row.addSpacing(8)
        self.source_mu_input = QLineEdit()
        self.source_mu_input.setPlaceholderText("MU Number (e.g. 1-3,5)")
        self.source_mu_input.setFont(QFont("Arial", 11))
        self.source_mu_input.setMinimumHeight(button_height)
        self.source_mu_input.setFixedHeight(button_height)
        self.source_mu_input.setFixedWidth(textbox_width)
        self.source_mu_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        source_row.addWidget(self.source_mu_input)
        source_row.addStretch(1)
        button_input_col.addLayout(source_row)
        
        # Row 6: Derivation + Matrix Column + Config Dropdown
        derivation_row = QHBoxLayout()
        derivation_btn = GeneralButton("Derivation", self.handle_derivation_clicked, parent=self)
        derivation_btn.setFixedWidth(button_width)
        derivation_btn.setFixedHeight(button_height)
        derivation_row.addWidget(derivation_btn)
        derivation_row.addSpacing(8)

        # Matrix column input
        self.matrix_col_input = QLineEdit()
        self.matrix_col_input.setPlaceholderText("Matrix Column ('0' or 'col0' etc.)")
        self.matrix_col_input.setFont(QFont("Arial", 11))
        self.matrix_col_input.setMinimumHeight(button_height)
        self.matrix_col_input.setFixedHeight(button_height)
        self.matrix_col_input.setFixedWidth(textbox_width)
        self.matrix_col_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        derivation_row.addWidget(self.matrix_col_input)
        derivation_row.addSpacing(8)

        # Configuration dropdown using custom AnalysisDropdown
        self.derivation_config_dropdown = AnalysisDropdown(
            "Configuration",
            items=["Single Differential", "Double Differential"],
            parent=self
        )
        derivation_row.addWidget(self.derivation_config_dropdown)

        derivation_row.addStretch(1)
        button_input_col.addLayout(derivation_row)


        plot_muap = PlotMUAP(
            self.analysis_plot, 
            self.matrix_code_dropdown, 
            self.orientation_dropdown
        )
        layout.addWidget(plot_muap)

    def has_invalid_filter_inputs(self):
        # Returns True if either dropdown is not at its placeholder
        matrix_code_selected = self.matrix_code_dropdown.currentIndex() != -1 and self.matrix_code_dropdown.currentIndex() != 0
        orientation_selected = self.orientation_dropdown.currentIndex() != -1 and self.orientation_dropdown.currentIndex() != 0
        return matrix_code_selected or orientation_selected

    def handle_emgsig_clicked(self):
        if self.has_invalid_filter_inputs():
            ErrorDialog('Invalid filter inputs', 'Error').exec_()
            return
        raw_text = self.channel_input.text()
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
            FileUploadFunc().plot_refsig(
                emgfile=emgfile,
                analysis_plot=self.analysis_plot,
                timeinseconds=self.time_seconds_checkbox.isChecked()
            )
        except Exception as e:
            ErrorDialog('Error plotting REFsig', 'Error').exec_()

    def handle_idr_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        mu_text = self.mu_input.text()
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
            self.analysis_plot.display_plot(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting IDR', 'Error').exec_()

    def handle_mupulses_clicked(self):
        emgfile = FileUploadFunc.file
        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return
        lw_text = self.linewidth_input.text()
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
            self.analysis_plot.display_plot(canvas)
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
        mu_text = self.source_mu_input.text()
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
                showimmediately=False
            )
            canvas = SaveablePlot(fig)
            self.analysis_plot.display_plot(canvas)
            plt.close(fig)
        except Exception as e:
            ErrorDialog('Error plotting Source', 'Error').exec_()
            
    def handle_derivation_clicked(self):
        emgfile = FileUploadFunc.file

        if emgfile is None:
            ErrorDialog('No file has been loaded', 'Error').exec_()
            return

        matrix_col_text = self.matrix_col_input.text().strip()
        if self.derivation_config_dropdown.currentIndex() < 0:
            ErrorDialog('invalid plot inputs (no differential selected)', 'Error').exec_()
            return

        if matrix_col_text == "":
            ErrorDialog('invalid plot inputs (no column name given)', 'Error').exec_()
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
            ErrorDialog('invalid plot inputs (invalid column input)', 'Error').exec_()
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
                ErrorDialog('Invalid derivation type selected', 'Error').exec_()
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
            self.analysis_plot.display_plot(canvas)
            plt.close(fig)

        except Exception as e:
            print("Full traceback:")
            traceback.print_exc()
            ErrorDialog(f'Error plotting Derivation:\n{str(e)}', 'Error').exec_()




        
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

        plot_emg_btn = GeneralButton("Plot EMG", lambda: self.open_plot_emg_btn())
        layout.addWidget(plot_emg_btn)
        layout.setAlignment(plot_emg_btn, Qt.AlignmentFlag.AlignTop)
        
    def open_plot_emg_btn(self):
        if FileUploadFunc.file == None:
            ErrorDialog("No file has been loaded", "Error").exec_()

        # Open the Motor Unit Properties dialog
        dialog = PlotEMGToolDialog(self.analysis_plot)
        dialog.exec_()
