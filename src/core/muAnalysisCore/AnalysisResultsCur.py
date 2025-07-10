import pandas as pd

# singleton object that stores the data associated with the current signal
# gets reset when new file is uploaded
class AnalysisResultsCur():
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.df = pd.DataFrame()
            return cls._instance
        
    def set_analysis_cur(self, df):
        self.df = df
        
    def get_analysis_cur(self):
        return self.df