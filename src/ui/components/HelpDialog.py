from .PlotDialog import PlotDialog

from ui.components.ImageSlider import ImageSlider

class HelpDialog(PlotDialog):
    def __init__(self, title="How to use"):
        super().__init__(title)
        #self.setWindowTitle("How to use")
        #self.setFixedSize(500, 500)
        #self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        # Layout
        # layout = QVBoxLayout()
        # layout.setContentsMargins(20, 20, 20, 20)
        # layout.setSpacing(15)

        window = ImageSlider()
        window.setMinimumSize(1200, 800)
        window.show()
        # layout.addWidget(window)

        self.set_canvas(window)

        self.exec_()






