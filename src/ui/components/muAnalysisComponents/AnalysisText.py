from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel

from ui.components.muAnalysisComponents.CleanTheme import CleanTheme


class AnalysisText(QLabel):

    """UI component that defines a variety of methods, each responsible for 
    a different text (e.g. headings, captions etc.) via the factory method
    """

    def create_major_title(text=""):
        """Creates the equivalent of a heading 1, the biggest hierarchical heading
        Params: 
            - text="": the text inside the heading 
        Returns: 
            - instance of major_title 
        """
        major_title = QLabel(text)
        major_title.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_TEXT_DARK};
            font-family: Arial;
            font-size: 14px;
            font-weight: 500;
            """
        )
        return major_title

    def create_title(text=""):
        """Create a headings that's used as the biggest hierarchical heading inside modals 
        Params: 
            - text="": the text inside the title 
        Returns: 
            - instance of title 
        """
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

    def create_title_dark(text=""):
        """Creates a dark heading that's used as the biggest hierarchical heading inside modals 
        Params: 
            - text="": the text inside the title 
        Returns: 
            - instance of title 
        """
        title = QLabel(text)
        title.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_DIALOG_TEXT};
            font-family: Arial;
            font-size: 14px;
            font-weight: 500;
            """
        )
        return title

    def create_heading(text=""):
        """Creates a heading that's used as a secondary heading inside modals
        Params: 
            - text="": the text inside the heading 
        Returns: 
            - instance of heading 
        """
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

    def create_heading_dark(text=""):
        """Creates a dark heading that's used as a secondary heading inside modals
        Params: 
            - text="": the text inside the heading 
        Returns: 
            - instance of heading 
        """
        heading = QLabel(text)
        heading.setStyleSheet(
            f"""
            color: {CleanTheme.ANALYSIS_DIALOG_TEXT};
            font-family: Arial;
            font-size: 12px;
            font-weight: 400;
            """
        )
        return heading

    def create_subtitle(text=""):
        """Creates a heading that's used as a secondary heading in sidebars 
        Params: 
            - text="": the text inside the subtitle 
        Returns: 
            - instance of subtitle 
        """
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

    def create_label(text=""):
        """Creates the labels used on top of UI components, such as dropdowns 
        Params: 
            - text="": the text inside the label 
        Returns: 
            - instance of label 
        """
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

    def create_prompt(text=""):
        """Creates the prompt used in the centre canvas 
        Params: 
            - text="": the text inside the prompt 
        Returns: 
            - instance of prompt 
        """
        prompt = QLabel(text)
        prompt.setStyleSheet(
            f"""
                color: {CleanTheme.ANALYSIS_TEXT_PROMPT};
                font-family: Arial;
                font-size: 27px;
                font-weight: 500
            """
        )
        return prompt

    def create_italic_text(text=""):
        """Creates caption text used for in-modal warnings. See SignalEditing. 
        Params: 
            - text="": the text inside the caption 
        Returns: 
            - instance of caption
        """
        italic = QLabel(text)
        italic.setStyleSheet(
            f"""
                color: {CleanTheme.ANALYSIS_TEXT_TERTIARY};
                font-family: Arial;
                font-size: 10px;
                font-style: italic;
                qproperty-alignment: 'AlignRight | AlignVCenter';
            """
        )
        return italic
