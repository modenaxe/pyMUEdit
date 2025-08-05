from PyQt5.QtWidgets import QComboBox, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown

class ResultSelection(QWidget):

    """Result sections tabbing to choose what data to display"""

    def __init__(self, model):
        super().__init__()
        self.model = model

        self.titles = []
        self.df = {}

        layout = QVBoxLayout(self)
        self.combo = AnalysisDropdown('Results Tab', self.titles)
   
        store.data_changed.connect(self.update_combo_from_df)
        store.data_cleared.connect(self.combo.clear)
        
        self.label = QLabel("Select results to view: ")
        self.label.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            margin: 0px;
            """
        )
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.combo.setCurrentIndex(0)
        self.combo.currentTextChanged.connect(self.on_selection_change)
        
    def _update_df(self, df):
        self.df = df
        if df.empty:
            self.titles = []
        else:
            self.titles = self.df['title'].tolist()
        
    def on_selection_change(self, text):
        self.label.setText(f"Selected: {text}")    
        self.model.select_result(-1*(self.combo.currentIndex()+1))
        
    def update_combo_from_df(self, df):
        self._update_df(df)
        self.combo.insertItem(0, self.titles[-1])
        self.combo.setCurrentIndex(0)
        
        
