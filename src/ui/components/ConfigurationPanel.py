from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QCheckBox, QScrollArea
from PyQt5.QtGui import QFont

from ui.components.ActionButton import ActionButton
from ui.components.CleanCard import CleanCard
from ui.components.CleanScrollBar import CleanScrollBar
from ui.components.CleanTheme import CleanTheme
from ui.components.CollapsiblePanel import CollapsiblePanel
from ui.components.FormDropdown import FormDropdown
from ui.components.FormInput import FormInput

class InputPanel(CollapsiblePanel):
    def __init__(self, title, gridname, musclename, parent=None):
        checkbox = QCheckBox()
        super().__init__(title, checkbox=checkbox, parent=parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        gridnames = ["GR04MM1305", "ELSCH064NM2", "GR08MM1305", "GR10MM0808", "Thin film", "4-wire needle", "Myomatrix Monopolar", "other"]
        self.gridname_dropdown = FormDropdown("Array Type", gridnames)
        self.gridname_dropdown.dropdown.setCurrentIndex(gridnames.index(gridname))
        self.add_widget(self.gridname_dropdown)

        self.muscle_input = FormInput("Muscle Name")
        self.muscle_input.input.setText(musclename)
        self.add_widget(self.muscle_input)

class ConfigurationPanel(QWidget):
    def __init__(self, emg_obj, parent=None):
        super().__init__(parent)

        self.emg_obj = emg_obj

        self.setMinimumSize(1024, 600)

        # Setup main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # left panel
        left_container = QWidget()
        left_container.setMinimumWidth(250)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # signal range dropdown panel
        left_layout.addWidget(InputPanel("Splitter #1", "GR04MM1305", ""))
        left_layout.addWidget(InputPanel("Splitter #2", "GR04MM1305", ""))

        left_layout.addStretch()

        # done button
        done_button = ActionButton("Done", primary=True)
        done_button.clicked.connect(self.doneClicked)
        left_layout.addWidget(done_button)

        # middle panel
        middle_container = CleanCard()

        middle_layout = QVBoxLayout(middle_container)
        middle_layout.setSpacing(15)

        # Add title
        page_title = QLabel("Channel Viewer")
        page_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        page_title.setStyleSheet(f"color: {CleanTheme.TEXT_PRIMARY};")
        middle_layout.addWidget(page_title)

        middle_layout.addStretch()

        # right panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(250)
        CleanScrollBar.apply(scroll_area)
        right_container = QWidget()
        right_container.setMinimumWidth(250)
        right_container.setContentsMargins(0, 0, 15, 0)

        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        right_layout.addWidget(InputPanel("Multiple Inputs #1", "GR04MM1305", "Tibialis Anterior"))
        right_layout.addWidget(InputPanel("Multiple Inputs #2", "GR04MM1305", "Tibialis Anterior"))
        right_layout.addWidget(InputPanel("Multiple Inputs #3", "GR04MM1305", ""))
        right_layout.addWidget(InputPanel("Multiple Inputs #4", "GR04MM1305", ""))

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

    def doneClicked(self):
        # TODO: set configuration in emg_obj
        return
