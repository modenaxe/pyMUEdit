from .PlotDialog import PlotDialog

from ui.components.ImageSlider import ImageSlider

class HelpDialog(PlotDialog):
    def __init__(self, title="How to use"):
        super().__init__(title)
        if hasattr(self, "min_btn"):
            self.min_btn.hide()
        if hasattr(self, "save_btn"): 
            self.save_btn.hide()

        window = ImageSlider()
        window.setMinimumSize(1200, 800)
        window.show()

        self.set_canvas(window)
        self.exec_()