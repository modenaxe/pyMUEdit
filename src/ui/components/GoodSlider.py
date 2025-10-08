from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QSlider, QStyle,
                             QStyleOptionSlider, QWidget)


class GoodSlider(QWidget):
    """A styled horizontal slider with a value label display"""

    def __init__(self,
                 orientation=Qt.Horizontal,
                 minimum=0,
                 maximum=100,
                 default=50,
                 display_value=True,
                 on_value_changed=None,
                 parent=None):
        """
        Initialize a GoodSlider

        Args:
            orientation (Qt.Orientation): Slider direction (horizontal or vertical)
            minimum (int): Minimum slider value
            maximum (int): Maximum slider value
            default (int): Initial slider value
            display_value (bool): Display slider value
            on_value_changed (Callable[[int]], optional): Callback function when value changes
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.callback = on_value_changed
        self.display_value = not display_value
        self._init_ui(orientation, minimum, maximum, default)

    def _init_ui(self, orientation, minimum, maximum, default):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(2)

        class NewSlider(QSlider):
            def keyPressEvent(self, event):
                if event.key():
                    event.ignore()

        self.slider = NewSlider(orientation)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setValue(default)
        self.slider.setSingleStep(1)
        self.slider.setFixedHeight(40)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.setStyleSheet("""
            QWidget {
                border: None
            }
        """)
        self.slider.setStyleSheet("""
            QSlider {
                min-height: 30px;
                padding: 0 2px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                margin: 0 -3px;
            }
            QSlider::sub-page:horizontal {
                background: #007bff;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #e0e0e0;
                border-radius: 4px;
                margin: 0 -3px;
            }
            QSlider::handle:horizontal {
                width: 28px;
                height: 28px;
                margin: -10px 0;
                border-radius: 14px;
                background: qradialgradient(
                    cx:0.5, cy:0.5,
                    fx:0.5, fy:0.5,
                    radius:0.5,
                    stop:0.8 white,
                    stop:0.81 rgba(96,96,96,70),
                    stop:1   rgba(255,255,255,0)
                );
            }
            QSlider::handle:horizontal:hover {
                border-color: #0056b3;
            }
        """)

        layout.addWidget(self.slider)
        self.value_label = QLabel(f"{default}", self)
        self.value_label.setStyleSheet("""
            color: #000;
            font-size: 20px;
        """)
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.value_label, alignment=Qt.AlignVCenter)
        self.value_label.setHidden(self.display_value)

        self.setLayout(layout)

    def _on_value_changed(self, val):
        self.value_label.setText(f"{val}")

        if callable(self.callback):
            self.callback(val)

    def set_slider_value(self, val):
        self.slider.setValue(val)

    def get_slider_value(self):
        return self.slider.value()

    def slider_increase(self):
        self.slider.setValue(self.slider.value() + 1)

    def slider_decrease(self):
        self.slider.setValue(self.slider.value() - 1)

    # show or hide the slider value
    def display_value(self, display_value):
        self.value_label.setHidden(not display_value)
