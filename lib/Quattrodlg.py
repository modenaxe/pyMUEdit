import os
import sys
import numpy as np
import scipy.io as sio
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QSpinBox,
    QFrame,
)


class ColoredCircle(QWidget):
    def __init__(self, color="red", parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(20, 20)
        self.setMaximumSize(20, 20)

    def paintEvent(self, event):
        import math
        from PyQt5.QtGui import QPainter, QBrush

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set the color
        if self.color == "red":
            brush = QBrush(QColor(255, 0, 0))
        elif self.color == "green":
            brush = QBrush(QColor(0, 255, 0))
        else:
            brush = QBrush(QColor(self.color))

        painter.setBrush(brush)
        painter.drawEllipse(0, 0, 20, 20)

    def set_color(self, color):
        self.color = color
        self.update()


class Quattrodlg(QMainWindow):
    """Python equivalent of MATLAB's Quattrodlg class"""

    def __init__(self):
        super().__init__()
        self.file = None  # File to update with the configuration
        self.initUI()

    def initUI(self):
        """Initialize the UI components"""
        self.setWindowTitle("Python App")
        self.setGeometry(100, 100, 550, 400)
        self.setStyleSheet("background-color: #262626;")

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Top section with image and indicators
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)

        # Image
        path_to_app = os.path.dirname(os.path.realpath(__file__))
        image_label = QLabel()
        image_path = os.path.join(path_to_app, "Quattrocento.jpg")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Image not found")
            image_label.setStyleSheet("color: white;")
        top_layout.addWidget(image_label)

        # Lamps
        self.lamp_S1 = ColoredCircle("red")
        self.lamp_S2 = ColoredCircle("red")
        self.lamp_M1 = ColoredCircle("red")
        self.lamp_M2 = ColoredCircle("red")
        self.lamp_M3 = ColoredCircle("red")
        self.lamp_M4 = ColoredCircle("red")

        # Channels count
        channels_label = QLabel("Channels")
        channels_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins'; font-size: 10pt;")
        self.edit_field_nchan = QSpinBox()
        self.edit_field_nchan.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt; font-weight: bold;"
        )

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 14pt; font-weight: bold;"
        )
        self.ok_button.clicked.connect(self.ok_button_pushed)

        # Add lamps and controls to top section
        lamps_layout = QHBoxLayout()
        lamps_layout.addWidget(self.lamp_S1)
        lamps_layout.addWidget(self.lamp_S2)
        lamps_layout.addWidget(self.lamp_M1)
        lamps_layout.addWidget(self.lamp_M2)
        lamps_layout.addWidget(self.lamp_M3)
        lamps_layout.addWidget(self.lamp_M4)

        controls_layout = QVBoxLayout()
        controls_layout.addWidget(channels_label)
        controls_layout.addWidget(self.edit_field_nchan)
        controls_layout.addWidget(self.ok_button)

        top_layout.addLayout(lamps_layout)
        top_layout.addLayout(controls_layout)

        main_layout.addWidget(top_section)

        # Create panels
        self.splitter1_panel = self.create_panel("Splitter #1", "S1")
        self.splitter2_panel = self.create_panel("Splitter #2", "S2")
        self.mi1_panel = self.create_panel("MI #1", "M1")
        self.mi2_panel = self.create_panel("MI #2", "M2")
        self.mi3_panel = self.create_panel("MI #3", "M3")
        self.mi4_panel = self.create_panel("MI #4", "M4")

        # Add panels to layout
        top_row = QHBoxLayout()
        top_row.addWidget(self.splitter1_panel)
        top_row.addWidget(self.splitter2_panel)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.mi1_panel)
        bottom_row.addWidget(self.mi2_panel)
        bottom_row.addWidget(self.mi3_panel)
        bottom_row.addWidget(self.mi4_panel)

        main_layout.addLayout(top_row)
        main_layout.addLayout(bottom_row)

        # Create checkboxes
        self.checkbox_S1 = QCheckBox("")
        self.checkbox_S1.stateChanged.connect(lambda state: self.checkbox_S1_value_changed(state))

        self.checkbox_S2 = QCheckBox("")
        self.checkbox_S2.stateChanged.connect(lambda state: self.checkbox_S2_value_changed(state))

        self.checkbox_M1 = QCheckBox("")
        self.checkbox_M1.stateChanged.connect(lambda state: self.checkbox_M1_value_changed(state))

        self.checkbox_M2 = QCheckBox("")
        self.checkbox_M2.stateChanged.connect(lambda state: self.checkbox_M2_value_changed(state))

        self.checkbox_M3 = QCheckBox("")
        self.checkbox_M3.stateChanged.connect(lambda state: self.checkbox_M3_value_changed(state))

        self.checkbox_M4 = QCheckBox("")
        self.checkbox_M4.stateChanged.connect(lambda state: self.checkbox_M4_value_changed(state))

        # Add checkboxes to panels
        self.splitter1_panel.layout().addWidget(self.checkbox_S1)  # type: ignore
        self.splitter2_panel.layout().addWidget(self.checkbox_S2)  # type: ignore
        self.mi1_panel.layout().addWidget(self.checkbox_M1)  # type: ignore
        self.mi2_panel.layout().addWidget(self.checkbox_M2)  # type: ignore
        self.mi3_panel.layout().addWidget(self.checkbox_M3)  # type: ignore
        self.mi4_panel.layout().addWidget(self.checkbox_M4)  # type: ignore

        # Pathname field (hidden)
        self.pathname = QLineEdit()
        self.pathname.setVisible(False)
        main_layout.addWidget(self.pathname)

        # Disable all panels initially
        self.splitter1_panel.setEnabled(False)
        self.splitter2_panel.setEnabled(False)
        self.mi1_panel.setEnabled(False)
        self.mi2_panel.setEnabled(False)
        self.mi3_panel.setEnabled(False)
        self.mi4_panel.setEnabled(False)

    def create_panel(self, title, code):
        """Create a panel for a port with dropdown and text field"""
        panel = QGroupBox(title)
        panel.setStyleSheet("QGroupBox { color: #f0f0f0; font-family: 'Poppins'; font-size: 14pt; font-weight: bold; }")
        layout = QVBoxLayout(panel)

        # Array type label
        array_type_label = QLabel("Array type")
        array_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        array_type_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        layout.addWidget(array_type_label)

        # Dropdown for array type
        dropdown = QComboBox()
        dropdown.addItems(
            [
                "GR04MM1305",
                "GR08MM1305",
                "GR10MM0808",
                "HD04MM1305",
                "HD08MM1305",
                "HD10MM0808",
                "GR10MM0804",
                "HD10MM0804",
                "MYOMRF-4x8",
                "MYOMNP-1x32",
            ]
        )
        dropdown.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt;")
        layout.addWidget(dropdown)

        # Muscle name label
        muscle_name_label = QLabel("Muscle name")
        muscle_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        muscle_name_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins';")
        layout.addWidget(muscle_name_label)

        # Text field for muscle name
        edit_field = QLineEdit()
        edit_field.setStyleSheet("color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt;")
        layout.addWidget(edit_field)

        # Store references to components
        setattr(self, f"dropdown_{code}", dropdown)
        setattr(self, f"edit_field_{code}", edit_field)

        return panel

    def checkbox_S1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_S1.set_color("green")
            self.splitter1_panel.setEnabled(True)
        else:
            self.lamp_S1.set_color("red")
            self.splitter1_panel.setEnabled(False)

    def checkbox_S2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_S2.set_color("green")
            self.splitter2_panel.setEnabled(True)
        else:
            self.lamp_S2.set_color("red")
            self.splitter2_panel.setEnabled(False)

    def checkbox_M1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_M1.set_color("green")
            self.mi1_panel.setEnabled(True)
        else:
            self.lamp_M1.set_color("red")
            self.mi1_panel.setEnabled(False)

    def checkbox_M2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_M2.set_color("green")
            self.mi2_panel.setEnabled(True)
        else:
            self.lamp_M2.set_color("red")
            self.mi2_panel.setEnabled(False)

    def checkbox_M3_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_M3.set_color("green")
            self.mi3_panel.setEnabled(True)
        else:
            self.lamp_M3.set_color("red")
            self.mi3_panel.setEnabled(False)

    def checkbox_M4_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_M4.set_color("green")
            self.mi4_panel.setEnabled(True)
        else:
            self.lamp_M4.set_color("red")
            self.mi4_panel.setEnabled(False)

    def ok_button_pushed(self):
        try:
            # Load the file
            self.file = sio.loadmat(self.pathname.text())

            # Get the checkbox values
            ports = np.zeros(6)
            ports[0] = 1 if self.checkbox_S1.isChecked() else 0
            ports[1] = 1 if self.checkbox_S2.isChecked() else 0
            ports[2] = 1 if self.checkbox_M1.isChecked() else 0
            ports[3] = 1 if self.checkbox_M2.isChecked() else 0
            ports[4] = 1 if self.checkbox_M3.isChecked() else 0
            ports[5] = 1 if self.checkbox_M4.isChecked() else 0

            # Set the number of grids
            self.file["signal"]["ngrid"] = np.sum(ports)

            # Get the grid and muscle values
            grid = [""] * 6
            grid[0] = self.dropdown_S1.currentText()
            grid[1] = self.dropdown_S2.currentText()
            grid[2] = self.dropdown_M1.currentText()
            grid[3] = self.dropdown_M2.currentText()
            grid[4] = self.dropdown_M3.currentText()
            grid[5] = self.dropdown_M4.currentText()

            muscle = [""] * 6
            muscle[0] = self.edit_field_S1.text()
            muscle[1] = self.edit_field_S2.text()
            muscle[2] = self.edit_field_M1.text()
            muscle[3] = self.edit_field_M2.text()
            muscle[4] = self.edit_field_M3.text()
            muscle[5] = self.edit_field_M4.text()

            # Find the indices of the selected ports
            idxports = np.where(ports == 1)[0]

            # Update the gridname and muscle for each selected port
            for i in range(int(self.file["signal"]["ngrid"][0, 0])):
                self.file["signal"]["gridname"][0, 0][0, i] = grid[idxports[i]]
                self.file["signal"]["muscle"][0, 0][0, i] = muscle[idxports[i]]

            # Save the updated file
            signal = self.file["signal"]
            sio.savemat(self.pathname.text(), {"signal": signal}, appendmat=False, do_compression=True, format="7.3")

            # Close the window
            self.close()

        except Exception as e:
            print(f"Error in OK button handler: {e}")
