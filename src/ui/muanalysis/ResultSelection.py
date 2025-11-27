from PyQt5.QtWidgets import QVBoxLayout, QWidget

from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisDropdown import \
    AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText


class ResultSelection(QWidget):

    """Result sections tabbing to choose what data to display"""

    def __init__(self, model):
        super().__init__()
        self.model = model

        self.titles = ["No results available"]
        self.df = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addSpacing(15)

        self.combo = AnalysisDropdown('Results Tab', self.titles)

        store.data_changed.connect(self.update_combo_from_df)
        store.data_cleared.connect(self.clear_combo)

        self.label = AnalysisText.create_major_title(
            "Select results to view: ")
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.combo.setCurrentIndex(0)
        self.combo.currentTextChanged.connect(self.on_selection_change)
        layout.addStretch(1)

    def _update_df(self, df):
        self.df = df
        if df.empty:
            self.titles = ["No results available"]
        else:
            self.titles = self.df['title'].tolist()

    def on_selection_change(self, text):
        if text == "No results available":
            self.label.setText("Select results to view: ")
        else:
            self.label.setText(f"Selected: {text}")
            self.model.select_result(-1 * (self.combo.currentIndex() + 1))

    def update_combo_from_df(self, df):
        if "No results available" in self.titles:
            self.combo.removeItem(0)
            self.titles = []
        self._update_df(df)
        self.combo.insertItem(0, self.titles[-1])
        self.combo.setCurrentIndex(0)

    def clear_combo(self):
        self.combo.clear()
        self.combo.addItem("No results available")
        self.combo.setCurrentIndex(0)
        self.titles = ["No results available"]
