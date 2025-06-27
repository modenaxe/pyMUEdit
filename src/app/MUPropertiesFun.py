import sys
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
)
from scipy.io import loadmat
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import warnings
import os
import copy
import itertools
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# This class holds all the functions used for file uploading
class MUPropertiesFunc:
    def __init__(self):
        # MVC value for calculations
        self.mvc_value = None

    # MVC value management
    def set_mvc(self, mvc_value):
        """Set the Maximum Voluntary Contraction value"""
        self.mvc_value = mvc_value
        print(f"MVC set to: {mvc_value} N")

    def get_mvc(self):
        """Get the current MVC value"""
        return self.mvc_value

    def calculate_mvc_based_statistics(self, force_data):
        """Calculate summary statistics based on MVC value"""
        if self.mvc_value is None:
            print("Warning: MVC value not set. Cannot calculate MVC-based statistics.")
            return None
        
        if force_data is None or len(force_data) == 0:
            print("Warning: No force data available for MVC-based calculations.")
            return None
        
        # Convert force data to percentage of MVC
        force_percentage = (force_data / self.mvc_value) * 100
        
        # Calculate summary statistics
        stats = {
            'mvc_value': self.mvc_value,
            'mean_force_percentage': np.mean(force_percentage),
            'max_force_percentage': np.max(force_percentage),
            'min_force_percentage': np.min(force_percentage),
            'std_force_percentage': np.std(force_percentage),
            'force_percentage_data': force_percentage
        }
        
        return stats
