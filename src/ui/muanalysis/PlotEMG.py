from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout,
    QHBoxLayout, 
    QPushButton, 
    QLineEdit,
    QDialog,
    QMessageBox,
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.CleanTheme import CleanTheme
from ui.components.FileSidebar.FileButton import FileButton
from app.PlotEMGFunc import parse_channel_input, plot_emgsig
from app.FileUploadFunc import FileUploadFunc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class PlotEMGToolDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Plot EMG Tool")
        self.setMinimumWidth(550)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setStyleSheet(f"background-color: {CleanTheme.ANALYSIS_BG_CARD};")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title_label = QLabel("Plot EMG Tools")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        layout.addWidget(title_label)
        
        # Add input + button
        input_layout = QHBoxLayout()
        
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel Number (e.g. 1-3,5,7)")
        self.channel_input.setFont(QFont("Arial", 11))
        self.channel_input.setMinimumHeight(32)
        self.channel_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                background-color: #ffffff;
                color: #212529;
            }
        """)
        
        emgsig_btn = QPushButton("EMGsig")
        emgsig_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        emgsig_btn.setStyleSheet("""
            QPushButton {
                background-color: #343a40;
                color: #f8f9fa;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
        """)
        emgsig_btn.clicked.connect(self.handle_emgsig_clicked)
        
        input_layout.addWidget(emgsig_btn)
        input_layout.addWidget(self.channel_input)
        layout.addLayout(input_layout)

    def handle_emgsig_clicked(self):
        raw_text = self.channel_input.text()
        emgfile = FileUploadFunc.file

        if emgfile is None:
            QMessageBox.warning(self, "No File", "No EMG file is currently loaded.")
            return

        try:
            # Pass the raw text string directly to plot_emgsig for validation
            plot_emgsig(
                emgfile=emgfile,
                channels=raw_text,  # Pass as string for validation
                manual_offset=0,
                addrefsig=False,
                timeinseconds=True,
                figsize=[20, 15],
                tight_layout=True,
                showimmediately=False,
            )
            # Show the plot in a dialog
            dialog = EMGsigResultDialog(raw_text)
            dialog.exec_()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Invalid channel input: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error plotting EMG: {str(e)}")



class EMGsigResultDialog(QDialog):
    def __init__(self, channels, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EMG Signal Plot")
        self.channels = channels  # This is now the raw text string
        self.emgfile = FileUploadFunc.file
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        # Create the layout for the dialog
        layout = QVBoxLayout(self)

        # Get the figure from the plot_emgsig function
        fig = plot_emgsig(
            emgfile=self.emgfile,
            channels=self.channels,  # Pass the raw text string
            manual_offset=0,
            addrefsig=False,
            timeinseconds=True,
            figsize=[20, 15],
            tight_layout=True,
            showimmediately=False
        )

        # Create a FigureCanvas and embed it in the dialog
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
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

# general class for any buttons inside dialog
class PropertiesInnerDialogButton(QPushButton):
    def __init__(self, text):
        super().__init__(text )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #495057;
                color: #e9ecee;
                border: none;
                height: 40%;
                max-width: 100%;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #4a5672;
            }}
        """
        )


class PlotEMGButton(QWidget):
    """Button widget for opening Motor Unit Properties dialog"""
    
    mvc_updated = pyqtSignal(float)  # Signal emitted when MVC is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Subtitle
        subtitle_label = QLabel("PLOT EMG")
        subtitle_label.setObjectName("motorUnitAnalysisSubTitle")
        subtitle_label.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            margin: 0px;
            """
        )
        subtitle_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(subtitle_label)
        
        # Motor Unit Properties button
        plot_emg_btn = QPushButton("Plot EMG")
        plot_emg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        plot_emg_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {CleanTheme.ANALYSIS_BG_BUTTON};
                color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                height: 40px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
                color: {CleanTheme.ANALYSIS_BG_BUTTON};
            }}
        """
        )
        plot_emg_btn.clicked.connect(self.open_plot_emg_btn)
        layout.addWidget(plot_emg_btn)
        layout.setAlignment(plot_emg_btn, Qt.AlignmentFlag.AlignTop)
        
        
        
    def open_plot_emg_btn(self):
        # Open the Motor Unit Properties dialog
        dialog = PlotEMGToolDialog(self)
        dialog.exec_()

