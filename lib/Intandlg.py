import os
import numpy as np
import scipy.io as sio
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap, QPainter, QBrush
from PyQt5.QtWidgets import (
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


class Intandlg(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.initUI()

    def initUI(self):
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
        image_path = os.path.join(path_to_app, "Intan.jpg")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Image not found")
            image_label.setStyleSheet("color: white;")
        top_layout.addWidget(image_label)

        # Indicators and metrics
        indicators_widget = QWidget()
        indicators_layout = QHBoxLayout(indicators_widget)

        # Create lamps
        self.lamp_A1 = ColoredCircle("red")
        self.lamp_A2 = ColoredCircle("red")
        self.lamp_B1 = ColoredCircle("red")
        self.lamp_B2 = ColoredCircle("red")
        self.lamp_C1 = ColoredCircle("red")
        self.lamp_C2 = ColoredCircle("red")
        self.lamp_D1 = ColoredCircle("red")
        self.lamp_D2 = ColoredCircle("red")

        # Add lamps to layout
        indicators_layout.addWidget(self.lamp_A1)
        indicators_layout.addWidget(self.lamp_A2)
        indicators_layout.addWidget(self.lamp_B1)
        indicators_layout.addWidget(self.lamp_B2)
        indicators_layout.addWidget(self.lamp_C1)
        indicators_layout.addWidget(self.lamp_C2)
        indicators_layout.addWidget(self.lamp_D1)
        indicators_layout.addWidget(self.lamp_D2)

        # Add metrics
        channels_label = QLabel("Channels")
        channels_label.setStyleSheet("color: #f0f0f0; font-family: 'Poppins'; font-size: 10pt;")
        self.edit_field_nchan = QSpinBox()
        self.edit_field_nchan.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt; font-weight: bold;"
        )

        self.edit_field_Din = QSpinBox()
        self.edit_field_Din.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt; font-weight: bold;"
        )

        self.edit_field_Ain = QSpinBox()
        self.edit_field_Ain.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 10pt; font-weight: bold;"
        )

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(
            "color: #f0f0f0; background-color: #262626; font-family: 'Poppins'; font-size: 14pt; font-weight: bold;"
        )
        self.ok_button.clicked.connect(self.ok_button_pushed)

        # Add metrics to layout
        metrics_layout = QVBoxLayout()
        metrics_layout.addWidget(channels_label)
        metrics_layout.addWidget(self.edit_field_nchan)
        metrics_layout.addWidget(self.edit_field_Din)
        metrics_layout.addWidget(self.edit_field_Ain)
        metrics_layout.addWidget(self.ok_button)

        indicators_layout.addLayout(metrics_layout)
        top_layout.addWidget(indicators_widget)

        main_layout.addWidget(top_section)

        # Grid panels section
        grid_panels_layout = QHBoxLayout()

        # Create port panels
        self.port_A1_panel = self.create_port_panel("Port A1", "A1")
        self.port_B1_panel = self.create_port_panel("Port B1", "B1")
        self.port_C1_panel = self.create_port_panel("Port C1", "C1")
        self.port_D1_panel = self.create_port_panel("Port D1", "D1")

        # Add first row of panels
        grid_panels_layout.addWidget(self.port_A1_panel)
        grid_panels_layout.addWidget(self.port_B1_panel)
        grid_panels_layout.addWidget(self.port_C1_panel)
        grid_panels_layout.addWidget(self.port_D1_panel)

        main_layout.addLayout(grid_panels_layout)

        # Second row of panels
        grid_panels_layout2 = QHBoxLayout()

        # Create port panels
        self.port_A2_panel = self.create_port_panel("Port A2", "A2")
        self.port_B2_panel = self.create_port_panel("Port B2", "B2")
        self.port_C2_panel = self.create_port_panel("Port C2", "C2")
        self.port_D2_panel = self.create_port_panel("Port D2", "D2")

        # Add second row of panels
        grid_panels_layout2.addWidget(self.port_A2_panel)
        grid_panels_layout2.addWidget(self.port_B2_panel)
        grid_panels_layout2.addWidget(self.port_C2_panel)
        grid_panels_layout2.addWidget(self.port_D2_panel)

        main_layout.addLayout(grid_panels_layout2)

        # Checkboxes for each port
        checkboxes_layout = QHBoxLayout()

        # First row checkboxes
        self.checkbox_A1 = QCheckBox("")
        self.checkbox_A1.stateChanged.connect(lambda state: self.checkbox_A1_value_changed(state))

        self.checkbox_B1 = QCheckBox("")
        self.checkbox_B1.stateChanged.connect(lambda state: self.checkbox_B1_value_changed(state))

        self.checkbox_C1 = QCheckBox("")
        self.checkbox_C1.stateChanged.connect(lambda state: self.checkbox_C1_value_changed(state))

        self.checkbox_D1 = QCheckBox("")
        self.checkbox_D1.stateChanged.connect(lambda state: self.checkbox_D1_value_changed(state))

        # Second row checkboxes
        self.checkbox_A2 = QCheckBox("")
        self.checkbox_A2.stateChanged.connect(lambda state: self.checkbox_A2_value_changed(state))

        self.checkbox_B2 = QCheckBox("")
        self.checkbox_B2.stateChanged.connect(lambda state: self.checkbox_B2_value_changed(state))

        self.checkbox_C2 = QCheckBox("")
        self.checkbox_C2.stateChanged.connect(lambda state: self.checkbox_C2_value_changed(state))

        self.checkbox_D2 = QCheckBox("")
        self.checkbox_D2.stateChanged.connect(lambda state: self.checkbox_D2_value_changed(state))

        # Add checkboxes to layout
        checkboxes_layout1 = QHBoxLayout()
        checkboxes_layout1.addWidget(self.checkbox_A1)
        checkboxes_layout1.addWidget(self.checkbox_B1)
        checkboxes_layout1.addWidget(self.checkbox_C1)
        checkboxes_layout1.addWidget(self.checkbox_D1)

        checkboxes_layout2 = QHBoxLayout()
        checkboxes_layout2.addWidget(self.checkbox_A2)
        checkboxes_layout2.addWidget(self.checkbox_B2)
        checkboxes_layout2.addWidget(self.checkbox_C2)
        checkboxes_layout2.addWidget(self.checkbox_D2)

        # Pathname field (hidden)
        self.pathname = QLineEdit()
        self.pathname.setVisible(False)

        # Disable all port panels initially
        self.port_A1_panel.setEnabled(False)
        self.port_A2_panel.setEnabled(False)
        self.port_B1_panel.setEnabled(False)
        self.port_B2_panel.setEnabled(False)
        self.port_C1_panel.setEnabled(False)
        self.port_C2_panel.setEnabled(False)
        self.port_D1_panel.setEnabled(False)
        self.port_D2_panel.setEnabled(False)

    def create_port_panel(self, title, port_code):
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
        setattr(self, f"dropdown_{port_code}", dropdown)
        setattr(self, f"edit_field_{port_code}", edit_field)

        return panel

    def checkbox_A1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_A1.set_color("green")
            self.port_A1_panel.setEnabled(True)
        else:
            self.lamp_A1.set_color("red")
            self.port_A1_panel.setEnabled(False)

    def checkbox_A2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_A2.set_color("green")
            self.port_A2_panel.setEnabled(True)
        else:
            self.lamp_A2.set_color("red")
            self.port_A2_panel.setEnabled(False)

    def checkbox_B1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_B1.set_color("green")
            self.port_B1_panel.setEnabled(True)
        else:
            self.lamp_B1.set_color("red")
            self.port_B1_panel.setEnabled(False)

    def checkbox_B2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_B2.set_color("green")
            self.port_B2_panel.setEnabled(True)
        else:
            self.lamp_B2.set_color("red")
            self.port_B2_panel.setEnabled(False)

    def checkbox_C1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_C1.set_color("green")
            self.port_C1_panel.setEnabled(True)
        else:
            self.lamp_C1.set_color("red")
            self.port_C1_panel.setEnabled(False)

    def checkbox_C2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_C2.set_color("green")
            self.port_C2_panel.setEnabled(True)
        else:
            self.lamp_C2.set_color("red")
            self.port_C2_panel.setEnabled(False)

    def checkbox_D1_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_D1.set_color("green")
            self.port_D1_panel.setEnabled(True)
        else:
            self.lamp_D1.set_color("red")
            self.port_D1_panel.setEnabled(False)

    def checkbox_D2_value_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.lamp_D2.set_color("green")
            self.port_D2_panel.setEnabled(True)
        else:
            self.lamp_D2.set_color("red")
            self.port_D2_panel.setEnabled(False)

    def ok_button_pushed(self):
        try:
            # Load the file
            self.file = sio.loadmat(self.pathname.text())

            # Get the checkbox values
            ports = np.zeros(8)
            ports[0] = 1 if self.checkbox_A1.isChecked() else 0
            ports[1] = 1 if self.checkbox_A2.isChecked() else 0
            ports[2] = 1 if self.checkbox_B1.isChecked() else 0
            ports[3] = 1 if self.checkbox_B2.isChecked() else 0
            ports[4] = 1 if self.checkbox_C1.isChecked() else 0
            ports[5] = 1 if self.checkbox_C2.isChecked() else 0
            ports[6] = 1 if self.checkbox_D1.isChecked() else 0
            ports[7] = 1 if self.checkbox_D2.isChecked() else 0

            # Set the number of grids
            self.file["signal"]["ngrid"] = np.sum(ports)

            # Get the grid and muscle values
            grid = [""] * 8
            grid[0] = self.dropdown_A1.currentText()
            grid[1] = self.dropdown_A2.currentText()
            grid[2] = self.dropdown_B1.currentText()
            grid[3] = self.dropdown_B2.currentText()
            grid[4] = self.dropdown_C1.currentText()
            grid[5] = self.dropdown_C2.currentText()
            grid[6] = self.dropdown_D1.currentText()
            grid[7] = self.dropdown_D2.currentText()

            muscle = [""] * 8
            muscle[0] = self.edit_field_A1.text()
            muscle[1] = self.edit_field_A2.text()
            muscle[2] = self.edit_field_B1.text()
            muscle[3] = self.edit_field_B2.text()
            muscle[4] = self.edit_field_C1.text()
            muscle[5] = self.edit_field_C2.text()
            muscle[6] = self.edit_field_D1.text()
            muscle[7] = self.edit_field_D2.text()

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
