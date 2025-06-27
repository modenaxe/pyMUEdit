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
from app.FileUploadFunc import FileUploadFunc

class MUPropertiesFunc:
    def __init__(self):
        # MVC value for calculations
        self.mvc_value = None

    # MVC value management
    def set_mvc(self, mvc_value):
        """Set the Maximum Voluntary Contraction value"""
        self.mvc_value = mvc_value


    def get_mvc(self):
        """Get the current MVC value"""
        return self.mvc_value.text()
    
    def convert(self, value):
      return str(value.text())
      
    def test(self, rec, start):
      if (len(self.convert(self.mvc_value)) == 0 or len(self.convert(rec)) == 0 or len(self.convert(start)) == 0):
        canvas = QMessageBox()
        canvas.setIcon(QMessageBox.Critical)
        canvas.setText("Error")
        canvas.setInformativeText('Missing Inputs')
        canvas.setWindowTitle("Error")
        canvas.exec_()
        return
      self.showselect(FileUploadFunc.file)

    
    def showselect(self,emgfile, how="ref_signal"):
      plt.close()
      data_to_plot = emgfile["REF_SIGNAL"][0]
      fig,ax = plt.subplots()
      ax.plot(data_to_plot)
      ax.set_xlabel("samples")
      ax.set_ylabel('Reference signal')
      ax.set_title('Click start and end range. Press q to save.')
      plt.show()
      coords = []
      while len(coords) < 2:
        pts = plt.ginput(1)
        coords.append(pts[0][0])
        ax.axvline(x=pts[0][0], color='r')
        plt.pause(0.05)

      points = [round(point) for point in coords]
      points.sort()
      
      print(points)

      return points
      


    # def calculate_mvc_based_statistics(self, force_data):
    #     """Calculate summary statistics based on MVC value"""
    #     if self.mvc_value is None:
    #         print("Warning: MVC value not set. Cannot calculate MVC-based statistics.")
    #         return None
        
    #     if force_data is None or len(force_data) == 0:
    #         print("Warning: No force data available for MVC-based calculations.")
    #         return None
        
    #     # Convert force data to percentage of MVC
    #     force_percentage = (force_data / self.mvc_value) * 100
        
    #     # Calculate summary statistics
    #     stats = {
    #         'mvc_value': self.mvc_value,
    #         'mean_force_percentage': np.mean(force_percentage),
    #         'max_force_percentage': np.max(force_percentage),
    #         'min_force_percentage': np.min(force_percentage),
    #         'std_force_percentage': np.std(force_percentage),
    #         'force_percentage_data': force_percentage
    #     }
        
    #     return stats
