import pandas as pd
import time

# singleton object that stores all calculated historical tabulated results within the current instance of the application
# fields:
# - title of table
# - timestamp
# - table as 2d arry

class AnalysisResultsHist():
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.df = pd.DataFrame()
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
        print(f"new row: {row}")
        self.df = pd.concat([self.df, row])
        
    def get_analysis_hist(self):
        return self.df
    
    def get_lastest_data(self):
        if self.df.empty:
            return {} 
        return self.df.iloc[-1]
    
    def is_empty(self):
        return self.df.empty