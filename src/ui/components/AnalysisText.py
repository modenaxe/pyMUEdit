from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont
from ui.components.CleanTheme import CleanTheme

class AnalysisText(QLabel):
    # each method returns instances of titles and subtitles

    def create_title(text=""):
        title = QLabel(text)
        title.setObjectName(text)
        title.setStyleSheet(f"color: {CleanTheme.ANALYSIS_TEXT_BUTTON}")
        title.setFont(QFont("Arial", 14, QFont.Bold))

        return title 

    def create_subtitle(text=""):
        subtitle = QLabel(text)
        subtitle.setObjectName(text)
        subtitle.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            margin: 0px;
            """
        )
        subtitle.setFont(QFont("Arial", 10, QFont.Bold))

        return subtitle


