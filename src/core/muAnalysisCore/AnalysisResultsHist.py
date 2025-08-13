import pandas as pd
import time
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import numbers 

class AnalysisResultsHist(QObject):
    """
    Singleton object that stores all calculated historical tabulated results
    within the current instance of the application.

    Attributes:
        df (pd.DataFrame): Stores historical analysis results with columns:
            - 'title': title of the result set
            - 'timestamp': time the result was stored
            - 'table': the actual 2D array (list of dicts) containing the results
        data_changed (pyqtSignal): Emitted whenever new data is added
        data_cleared (pyqtSignal): Emitted whenever all data is cleared
    """
    
    _instance = None
    data_changed = pyqtSignal(object)  # signal that passes the updated DataFrame
    data_cleared = pyqtSignal()        # signal emitted when data is cleared
    
    def __new__(cls):
        """
        Ensure that only one instance of AnalysisResultsHist exists (singleton pattern).
        If no instance exists, create one with an empty DataFrame.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.df = pd.DataFrame()
            QObject.__init__(cls._instance)
        return cls._instance
        
    def set_analysis_hist(self, df):
        """
        Replace the stored analysis history with a new DataFrame.

        Args:
            df (pd.DataFrame): New DataFrame to store.
        """
        self.df = df
        
    def append_analysis_hist(self, title, table):
        """
        Add a new analysis result entry to the history.

        Args:
            title (str): Title of the analysis result.
            table (list[dict]): 2D array (list of dicts) of results to store.
        """
        timestamp = time.time()
        table = self.data_clean(table)
        
        row = pd.DataFrame([{
            'title': title,
            'timestamp': timestamp,
            'table': table
        }])
        self.df = pd.concat([self.df, row])
        # Emit signal to notify listeners that the data has changed
        self.data_changed.emit(self.df)
        
    def get_analysis_hist(self):
        """
        Retrieve the full DataFrame of historical results.
        """
        return self.df
    
    def get_lastest_data(self):
        """
        Retrieve the most recently added analysis result.
        Returns:
            dict or pd.Series: Latest result row, or empty dict if no data exists.
        """
        if self.df.empty:
            return {} 
        return self.df.iloc[-1]
    
    def is_empty(self):
        """
        Check if there are any stored results.
        Returns:
            bool: True if no data exists, otherwise False.
        """
        return self.df.empty
    
    def clear_results(self):
        """
        Remove all stored results and emit the data_cleared signal.
        """
        self.df = pd.DataFrame()
        self.data_cleared.emit()
        
    def data_clean(self, table):
        """
        Clean up the input result table:
            - Replace NaN numeric values with empty strings
            - Round float values to 2 decimal places
            - Convert all non-numeric values to strings

        Args:
            table (list[dict]): The table data to clean.

        Returns:
            list[dict]: Cleaned table data.
        """
        for row in range(0, len(table)):
            keys = list(table[row].keys())
            for key in keys:
                if isinstance(table[row][key], numbers.Number):
                    if np.isnan(table[row][key]):
                        table[row][key] = ""
                
                    if isinstance(table[row][key], float):
                        table[row][key] = round(table[row][key], 2)
                else:
                    # Ensure non-numeric values are strings so they can be displayed by the QAbstractTableModel
                    table[row][key] = str(table[row][key])        
        return table

# Singleton instance for global use
store = AnalysisResultsHist()