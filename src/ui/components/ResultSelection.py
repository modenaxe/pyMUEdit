from PyQt5.QtWidgets import QComboBox, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from ui.components.CleanTheme import CleanTheme

class ResultSelection(QWidget):
    def __init__(self, df, model):
        super().__init__()
        self.model = model
        self.df = df
        if df.empty:
            self.titles = []
        else:
            self.titles = self._df['title'].tolist()

            
        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.combo.addItems(self.titles)
        
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
        self._df = df
        if self._df.empty:
            self.titles = []
        else:
            self.titles = self._df['title'].tolist()
        
    def on_selection_change(self, text):
        self.label.setText(f"Selected: {text}")    
        self.model.select_result(-1*(self.combo.currentIndex()+1))
        
    def update_combo_from_df(self, df):
        print("called")
        self._update_df(df)
        self.combo.insertItem(0, self.titles[-1])
        self.combo.setCurrentIndex(0)
        
        