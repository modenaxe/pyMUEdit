# core/utils/scaling_config.py

import os
import sys
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QGuiApplication
import ctypes
from ctypes import wintypes
import subprocess

def get_xft_scale():
    out = subprocess.check_output(['xrdb','-query']).decode()
    for line in out.splitlines():
        if line.startswith('Xft.dpi:'):
            dpi = float(line.split(':',1)[1].strip())
            return dpi/96.0
    return 1.0

# Get Windows Real Scale Factor
def get_windows_scale():
    shcore = ctypes.windll.shcore
    shcore.SetProcessDpiAwareness(2)
    
    user32 = ctypes.windll.user32
    MONITOR_DEFAULTTOPRIMARY = 1
    hmonitor = user32.MonitorFromWindow(user32.GetDesktopWindow(),
                                        MONITOR_DEFAULTTOPRIMARY)
    
    dpi_x = ctypes.c_uint()
    dpi_y = ctypes.c_uint()
    shcore.GetDpiForMonitor(hmonitor, 0,
                            ctypes.byref(dpi_x),
                            ctypes.byref(dpi_y))
    
    return dpi_x.value / 96.0


def get_adaptive_scale():
    if sys.platform.startswith("win"):
        scale = f"{get_windows_scale():.2f}"
    elif sys.platform.startswith("darwin"):
        # I don’t have a Mac, so skip that for now.
        scale = f"{1}"
    elif sys.platform.startswith("linux"):
        scale = f"{get_xft_scale()*0.8:.2f}"
    else:
        return "1"
    
    return scale


def apply_qt_scaling():
    """
    Apply high DPI scaling and fixed Qt screen scale factor
    based on screen resolution.
    """

    scale = get_adaptive_scale()
    print(scale)

    # Apply fixed scaling

    os.environ["QT_SCALE_FACTOR"] = f"{1/float(scale):.2f}"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = scale

    print(f"[INFO] Adaptive QT scale factor applied: {scale}")
