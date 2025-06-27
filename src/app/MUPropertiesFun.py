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
      # print()
    
    def showselect(self,emgfile, how="ref_signal", title="", titlesize=12, nclic=2):
      plt.close()
      if how == "ref_signal":
          data_to_plot = emgfile["REF_SIGNAL"][0]
          y_label = "Reference signal"
      elif how == "mean_emg":
          data_to_plot = emgfile["RAW_SIGNAL"].mean(axis=1)
          y_label = "Mean EMG signal"
      else:
          raise ValueError(
              "Wrong argument in showselect(). how can only be 'ref_signal' or "
              + f"'mean_emg'. {how} was passed instead."
          )

      fig,ax = plt.subplots()
      ax.plot(data_to_plot)
      ax.set_xlabel("samples")
      ax.set_ylabel(y_label)
      plt.show()
      # plt.figure()
      # plt.plot(data_to_plot)
      # plt.xlabel("Samples")
      # plt.ylabel(y_label)
      # plt.title(title, fontweight="bold", fontsize=titlesize)

      # ginput_res = plt.ginput(n=-1, timeout=0, mouse_add=False, show_clicks=True)

      # plt.close()

      # points = [round(point[0]) for point in ginput_res]
      # points.sort()

      # if nclic > 0 and nclic != len(points):
      #     raise ValueError("Wrong number of inputs, read the title")
      
      # print(points)

      # return points
      


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
