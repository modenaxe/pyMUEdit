from PyQt5.QtCore import QAbstractTableModel, Qt
from core.muAnalysisCore.AnalysisResultsHist import store

class ResultsTable(QAbstractTableModel):

    """Actual data handling within tables that are displayed in results section"""

    def __init__(self):
        super().__init__()
        
        store.data_changed.connect(self.update_dataframe)
        store.data_cleared.connect(self.clear_results)

        self._data = [] # list of dictionaries 
        self.columns = [] 


    def _updateData(self, df):
        if df.empty:
            self.df = df
            self._data = []
            self.columns = []
        else:
            self.df = df
            self._data = self.df.iloc[-1]['table']    
            self.columns = list(self._data[0].keys())    
    
    def rowCount(self, parent=None):
        return len(self._data)
    
    def columnCount(self, parent=None):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            key = self.columns[col]
            return self._data[row][key]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]
        return super().headerData(section, orientation, role)
        
    def update_dataframe(self, new_df):
        # Notify the view that the model is about to change
        self.beginResetModel()
        self._updateData(new_df)
        self.endResetModel()    
        
    def select_result(self, index):
        if index < len(self.df):
            self.beginResetModel()
            self._data = self.df.iloc[index]['table']
            self.columns = list(self._data[0].keys()) 
            print(self.columns)
            self.endResetModel() 
    
    def get_cur_results(self):
        return self._data
    
    def clear_results(self):
        self.update_dataframe(store.get_analysis_hist())