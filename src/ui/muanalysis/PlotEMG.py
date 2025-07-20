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
from app.muAnalysisFunctions.PlotEMGFunc import parse_channel_input, plot_emgsig
from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.PropertiesInnerDialogButton import PropertiesInnerDialogButton
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog


class PlotEMGToolDialog(QDialog):

    """Dialog containing options for plotting"""
    
    def __init__(self, analysis_plot, parent=None):
        super().__init__(parent)
        self.analysis_plot = analysis_plot
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Plot EMG Tool")
        self.setMinimumWidth(550)
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
        self.ref_signal_checkbox = QCheckBox("Reference signal")
        self.ref_signal_checkbox.setFont(QFont("Arial", 11))
        self.ref_signal_checkbox.setStyleSheet(f"""
            QCheckBox {{ color: {CleanTheme.ANALYSIS_TEXT_BUTTON}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border: 2px solid #ced4da; border-radius: 3px; background-color: #ffffff; }}
            QCheckBox::indicator:checked {{ background-color: {CleanTheme.ANALYSIS_BG_BUTTON}; border-color: {CleanTheme.ANALYSIS_BG_BUTTON}; }}
        """)
        checkbox_col.addWidget(self.ref_signal_checkbox)
        self.time_seconds_checkbox = QCheckBox("Time in seconds")
        self.time_seconds_checkbox.setFont(QFont("Arial", 11))
        self.time_seconds_checkbox.setStyleSheet(f"""
            QCheckBox {{ color: {CleanTheme.ANALYSIS_TEXT_BUTTON}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border: 2px solid #ced4da; border-radius: 3px; background-color: #ffffff; }}
            QCheckBox::indicator:checked {{ background-color: {CleanTheme.ANALYSIS_BG_BUTTON}; border-color: {CleanTheme.ANALYSIS_BG_BUTTON}; }}
        """)
        checkbox_col.addWidget(self.time_seconds_checkbox)
        filter_row_layout.addLayout(checkbox_col)

        # Right: Dropdowns (vertical)
        dropdown_col = QVBoxLayout()
        dropdown_col.setSpacing(10)
        self.matrix_code_dropdown = AnalysisDropdown(
            "Matrix Code",
            items=["GR08MM1305", "GR08MM1308", "None"],
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

        # --- Plot EMGsig and REFsig Buttons (vertical) and Channel Input (side by side) ---
        button_col = QVBoxLayout()
        emgsig_btn = GeneralButton("Plot EMGsig", self.handle_emgsig_clicked, parent=self)
        refsig_btn = GeneralButton("Plot REFsig", self.handle_refsig_clicked, parent=self)
        # Set both buttons to the same width (use the max of their size hints)
        max_width = max(emgsig_btn.sizeHint().width(), refsig_btn.sizeHint().width())
        emgsig_btn.setFixedWidth(max_width)
        refsig_btn.setFixedWidth(max_width)
        button_col.addWidget(emgsig_btn)
        button_col.addWidget(refsig_btn)

        channel_col = QVBoxLayout()
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel Number (e.g. 1-3,5,7)")
        self.channel_input.setFont(QFont("Arial", 11))
        self.channel_input.setMinimumHeight(32)
        self.channel_input.setStyleSheet("""
            QLineEdit { padding: 8px; border: 2px solid #ced4da; border-radius: 6px; background-color: #ffffff; color: #212529; }
        """)
        channel_col.addWidget(self.channel_input)
        channel_col.addStretch(1)

        emg_row_layout = QHBoxLayout()
        emg_row_layout.addLayout(button_col)
        emg_row_layout.addLayout(channel_col)
        layout.addLayout(emg_row_layout)

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


# TL : useless after W18ABANANA-37-center-plots
# class EMGsigResultDialog(QDialog):
#     def __init__(self, channels, time_in_seconds, add_ref_signal, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("EMG Signal Plot")
#         self.channels = channels  # This is now the raw text string
#         self.emgfile = FileUploadFunc.file
#         self.time_in_seconds = time_in_seconds
#         self.add_ref_signal = add_ref_signal
#         self.resize(1000, 700)
#         self.init_ui()
#
#     def init_ui(self):
#         # Create the layout for the dialog
#         layout = QVBoxLayout(self)
#
#         # Get the figure from the plot_emgsig function
#         fig = plot_emgsig(
#             emgfile=self.emgfile,
#             channels=self.channels,  # Pass the raw text string
#             manual_offset=0,
#             addrefsig=self.add_ref_signal,
#             timeinseconds=self.time_in_seconds,
#             figsize=[20, 15],
#             tight_layout=True,
#             showimmediately=False
#         )
#
#         # Create a FigureCanvas and embed it in the dialog
#         canvas = FigureCanvas(fig)
#         layout.addWidget(canvas)

        
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
        # Open the Motor Unit Properties dialog
        dialog = PlotEMGToolDialog(self.analysis_plot)
        dialog.exec_()
