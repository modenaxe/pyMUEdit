from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisDropdown import \
    AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class ResultSelection(QWidget):

    """Result sections tabbing to choose what data to display"""

    def __init__(self, model):
        super().__init__()
        self.model = model

        self.titles = []
        self.df = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addSpacing(15)

        self.combo = AnalysisDropdown('Results Tab', self.titles)

        store.data_changed.connect(self.update_combo_from_df)
        store.data_cleared.connect(self.combo.clear)

        self.label = AnalysisText.create_major_title("Select results to view: ")
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.combo.setCurrentIndex(0)
        self.combo.currentTextChanged.connect(self.on_selection_change)
        layout.addStretch(1)

    def _update_df(self, df):
        self.df = df
        if df.empty:
            self.titles = []
        else:
            self.titles = self.df['title'].tolist()

    def on_selection_change(self, text):
        self.label.setText(f"Selected: {text}")
        self.model.select_result(-1 * (self.combo.currentIndex() + 1))

    def update_combo_from_df(self, df):
        self._update_df(df)
        self.combo.insertItem(0, self.titles[-1])
        self.combo.setCurrentIndex(0)
