import copy

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QMessageBox,
                             QVBoxLayout, QWidget)
from scipy import signal

from app.muAnalysisFunctions.FileUploadFunc import FileUploadFunc
from core.muAnalysisCore.SelectRange import SelectRange
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown
from ui.components.muAnalysisComponents.AnalysisLabeledDropdown import AnalysisLabeledDropdown
from ui.components.muAnalysisComponents.AnalysisDropdownDialog import AnalysisDropdownDialog
from ui.components.muAnalysisComponents.AnalysisLabeledDropdownDialog import AnalysisLabeledDropdownDialog
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.SaveablePlot import SaveablePlot


class SignalEditing(QWidget):

    """Responsible for the Signal Editing button on the sidebar, and the modal 
    that appears alongside it 
    """

    def __init__(self, mu, analysis_plot, parent=None):
        """Initialises the signal editing button
        Params:
            - mu: instance that allows access to the file (legacy)
            - analysis_plot: instance that helps with centre plotting 
        Returns:
            - instance of SignalEditing (button)
        """
        super().__init__(parent)

        self.mu = mu
        self.analysis_plot = analysis_plot

        layout = QVBoxLayout(self)
        btn = GeneralButton(
            "Signal Editing",
            lambda: self.show_window(),
            parent=self)
        layout.addWidget(btn, stretch=1)

    def show_window(self):
        """Creates the UI for the modal/popup that appears after pressing the button
        Params: None 
        Returns: None
        """
        if FileUploadFunc.file is None:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return

        window = QDialog()
        window.setWindowTitle("Signal Editing Window")
        window.setStyleSheet(
            f"""
            background-color: {CleanTheme.ANALYSIS_DIALOG_BACKGROUND};
            """
        )
        window_layout = QVBoxLayout()
        window.setLayout(window_layout)
        window_layout.setSpacing(10)
        self.window = window

        # Title
        title = AnalysisText.create_title_dark("Signal Editing")
        window_layout.addWidget(title)

        window_layout.addSpacing(10)

        # Filter emg
        emg_sig_subtitle = AnalysisText.create_heading_dark("EMG Signal")
        window_layout.addWidget(emg_sig_subtitle)

        filter_emg = QFrame()
        window_layout.addWidget(filter_emg)

        filter_emg_layout = QHBoxLayout(filter_emg)
        filter_emg_layout.setContentsMargins(0, 0, 0, 0)

        filter_emg_order = AnalysisInput("Filter Order", "2", parent=window)
        filter_emg_order.set("2")
        filter_emg_layout.addWidget(filter_emg_order)
        self.filter_emg_order = filter_emg_order

        filter_emg_freq = AnalysisInput(
            "BandPass Freq", "20-500", parent=window)
        filter_emg_freq.set("20-500")
        filter_emg_layout.addWidget(filter_emg_freq)
        self.filter_emg_freq = filter_emg_freq

        # Aligning everything to the bottom 
        filter_v_emg = QFrame()
        filter_v_emg_layout = QVBoxLayout(filter_v_emg)
        filter_v_emg_layout.setContentsMargins(0, 0, 0, 0)
        filter_v_emg_layout.addStretch()

        filter_emg_btn = GeneralButton(
            "Filter EMG signal",
            lambda: self.filter_emg_signal(),
            parent=self)
        filter_v_emg_layout.addWidget(filter_emg_btn)
        filter_emg_layout.addWidget(filter_v_emg, stretch=1)

        window_layout.addSpacing(10)

        # Reference signal
        refsig_subtitle = AnalysisText.create_heading_dark("Reference Signal")
        window_layout.addWidget(refsig_subtitle)

        filter_refsig = QFrame()
        window_layout.addWidget(filter_refsig)
        filter_refsig_layout = QHBoxLayout(filter_refsig)
        filter_refsig_layout.setContentsMargins(0, 0, 0, 0)

        filter_refsig_order = AnalysisInput("Filter Order", "4", parent=window)
        filter_refsig_order.set("4")
        filter_refsig_layout.addWidget(filter_refsig_order)
        self.filter_refsig_order = filter_refsig_order

        filter_refsig_freq = AnalysisInput("Cutoff Freq", "15", parent=window)
        filter_refsig_freq.set("15")
        filter_refsig_layout.addWidget(filter_refsig_freq)
        self.filter_refsig_freq = filter_refsig_freq

        # Aligning everything to the bottom 
        filter_v_refsig = QFrame()
        filter_v_refsig_layout = QVBoxLayout(filter_v_refsig)
        filter_v_refsig_layout.setContentsMargins(0, 0, 0, 0)
        filter_v_refsig_layout.addStretch()

        filter_refsig_btn = GeneralButton(
            "Filter Refsig", lambda: self.filter_refsig(), parent=self)
        filter_v_refsig_layout.addWidget(filter_refsig_btn)
        filter_refsig_layout.addWidget(filter_v_refsig, stretch=1)

        # Remove offset 
        remove_offset = QFrame()
        window_layout.addWidget(remove_offset)
        remove_offset_layout = QHBoxLayout(remove_offset)
        remove_offset_layout.setContentsMargins(0, 0, 0, 0)

        remove_offset_value = AnalysisInput("Offset Value", "4", parent=window)
        remove_offset_value.set("4")
        remove_offset_layout.addWidget(remove_offset_value)
        self.remove_offset_value = remove_offset_value

        remove_auto_offset = AnalysisInput(
            "Automatic Offset", "0", parent=window)
        remove_auto_offset.set("0")
        remove_offset_layout.addWidget(remove_auto_offset)
        self.remove_auto_offset = remove_auto_offset

        # Aligning everything to the bottom 
        remove_v_offset = QFrame()
        remove_v_offset_layout = QVBoxLayout(remove_v_offset)
        remove_v_offset_layout.setContentsMargins(0, 0, 0, 0)
        remove_v_offset_layout.addStretch()

        remove_offset_btn = GeneralButton(
            "Remove Offset", lambda: self.remove_offset(), parent=self)
        remove_v_offset_layout.addWidget(remove_offset_btn)
        remove_offset_layout.addWidget(remove_v_offset, stretch=1)

        # Convert row
        convert = QFrame()
        convert.setStyleSheet(f"padding: 0px")
        window_layout.addWidget(convert)
        convert_layout = QHBoxLayout(convert)
        convert_layout.setContentsMargins(0, 0, 0, 0)

        convert_operator = AnalysisLabeledDropdownDialog(
            "Operator",
            ["Multiply", "Divide"],
            parent=self
        )
        convert_layout.addWidget(convert_operator, stretch=1)
        self.convert_operator = convert_operator

        convert_factor = AnalysisInput("Factor", "2.5", parent=window)
        convert_factor.set("2.5")
        convert_layout.addWidget(convert_factor, stretch=1)
        self.convert_factor = convert_factor

        # Aligning everything to the bottom 
        convert_v = QFrame()
        convert_v_layout = QVBoxLayout(convert_v)
        convert_v_layout.setContentsMargins(0, 0, 0, 0)
        convert_v_layout.addStretch()

        convert_btn = GeneralButton(
            "Convert", lambda: self.convert(), parent=self)
        convert_v_layout.addWidget(convert_btn)
        convert_layout.addWidget(convert_v, stretch=1)

        # Percent row
        percent = QFrame()
        window_layout.addWidget(percent)
        percent_layout = QHBoxLayout(percent)
        percent_layout.setContentsMargins(0, 0, 0, 0)

        percent_mvc_value = AnalysisInput("MVC Value", "0.0", parent=window)
        percent_mvc_value.set("0.0")
        percent_layout.addWidget(percent_mvc_value)
        self.percent_mvc_value = percent_mvc_value

        # aligning everything to the bottom
        percent_v = QFrame()
        percent_v_layout = QVBoxLayout(percent_v)
        percent_v_layout.setContentsMargins(0, 0, 0, 0)
        percent_v_layout.addStretch()

        percent_h = QFrame()
        percent_h_layout = QHBoxLayout(percent_h)
        percent_h_layout.setContentsMargins(0, 0, 0, 0)

        percent_warning = AnalysisText.create_italic_text(
            "*Only for absolute\nvalued RefSigs")
        percent_h_layout.addWidget(percent_warning)

        percent_btn = GeneralButton(
            "To Percent",
            lambda: self.to_percent(),
            parent=self)
        percent_h_layout.addWidget(percent_btn)

        percent_v_layout.addWidget(percent_h)

        percent_layout.addWidget(percent_v, stretch=1)

        window_layout.addStretch()
        window.exec()

    def is_int(self, n):
        """Checks if a given string is a valid int for filter_emg or 
        filter_refsig. If it is, returns n + 1.
        Params: 
            - n: an int 
        Returns:
            - Boolean: True if it's a valid 
        """
        try:
            v = int(n)
            return v + 1
        except ValueError:
            return False

    def filter_emg_signal(self):
        """Filters and plots the EMG signal based on specifications
        Params: None 
        Returns: None
        """
        order = self.is_int(self.filter_emg_order.get())
        try:
            lo, hi = map(
                self.is_int, self.filter_emg_freq.get().split(
                    "-", maxsplit=1))
        except ValueError as e:
            ErrorDialog("EMG signal bandpass frequencies must be separated by a -").exec_()
            return
        if not order or order - 1 < 0:
            ErrorDialog(
                "EMG signal filter order must be a non-negative integer",
                "Invalid Input").exec_()
            return
        elif not lo or not hi or lo - 1 <= 0 or hi - 1 <= 0 or lo >= hi:
            ErrorDialog(
                "EMG signal bandpass frequencies must be non-zero positive integers.",
                "Invalid Input").exec_()
            return

        filtered_file = copy.deepcopy(self.mu.file)

        # Subtracting 1 to account for is_int()
        order -= 1
        lo -= 1
        hi -= 1

        sos = signal.butter(
            N=order,
            Wn=[lo, hi],
            btype="bandpass",
            output="sos",
            fs=filtered_file["FSAMP"],
        )
        for col in filtered_file["RAW_SIGNAL"]:
            filtered_file["RAW_SIGNAL"][col] = signal.sosfiltfilt(
                sos,
                x=filtered_file["RAW_SIGNAL"][col],
            )

        self.mu.plot_idr(filtered_file, self.analysis_plot)

    def filter_refsig(self):
        """Filters and plots the reference signal based on specifications
        Params: None 
        Returns: None
        """
        order = self.is_int(self.filter_refsig_order.get())
        cutoff = self.is_int(self.filter_refsig_freq.get())
        if not order or order - 1 < 0:
            ErrorDialog(
                "Reference signal filter order must be a non-negative integer",
                "Invalid Input").exec_()
            return
        elif not cutoff or cutoff - 1 <= 0:
            ErrorDialog(
                "Reference signal filter cutoff frequency must be a non-zero positive integer",
                "Invalid Input").exec_()
            return

        filtered_file = copy.deepcopy(self.mu.file)

        # Subtracting 1 to account for is_int()
        order -= 1
        cutoff -= 1

        sos = signal.butter(
            N=order,
            Wn=cutoff,
            btype="lowpass",
            output="sos",
            fs=filtered_file["FSAMP"],
        )
        filtered_file["REF_SIGNAL"][0] = signal.sosfiltfilt(
            sos,
            x=filtered_file["REF_SIGNAL"][0],
        )

        self.mu.plot_refsig(filtered_file, self.analysis_plot)

    def remove_offset(self):
        """Removes and plots user-specified/selected refsig offset (from the y-axis) 
        Params: None 
        Returns: None
        """
        try:
            offset = int(self.remove_offset_value.get())
            auto = int(self.remove_auto_offset.get())

            plt.close()

            # Setting up the plot
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Time(sec)")
            self.ax.set_ylabel('MVC')

            self.fig.set_figheight(5)
            self.fig.set_figwidth(5)

            if (auto <= 0):
                if (offset != 0):
                    self.mu.file["REF_SIGNAL"][0] = self.mu.file["REF_SIGNAL"][0] - offset
                    self.mu.plot_refsig(self.mu.file, self.analysis_plot)
                else:
                    self.window.accept()
                    SelectRange(self.analysis_plot, self.two_point, False)
            else:
                offset = self.mu.file["REF_SIGNAL"].iloc[0:auto].mean()
                self.mu.file["REF_SIGNAL"][0] = (
                    self.mu.file["REF_SIGNAL"][0] - float(offset))
                self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog(
                "Offset and Automatic Offset value must be a valid integer",
                "Invalid Input").exec_()

    def two_point(self, x, y):
        """two_point function required for SelectRange. Ran after two points in 
        ranged are gathered
        Params: None 
        Returns: None
        """
        offsetval = self.mu.file["REF_SIGNAL"].loc[x:y].mean()
        self.mu.file["REF_SIGNAL"][0] = (
            self.mu.file["REF_SIGNAL"][0] - float(offsetval))

        self.mu.plot_refsig(self.mu.file, self.analysis_plot)

    def convert(self):
        """Multiplies/Divides and plots values in the y-axis by the user-
        specified value
        Params: None 
        Returns: None
        """
        try:
            factor = float(self.convert_factor.get())
            if (self.convert_operator.get() == "Multiply"):
                self.mu.file["REF_SIGNAL"] = (
                    self.mu.file["REF_SIGNAL"] * factor)
            elif (self.convert_operator.get() == "Divide"):
                self.mu.file["REF_SIGNAL"] = (
                    self.mu.file["REF_SIGNAL"] / factor)

            self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog(
                "Conversion factor must be a valid number",
                "Invalid Input").exec_()

    def to_percent(self):
        """Divides and plots values on the y-axis by percentage
        Params: None 
        Returns: None
        """
        try:
            percent = float(self.percent_mvc_value.get())
            self.mu.file["REF_SIGNAL"] = (
                self.mu.file["REF_SIGNAL"] * 100 / percent)

            self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog(
                "MVC value must be a valid float",
                "Invalid Input").exec_()
