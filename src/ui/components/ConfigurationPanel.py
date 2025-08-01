import os

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QCheckBox, QScrollArea
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, QRectF

from ui.components.ActionButton import ActionButton
from ui.components.CleanCard import CleanCard
from ui.components.CleanScrollBar import CleanScrollBar
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from ui.components.FormInput import FormInput
from ui.components.FormSpinBox import FormSpinBox

class InputPanel(CollapsiblePanel):
    def __init__(self, title, gridname, musclename, checkbox_callback, parent=None):
        self.checkbox = QCheckBox()
        # connect the state change of the checkbox to the lamp colour change functionality
        self.checkbox.stateChanged.connect(lambda state: checkbox_callback(title, state))
        super().__init__(title, checkbox=self.checkbox, parent=parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        gridnames = ["GR04MM1305", "ELSCH064NM2", "GR08MM1305", "GR10MM0808", "Thin film", "4-wire needle", "Myomatrix Monopolar", "other"]
        self.gridname_dropdown = FormDropdown("Array Type", gridnames)
        self.gridname_dropdown.dropdown.setCurrentIndex(gridnames.index(gridname))
        self.add_widget(self.gridname_dropdown)

        self.muscle_input = FormInput("Muscle Name")
        self.muscle_input.input.setText(musclename)
        self.add_widget(self.muscle_input)

    # disable the Input Panel (but not the checkbox to make it still interactable)
    def disable_panel(self):
        for child in self.content_widget.findChildren(QWidget):
            child.setEnabled(False)

class QuattrocentoVisualisation(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.pixmap = self.pixmap.scaled(700, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(self.pixmap)
        self.setFixedSize(self.pixmap.size())
        self.setScaledContents(True)

        self.lamps = {}

    def add_lamp(self, name, rect, colour):
        # Add a new lamp box to the quattrocento image
        self.lamps[name] = [rect, colour]

    def update_lamp_colour(self, name, new_colour):
        # Change the colour of the specific lamp box (by index)
        if name in self.lamps:
            self.lamps[name][1] = new_colour
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create all of the lamp boxes (overlaid on top of quattrocento image)
        for lamp in self.lamps.values():
            painter.setBrush(lamp[1])
            painter.setPen(QPen(lamp[1].darker(150), 2))
            painter.drawRoundedRect(lamp[0], 10, 10)

        painter.end()

class ConfigurationPanel(QWidget):
    def __init__(self, emg_obj, parent=None):
        super().__init__(parent)

        self.emg_obj = emg_obj
        self.data = emg_obj["data"]

        self.setMinimumSize(1200, 700)

        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Add title
        page_title = QLabel("Set Configuration")
        page_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        page_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        main_layout.addWidget(page_title)

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(200)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # signal range dropdown panel
        self.splitter1 = InputPanel("Splitter #1", "GR04MM1305", "", self.checkbox_state_change)
        self.splitter1.disable_panel()
        self.splitter2 = InputPanel("Splitter #2", "GR04MM1305", "", self.checkbox_state_change)
        self.splitter2.disable_panel()
        left_layout.addWidget(self.splitter1)
        left_layout.addWidget(self.splitter2)

        left_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.doneClicked)
        left_layout.addWidget(done_button)

        # middle panel
        middle_container = CleanCard()
        middle_container.layout.setSpacing(50)

        # add title
        page_title = QLabel("Quattrocento Visualisation")
        page_title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        page_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle_container.layout.addWidget(page_title)

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Quattrocento.jpg")
        if not os.path.exists(image_path):
            raise FileExistsError("Quattrocento diagram not found")

        # create the quattrocento visualisation
        self.quattrocento_label = QuattrocentoVisualisation(image_path)
        # Create lamps for splitters 1 and 2
        self.quattrocento_label.add_lamp("Splitter #1",
                                         QRectF(22, 75, 315, 65), QColor(255, 0, 0, 100))
        self.quattrocento_label.add_lamp("Splitter #2",
                                         QRectF(365, 75, 315, 65), QColor(255, 0, 0, 100))

        # Create lamps for mixed inputs 1-4
        self.quattrocento_label.add_lamp("Multiple Inputs #1",
                                         QRectF(14, 243, 155, 40), QColor(255, 0, 0, 100))
        self.quattrocento_label.add_lamp("Multiple Inputs #2",
                                         QRectF(183, 243, 155, 40), QColor(255, 0, 0, 100))
        self.quattrocento_label.add_lamp("Multiple Inputs #3",
                                         QRectF(351, 243, 155, 40), QColor(255, 0, 0, 100))
        self.quattrocento_label.add_lamp("Multiple Inputs #4",
                                         QRectF(520, 243, 155, 40), QColor(255, 0, 0, 100))
        middle_container.layout.addWidget(self.quattrocento_label)

        # add number of channels input box
        num_channels_input_box = FormSpinBox("Number of Channels", 1, 1, 500)
        num_channels_input_box.spinbox.setValue(self.data.shape[0])
        middle_container.layout.addWidget(num_channels_input_box)

        middle_container.layout.addStretch()

        # right panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(200)
        CleanScrollBar.apply(scroll_area)
        right_container = QWidget()
        right_container.setMinimumWidth(200)
        right_container.setContentsMargins(0, 0, 15, 0)

        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        self.mul_input_1 = InputPanel("Multiple Inputs #1", "GR04MM1305", "",
                                      self.checkbox_state_change)
        self.mul_input_1.disable_panel()
        self.mul_input_2 = InputPanel("Multiple Inputs #2", "GR04MM1305", "",
                                      self.checkbox_state_change)
        self.mul_input_2.disable_panel()
        self.mul_input_3 = InputPanel("Multiple Inputs #3", "GR04MM1305", "",
                                      self.checkbox_state_change)
        self.mul_input_3.disable_panel()
        self.mul_input_4 = InputPanel("Multiple Inputs #4", "GR04MM1305", "",
                                      self.checkbox_state_change)
        self.mul_input_4.disable_panel()
        right_layout.addWidget(self.mul_input_1)
        right_layout.addWidget(self.mul_input_2)
        right_layout.addWidget(self.mul_input_3)
        right_layout.addWidget(self.mul_input_4)

        right_layout.addStretch()
        scroll_area.setWidget(right_container)

        # combine panels in layout
        content_layout = QHBoxLayout()
        content_layout.addWidget(left_container, stretch=0)
        content_layout.addWidget(middle_container, stretch=1)
        content_layout.addWidget(scroll_area, stretch=0)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.resize(1024, 600)

    def checkbox_state_change(self, name, state):
        if state == Qt.Checked:
            # When checked, lamp will green
            new_colour = QColor(0, 255, 0, 100)
        else:
            # When unchecked, lamp will red
            new_colour = QColor(255, 0, 0, 100)

        self.quattrocento_label.update_lamp_colour(name, new_colour)

    def doneClicked(self):
        # TODO: set configuration in emg_obj
        self.close()
