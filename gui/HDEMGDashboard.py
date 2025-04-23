import sys
import os
import traceback
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QPushButton, QStyle, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt

# Import UI setup function
from ui.HDEMGDashboardUI import setup_ui, update_sidebar_selection

# Import for external windows/widgets
from ImportDataWindow import ImportDataWindow
from ui.MUAnalysisUI import MUAnalysis
from ExportResults import ExportResultsWindow
from DecompositionApp import DecompositionApp

# Import visualization storage for recent visualizations
try:
    from VisualizationStorage import VisualizationStorage
    has_viz_storage = True
except ImportError:
    has_viz_storage = False
    print("WARNING: VisualizationStorage not available, recent visualizations feature will be disabled")


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables for external windows/widgets
        self.import_data_page = None
        self.export_results_window = None
        self.mu_analysis_page = None
        self.manual_editing_page = None
        self.decomposition_page = None
        
        # Initialize visualization storage if available
        self.viz_storage = VisualizationStorage() if has_viz_storage else None
        
        # Load recent visualizations if storage is available
        if self.viz_storage:
            self.recent_visualizations = self.viz_storage.get_visualizations()
        else:
            # Sample data for the UI (used when viz_storage not available)
            self.recent_visualizations = [
                {
                    "title": "HDEMG Analysis",
                    "date": "Last modified: Jan 15, 2025",
                    "type": "hdemg",
                    "icon": "visualization_icon",
                },
                {
                    "title": "Neuro Analysis",
                    "date": "Last modified: Jan 14, 2025",
                    "type": "neuro",
                    "icon": "visualization_icon",
                },
                {
                    "title": "EMG Recording 23",
                    "date": "Last modified: Jan 13, 2025",
                    "type": "emg",
                    "icon": "visualization_icon",
                },
                {
                    "title": "EEG Study Results",
                    "date": "Last modified: Jan 10, 2025",
                    "type": "eeg",
                    "icon": "visualization_icon",
                },
            ]

        # Colors and other UI settings
        self.colors = {
            "bg_main": "#f5f5f5",
            "bg_sidebar": "#f0f0f0",
            "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8",
            "bg_card_neuro": "#7cb342",
            "bg_card_emg": "#e91e63",
            "bg_card_eeg": "#9c27b0",
            "bg_card_default": "#607d8b",
            "border": "#d0d0d0",
            "text_primary": "#333333",
            "text_secondary": "#777777",
            "accent": "#000000",
            "sidebar_selected_bg": "#e6e6e6",
        }

        # Sample data for datasets
        self.recent_datasets = [
            {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"},
            {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"},
            {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"},
            {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"},
        ]

        # Initialize external widgets if available
        self.initialize_external_widgets()

        # Set up the UI (imported from main_window_ui.py)
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Start on dashboard view
        self.show_dashboard_view()

    def initialize_external_widgets(self):
        """Initialize external widgets if their modules are available."""
        # Initialize MU Analysis page
        if MUAnalysis:
            self.mu_analysis_page = MUAnalysis()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            if hasattr(self.mu_analysis_page, "set_export_window_opener"):
                self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")

        # Initialize Import Data page
        if ImportDataWindow:
            self.import_data_page = ImportDataWindow(parent=self)
            # Use the correct windowflags
            self.import_data_page.setWindowFlags(getattr(Qt.WindowType, "Widget"))
            if hasattr(self.import_data_page, "return_to_dashboard_requested"):
                self.import_data_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            # Connect the new signal for decomposition
            if hasattr(self.import_data_page, "decomposition_requested"):
                self.import_data_page.decomposition_requested.connect(self.create_decomposition_view)

    def create_decomposition_view(self, emg_obj=None, filename=None, pathname=None, imported_signal=None, 
                                visualization_data=None):
        """
        Creates a decomposition view with the provided data and adds it to the stacked widget.
        
        Args:
            emg_obj: Optional EMG object with loaded data
            filename: Optional filename for the data source
            pathname: Optional directory path of the data source
            imported_signal: Optional dict with imported signal data
            visualization_data: Optional dict with visualization metadata for reopening a saved visualization
        """
        try:
            print("Creating decomposition view with provided data")

            # Create a wrapper widget to hold the DecompositionApp
            wrapper = QWidget()
            wrapper.setObjectName("decomposition_wrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)

            # Create DecompositionApp instance
            decomp_app = DecompositionApp(
                emg_obj=emg_obj,
                filename=filename,
                pathname=pathname,
                imported_signal=imported_signal,
                parent=self,  # Set parent for proper widget hierarchy
            )

            # If reopening a visualization from saved visualization_data
            if visualization_data:
                filepath = visualization_data.get("filepath")
                print(f"Loading visualization from {filepath}")
                
                if filepath and os.path.exists(filepath):
                    try:
                        # Load the .mat file for signal data
                        import scipy.io as sio
                        
                        data = sio.loadmat(filepath)
                        
                        # Extract directory and filename
                        pathname = os.path.dirname(filepath)
                        filename = os.path.basename(filepath)
                        
                        # Set the data in the decomposition app
                        if "signal" in data:
                            decomp_app.filename = filename
                            decomp_app.pathname = pathname
                            
                            # Initialize emg_obj if needed
                            if decomp_app.emg_obj is None:
                                from EmgDecomposition import offline_EMG
                                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
                                if not os.path.exists(temp_dir):
                                    os.makedirs(temp_dir)
                                decomp_app.emg_obj = offline_EMG(save_dir=temp_dir, to_filter=True)
                                
                            # Load signal data into the emg_obj
                            signal_data = data["signal"]
                            if hasattr(signal_data, 'dtype') and signal_data.dtype.names is not None:
                                # Convert the MATLAB struct into a dictionary
                                decomp_app.emg_obj.signal_dict = {}
                                for field in signal_data.dtype.names:
                                    if signal_data[field].size > 0:
                                        # Extract the field data correctly based on dimensions
                                        field_data = signal_data[field]
                                        if field_data.ndim > 1:
                                            decomp_app.emg_obj.signal_dict[field] = field_data[0, 0]
                                        else:
                                            decomp_app.emg_obj.signal_dict[field] = field_data
                            
                            # Set the decomposition result for direct access
                            decomp_app.decomposition_result = data["signal"]
                            
                            # Set UI parameters if available
                            if "parameters" in data and hasattr(data["parameters"], "dtype"):
                                try:
                                    # Handle parameters based on data structure
                                    if data["parameters"].ndim > 1:
                                        params = data["parameters"][0, 0]
                                    else:
                                        params = data["parameters"]
                                    
                                    # Process parameter fields
                                    if hasattr(params, "dtype") and params.dtype.names is not None:
                                        parameter_dict = {}
                                        for field in params.dtype.names:
                                            # Check dimensions of the field value before accessing
                                            field_array = params[field]
                                            if field_array.ndim > 1:
                                                field_value = field_array[0, 0]
                                            else:
                                                # For 1D arrays
                                                if field_array.size > 0:
                                                    field_value = field_array[0]
                                                else:
                                                    continue  # Skip empty arrays
                                            
                                            parameter_dict[field] = field_value
                                        
                                        # Store parameters in the app
                                        decomp_app.ui_params = parameter_dict
                                        
                                        # Map parameters to UI controls
                                        for field, value in parameter_dict.items():
                                            try:
                                                # Number fields
                                                if field == "NITER" and hasattr(decomp_app, "number_iterations_field"):
                                                    decomp_app.number_iterations_field.setValue(int(value))
                                                elif field == "nwindows" and hasattr(decomp_app, "number_windows_field"):
                                                    decomp_app.number_windows_field.setValue(int(value))
                                                elif field == "threshold_target" and hasattr(decomp_app, "threshold_target_field"):
                                                    decomp_app.threshold_target_field.setValue(float(value))
                                                elif field == "nbextchan" and hasattr(decomp_app, "nb_extended_channels_field"):
                                                    decomp_app.nb_extended_channels_field.setValue(int(value))
                                                elif field == "duplicatesthresh" and hasattr(decomp_app, "duplicate_threshold_field"):
                                                    decomp_app.duplicate_threshold_field.setValue(float(value))
                                                elif field == "silthr" and hasattr(decomp_app, "sil_threshold_field"):
                                                    decomp_app.sil_threshold_field.setValue(float(value))
                                                elif field == "covthr" and hasattr(decomp_app, "cov_threshold_field"):
                                                    decomp_app.cov_threshold_field.setValue(float(value))
                                                
                                                # Dropdown controls
                                                elif field == "checkEMG" and hasattr(decomp_app, "check_emg_dropdown"):
                                                    value = "Yes" if int(value) == 1 else "No"
                                                    index = decomp_app.check_emg_dropdown.findText(value)
                                                    if index >= 0:
                                                        decomp_app.check_emg_dropdown.setCurrentIndex(index)
                                                elif field == "peeloff" and hasattr(decomp_app, "peeloff_dropdown"):
                                                    value = "Yes" if int(value) == 1 else "No"
                                                    index = decomp_app.peeloff_dropdown.findText(value)
                                                    if index >= 0:
                                                        decomp_app.peeloff_dropdown.setCurrentIndex(index)
                                                elif field == "covfilter" and hasattr(decomp_app, "cov_filter_dropdown"):
                                                    value = "Yes" if int(value) == 1 else "No"
                                                    index = decomp_app.cov_filter_dropdown.findText(value)
                                                    if index >= 0:
                                                        decomp_app.cov_filter_dropdown.setCurrentIndex(index)
                                                elif field == "initialization" and hasattr(decomp_app, "initialisation_dropdown"):
                                                    value = "EMG max" if int(value) == 0 else "Random"
                                                    index = decomp_app.initialisation_dropdown.findText(value)
                                                    if index >= 0:
                                                        decomp_app.initialisation_dropdown.setCurrentIndex(index)
                                                elif field == "refineMU" and hasattr(decomp_app, "refine_mus_dropdown"):
                                                    value = "Yes" if int(value) == 1 else "No"
                                                    index = decomp_app.refine_mus_dropdown.findText(value)
                                                    if index >= 0:
                                                        decomp_app.refine_mus_dropdown.setCurrentIndex(index)
                                                elif field == "contrastfunc" and hasattr(decomp_app, "contrast_function_dropdown"):
                                                    value_str = str(value)
                                                    if isinstance(value, (bytes, np.bytes_)):
                                                        value_str = value.decode('utf-8')
                                                    index = decomp_app.contrast_function_dropdown.findText(value_str)
                                                    if index >= 0:
                                                        decomp_app.contrast_function_dropdown.setCurrentIndex(index)
                                            except Exception as param_err:
                                                print(f"Error setting parameter {field}: {param_err}")
                                except Exception as e:
                                    print(f"Error setting parameters: {e}")
                                    traceback.print_exc()
                            
                            # Update file info display
                            file_info = f"File: {filename}\n"
                            if hasattr(decomp_app.emg_obj, "signal_dict"):
                                signal = decomp_app.emg_obj.signal_dict
                                if "data" in signal:
                                    try:
                                        if hasattr(signal["data"], "shape") and len(signal["data"].shape) >= 2:
                                            nchannels, nsamples = signal["data"].shape
                                            file_info += f"Channels: {nchannels}\n"
                                            file_info += f"Samples: {nsamples}\n"
                                    except Exception:
                                        pass
                                      
                                if "fsamp" in signal:
                                    try:
                                        fsamp_value = signal["fsamp"]
                                        if hasattr(fsamp_value, "shape") and fsamp_value.size > 0:
                                            fsamp_value = fsamp_value.item() if fsamp_value.size == 1 else fsamp_value[0]
                                        file_info += f"Sample rate: {fsamp_value} Hz\n"
                                    except Exception:
                                        pass
                                        
                                if "nelectrodes" in signal:
                                    try:
                                        nelectrodes_value = signal["nelectrodes"]
                                        if hasattr(nelectrodes_value, "shape") and nelectrodes_value.size > 0:
                                            nelectrodes_value = nelectrodes_value.item() if nelectrodes_value.size == 1 else nelectrodes_value[0]
                                        file_info += f"Electrodes: {nelectrodes_value}\n"
                                    except Exception:
                                        pass
                                    
                            decomp_app.file_info_display.setText(file_info)
                            
                            # Update UI elements directly
                            decomp_app.edit_field.setText(f"Loaded {filename}")
                            decomp_app.status_text.setText("Visualization loaded successfully")
                            decomp_app.status_progress.setValue(100)

                            decomp_app.update_ui_with_loaded_data()
                            
                            # Count motor units for display
                            total_mus = 0
                            if hasattr(decomp_app, "motor_units_label"):
                                try:
                                    from DecompositionApp import count_motor_units
                                    total_mus = count_motor_units(decomp_app.decomposition_result)
                                    decomp_app.motor_units_label.setText(f"Motor Units: {total_mus}")
                                except Exception as e:
                                    print(f"Error counting motor units: {e}")
                                    decomp_app.motor_units_label.setText("Motor Units: --")
                            
                            # Now restore visualization state from Python structure if it exists
                            if "viz_state" in visualization_data and visualization_data["viz_state"] is not None:
                                viz_state = visualization_data["viz_state"]
                                
                                # Direct restoration approach using last_plot_data - SOLUTION 3
                                if "last_plot_data" in viz_state:
                                    try:
                                        last_plot = viz_state["last_plot_data"]
                                        
                                        # Check if we have the essential plot data
                                        if "time2" in last_plot and "icasig" in last_plot:
                                            # Convert stored arrays to numpy arrays
                                            time = np.array(last_plot["time2"])
                                            icasig = np.array(last_plot["icasig"])
                                            
                                            # Restore Motor Unit Outputs plot
                                            decomp_app.ui_plot_pulsetrain.clear()
                                            
                                            # Use the exact same plotting parameters
                                            decomp_app.ui_plot_pulsetrain.plot(
                                                time, 
                                                icasig, 
                                                pen=pg.mkPen(color="#000000", width=1)
                                            )
                                            
                                            # Restore spike markers
                                            if "spikes" in last_plot and last_plot["spikes"]:
                                                spikes = last_plot["spikes"]
                                                
                                                # Ensure spikes are valid indices
                                                valid_indices = [i for i in spikes if i < len(time)]
                                                
                                                if valid_indices:
                                                    # Create scatter plot item with the exact same appearance
                                                    scatter = pg.ScatterPlotItem(
                                                        x=[time[i] for i in valid_indices],
                                                        y=[icasig[i] for i in valid_indices],
                                                        size=10,
                                                        pen=pg.mkPen(None),
                                                        brush=pg.mkBrush("#FF0000"),
                                                    )
                                                    decomp_app.ui_plot_pulsetrain.addItem(scatter)
                                            
                                            # Set exact Y range as during decomposition
                                            decomp_app.ui_plot_pulsetrain.setYRange(-0.2, 1.5)
                                            
                                            # Restore title with iteration, SIL and CoV information
                                            iteration = last_plot.get("iteration_counter", 0)
                                            sil = last_plot.get("sil", 0)
                                            cov = last_plot.get("cov", 0)
                                            
                                            if isinstance(sil, (int, float)) and isinstance(cov, (int, float)):
                                                title = f"Iteration #{iteration}: SIL = {sil:.4f}, CoV = {cov:.4f}"
                                                decomp_app.ui_plot_pulsetrain.setTitle(title)
                                            
                                            # Restore reference plot with target signal
                                            if "time" in last_plot and "target" in last_plot:
                                                ref_time = np.array(last_plot["time"])
                                                ref_target = np.array(last_plot["target"])
                                                
                                                if len(ref_time) > 0 and len(ref_target) > 0:
                                                    decomp_app.ui_plot_reference.clear()
                                                    decomp_app.ui_plot_reference.plot(
                                                        ref_time, 
                                                        ref_target, 
                                                        pen=pg.mkPen(color="#000000", width=2, style=Qt.PenStyle.DashLine)
                                                    )
                                                    
                                                    # Restore plateau markers if available
                                                    if "plateau_coords" in last_plot and last_plot["plateau_coords"]:
                                                        for coord in last_plot["plateau_coords"]:
                                                            if coord < len(ref_time):
                                                                line = pg.InfiniteLine(
                                                                    pos=ref_time[coord], 
                                                                    angle=90, 
                                                                    pen=pg.mkPen(color="#FF0000", width=2)
                                                                )
                                                                decomp_app.ui_plot_reference.addItem(line)
                                            
                                            # Update the status display
                                            decomp_app.edit_field.setText("Visualization restored successfully")
                                            decomp_app.status_text.setText("Ready")
                                            decomp_app.status_progress.setValue(100)
                                            
                                            # Enable buttons for analysis
                                            if hasattr(decomp_app, 'save_output_button'):
                                                decomp_app.save_output_button.setEnabled(True)
                                            
                                            if hasattr(decomp_app, 'save_visualization_button'):
                                                decomp_app.save_visualization_button.setEnabled(True)
                                            
                                            print("Visualization plots restored directly from last_plot_data")
                                    except Exception as e:
                                        print(f"Error in direct restoration from last_plot_data: {e}")
                                        traceback.print_exc()
                                    
                                else:
                                    # Fallback to restoring from individual components
                                    # Restore reference plot
                                    if isinstance(viz_state, dict) and "reference_plot" in viz_state:
                                        try:
                                            ref_data = viz_state["reference_plot"]

                                            # Convert to numpy arrays, ensure they're not scalars
                                            time = np.array(ref_data["time"])
                                            target = np.array(ref_data["target"])
                                            
                                            # Check lengths match and are non-zero
                                            if len(time) > 0 and len(target) > 0 and len(time) == len(target):
                                                decomp_app.ui_plot_reference.clear()
                                                decomp_app.ui_plot_reference.plot(
                                                    time, target,
                                                    pen=pg.mkPen(color="#000000", width=2, style=Qt.PenStyle.DashLine)
                                                )
                                        except Exception as ref_err:
                                            print(f"Error restoring reference plot: {ref_err}")
                                            traceback.print_exc()
                                    
                                    # Restore plateau markers
                                    if "plateau_markers" in viz_state:
                                        try:
                                            markers = viz_state["plateau_markers"]
                                            for marker_pos in markers:
                                                line = pg.InfiniteLine(
                                                    pos=float(marker_pos), angle=90, pen=pg.mkPen(color="#FF0000", width=2)
                                                )
                                                decomp_app.ui_plot_reference.addItem(line)
                                        except Exception as marker_err:
                                            print(f"Error restoring plateau markers: {marker_err}")
                                            traceback.print_exc()
                                    
                                    # Restore pulse train plots
                                    if "pulse_plot" in viz_state:
                                        try:
                                            decomp_app.ui_plot_pulsetrain.clear()
                                            
                                            for pulse_item in viz_state["pulse_plot"]:
                                                # Convert to numpy arrays, ensure they're not scalars
                                                time = np.array(pulse_item["time"])
                                                values = np.array(pulse_item["values"])
                                                color = pulse_item.get("color", "#000000")
                                                
                                                # Check lengths match and are non-zero
                                                if len(time) > 0 and len(values) > 0 and len(time) == len(values):
                                                    decomp_app.ui_plot_pulsetrain.plot(
                                                        time, values,
                                                        pen=pg.mkPen(color=color, width=1)
                                                    )
                                        except Exception as pulse_err:
                                            print(f"Error restoring pulse plots: {pulse_err}")
                                            traceback.print_exc()
                                    
                                    # Restore scatter plots (spikes)
                                    if "scatter_plot" in viz_state:
                                        try:
                                            for scatter_item in viz_state["scatter_plot"]:
                                                # Convert to numpy arrays, ensure they're not scalars
                                                x = np.array(scatter_item["x"])
                                                y = np.array(scatter_item["y"])
                                                size = scatter_item.get("size", 10)
                                                color = scatter_item.get("color", "#FF0000")
                                                
                                                # Check lengths match and are non-zero
                                                if len(x) > 0 and len(y) > 0 and len(x) == len(y):
                                                    scatter = pg.ScatterPlotItem(
                                                        x=x, y=y,
                                                        size=size,
                                                        pen=pg.mkPen(None),
                                                        brush=pg.mkBrush(color)
                                                    )
                                                    decomp_app.ui_plot_pulsetrain.addItem(scatter)
                                        except Exception as scatter_err:
                                            print(f"Error restoring scatter plots: {scatter_err}")
                                            traceback.print_exc()
                                    
                                    # Restore pulse plot title
                                    if "pulse_plot_title" in viz_state:
                                        try:
                                            title = viz_state["pulse_plot_title"]
                                            decomp_app.ui_plot_pulsetrain.setTitle(title)
                                        except Exception as title_err:
                                            print(f"Error restoring plot title: {title_err}")
                                            traceback.print_exc()
                                    
                                    # Restore Y range
                                    if "pulse_plot_y_range" in viz_state:
                                        try:
                                            y_range = viz_state["pulse_plot_y_range"]
                                            if len(y_range) >= 2:
                                                decomp_app.ui_plot_pulsetrain.setYRange(y_range[0], y_range[1])
                                        except Exception as range_err:
                                            print(f"Error restoring Y range: {range_err}")
                                            traceback.print_exc()
                                            # Use default range
                                            decomp_app.ui_plot_pulsetrain.setYRange(-0.2, 1.5)
                                    else:
                                        # Use default range
                                        decomp_app.ui_plot_pulsetrain.setYRange(-0.2, 1.5)
                                    
                                    # Restore statistics
                                    if "statistics" in viz_state:
                                        try:
                                            stats = viz_state["statistics"]
                                            sil = stats.get("sil", 0)
                                            cov = stats.get("cov", 0)
                                            iteration = stats.get("iteration", 0)
                                            
                                            if hasattr(decomp_app, "sil_value_label") and hasattr(decomp_app, "cov_value_label"):
                                                decomp_app.sil_value_label.setText(f"SIL: {sil:.4f}")
                                                decomp_app.cov_value_label.setText(f"CoV: {cov:.4f}")
                                                decomp_app.iteration_counter = iteration
                                        except Exception as stats_err:
                                            print(f"Error restoring statistics: {stats_err}")
                                            traceback.print_exc()
                            else:
                                # If no visualization state, use default
                                decomp_app.ui_plot_pulsetrain.setYRange(-0.2, 1.5)
                            
                            # Enable buttons for analysis
                            if hasattr(decomp_app, 'save_output_button'):
                                decomp_app.save_output_button.setEnabled(True)
                            
                            # Enable visualization save button if it exists
                            if hasattr(decomp_app, 'save_visualization_button'):
                                decomp_app.save_visualization_button.setEnabled(True)
                            
                            # Enable edit mode button if it exists
                            if hasattr(decomp_app, 'edit_mode_btn'):
                                decomp_app.edit_mode_btn.setEnabled(True)
                        else:
                            print("No signal data found in MAT file")
                    
                    except Exception as e:
                        print(f"Error loading visualization data: {e}")
                        traceback.print_exc()
                        # Add a custom error message to alert the user
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            self,
                            "Visualization Load Error",
                            f"Could not load visualization data: {str(e)}"
                        )
                else:
                    print(f"Visualization file not found: {filepath}")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "File Not Found",
                        f"The visualization file could not be found at the specified location:\n{filepath}"
                    )

            # Set window flags to make it a widget instead of a window
            decomp_app.setWindowFlags(Qt.WindowType.Widget)

            # Add to layout
            wrapper_layout.addWidget(decomp_app)

            # Connect back button to show dashboard
            if hasattr(decomp_app, "back_to_import_btn"):
                decomp_app.back_to_import_btn.clicked.connect(self.show_dashboard_view)

            # Replace the placeholder with our real decomposition view
            self.decomposition_page = wrapper

            # Remove the old placeholder if it exists
            for i in range(self.central_stacked_widget.count()):
                widget = self.central_stacked_widget.widget(i)
                if widget and (
                    widget.objectName() == "decomposition_placeholder"
                    or (hasattr(widget, "objectName") and widget.objectName() == "decomposition_placeholder")
                ):
                    self.central_stacked_widget.removeWidget(widget)
                    break

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(wrapper)

            # Show the decomposition view
            self.show_decomposition_view()

        except Exception as e:
            print(f"Error creating decomposition view: {e}")
            traceback.print_exc()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Error",
                f"Failed to create decomposition view: {str(e)}"
            )

    def connect_signals(self):
        """Connect UI signals to slot methods."""
        # Connect sidebar buttons
        self.sidebar_buttons["dashboard"].clicked.connect(self.show_dashboard_view)
        self.sidebar_buttons["mu_analysis"].clicked.connect(self.show_mu_analysis_view)
        self.sidebar_buttons["decomposition"].clicked.connect(self.show_decomposition_view)
        self.sidebar_buttons["manual_edit"].clicked.connect(self.show_manual_editing_view)

        if ImportDataWindow:
            self.sidebar_buttons["import"].clicked.connect(self.show_import_data_view)
        else:
            self.sidebar_buttons["import"].setEnabled(False)

        if not MUAnalysis:
            self.sidebar_buttons["mu_analysis"].setEnabled(False)

        # Connect "New Analysis" button on the dashboard
        new_viz_btn = None
        content_widget = self.dashboard_page.widget()
        if content_widget and content_widget.layout():
            for layout_idx in range(content_widget.layout().count()):
                item = content_widget.layout().itemAt(layout_idx)
                if item and isinstance(item.layout(), QHBoxLayout):
                    for i in range(item.layout().count()):
                        layout_item = item.layout().itemAt(i)
                        if layout_item and layout_item.widget():
                            widget = layout_item.widget()
                            if isinstance(widget, QPushButton) and widget.text() == "+ New Analysis":
                                new_viz_btn = widget
                                break
                if new_viz_btn:
                    break

        if new_viz_btn and ImportDataWindow:
            new_viz_btn.clicked.connect(self.show_import_data_view)
            
        # Connect visualization cards to open_visualization method
        self.connect_visualization_cards()

    def connect_visualization_cards(self):
        """
        Connect all visualization cards to their click handlers.
        This allows users to click on recent visualization cards to reopen them.
        """
        try:
            content_widget = self.dashboard_page.widget()
            if not content_widget:
                return
                
            # Import the VisualizationCard class directly from the module
            # This approach avoids potential import issues
            try:
                from ui.components.VisualizationCard import VisualizationCard
                # Find all visualization cards
                cards = content_widget.findChildren(VisualizationCard)
                
                for card in cards:
                    # Disconnect existing connections first to avoid duplicates
                    try:
                        card.clicked.disconnect()
                    except (TypeError, RuntimeError):
                        pass  # No connections to disconnect or card is invalid
                        
                    # Connect with the visualization data
                    if hasattr(card, 'viz_data') and card.viz_data:
                        # Use a lambda with default arg to capture the current value
                        card.clicked.connect(lambda checked=False, data=card.viz_data: self.open_visualization(data))
            except ImportError:
                print("WARNING: Could not find VisualizationCard class for connecting")
        except Exception as e:
            print(f"Error connecting visualization cards: {e}")
            traceback.print_exc()

    # Navigation methods
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")
        
        # Refresh recent visualizations list if storage is available
        if has_viz_storage and self.viz_storage:
            self.recent_visualizations = self.viz_storage.get_visualizations()
            
            # Try to update the visualization cards with fresh data
            try:
                # Find the visualizations section and update it
                from ui.HDEMGDashboardUI import refresh_visualizations_section
                refresh_visualizations_section(self)
            except (ImportError, AttributeError):
                # If the refresh function is not available, just reconnect cards
                self.connect_visualization_cards()

        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)
        update_sidebar_selection(self, "dashboard")

    def show_mu_analysis_view(self):
        """Switches the central widget to the MU Analysis page."""
        if hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
            print("Switching to MU Analysis View")
            self.central_stacked_widget.setCurrentWidget(self.mu_analysis_page)
            update_sidebar_selection(self, "mu_analysis")
        else:
            print("MU Analysis view is not available.")

    def show_import_data_view(self):
        """Switches the central widget to the Import Data page."""
        if ImportDataWindow is None or self.import_data_page is None:
            print("ImportDataWindow not available.")
            return
        print("Switching to Import Data view")
        self.central_stacked_widget.setCurrentWidget(self.import_data_page)
        update_sidebar_selection(self, "import")

    def show_manual_editing_view(self):
        """Switches to Manual Editing view."""
        print("Switching to Manual Editing View")
        if hasattr(self, "manual_editing_page") and self.manual_editing_page:
            self.central_stacked_widget.setCurrentWidget(self.manual_editing_page)
            update_sidebar_selection(self, "manual_edit")
        else:
            print("Manual Editing view widget not found.")

    def show_decomposition_view(self):
        """Switches to Decomposition view."""
        print("Switching to Decomposition View")
        if hasattr(self, "decomposition_page") and self.decomposition_page:
            self.central_stacked_widget.setCurrentWidget(self.decomposition_page)
            update_sidebar_selection(self, "decomposition")
        else:
            print("Decomposition view widget not found.")

    def open_visualization(self, visualization_data):
        """
        Handles opening a saved visualization.
        
        Args:
            visualization_data: Dictionary with metadata about the visualization to open
        """
        if isinstance(visualization_data, str):
            # Old-style function with just the title
            print(f"Clicked visualization/analysis card: {visualization_data}")
            # Map visualization titles to corresponding views
            if "HDEMG Analysis" in visualization_data and hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
                self.show_mu_analysis_view()
            else:
                print(f"No specific action defined for card '{visualization_data}'. Staying on Dashboard.")
            return
            
        # New-style function with visualization data dictionary
        if not visualization_data:
            print("No visualization data provided")
            return
            
        print(f"Opening visualization: {visualization_data.get('title')}")
        
        # Check if the file exists
        filepath = visualization_data.get('filepath')
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The visualization file could not be found at the specified location:\n{filepath}"
            )
            return
            
        try:
            # Create a decomposition view with the visualization data
            self.create_decomposition_view(visualization_data=visualization_data)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening Visualization",
                f"Failed to open visualization: {str(e)}"
            )
            traceback.print_exc()

    def open_export_results_window(self):
        """Opens the Export Results window, creating it if necessary."""
        print(">>> Main Window: Request received to open Export Results window.")
        if ExportResultsWindow is None:
            print("ERROR: ExportResultsWindow class is not available (check import).")
            return

        window_exists = False
        if self.export_results_window:
            try:
                # Check if the window still exists and hasn't been closed/deleted
                if self.export_results_window.isVisible() or not self.export_results_window.isHidden():
                    window_exists = True
                    print(">>> Main Window: Existing ExportResultsWindow instance seems valid.")
                else:
                    print(
                        ">>> Main Window: Existing window reference present but window is hidden/closed; will create new."
                    )
                    self.export_results_window = None  # Force recreation
                    window_exists = False
            except RuntimeError:  # Window was likely deleted
                print(">>> Main Window: Existing window reference invalid (RuntimeError); will create new.")
                self.export_results_window = None
                window_exists = False
            except Exception as e:  # Catch other potential issues
                print(f">>> Main Window: Error checking existing window ({type(e).__name__}); will create new.")
                self.export_results_window = None
                window_exists = False

        if not window_exists:
            try:
                print(">>> Main Window: Creating NEW ExportResultsWindow instance.")
                # Ensure it's created as a top-level window (parent=None)
                self.export_results_window = ExportResultsWindow(parent=None)
                # Position it relative to the main window for convenience
                main_geo = self.geometry()
                new_x = main_geo.x() + 100
                new_y = main_geo.y() + 100
                width = 600  # Define desired size
                height = 550
                self.export_results_window.setGeometry(new_x, new_y, width, height)
                print(f">>> Set geometry for new window to ({new_x}, {new_y}, {width}, {height})")
            except Exception as e:
                print(f"FATAL ERROR during ExportResultsWindow creation: {e}")
                traceback.print_exc()
                self.export_results_window = None  # Ensure it's None if creation failed
                return  # Stop execution here

        # After potentially creating or confirming existence, try to show/activate
        if self.export_results_window:
            try:
                print(">>> Main Window: Attempting to show and activate ExportResultsWindow.")
                self.export_results_window.show()
                self.export_results_window.raise_()  # Bring to front
                self.export_results_window.activateWindow()  # Give focus
                QApplication.processEvents()  # Ensure UI updates
                print(">>> ExportResultsWindow shown and activated.")
            except RuntimeError:  # Catch if window was deleted between check and show
                print(">>> Error: ExportResultsWindow was deleted before it could be shown.")
                self.export_results_window = None
            except Exception as e:
                print(f"Error displaying/activating ExportResultsWindow: {e}")
                traceback.print_exc()
        else:
            print("ERROR - self.export_results_window is None even after creation attempt.")

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())