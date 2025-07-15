import pandas as pd
import time
import random
from PyQt5.QtCore import QObject, pyqtSignal

# singleton object that stores all calculated historical tabulated results within the current instance of the application
# fields:
# - title of table
# - timestamp
# - table as 2d arry

class AnalysisResultsHist(QObject):
    _instance = None
    data_changed = pyqtSignal(object)
    data_cleared = pyqtSignal()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.df = pd.DataFrame()
            QObject.__init__(cls._instance)
        return cls._instance
        
    def set_analysis_hist(self, df):
        self.df = df
        
    def append_analysis_hist(self, title, table):
        timestamp = time.time()
        row = pd.DataFrame([{
            'title': title,
            'timestamp': timestamp,
            'table': table
        }])
        self.df = pd.concat([self.df, row])
        self.data_changed.emit(self.df)
        
    def get_analysis_hist(self):
        return self.df
    
    def get_lastest_data(self):
        if self.df.empty:
            return {} 
        return self.df.iloc[-1]
    
    def is_empty(self):
        return self.df.empty
    
    def clear_results(self):
        self.df = pd.DataFrame()
        self.data_cleared.emit()
    
    
store = AnalysisResultsHist()