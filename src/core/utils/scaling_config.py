# core/utils/scaling_config.py

import os
import sys
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QGuiApplication

def get_adaptive_scale():
    screen = QGuiApplication.primaryScreen()

    # geometry = logical size
    geometry = screen.geometry()
    logical_width = geometry.width()
    logical_height = geometry.height()

    # devicePixelRatio = scale factor from system (e.g. 1.5 for 150%)
    scale_factor = screen.devicePixelRatio()

    # approximate physical resolution
    physical_width = int(logical_width * scale_factor)
    physical_height = int(logical_height * scale_factor)
    
    if sys.platform == 'darwin':
        return "1"

    # use physical resolution to decide scaling
    if physical_width >= 2560:
        return "1.25"
    elif physical_width >= 1920:
        return "1"
    else:
        return "1"


def apply_qt_scaling():
    """
    Apply high DPI scaling and fixed Qt screen scale factor
    based on screen resolution.
    """
    # Enable high DPI support before QApplication is created
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # Temporary QApplication just to access screen info
    temp_app = QGuiApplication(sys.argv)
    scale = get_adaptive_scale()
    temp_app.quit()

    # Apply fixed scaling
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = scale

    print(f"[INFO] Adaptive QT scale factor applied: {scale}")
