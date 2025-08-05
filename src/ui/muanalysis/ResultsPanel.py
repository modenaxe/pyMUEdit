import sys
import csv
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QTableView, 
    QFileDialog
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from core.muAnalysisCore.AnalysisResultsHist import store


class ResultsPanel(QFrame):

    """Results panel where data is displayed on right sidebar"""

    def __init__(self, parent, combo, model = {}):
        super().__init__(parent)
        
        self.model = model
        
        self.setObjectName("ResultsPanel")
        self.setStyleSheet(
            f"""
            #rightSidebar {{
                background-color: {CleanTheme.ANALYSIS_BG_TOPBAR};
                border-bottom: 1px solid {CleanTheme.ANALYSIS_TEXT_BUTTON};
            }}
        """
        )    
        
        # save results button
        save_button = GeneralButton("Save", lambda: self.save_results())
        
        # clear results button
        clear_button = GeneralButton("Clear", lambda: self.clear_results())

        self.combo_box = combo

        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        
        # title
        title = AnalysisText.create_major_title("Results") 
        
        # layout
        # top_layout = QVBoxLayout()
        # top_layout.addWidget(title)
        # # top_layout.addStretch(1)
        # top_layout.addWidget(save_button)
        # top_layout.addStretch(1)
        
        # another layout 
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(title)
        self.layout.addWidget(save_button)
        # self.layout.addLayout(top_layout, stretch=1)
        self.layout.addWidget(self.combo_box, stretch=1)
        self.layout.addWidget(self.table_view, stretch=3)
        self.layout.addWidget(clear_button, stretch=1)

    def save_results(self):
        results = self.model.get_cur_results()
        res_dialog = QFileDialog()
        file_path, _ = res_dialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                headers = self.model.columns
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(results)

                print(f"Data saved to {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")
                
    def clear_results(self):
        store.clear_results()
