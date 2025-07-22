import copy
from scipy import signal
from PyQt5.QtWidgets import (
    QWidget, 
    QFrame,
    QVBoxLayout, 
    QHBoxLayout,
    QDialog,
    QMessageBox,
)
import matplotlib.pyplot as plt
from ui.components.SaveablePlot import SaveablePlot
from ui.components.muAnalysisComponents.CleanTheme import CleanTheme
from ui.components.muAnalysisComponents.AnalysisText import AnalysisText
from ui.components.muAnalysisComponents.AnalysisInput import AnalysisInput
from ui.components.muAnalysisComponents.GeneralButton import GeneralButton
from ui.components.muAnalysisComponents.AnalysisDropdown import AnalysisDropdown, AnalysisLabeledDropdown
from ui.components.muAnalysisComponents.ErrorDialog import ErrorDialog
from core.muAnalysisCore.SelectRange import SelectRange

class SignalEditing(QWidget):

    """
    All the code responsible for filtering the plot. This includes:
    - the button on the dashboard and the popup
    - the functionality behind the buttons you press inside the popup that filter the plot 
    """
    def __init__(self, mu, analysis_plot, parent=None):
        super().__init__(parent)

        self.mu = mu
        self.analysis_plot = analysis_plot

        layout = QVBoxLayout(self)
        btn = GeneralButton("Signal Editing", lambda: self.show_window(), parent=self)
        layout.addWidget(btn, stretch=1)

    # the popup
    def show_window(self):
        window = QDialog()
        window.setWindowTitle("Signal Editing Window")
        window.setStyleSheet(
            f"""
            background-color: {CleanTheme.ANALYSIS_BG_SIDEBAR};
            """
        )
        window_layout = QVBoxLayout()
        window.setLayout(window_layout)
        window_layout.setSpacing(10)

        # title
        title = AnalysisText.create_title("Signal Editing") 
        window_layout.addWidget(title)

        # spacing 
        window_layout.addSpacing(10)

        # FILTER EMG 
        # subtitle 
        emg_sig_subtitle = AnalysisText.create_heading("EMG Signal")
        window_layout.addWidget(emg_sig_subtitle)

        # filter emg signal row
        filter_emg = QFrame()
        window_layout.addWidget(filter_emg)

        filter_emg_layout = QHBoxLayout(filter_emg)
        filter_emg_layout.setContentsMargins(0, 0, 0, 0)

        filter_emg_order = AnalysisInput("Filter Order", "2", parent=window)
        filter_emg_order.set("2")
        filter_emg_layout.addWidget(filter_emg_order)
        self.filter_emg_order = filter_emg_order

        filter_emg_freq = AnalysisInput("BandPass Freq", "20-500", parent=window)
        filter_emg_freq.set("20-500")
        filter_emg_layout.addWidget(filter_emg_freq)
        self.filter_emg_freq = filter_emg_freq

        # adding a new container to make sure the button is aligned with the bottom 
        filter_v_emg = QFrame()
        filter_v_emg_layout = QVBoxLayout(filter_v_emg)
        filter_v_emg_layout.setContentsMargins(0, 0, 0, 0)
        filter_v_emg_layout.addStretch()

        filter_emg_btn = GeneralButton("Filter EMG signal", lambda: self.filter_emg_signal(), parent=self)
        filter_v_emg_layout.addWidget(filter_emg_btn)
        filter_emg_layout.addWidget(filter_v_emg, stretch=1)

        # spacing 
        window_layout.addSpacing(10)

        # REFERENCE SIGNAL
        # another subtitle 
        refsig_subtitle = AnalysisText.create_heading("Reference Signal")
        window_layout.addWidget(refsig_subtitle)

        # filter reference signal row  
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

        # adding a new container to make sure the button is aligned with the bottom 
        filter_v_refsig = QFrame()
        filter_v_refsig_layout = QVBoxLayout(filter_v_refsig)
        filter_v_refsig_layout.setContentsMargins(0, 0, 0, 0)
        filter_v_refsig_layout.addStretch()

        filter_refsig_btn = GeneralButton("Filter Refsig", lambda: self.filter_refsig(), parent=self)
        filter_v_refsig_layout.addWidget(filter_refsig_btn)
        filter_refsig_layout.addWidget(filter_v_refsig, stretch=1)

        # remove offset row  
        remove_offset = QFrame()
        window_layout.addWidget(remove_offset)
        remove_offset_layout = QHBoxLayout(remove_offset)
        remove_offset_layout.setContentsMargins(0, 0, 0, 0)

        remove_offset_value = AnalysisInput("Offset Value", "4", parent=window)
        remove_offset_value.set("4")
        remove_offset_layout.addWidget(remove_offset_value)
        self.remove_offset_value = remove_offset_value

        remove_auto_offset = AnalysisInput("Automatic Offset", "0", parent=window)
        remove_auto_offset.set("0")
        remove_offset_layout.addWidget(remove_auto_offset)
        self.remove_auto_offset = remove_auto_offset

        # aligning button to bottom
        remove_v_offset = QFrame()
        remove_v_offset_layout = QVBoxLayout(remove_v_offset)
        remove_v_offset_layout.setContentsMargins(0, 0, 0, 0)
        remove_v_offset_layout.addStretch()

        remove_offset_btn = GeneralButton("Remove Offset", lambda: self.remove_offset(), parent=self)
        remove_v_offset_layout.addWidget(remove_offset_btn)
        remove_offset_layout.addWidget(remove_v_offset, stretch=1)


        # convert row 
        convert = QFrame()
        convert.setStyleSheet(f"padding: 0px")
        window_layout.addWidget(convert)
        convert_layout = QHBoxLayout(convert)
        convert_layout.setContentsMargins(0, 0, 0, 0)
        # ficing dropdown
        convert_operator = AnalysisLabeledDropdown(
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

        # aligning button to bottom
        convert_v = QFrame()
        convert_v_layout = QVBoxLayout(convert_v)
        convert_v_layout.setContentsMargins(0, 0, 0, 0)
        convert_v_layout.addStretch()

        convert_btn = GeneralButton("Convert", lambda: self.convert(), parent=self)
        convert_v_layout.addWidget(convert_btn)
        convert_layout.addWidget(convert_v, stretch=1)


        # percent row 
        percent = QFrame()
        window_layout.addWidget(percent)
        percent_layout = QHBoxLayout(percent)
        percent_layout.setContentsMargins(0, 0, 0, 0)

        percent_mvc_value = AnalysisInput("MVC Value", "0.0", parent=window)
        percent_mvc_value.set("0.0")
        percent_layout.addWidget(percent_mvc_value)
        self.percent_mvc_value = percent_mvc_value

        # aligning button to bottom
        percent_v = QFrame()
        percent_v_layout = QVBoxLayout(percent_v)
        percent_v_layout.setContentsMargins(0, 0, 0, 0)
        percent_v_layout.addStretch()

        percent_h = QFrame()
        percent_h_layout = QHBoxLayout(percent_h)
        percent_h_layout.setContentsMargins(0, 0, 0, 0)

        percent_warning = AnalysisText.create_italic_text("*Only for absolute\nvalued RefSigs")
        percent_h_layout.addWidget(percent_warning)

        percent_btn = GeneralButton("To Percent", lambda: self.to_percent(), parent=self)
        percent_h_layout.addWidget(percent_btn)

        percent_v_layout.addWidget(percent_h)

        percent_layout.addWidget(percent_v, stretch=1)

        window_layout.addStretch()
        window.exec()
        
    # returns boolean value based on whethere or not there's a valid file loaded
    def valid_file(self):
        if not self.mu.file:
            ErrorDialog("No file has been loaded", "Error").exec_()
            return False 
        return True 

    # given a string, checks if it's a valid int 
    # if true, return the int + 1 (to make validation a little easier) 
    # if false, return false
    def is_int(self, n):
        try:
            v = int(n) 
            return v + 1
        except ValueError:
            return False

    # filtering emg signals 
    def filter_emg_signal(self):
        if not self.valid_file(): 
            return

        print("filtering emg signals")

        # determining if values are valid 
        order = self.is_int(self.filter_emg_order.get())
        lo, hi = map(self.is_int, self.filter_emg_freq.get().split("-", maxsplit=1))
        if not order or order - 1 < 0:
            ErrorDialog("EMG signal filter order must be a non-negative integer", "Invalid Input").exec_()
            return 
        elif not lo or not hi or lo - 1 <= 0 or hi - 1<= 0 or lo >= hi:
            ErrorDialog("EMG signal bandpass frequencies must be non-zero positive integers written in the form `x-y` where the left limit must be smaller than the right limit.", "Invalid Input").exec_()
            return

        # main code (copied over from openhdemg)
        # haven't checked if this actually works, it doesn't seem to change anything regardless of the input
        filtered_file = copy.deepcopy(self.mu.file)

        # subtracting 1 to account for is_int() 
        order -= 1 
        lo -= 1 
        hi -= 1

        # Calculate the components of the filter and apply them with filtfilt to
        # obtain Zero-lag filtering. sos should be preferred over filtfilt as
        # second-order sections have fewer numerical problems.
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

    # filtering and plotting reference signals 
    def filter_refsig(self):
        if not self.valid_file(): 
            return
        
        print("filtering refsig")

        # determining if values are valid 
        order = self.is_int(self.filter_refsig_order.get())
        cutoff = self.is_int(self.filter_refsig_freq.get())
        if not order or order - 1 < 0:
            ErrorDialog("Reference signal filter order must be a non-negative integer", "Invalid Input").exec_()
            return
        elif not cutoff or cutoff - 1 <= 0:
            ErrorDialog("Reference signal filter cutoff frequency must be a non-zero positive integer", "Invalid Input").exec_()
            return

        # main code (copied from openhdemg)
        filtered_file = copy.deepcopy(self.mu.file)

        # subtracting 1 to account for is_int() 
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

    # TL : notes on what this function does (or is supposed to do) 
    # if you provide a non-zero offset value:
    #   shifts the values on the y-axis down by the offset 
    #
    def remove_offset(self):
        if not self.valid_file(): 
            return
        
        print("removing offset")
        try:
            # getting values (openhdemg doesn't accept floats)
            offset = int(self.remove_offset_value.get())
            auto = int(self.remove_auto_offset.get())

            plt.close()

            # setting up the plot 
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("Time(sec)")
            self.ax.set_ylabel('MVC')

            self.fig.set_figheight(5)
            self.fig.set_figwidth(5)

            # logic from openhdemg : computing offset and applying offset
            if (auto <= 0):
                if (offset != 0):
                    self.mu.file["REF_SIGNAL"][0] = self.mu.file["REF_SIGNAL"][0] - offset
                    self.mu.plot_refsig(self.mu.file, self.analysis_plot) 
                else:
                    SelectRange(self.analysis_plot, self.two_point)
            else :
                # subtracting 
                offset = self.mu.file["REF_SIGNAL"].iloc[0:auto].mean()
                self.mu.file["REF_SIGNAL"][0] = (self.mu.file["REF_SIGNAL"][0] - float(offset))
                self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog("Offset and Automatic Offset value must be a valid integer", "Invalid Input").exec_()

    # defining two_point for SelectRange 
    # executes after points are selected (don't need to revert center plot)
    def two_point(self, x, y):
        offsetval = self.mu.file["REF_SIGNAL"].loc[x:y].mean()
        self.mu.file["REF_SIGNAL"][0] = (self.mu.file["REF_SIGNAL"][0] - float(offsetval))

        self.mu.plot_refsig(self.mu.file, self.analysis_plot)


    def convert(self):
        if not self.valid_file(): 
            return
        
        print("converting")

        try:
            # converting factor 
            factor = float(self.convert_factor.get())
            if (self.convert_operator.get() == "Multiply"):
                self.mu.file["REF_SIGNAL"] = (self.mu.file["REF_SIGNAL"] * factor)
            elif (self.convert_operator.get() == "Divide"):
                self.mu.file["REF_SIGNAL"] = (self.mu.file["REF_SIGNAL"] / factor)

            # updating the plot (replotting)
            self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog("Conversion factor must be a valid number", "Invalid Input").exec_()


    def to_percent(self):
        if not self.valid_file(): 
            return
        
        print("to percenting")
        try:
            percent = float(self.percent_mvc_value.get())
            self.mu.file["REF_SIGNAL"] = (self.mu.file["REF_SIGNAL"] * 100 / percent)

            # plotting 
            self.mu.plot_refsig(self.mu.file, self.analysis_plot)
        except ValueError as e:
            ErrorDialog("MVC value must be a valid float", "Invalid Input").exec_()

