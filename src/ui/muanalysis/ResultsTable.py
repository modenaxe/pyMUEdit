from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QBrush, QColor, QFont

from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.CleanTheme import CleanTheme


class ResultsTable(QAbstractTableModel):
    """
    Table model for displaying analysis results in the results section.

    This model:
    - Connects to the shared `store` to receive updates when analysis data changes or is cleared.
    - Stores tabular result data as a list of dictionaries (`_data`) along with column headers.
    - Supports standard QAbstractTableModel methods (`rowCount`, `columnCount`, `data`, `headerData`)
      for integration with PyQt table views.
    - Handles dynamic updates, result selection from historical data, and clearing results.
    """

    def __init__(self):
        super().__init__()

        store.data_changed.connect(self.update_dataframe)
        store.data_cleared.connect(self.clear_results)

        self._data = []  # list of dictionaries
        self.columns = []

    def _updateData(self, df):
        """
        Internal helper to update stored table data from a DataFrame.
        """
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
        """
        Customize table headers.

        - DisplayRole (horizontal): show column names.
        - FontRole (horizontal): make headers bold.
        - BackgroundRole (horizontal): apply CleanTheme.HEADER background color.
        - Fallback: call the base implementation for other roles/orientations.
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]

        elif role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font

        elif role == Qt.BackgroundRole and orientation == Qt.Horizontal:
            return QBrush(QColor(CleanTheme.HEADER))
        return super().headerData(section, orientation, role)

    def update_dataframe(self, new_df):
        """
        Public slot connected to store.data_changed.

        Updates the model's data from a new DataFrame while
        notifying the view to refresh.
        """
        self.beginResetModel()
        self._updateData(new_df)
        self.endResetModel()

    def select_result(self, index):
        """
        Replace current table data with results from a specific index in the history.

        Called when user selects a past result from the analysis history.
        """
        if index < len(self.df):
            self.beginResetModel()
            self._data = self.df.iloc[index]['table']
            self.columns = list(self._data[0].keys())
            self.endResetModel()

    def get_cur_results(self):
        return self._data

    def clear_results(self):
        self.update_dataframe(store.get_analysis_hist())
