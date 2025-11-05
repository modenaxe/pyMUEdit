from PyQt5.QtWidgets import QHBoxLayout

from ui.components.muAnalysisComponents.AnalysisDropdownDialog import \
    AnalysisDropdownDialog
from ui.components import ActionButton


class ComputeThresholdSection(QHBoxLayout):
    """
    UI layout container that holds input widgets for computing thresholds.

    This horizontal box layout includes:
    - An event type dropdown menu (options: 'rt', 'dert', 'rt_dert')
    - A threshold type dropdown menu (options: 'abs', 'rel', 'abs_rel')
    - A button to trigger threshold computation using the provided function

    When the button is clicked, it calls the `compute_thresh` method of the
    given `func` object, passing the currently selected event and type.

    Args:
        func: An object that implements a `compute_thresh(event, type)` method.
    """

    def __init__(self, func):
        super().__init__()
        event_ = AnalysisDropdownDialog(
            "Event", items=['rt', 'dert', 'rt_dert'])
        event_.setCurrentIndex(0)
        type_ = AnalysisDropdownDialog("Type", items=['abs', 'rel', 'abs_rel'])
        type_.setCurrentIndex(0)
        button = ActionButton("Compute Thresholds")
        button.clicked.connect(
            lambda: func.compute_thresh(
                event_.currentText(), type_.currentText())
        )
        button.setMinimumHeight(40)

        self.addWidget(button)
        self.addWidget(event_)
        self.addWidget(type_)
