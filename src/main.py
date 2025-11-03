import sys
import os
from PyQt5.QtGui import QIcon

# Fix matplotlib backend BEFORE importing any other modules
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend to match PyQt5

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.ImportDataWindow import ImportDataWindow
from PyQt5.QtWidgets import QApplication
from core.utils.config.scaling_config import apply_qt_scaling # Added for high DPI scaling attributes
from core.database.database import init_db


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

    # set application icon
    app.setWindowIcon(QIcon("assets/pyMUEdit-icon.png"))

    # Create and show the main window
    window = ImportDataWindow()
    window.show()

    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
