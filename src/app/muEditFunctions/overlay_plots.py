"""
    overlay_plots module allows users to overlay two decomposed plot
    in the MUediting tab. It is aimed to visually validate the 
    correctness of pyMUEdit decomposition algorithms by 
    benchmarking it against MATLAB output. As such, this feature
    will remain only during the development and testing phase 
    of pyMUEdit. 

    Due to this feature being temporary, design decisions have
    been made to keep the feature separate and lightweight enough
    to be enventually removed when pyMUEdit is deployed.
"""

import os
from PyQt5.QtWidgets import QFileDialog
from app.muEditFunctions.importer import import_data
from core.logger import logger

def overlay_file_button_pushed(self, checked=True):
    """
    Overlays the current decomposition plot with 
    a MATLAB decomposition on top.
    """

    filepath, _ = QFileDialog.getOpenFileName(
        self, "Select file", "", "MAT Files (*.mat);;All Files (*.*)"
    )

    if not filepath:
        if hasattr(self, "overlay_switch"):
            self.overlay_switch.blockSignals(True)
            self.overlay_switch.setChecked(False)
            self.overlay_switch.blockSignals(False)
        return
    
    filename = os.path.basename(filepath)
    pathname = os.path.dirname(filepath)

    try:
        loader = MUeditOverlayLoader(filename, pathname)
        overlay_data = loader.load()
        self.overlay_data = overlay_data
    except Exception as e:
        logger.exception(f"Overlay import error: {e}")

    logger.debug("[Overlay] Overlay file loaded successfully")

    try:
        self.update_display_mus(pluse_train_color="#D95535")
        logger.debug("[Overlay] Overlay plots drawn successfully")
        self.show_tip(f"Overlay added: {filename}")
    except Exception as e:
        logger.exception(f"Overlay file error: {e}")


def clear_overlay_data(self):
    """
    Removes the overlay plots
    """
    
    # Rempves overlay data from MUeditManual class
    if hasattr(self, "overlay_data"):
        logger.debug("[Overlay] Cleared overlay_data attribute")
        del self.overlay_data

    # Clears overlay
    if hasattr(self, "spiketrain_plot"):
        self.spiketrain_plot.clear()

    if hasattr(self, "dr_plot"):
        self.dr_plot.clear()

    try:
        self.update_display_mus(pluse_train_color="#D95535")
        logger.debug(f"Overlay plot cleared. Reverting to base plot")
    except Exception as e:
        logger.exception(f"[Overlay] Failed to revert back to base plots")

class MUeditOverlayLoader:
    """
    A ligthweight class designed to import_data for the overlay
    It is meant to be kept separate from MUeditManual class
    """

    def __init__(self, filename, pathname):
        self.filename = filename
        self.pathname = pathname
        self.MUedition = None
        self.ish5 = False
        self.is_overlay = True 

    def load(self):        
        """
        Loads the the overlay using import data
        However, doesn't the UI setup logic
        """

        import_data(self)
        return self.MUedition
