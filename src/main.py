import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.HDEMGDashboard import HDEMGDashboard
from PyQt5.QtWidgets import QApplication
from core.utils.scaling_config import apply_qt_scaling # Added for high DPI scaling attributes


import warnings
warnings.filterwarnings("ignore") #ignore warning


def main():
    """
    Main function to launch the HDEMG Dashboard application.
    """
    # Configure DPI scaling settings to prevent UI distortion under high-resolution displays || Modified by alex
    apply_qt_scaling()
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("HDEMG Analysis Tool")
    app.setOrganizationName("EMG Lab")

    # Create and show the main window
    window = HDEMGDashboard()
    window.show()

    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
