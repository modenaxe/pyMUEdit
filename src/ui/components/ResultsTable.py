import pandas as pd
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt

class ResultsTable(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        if df.empty:
            print('hi1')
            self.df = df
            self._data = []
            self.columns = []
        else:
            print('bye1')
            self.df = df
            self._data = self.df.loc[-1, 'table']         
            self.columns = list(self._data[0].keys())   

    def _updateData(self, df):
        if df.empty:
            print('hi2')
            self.df = df
            self._data = []
            self.columns = []
        else:
            print('bye2')
            self.df = df
            self._data = self.df.iloc[-1]['table']    
            self.columns = list(self._data[0].keys())    
            print(self._data)
    
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