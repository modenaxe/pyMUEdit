import csv

from PyQt5.QtWidgets import (QDialog, QFileDialog, QFrame, QTableView,
                             QVBoxLayout)

from core.muAnalysisCore.AnalysisResultsHist import store
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ConfirmationDialog import \
    ConfirmationDialog
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.GeneralRedButton import \
    GeneralRedButton


class ResultsPanel(QFrame):

    """Results panel where data is displayed on right sidebar"""

    def __init__(self, parent, combo, model={}):
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
        clear_button = ClearButton(self)

        self.combo_box = combo

        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        # title
        title = AnalysisText.create_major_title("Results")

        # another layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(title)
        self.layout.addWidget(save_button)
        self.layout.addWidget(self.combo_box)
        self.layout.addWidget(self.table_view, stretch=5)
        self.layout.addWidget(clear_button)

    def save_results(self):
        results = self.model.get_cur_results()
        res_dialog = QFileDialog()
        file_path, _ = res_dialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)")

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


class ClearButton(GeneralRedButton):
    def __init__(self, parent=None):
        super().__init__("Clear Results", parent)
        self.clicked.connect(lambda: self.clear_results())
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #475058;
                color: #fff;
                border-radius: 5px;
                font-size: 1em;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #495057;
            }
            """
        )

    def clear_results(self):
        if store.is_empty():
            error_dialog = ErrorDialog("No Results to Clear", title="Error")
            error_dialog.exec()
            return

        confirm_dialog = ConfirmationDialog(
            "This will clear the current results", "Confirm Clear Results"
        )
        if confirm_dialog.exec_() == QDialog.Accepted:
            store.clear_results()
