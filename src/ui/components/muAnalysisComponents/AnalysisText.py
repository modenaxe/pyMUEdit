from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class AnalysisText(QLabel):

    """
    (Factory Method)
    Each method returns an instance of different types of text (titles, headings, text etc.)
    """

    # for titles 
    def create_title(text=""):
        title = QLabel(text)
        title.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_BG_CARD};
            font-family: Arial;
            font-size: 14px;
            font-weight: 500;
            """
        )
        return title 

    # for headings you see on popups, such as the signal editing popup 
    def create_heading(text=""):
        heading = QLabel(text)
        heading.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_BUTTON};
            font-family: Arial;
            font-size: 12px;
            font-weight: 400;
            """
        )

        return heading 

    # for the small titles you see on the sidebars 
    def create_subtitle(text=""):
        subtitle = QLabel(text)
        subtitle.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            margin: 0px;
            font-family: Arial;
            font-size: 10px;
            font-weight: 500;
            """
        )

        return subtitle

    # for the labels you see on inputs
    def create_label(text=""):
        label = QLabel(text)
        label.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
            font-family: Arial;
            font-size: 11px;
            font-weight: 500;
            """
        )

        return label 
