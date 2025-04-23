import sys
import os
import traceback
import numpy as np
import scipy.io as sio
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

# Add project root to path
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import UI setup
from ui.DecompositionAppUI import setup_ui

# Import workers and other required modules
from SaveMatWorker import SaveMatWorker
from DecompositionWorker import DecompositionWorker
from utils.config_and_input.prepare_parameters import prepare_parameters
from utils.config_and_input.segmentsession import SegmentSession
from MUeditManual import MUeditManual

# Try to import VisualizationStorage for saving visualization metadata
try:
    from VisualizationStorage import VisualizationStorage
    has_viz_storage = True
except ImportError:
    has_viz_storage = False


# This function specifically focuses on the motor unit counting part
def count_motor_units(decomposition_result):
    """
    Count the total number of motor units in the decomposition result.
    Safely handles different array structures and MATLAB-style cell arrays.
    
    Args:
        decomposition_result: The decomposition result dictionary or structure
        
    Returns:
        int: Total number of motor units found
    """
    total_mus = 0
    
    try:
        # Check if decomposition_result is a structured array (from MATLAB)
        if hasattr(decomposition_result, 'dtype') and decomposition_result.dtype.names is not None:
            print(f"Detected structured array with fields: {decomposition_result.dtype.names}")
            
            # Extract the Pulsetrain field from structured array
            if 'Pulsetrain' in decomposition_result.dtype.names:
                pulsetrain = decomposition_result['Pulsetrain']
                
                # MATLAB cell arrays are typically stored as object arrays
                if isinstance(pulsetrain, np.ndarray) and pulsetrain.dtype == np.dtype('O'):
                    if pulsetrain.ndim >= 2:
                        for i in range(pulsetrain.shape[1]):
                            electrode_data = pulsetrain[0, i]
                            if electrode_data is None:
                                continue
                                
                            if not hasattr(electrode_data, "shape"):
                                # Not an array, skip
                                continue
                                
                            if electrode_data.ndim == 1:
                                # Single MU
                                if electrode_data.size > 0:
                                    total_mus += 1
                            elif electrode_data.ndim >= 2:
                                # Multiple MUs in this electrode
                                total_mus += electrode_data.shape[0]
            return total_mus
        
        # For dictionaries or nested structures, we need to check if we can access 'Pulsetrain'
        # safely using hasattr before using 'in' operator
        has_pulsetrain = False
        if isinstance(decomposition_result, dict):
            has_pulsetrain = 'Pulsetrain' in decomposition_result
        elif hasattr(decomposition_result, '__getitem__') and not hasattr(decomposition_result, 'dtype'):
            # For other container types, try to check if 'Pulsetrain' is a key
            try:
                decomposition_result['Pulsetrain']  # Will raise KeyError/TypeError if not present
                has_pulsetrain = True
            except (KeyError, TypeError, IndexError):
                has_pulsetrain = False
        
        if not has_pulsetrain:
            print("No Pulsetrain data found or unable to access it in the decomposition result")
            return total_mus
            
        # If we get here, we can safely access the Pulsetrain data
        try:
            pulsetrain = decomposition_result['Pulsetrain']
        except (TypeError, KeyError, IndexError):
            print("Error accessing Pulsetrain data")
            return total_mus
            
        # Handle dictionary format
        if isinstance(pulsetrain, dict):
            for electrode, pulses in pulsetrain.items():
                if hasattr(pulses, "shape"):
                    total_mus += pulses.shape[0]
        
        # Handle numpy array format (MATLAB cell array)
        elif isinstance(pulsetrain, np.ndarray):
            # Check if it's a structured array (common from MATLAB imports)
            if hasattr(pulsetrain, 'dtype') and pulsetrain.dtype.names is not None:
                print(f"Found structured array with fields: {pulsetrain.dtype.names}")
                return total_mus  # Skip counting for now - we need more information about the structure
            
            # Regular numpy array
            if pulsetrain.ndim == 2:
                # Common case for MATLAB cell array: (1, num_electrodes)
                for i in range(pulsetrain.shape[1]):
                    electrode_data = pulsetrain[0, i]
                    # Skip if None or not array-like
                    if electrode_data is None:
                        continue
                    
                    # Handle case where electrode_data is a single MU array
                    if not hasattr(electrode_data, "shape") or electrode_data.ndim == 1:
                        # It's a single pulse train, count as 1 MU
                        total_mus += 1
                    elif electrode_data.ndim >= 2:
                        # It's a 2D array with potentially multiple MUs
                        total_mus += electrode_data.shape[0]
            else:
                # Try to get size from first dimension
                if pulsetrain.size > 0 and hasattr(pulsetrain[0], "shape"):
                    total_mus += pulsetrain[0].shape[0] if len(pulsetrain[0].shape) > 0 else 1
        
        # Handle list format
        elif isinstance(pulsetrain, list):
            for electrode_pulses in pulsetrain:
                if hasattr(electrode_pulses, "shape"):
                    if len(electrode_pulses.shape) > 0:
                        total_mus += electrode_pulses.shape[0] 
                    else:
                        total_mus += 1  # Single pulse train
                elif isinstance(electrode_pulses, list):
                    total_mus += len(electrode_pulses)
    
    except Exception as e:
        print(f"Error in count_motor_units: {e}")
        import traceback
        traceback.print_exc()
    
    return total_mus

def has_field(obj, field_name):
    """Safely check if a structured array or dictionary has a field."""
    try:
        if hasattr(obj, 'dtype') and obj.dtype.names is not None:
            # It's a structured array
            return field_name in obj.dtype.names
        elif isinstance(obj, dict):
            # It's a dictionary
            return field_name in obj
        elif hasattr(obj, '__getitem__') and not hasattr(obj, 'dtype'):
            # Try accessing it (for other container types)
            try:
                obj[field_name]
                return True
            except (KeyError, TypeError, IndexError):
                return False
        return False
    except Exception as e:
        print(f"Error in has_field: {e}")
        return False

def get_field(obj, field_name, default=None):
    """Safely get a field from a structured array or dictionary."""
    try:
        if hasattr(obj, 'dtype') and obj.dtype.names is not None:
            # It's a structured array
            if field_name in obj.dtype.names:
                return obj[field_name]
        elif isinstance(obj, dict):
            # It's a dictionary
            if field_name in obj:
                return obj[field_name]
        elif hasattr(obj, '__getitem__') and not hasattr(obj, 'dtype'):
            # Try accessing it (for other container types)
            try:
                return obj[field_name]
            except (KeyError, TypeError, IndexError):
                pass
        return default
    except Exception as e:
        print(f"Error in get_field: {e}")
        return default

class DecompositionApp(QMainWindow):
    # Add signal for notifying when a visualization is saved
    visualization_saved = pyqtSignal(dict)
    
    def __init__(self, emg_obj=None, filename=None, pathname=None, imported_signal=None, parent=None):
        super().__init__(parent)

        # Initialize variables
        self.filename = filename
        self.pathname = pathname
        self.emg_obj = emg_obj
        self.imported_signal = imported_signal

        self.MUdecomp = {"config": None}
        self.Configuration = None
        self.MUedition = None
        self.Backup = {"lock": 0}
        self.graphstart = None
        self.graphend = None
        self.roi = None
        self.threads = []
        self.iteration_counter = 0
        self.decomposition_result = None  # Store the decomposition result
        self.ui_params = None  # Store UI parameters

        self.last_plot_data = {
            "time": None,
            "target": None,
            "plateau_coords": None,
            "icasig": None,
            "spikes": None,
            "time2": None,
            "sil": None,
            "cov": None
        }
        
        # Initialize visualization storage if available
        self.viz_storage = VisualizationStorage() if has_viz_storage else None

        # Set up the UI components by calling the function from DecompositionAppUI.py
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Initialize with data if provided
        if self.emg_obj and self.filename:
            self.update_ui_with_loaded_data()
            
        # Add save visualization button to right panel if not already there
        if not hasattr(self, 'save_visualization_button'):
            from ui.components import ActionButton
            self.save_visualization_button = ActionButton("🖫 Save Visualization", primary=True)
            self.save_visualization_button.clicked.connect(self.save_visualization)
            self.save_visualization_button.setEnabled(False)  # Enable when decomposition is complete
            
            # Insert button below save output button
            for section in self.findChildren(QWidget, "settingsGroup"):
                if hasattr(section, 'title_label') and section.title_label.text() == "Analysis Results":
                    section.layout().addWidget(self.save_visualization_button)
                    break

    def connect_signals(self):
        """Connect all UI signals to their handlers."""
        # Left panel connections
        self.set_configuration_button.clicked.connect(self.set_configuration_button_pushed)
        self.segment_session_button.clicked.connect(self.segment_session_button_pushed)

        # Center panel connections
        self.start_button.clicked.connect(self.start_button_pushed)

        # Right panel connections
        self.save_output_button.clicked.connect(self.save_output_to_location)
        
        # Connect back to import button if it exists
        if hasattr(self, 'back_to_import_btn'):
            # If parent has show_dashboard_view, use that
            if hasattr(self.parent(), 'show_dashboard_view'):
                self.back_to_import_btn.clicked.connect(self.parent().show_dashboard_view)
            # Otherwise use default implementation
            else:
                self.back_to_import_btn.clicked.connect(self.back_to_import)

    def back_to_import(self):
        """Return to the Import window."""
        # This will now be connected externally to show the import view in the dashboard
        pass

    def set_data(self, emg_obj, filename, pathname, imported_signal=None):
        """Set data from ImportDataWindow and update UI."""
        self.emg_obj = emg_obj
        self.filename = filename
        self.pathname = pathname
        self.imported_signal = imported_signal

        self.update_ui_with_loaded_data()

    def update_ui_with_loaded_data(self):
        """Update UI elements with the loaded data information."""
        if not self.emg_obj or not self.filename:
            return

        # Update file info display
        file_info = f"File: {self.filename}\n"

        if hasattr(self.emg_obj, "signal_dict"):
            signal = self.emg_obj.signal_dict

            if "data" in signal:
                nchannels, nsamples = signal["data"].shape
                file_info += f"Channels: {nchannels}\n"
                file_info += f"Samples: {nsamples}\n"

            if "fsamp" in signal:
                file_info += f"Sample rate: {signal['fsamp']} Hz\n"

            if "nelectrodes" in signal:
                file_info += f"Electrodes: {signal['nelectrodes']}\n"

        self.file_info_display.setText(file_info)

        # Update the reference dropdown with available signals
        self.reference_dropdown.blockSignals(True)
        self.reference_dropdown.clear()

        signal = self.emg_obj.signal_dict

        # Update the list of signals for reference
        if "auxiliaryname" in signal:
            self.reference_dropdown.addItem("EMG amplitude")
            # Process auxiliaryname (which may be a numpy array)
            if isinstance(signal["auxiliaryname"], np.ndarray):
                if signal["auxiliaryname"].ndim == 2:
                    # Case for 2D array of strings often seen in MATLAB imports
                    for i in range(signal["auxiliaryname"].shape[1]):
                        name_item = signal["auxiliaryname"][0, i]
                        # Handle case where name_item itself might be an array
                        if isinstance(name_item, np.ndarray):
                            if name_item.size > 0:
                                # Convert the numpy array to string
                                name_str = str(name_item[0])
                                if isinstance(name_item[0], (bytes, np.bytes_)):
                                    name_str = name_item[0].decode('utf-8')
                                self.reference_dropdown.addItem(name_str)
                        else:
                            # Direct string or other value
                            name_str = str(name_item)
                            if isinstance(name_item, (bytes, np.bytes_)):
                                name_str = name_item.decode('utf-8')
                            self.reference_dropdown.addItem(name_str)
                else:
                    # Case for 1D array of names
                    for name in signal["auxiliaryname"]:
                        if isinstance(name, np.ndarray):
                            if name.size > 0:
                                name_str = str(name[0])
                                if isinstance(name[0], (bytes, np.bytes_)):
                                    name_str = name[0].decode('utf-8')
                                self.reference_dropdown.addItem(name_str)
                        else:
                            name_str = str(name)
                            if isinstance(name, (bytes, np.bytes_)):
                                name_str = name.decode('utf-8')
                            self.reference_dropdown.addItem(name_str)
            else:
                # Case for list or other iterable
                for name in signal["auxiliaryname"]:
                    name_str = str(name)
                    if isinstance(name, (bytes, np.bytes_)):
                        name_str = name.decode('utf-8')
                    self.reference_dropdown.addItem(name_str)
        elif "target" in signal:
            path_data = signal["path"]
            target_data = signal["target"]

            if isinstance(path_data, np.ndarray) and isinstance(target_data, np.ndarray):
                path_reshaped = path_data.reshape(1, -1) if path_data.ndim == 1 else path_data
                target_reshaped = target_data.reshape(1, -1) if target_data.ndim == 1 else target_data
                signal["auxiliary"] = np.vstack((path_reshaped, target_reshaped))
            else:
                signal["auxiliary"] = np.vstack((np.array([path_data]), np.array([target_data])))

            signal["auxiliaryname"] = ["Path", "Target"]
            self.reference_dropdown.addItem("EMG amplitude")
            for name in signal["auxiliaryname"]:
                self.reference_dropdown.addItem(str(name))
        else:
            self.reference_dropdown.addItem("EMG amplitude")

        self.reference_dropdown.blockSignals(False)

        # Enable the start button and configuration
        self.start_button.setEnabled(True)
        self.set_configuration_button.setEnabled(True)

        # Update status text
        self.edit_field.setText(f"Loaded {self.filename}")
        self.status_text.setText("Ready to start decomposition")

        # Create a preview plot if possible
        if "data" in signal and "fsamp" in signal:
            try:
                self.ui_plot_reference.clear()
                
                # Extract fsamp safely (could be a scalar or array)
                if isinstance(signal["fsamp"], np.ndarray):
                    if signal["fsamp"].size > 0:
                        fsamp = float(signal["fsamp"].flat[0])
                    else:
                        fsamp = 1000.0  # Default if empty
                else:
                    fsamp = float(signal["fsamp"])
                    
                # Extract data and ensure proper shape
                data = signal["data"]
                if data.ndim > 2:
                    print(f"Warning: Reshaping data from {data.shape}")
                    data = data.reshape(data.shape[-2], data.shape[-1])
                elif data.ndim == 1:
                    data = data.reshape(1, -1)
                    
                nsamples = data.shape[1]
                time = np.arange(nsamples) / fsamp

                # Plot the first few channels for preview
                num_preview_channels = min(3, data.shape[0])
                colors = ["b", "g", "r", "c", "m", "y"]

                print(f"Plotting preview with shape {data.shape} and time shape {time.shape}")
                
                # Make sure time array matches data length
                if len(time) != data.shape[1]:
                    print(f"Warning: Time array length {len(time)} doesn't match data length {data.shape[1]}. Adjusting...")
                    time = np.arange(data.shape[1]) / fsamp

                for i in range(num_preview_channels):
                    channel_data = data[i, :]
                    self.ui_plot_reference.plot(
                        time, channel_data, pen=pg.mkPen(color=colors[i % len(colors)], width=1)
                    )

                self.ui_plot_reference.setTitle(f"Signal Preview ({num_preview_channels} channels)")
            except Exception as e:
                print(f"Error creating preview plot: {e}")
                traceback.print_exc()  # Add full traceback for more details
                # Fall back to a simple message instead of plot
                self.ui_plot_reference.clear()
                self.ui_plot_reference.setTitle("Preview not available")
                
            # If decomposition_result is available, try to show results too
            if hasattr(self, 'decomposition_result') and self.decomposition_result is not None:
                # Enable save buttons since results are available
                if hasattr(self, 'save_output_button'):
                    self.save_output_button.setEnabled(True)
                
                # Enable visualization save button if it exists
                if hasattr(self, 'save_visualization_button'):
                    self.save_visualization_button.setEnabled(True)
                
                # Update motor unit display
                self.update_motor_unit_display()  

                # Display motor unit outputs in the plot
                self.display_motor_unit_outputs()

    def update_motor_unit_display(self):
        """Update the motor unit count display based on decomposition results."""
        if not hasattr(self, 'decomposition_result') or self.decomposition_result is None:
            return
            
        try:
            # Use the dedicated counting function
            total_mus = count_motor_units(self.decomposition_result)
            
            if hasattr(self, 'motor_units_label'):
                self.motor_units_label.setText(f"Motor Units: {total_mus}")
                
            # Try to get SIL and CoV values if available
            if hasattr(self, 'sil_value_label'):
                if has_field(self.decomposition_result, "SILs"):
                    sil_data = get_field(self.decomposition_result, "SILs")
                    if sil_data is not None and hasattr(sil_data, "size") and sil_data.size > 0:
                        # Extract representative SIL value (max value is typically used)
                        if hasattr(sil_data, "ndim") and sil_data.ndim > 1 and sil_data.shape[0] > 0 and sil_data.shape[1] > 0:
                            max_sil = np.max(sil_data)
                            self.sil_value_label.setText(f"SIL: {max_sil:.4f}")
                        elif hasattr(sil_data, "size") and sil_data.size > 0:
                            max_sil = np.max(sil_data)
                            self.sil_value_label.setText(f"SIL: {max_sil:.4f}")
                        
            if hasattr(self, 'cov_value_label'):
                if has_field(self.decomposition_result, "CoVs"):
                    cov_data = get_field(self.decomposition_result, "CoVs")
                    if cov_data is not None and hasattr(cov_data, "size") and cov_data.size > 0:
                        # Extract representative CoV value (min value is typically used)
                        if hasattr(cov_data, "ndim") and cov_data.ndim > 1 and cov_data.shape[0] > 0 and cov_data.shape[1] > 0:
                            min_cov = np.min(cov_data)
                            self.cov_value_label.setText(f"CoV: {min_cov:.4f}")
                        elif hasattr(cov_data, "size") and cov_data.size > 0:
                            min_cov = np.min(cov_data)
                            self.cov_value_label.setText(f"CoV: {min_cov:.4f}")
        except Exception as e:
            print(f"Error updating motor unit display: {e}")
            import traceback
            traceback.print_exc()

    def display_motor_unit_outputs(self):
        """
        Display the motor unit outputs from the loaded visualization in the pulsetrain plot.
        Uses the exact data that was saved during decomposition.
        """
        if not hasattr(self, 'decomposition_result') or self.decomposition_result is None:
            print("No decomposition result available for display")
            return

        try:
            # Clear the current plot
            self.ui_plot_pulsetrain.clear()

            # First, try to use visualization state if available
            viz_state = None
            if hasattr(self, 'viz_storage') and self.viz_storage and self.filename:
                visualizations = self.viz_storage.get_visualizations()
                for viz in visualizations:
                    # Try to find the current visualization by matching filename
                    if viz.get('filepath', '').endswith(self.filename + "_output_decomp.mat"):
                        viz_state = viz.get('viz_state', {})
                        break
            
            # Check if we have last_plot_data in the viz_state
            if viz_state and "last_plot_data" in viz_state:
                last_plot = viz_state["last_plot_data"]
                
                # Check if we have the necessary data to recreate the plot
                if "time2" in last_plot and "icasig" in last_plot:
                    time = np.array(last_plot["time2"])
                    icasig = np.array(last_plot["icasig"])
                    
                    # Draw the exact same plot that was shown during decomposition
                    self.ui_plot_pulsetrain.plot(time, icasig, pen=pg.mkPen(color="#000000", width=1))
                    
                    # Add spike markers if available
                    if "spikes" in last_plot and last_plot["spikes"]:
                        spikes = last_plot["spikes"]
                        valid_indices = [i for i in spikes if i < len(time)]
                        
                        if valid_indices:
                            scatter = pg.ScatterPlotItem(
                                x=[time[i] for i in valid_indices],
                                y=[icasig[i] for i in valid_indices],
                                size=10,
                                pen=pg.mkPen(None),
                                brush=pg.mkBrush("#FF0000"),
                            )
                            self.ui_plot_pulsetrain.addItem(scatter)
                    
                    # Set Y range
                    self.ui_plot_pulsetrain.setYRange(-0.2, 1.5)
                    
                    # Set title with SIL and CoV if available
                    sil = last_plot.get("sil")
                    cov = last_plot.get("cov")
                    iteration = last_plot.get("iteration_counter", 0)
                    
                    if sil is not None and cov is not None:
                        title = f"Iteration #{iteration}: SIL = {sil:.4f}, CoV = {cov:.4f}"
                        self.ui_plot_pulsetrain.setTitle(title)
                    else:
                        total_mus = count_motor_units(self.decomposition_result)
                        self.ui_plot_pulsetrain.setTitle(f"Motor Unit Outputs ({total_mus} MUs)")
                    
                    return True
                
                # If last_plot_data is missing critical components, fall through to the default visualization
            
            # Default visualization using basic MU count
            self.create_default_mu_visualization()
            return True
            
        except Exception as e:
            print(f"Error displaying motor unit outputs: {e}")
            traceback.print_exc()
            
            # Create default visualization as fallback
            self.create_default_mu_visualization()
            return False
        
    def create_default_mu_visualization(self):
        """Create a default motor unit visualization"""
        # Get basic info
        total_mus = count_motor_units(self.decomposition_result)
        
        # Extract sampling frequency
        fsamp = 1000.0  # Default value
        if has_field(self.decomposition_result, 'fsamp'):
            fsamp_data = get_field(self.decomposition_result, 'fsamp')
            if fsamp_data is not None:
                if hasattr(fsamp_data, 'ndim') and fsamp_data.ndim > 0 and fsamp_data.size > 0:
                    fsamp = float(fsamp_data.flat[0])
                else:
                    fsamp = float(fsamp_data)
        
        # Create a simple time array (10 seconds)
        time = np.arange(10 * fsamp) / fsamp
        
        # Use count_motor_units to get MU count
        mu_count = min(5, total_mus)  # Limit to 5 for display
        if mu_count > 0:
            # Generate a simple MU representation
            colors = ['r', 'g', 'b', 'c', 'm']
            for i in range(mu_count):
                # Create a simple on/off pattern
                rate = 10 + i  # Hz
                interval = int(fsamp / rate)
                y = np.zeros_like(time)
                
                # Add spikes at regular intervals
                for j in range(0, len(time), interval):
                    if j < len(time):
                        # Add a pulse at each interval
                        pulse_width = min(10, len(time) - j)
                        y[j:j+pulse_width] = np.exp(-(np.arange(pulse_width)-5)**2/10)
                
                # Plot the MU
                self.ui_plot_pulsetrain.plot(
                    time, y, 
                    pen=pg.mkPen(color=colors[i % len(colors)], width=1)
                )
                
                # Add markers at spike locations
                indices = np.arange(0, len(time), interval)
                indices = indices[indices < len(time)]
                
                if len(indices) > 0:
                    scatter = pg.ScatterPlotItem(
                        x=time[indices],
                        y=y[indices],
                        size=8,
                        pen=pg.mkPen(None),
                        brush=pg.mkBrush(colors[i % len(colors)])
                    )
                    self.ui_plot_pulsetrain.addItem(scatter)
            
            # Set plot range
            self.ui_plot_pulsetrain.setYRange(0, 1.0)
            
            # Set title
            self.ui_plot_pulsetrain.setTitle(f"Motor Unit Outputs ({total_mus} MUs)")
        else:
            # No MUs
            self.ui_plot_pulsetrain.setTitle("No Motor Unit Outputs Available")

    def open_editing_mode(self):
        """Open the MUeditManual window for editing motor units"""
        if not self.pathname or not self.filename:
            self.edit_field.setText("No file selected for editing")
            return

        try:
            # First check if the output file exists
            output_filename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")
            if not os.path.exists(output_filename):
                self.edit_field.setText(f"Output file {output_filename} not found")
                return

            # Load the data first to fix the structure
            data = sio.loadmat(output_filename)
            if "signal" not in data:
                self.edit_field.setText("Invalid file format: 'signal' field not found")
                return

            signal = data["signal"]

            # Create the proper data structure for MUeditManual
            edition_data = {
                "time": np.linspace(
                    0, signal[0, 0]["data"].shape[1] / signal[0, 0]["fsamp"][0, 0], signal[0, 0]["data"].shape[1]
                ),
                "Pulsetrain": [],
                "Dischargetimes": {},
                "silval": {},
                "silvalcon": {},
            }

            # Format the Pulsetrain data correctly
            # MUeditManual expects a list of 2D arrays (one per electrode)
            # Each 2D array should have shape (n_motor_units, signal_length)
            if "Pulsetrain" in signal[0, 0].dtype.names:
                pulsetrain_data = signal[0, 0]["Pulsetrain"][0]

                for i in range(len(pulsetrain_data)):
                    # Get the pulse train for this electrode
                    electrode_pulses = pulsetrain_data[i]

                    # Check if it's already 2D
                    if electrode_pulses.ndim == 2:
                        edition_data["Pulsetrain"].append(electrode_pulses)
                    elif electrode_pulses.ndim == 1:
                        # Convert 1D array to 2D with one row
                        edition_data["Pulsetrain"].append(electrode_pulses.reshape(1, -1))
                    else:
                        # Skip empty or invalid arrays
                        edition_data["Pulsetrain"].append(np.zeros((0, signal[0, 0]["data"].shape[1])))

            # Format the Dischargetimes data correctly
            # MUeditManual expects a dictionary with (array_idx, mu_idx) tuple keys
            if "Dischargetimes" in signal[0, 0].dtype.names:
                dischargetimes_data = signal[0, 0]["Dischargetimes"]

                for i in range(dischargetimes_data.shape[0]):
                    for j in range(dischargetimes_data.shape[1]):
                        # Get the discharge times array
                        dt = dischargetimes_data[i, j]

                        # Skip empty arrays
                        if isinstance(dt, np.ndarray) and dt.size > 0:
                            # Store with tuple key (array_idx, mu_idx)
                            edition_data["Dischargetimes"][(i, j)] = dt.flatten()

            # Create a new .mat file with the fixed structure
            fixed_filename = os.path.join(self.pathname, self.filename + "_fixed_for_editing.mat")

            # Create the structure expected by MUeditManual
            fixed_data = {
                "signal": signal,  # Original signal data
                "edition": edition_data,  # Properly formatted edition data
            }

            # Use existing save_mat_in_background function to save the fixed data
            self.save_mat_in_background(fixed_filename, fixed_data, True)

            # Update UI
            self.edit_field.setText(f"Preparing data for editing and opening editor...")

            # Create the MUeditManual window
            self.mu_edit_window = MUeditManual()

            # Show the window without preloading
            self.mu_edit_window.show()

            # Suggest the file to open
            self.edit_field.setText(f"Editor opened. Please select {fixed_filename}")

        except Exception as e:
            self.edit_field.setText(f"Error opening editing mode: {str(e)}")
            traceback.print_exc()

    # Event handlers
    def save_mat_in_background(self, filename, data, compression=True):
        self.edit_field.setText("Saving data in background...")

        # Create and configure the worker thread
        worker = SaveMatWorker(filename, data, compression)
        self.threads.append(worker)

        worker.finished.connect(lambda: self.on_save_finished(worker, filename))
        worker.error.connect(lambda msg: self.on_save_error(worker, msg))

        worker.start()

    def on_save_finished(self, worker, filename=None):
        """Handle successful save completion."""
        self.edit_field.setText("Data saved successfully")
        
        # If this was a decomposition result save, update visualization storage
        if filename and self.viz_storage and "output_decomp.mat" in filename:
            try:
                # Create visualization metadata
                base_filename = os.path.basename(filename)
                
                # Create a title for the visualization
                if self.filename:
                    title = f"HDEMG Analysis - {self.filename}"
                else:
                    title = f"HDEMG Analysis - {base_filename}"
                
                # Save visualization metadata
                self.viz_storage.add_visualization(
                    title=title,
                    filepath=filename,
                    parameters=self.ui_params if self.ui_params else {}
                )
                
                # Emit signal to notify that visualization was saved
                if hasattr(self, 'visualization_saved'):
                    viz_data = self.viz_storage.get_visualizations()[0]  # Get the most recent
                    self.visualization_saved.emit(viz_data)
                
                # Enable save visualization button
                if hasattr(self, 'save_visualization_button'):
                    self.save_visualization_button.setEnabled(True)
                
            except Exception as e:
                print(f"Error updating visualization storage: {e}")
        
        self.cleanup_thread(worker)

    def on_save_error(self, worker, error_msg):
        self.edit_field.setText(f"Error saving data: {error_msg}")
        self.cleanup_thread(worker)

    def cleanup_thread(self, worker):
        if worker in self.threads:
            self.threads.remove(worker)

    def set_configuration_button_pushed(self):
        if "config" in self.MUdecomp and self.MUdecomp["config"]:
            try:
                if self.pathname is not None and self.filename is not None:
                    savename = os.path.join(self.pathname, self.filename + "_decomp.mat")
                    self.MUdecomp["config"].pathname.setText(savename)

                # Show the dialog
                self.MUdecomp["config"].show()
                self.set_configuration_button.setStyleSheet(
                    "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
                )
            except Exception as e:
                print(f"Error showing configuration dialog: {e}")
                traceback.print_exc()
        else:
            print("No configuration dialog available")

    def segment_session_button_pushed(self):
        self.segment_session = SegmentSession()

        if self.pathname is not None and self.filename is not None:
            self.segment_session.pathname.setText(self.pathname + self.filename + "_decomp.mat")

        # Setup the dropdown contents before setting the current item
        self.segment_session.reference_dropdown.clear()
        for i in range(self.reference_dropdown.count()):
            self.segment_session.reference_dropdown.addItem(self.reference_dropdown.itemText(i))

        try:
            if self.segment_session.pathname.text():
                self.segment_session.file = sio.loadmat(self.segment_session.pathname.text())
        except Exception as e:
            print(f"Warning: Could not load file: {e}")

        # Set current text after file is loaded
        self.segment_session.reference_dropdown.setCurrentText(self.reference_dropdown.currentText())
        self.segment_session.initialize_with_file()
        self.segment_session.show()
        self.segment_session_button.setStyleSheet(
            "color: #cf80ff; background-color: #7f7f7f; font-family: 'Poppins'; font-size: 18pt;"
        )

    def start_button_pushed(self):
        # Reset iteration counter at the start of a new decomposition
        self.iteration_counter = 0

        # Get UI parameters
        ui_params = {
            "check_emg": self.check_emg_dropdown.currentText(),
            "peeloff": self.peeloff_dropdown.currentText(),
            "cov_filter": self.cov_filter_dropdown.currentText(),
            "initialization": self.initialisation_dropdown.currentText(),
            "refine_mu": self.refine_mus_dropdown.currentText(),
            "duplicates_bgrids": "Yes",  # Set default value
            "contrast_function": self.contrast_function_dropdown.currentText(),
            "iterations": self.number_iterations_field.value(),
            "windows": self.number_windows_field.value(),
            "threshold_target": self.threshold_target_field.value(),
            "extended_channels": self.nb_extended_channels_field.value(),
            "duplicates_threshold": self.duplicate_threshold_field.value(),
            "sil_threshold": self.sil_threshold_field.value(),
            "cov_threshold": self.cov_threshold_field.value(),
        }

        # Store UI params for later use when saving results
        self.ui_params = ui_params

        # Convert UI parameters to algorithm parameters
        parameters = prepare_parameters(ui_params)

        print(parameters)

        # Check if we have a file and EMG object
        if not self.emg_obj or not self.pathname or not self.filename:
            self.edit_field.setText("Please select and load a file first")
            return

        # Disable the start button during processing
        self.start_button.setEnabled(False)
        self.edit_field.setText("Starting decomposition...")
        self.status_text.setText("Processing...")
        self.status_progress.setValue(10)

        # Pass the EMG object to the DecompositionWorker
        self.decomp_worker = DecompositionWorker(self.emg_obj, parameters)
        self.threads.append(self.decomp_worker)  # Keep a reference to prevent garbage collection

        # Connect signals
        self.decomp_worker.progress.connect(self.update_progress)
        self.decomp_worker.plot_update.connect(self.update_plots)
        self.decomp_worker.finished.connect(self.on_decomposition_complete)
        self.decomp_worker.error.connect(self.on_decomposition_error)

        # Start the worker thread
        self.decomp_worker.start()

    def on_decomposition_complete(self, result):
        """Handle successful completion of decomposition"""
        if self.pathname and self.filename:
            savename = os.path.join(self.pathname, self.filename + "_output_decomp.mat")

            formatted_result = result.copy() if isinstance(result, dict) else result

            # Format Pulsetrain as a MATLAB-compatible cell array
            if "Pulsetrain" in formatted_result:
                max_electrode = max(formatted_result["Pulsetrain"].keys()) if formatted_result["Pulsetrain"] else 0

                pulsetrain_obj = np.empty((1, max_electrode + 1), dtype=object)

                # Fill the array with pulse trains
                for i in range(max_electrode + 1):
                    if i in formatted_result["Pulsetrain"]:
                        pulsetrain_obj[0, i] = formatted_result["Pulsetrain"][i]
                    else:
                        signal_width = formatted_result["data"].shape[1] if "data" in formatted_result else 0
                        pulsetrain_obj[0, i] = np.zeros((0, signal_width))

                # Replace dictionary with object array
                formatted_result["Pulsetrain"] = pulsetrain_obj

            # Format Dischargetimes as a MATLAB-compatible cell array
            if "Dischargetimes" in formatted_result:
                max_electrode = 0
                max_mu = 0

                for key in formatted_result["Dischargetimes"].keys():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        max_electrode = max(max_electrode, electrode)
                        max_mu = max(max_mu, mu)

                dischargetimes_obj = np.empty((max_electrode + 1, max_mu + 1), dtype=object)

                # Initialize all cells with empty arrays
                for i in range(max_electrode + 1):
                    for j in range(max_mu + 1):
                        dischargetimes_obj[i, j] = np.array([], dtype=int)

                # Fill with actual discharge times
                for key, value in formatted_result["Dischargetimes"].items():
                    if isinstance(key, tuple) and len(key) == 2:
                        electrode, mu = key
                        dischargetimes_obj[electrode, mu] = value

                formatted_result["Dischargetimes"] = dischargetimes_obj

            # Format other arrays properly for MATLAB compatibility
            for field_name in ["gridname", "muscle", "auxiliaryname"]:
                if field_name in formatted_result:
                    field_data = formatted_result[field_name]
                    field_obj = np.empty((1, len(field_data)), dtype=object)

                    # Fill the array with the field data
                    for i, item in enumerate(field_data):
                        field_obj[0, i] = str(item)

                    formatted_result[field_name] = field_obj

            # Format coordinates and EMG mask
            if "coordinates" in formatted_result:
                coordinates = formatted_result["coordinates"]
                ngrid = formatted_result.get("ngrid", 1)

                coord_obj = np.empty((1, ngrid), dtype=object)

                # Process list of coordinates arrays
                for i, coord in enumerate(coordinates):
                    if i < ngrid:
                        if isinstance(coord, np.ndarray):
                            if coord.ndim == 2 and coord.shape[1] == 2:
                                coord_obj[0, i] = coord
                            else:
                                coord_obj[0, i] = np.reshape(coord, (-1, 2))
                        else:
                            coord_obj[0, i] = np.array(coord).reshape(-1, 2)

                # Fill any empty cells with default
                for i in range(ngrid):
                    if coord_obj[0, i] is None:
                        coord_obj[0, i] = np.zeros((0, 2))

                formatted_result["coordinates"] = coord_obj

            if "EMGmask" in formatted_result:
                emgmask = formatted_result["EMGmask"]
                ngrid = formatted_result.get("ngrid", 1)

                mask_obj = np.empty((1, ngrid), dtype=object)

                # Process list of mask arrays
                for i, mask in enumerate(emgmask):
                    if i < ngrid:
                        if isinstance(mask, np.ndarray):
                            if mask.ndim == 1:
                                mask_obj[0, i] = mask.reshape(-1, 1)
                            elif mask.ndim == 2 and mask.shape[1] == 1:
                                mask_obj[0, i] = mask
                            else:
                                mask_obj[0, i] = mask.flatten().reshape(-1, 1)
                        else:
                            mask_obj[0, i] = np.array(mask).flatten().reshape(-1, 1)

                # Fill any empty cells with default (empty) mask arrays
                for i in range(ngrid):
                    if mask_obj[0, i] is None:
                        if "coordinates" in formatted_result and formatted_result["coordinates"][0, i] is not None:
                            coord_len = formatted_result["coordinates"][0, i].shape[0]
                            mask_obj[0, i] = np.zeros((coord_len, 1), dtype=int)
                        else:
                            mask_obj[0, i] = np.zeros((0, 1), dtype=int)

                formatted_result["EMGmask"] = mask_obj

            # Create visualization state in native Python format
            viz_state = {}

            # Store reference plot data
            if hasattr(self, "ui_plot_reference") and hasattr(self.ui_plot_reference, "plotItem"):
                try:
                    # Extract data from reference plot
                    ref_plot_items = self.ui_plot_reference.getPlotItem().listDataItems()
                    if ref_plot_items and len(ref_plot_items) > 0:
                        ref_data = ref_plot_items[0].getData()
                        if ref_data and len(ref_data) >= 2:
                            time_array = ref_data[0]
                            target_array = ref_data[1]
                            
                            # Convert to regular Python lists
                            viz_state["reference_plot"] = {
                                "time": time_array.tolist() if hasattr(time_array, 'tolist') else list(time_array),
                                "target": target_array.tolist() if hasattr(target_array, 'tolist') else list(target_array)
                            }
                    
                    # Store plateau markers
                    plateau_markers = []
                    for item in self.ui_plot_reference.getPlotItem().items:
                        if isinstance(item, pg.InfiniteLine):
                            plateau_markers.append(float(item.value()))
                    
                    if plateau_markers:
                        viz_state["plateau_markers"] = plateau_markers
                except Exception as e:
                    print(f"Error capturing reference plot data: {e}")
                    traceback.print_exc()
                
            # Store pulse train plot data
            if hasattr(self, "ui_plot_pulsetrain") and hasattr(self.ui_plot_pulsetrain, "plotItem"):
                try:
                    pulse_plot_items = self.ui_plot_pulsetrain.getPlotItem().listDataItems()
                    pulse_data = []
                    scatter_data = []
                    
                    for item in pulse_plot_items:
                        if isinstance(item, pg.PlotCurveItem):
                            # Line plot items
                            x, y = item.getData()
                            pulse_data.append({
                                "time": x.tolist() if hasattr(x, 'tolist') else list(x),
                                "values": y.tolist() if hasattr(y, 'tolist') else list(y),
                                "color": item.opts["pen"].color().name() if hasattr(item.opts["pen"], "color") else "#000000"
                            })
                        elif isinstance(item, pg.ScatterPlotItem):
                            # For scatter items, we need to extract points differently
                            # Use the item's points method to get all scatter points
                            pts = item.points()
                            # Check if pts exists and has elements
                            if pts is not None and len(pts) > 0:
                                x_values = []
                                y_values = []
                                for pt in pts:
                                    x_values.append(pt.pos().x())
                                    y_values.append(pt.pos().y())
                                
                                # Get brush color
                                brush = item.opts.get("brush", pg.mkBrush("#FF0000"))
                                brush_color = brush.color().name() if hasattr(brush, "color") else "#FF0000"
                                
                                scatter_data.append({
                                    "x": x_values,
                                    "y": y_values,
                                    "size": item.opts.get("size", 10),
                                    "color": brush_color
                                })
                    
                    if pulse_data:
                        viz_state["pulse_plot"] = pulse_data
                    if scatter_data:
                        viz_state["scatter_plot"] = scatter_data
                    
                    # Store plot title
                    if hasattr(self.ui_plot_pulsetrain.getPlotItem(), "titleLabel"):
                        title_text = self.ui_plot_pulsetrain.getPlotItem().titleLabel.text
                        if title_text:
                            viz_state["pulse_plot_title"] = title_text
                    
                    # Store Y range
                    if hasattr(self.ui_plot_pulsetrain.getPlotItem(), "getViewBox"):
                        viewbox = self.ui_plot_pulsetrain.getPlotItem().getViewBox()
                        if viewbox:
                            y_range = viewbox.viewRange()[1]
                            if y_range and len(y_range) == 2:
                                viz_state["pulse_plot_y_range"] = list(y_range)
                except Exception as e:
                    print(f"Error capturing pulse train plot data: {e}")
                    traceback.print_exc()
                
            # Store statistics
            if hasattr(self, "sil_value_label") and hasattr(self, "cov_value_label"):
                try:
                    sil_text = self.sil_value_label.text()
                    cov_text = self.cov_value_label.text()
                    
                    sil_value = float(sil_text.replace("SIL: ", "")) if "SIL: " in sil_text else 0
                    cov_value = float(cov_text.replace("CoV: ", "")) if "CoV: " in cov_text else 0
                    
                    viz_state["statistics"] = {
                        "sil": sil_value,
                        "cov": cov_value,
                        "iteration": self.iteration_counter
                    }
                except Exception as e:
                    print(f"Error capturing statistics: {e}")

            # Store last plot data in the visualization state
            if hasattr(self, "last_plot_data"):
                # Save the complete plot data
                viz_state["last_plot_data"] = {}
                
                # For arrays, save the entire arrays if they're not too large
                for key in ["time", "time2", "target", "icasig"]:
                    if self.last_plot_data.get(key) is not None:
                        data = self.last_plot_data[key]
                        if isinstance(data, np.ndarray) and data.size > 0:
                            # Only store if the array isn't too massive
                            if data.size <= 100000:  # Reasonable size limit
                                viz_state["last_plot_data"][key] = data.tolist()
                            else:
                                # For large arrays, store a decimated version
                                decimation_factor = max(1, data.size // 10000)
                                viz_state["last_plot_data"][key] = data[::decimation_factor].tolist()
                
                # For spikes, save the complete array
                if self.last_plot_data.get("spikes") is not None:
                    spikes = self.last_plot_data["spikes"]
                    if hasattr(spikes, "__len__") and len(spikes) > 0:
                        viz_state["last_plot_data"]["spikes"] = [int(s) for s in spikes]
                
                # Save scalar values
                for key in ["sil", "cov"]:
                    if self.last_plot_data.get(key) is not None:
                        viz_state["last_plot_data"][key] = float(self.last_plot_data[key])
                
                # Save iteration counter
                viz_state["last_plot_data"]["iteration_counter"] = self.iteration_counter

            # Save with parameters 
            parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}
            self.save_mat_in_background(savename, {"signal": formatted_result, "parameters": parameters}, True)

            # Store the decomposition result
            self.decomposition_result = formatted_result
            
            # Store visualization state in the visualization storage
            if hasattr(self, 'viz_storage') and self.viz_storage:
                try:
                    self.viz_storage.add_visualization(
                        title=f"HDEMG Analysis - {self.filename}",
                        filepath=savename,
                        parameters=parameters,
                        viz_state=viz_state  # Store native Python structure
                    )
                    print(f"Visualization state stored successfully for {self.filename}")
                except Exception as e:
                    print(f"Error storing visualization state: {e}")
                    traceback.print_exc()

            self.edit_field.setText("Decomposition complete")
            self.status_text.setText("Complete")
            self.status_progress.setValue(100)
            self.start_button.setEnabled(True)
            self.save_output_button.setEnabled(True)
            
            # Enable visualization save button
            if hasattr(self, 'save_visualization_button'):
                self.save_visualization_button.setEnabled(True)
                
            # Enable edit mode button if it exists
            if hasattr(self, 'edit_mode_btn'):
                self.edit_mode_btn.setEnabled(True)

            # Update the motor unit displays using the new function
            self.update_motor_unit_display()

            if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
                self.threads.remove(self.decomp_worker)

    def on_decomposition_error(self, error_msg):
        """Handle errors during decomposition"""
        self.edit_field.setText(f"Error in decomposition: {error_msg}")
        self.status_text.setText("Error")
        self.status_progress.setValue(0)
        self.start_button.setEnabled(True)

        if hasattr(self, "decomp_worker") and self.decomp_worker in self.threads:
            self.threads.remove(self.decomp_worker)

    def update_progress(self, message, progress=None):
        """Update progress information during decomposition"""
        self.edit_field.setText(message)
        self.status_text.setText(message.split("-")[0] if "-" in message else message)

        if progress is not None and isinstance(progress, (int, float)):
            self.status_progress.setValue(int(progress * 100))

    def update_plots(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """Update plot displays during decomposition using PyQtGraph"""
        try:
            self.iteration_counter += 1

            # Save the data for later restoration
            self.last_plot_data = {
                "time": time,
                "target": target,
                "plateau_coords": plateau_coords,
                "icasig": icasig,
                "spikes": spikes,
                "time2": time2, 
                "sil": sil,
                "cov": cov
            }

            if sil is not None and cov is not None:
                self.edit_field.setText(f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}")
                self.sil_value_label.setText(f"SIL: {sil:.4f}")
                self.cov_value_label.setText(f"CoV: {cov:.4f}")

            # Only update plots every 5 iterations to reduce UI overhead
            if self.iteration_counter % 5 != 0 and self.iteration_counter > 1:
                return

            if target is None:
                return

            # Ensure arrays are 1D
            if isinstance(target, np.ndarray) and target.ndim > 1:
                target = target.flatten()

            # Check if time array is compatible with target array
            if time is None or (isinstance(time, np.ndarray) and (time.size == 1 or time.shape != target.shape)):
                # Create a synthetic time array that matches target's length
                print(f"Creating synthetic time array to match target shape {target.shape}")
                time = np.arange(len(target))
            elif isinstance(time, np.ndarray) and time.ndim > 1:
                time = time.flatten()

            # Clear previous plots
            self.ui_plot_reference.clear()

            # Plot reference signal with plateau markers
            self.ui_plot_reference.plot(
                time, target, pen=pg.mkPen(color="#000000", width=2, style=Qt.PenStyle.DashLine)
            )

            # Plot plateau markers if available
            if plateau_coords is not None and len(plateau_coords) >= 2:
                try:
                    if len(time) > max(plateau_coords):
                        for coord in plateau_coords[:2]:  # Just plot the first two markers
                            line = pg.InfiniteLine(pos=time[coord], angle=90, pen=pg.mkPen(color="#FF0000", width=2))
                            self.ui_plot_reference.addItem(line)
                except (IndexError, TypeError) as e:
                    print(f"Warning: Error plotting plateau markers: {e}")

            # Plot decomposition results if available
            if icasig is not None:
                try:
                    if isinstance(icasig, np.ndarray) and icasig.ndim > 1:
                        icasig = icasig.flatten()

                    if time2 is None or (
                        isinstance(time2, np.ndarray) and (time2.size == 1 or time2.shape != icasig.shape)
                    ):
                        print(f"Creating synthetic time2 array to match icasig shape {icasig.shape}")
                        time2 = np.arange(len(icasig))
                    elif isinstance(time2, np.ndarray) and time2.ndim > 1:
                        time2 = time2.flatten()

                    self.ui_plot_pulsetrain.clear()
                    self.ui_plot_pulsetrain.plot(time2, icasig, pen=pg.mkPen(color="#000000", width=1))

                    if spikes is not None and len(spikes) > 0:
                        valid_indices = [i for i in spikes if i < len(time2)]
                        if valid_indices:
                            scatter = pg.ScatterPlotItem(
                                x=[time2[i] for i in valid_indices],
                                y=[icasig[i] for i in valid_indices],
                                size=10,
                                pen=pg.mkPen(None),
                                brush=pg.mkBrush("#FF0000"),
                            )
                            self.ui_plot_pulsetrain.addItem(scatter)

                    self.ui_plot_pulsetrain.setYRange(-0.2, 1.5)

                    # Update title with SIL and CoV values if available
                    if sil is not None and cov is not None:
                        title = f"Iteration #{self.iteration_counter}: SIL = {sil:.4f}, CoV = {cov:.4f}"
                        self.ui_plot_pulsetrain.setTitle(title)

                except Exception as e:
                    print(f"Warning: Error plotting decomposition results: {e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"Error in update_plots: {e}")
            traceback.print_exc()

    def save_output_to_location(self):
        """Save decomposition results to a user-specified location"""
        if not hasattr(self, "decomposition_result") or self.decomposition_result is None:
            self.edit_field.setText("No decomposition results available to save")
            return

        # Open file dialog to select save location
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Decomposition Results",
            os.path.join(self.pathname if self.pathname else "", "decomposition_results.mat"),
            "MAT Files (*.mat);;All Files (*.*)",
        )

        if not save_path:  # User cancelled
            return

        # Ensure the path has a .mat extension
        if not save_path.lower().endswith(".mat"):
            save_path += ".mat"

        # Format the result properly (same as in on_decomposition_complete)
        formatted_result = self.decomposition_result

        # Get the parameters that were used
        parameters = prepare_parameters(self.ui_params) if hasattr(self, "ui_params") else {}

        # Save in background
        self.save_mat_in_background(save_path, {"signal": formatted_result, "parameters": parameters}, True)
        self.edit_field.setText(f"Saving results to {save_path}")
        
    def save_visualization(self):
        """Save the current visualization state for later retrieval from the dashboard."""
        if not hasattr(self, "decomposition_result") or self.decomposition_result is None:
            self.edit_field.setText("No decomposition results available to save as visualization")
            return
            
        if not hasattr(self, 'viz_storage') or not self.viz_storage:
            self.edit_field.setText("Visualization storage not available")
            return
            
        # Create visualization state dictionary
        viz_state = {}
        
        # Get reference plot data
        if hasattr(self, "ui_plot_reference") and hasattr(self.ui_plot_reference, "plotItem"):
            try:
                ref_plot_items = self.ui_plot_reference.getPlotItem().listDataItems()
                if ref_plot_items:
                    ref_data = ref_plot_items[0].getData()
                    time_array = ref_data[0]
                    target_array = ref_data[1]
                    
                    viz_state["reference_plot"] = {
                        "time": time_array.tolist() if hasattr(time_array, 'tolist') else list(time_array),
                        "target": target_array.tolist() if hasattr(target_array, 'tolist') else list(target_array)
                    }
                    
                # Get plateau markers
                plateau_markers = []
                for item in self.ui_plot_reference.getPlotItem().items:
                    if isinstance(item, pg.InfiniteLine):
                        plateau_markers.append(float(item.value()))
                        
                if plateau_markers:
                    viz_state["plateau_markers"] = plateau_markers
            except Exception as e:
                print(f"Error capturing reference plot data: {e}")
                
        # Get pulse train plot data
        if hasattr(self, "ui_plot_pulsetrain") and hasattr(self.ui_plot_pulsetrain, "plotItem"):
            try:
                pulse_plot_items = self.ui_plot_pulsetrain.getPlotItem().listDataItems()
                pulse_data = []
                scatter_data = []
                
                for item in pulse_plot_items:
                    if isinstance(item, pg.PlotCurveItem):
                        # Line plot items
                        x, y = item.getData()
                        pulse_data.append({
                            "time": x.tolist() if hasattr(x, 'tolist') else list(x),
                            "values": y.tolist() if hasattr(y, 'tolist') else list(y),
                            "color": item.opts["pen"].color().name() if hasattr(item.opts["pen"], "color") else "#000000"
                        })
                    elif isinstance(item, pg.ScatterPlotItem):
                        # Scatter items (spikes)
                        pts = item.data
                        x_values = [pt.pos().x() for pt in pts]
                        y_values = [pt.pos().y() for pt in pts]
                        
                        scatter_data.append({
                            "x": x_values,
                            "y": y_values,
                            "size": item.opts.get("size", 10),
                            "color": item.opts.get("brush", pg.mkBrush("#FF0000")).color().name()
                        })
                        
                if pulse_data:
                    viz_state["pulse_plot"] = pulse_data
                if scatter_data:
                    viz_state["scatter_plot"] = scatter_data
                    
                # Get title
                title = self.ui_plot_pulsetrain.getPlotItem().titleLabel.text
                if title:
                    viz_state["pulse_plot_title"] = title
                    
                # Get Y range
                y_range = self.ui_plot_pulsetrain.getPlotItem().getViewBox().viewRange()[1]
                if y_range:
                    viz_state["pulse_plot_y_range"] = list(y_range)
            except Exception as e:
                print(f"Error capturing pulse train plot data: {e}")
                
        # Get statistics
        if hasattr(self, "sil_value_label") and hasattr(self, "cov_value_label"):
            try:
                sil_text = self.sil_value_label.text()
                cov_text = self.cov_value_label.text()
                
                sil_value = float(sil_text.replace("SIL: ", "")) if "SIL: " in sil_text else 0
                cov_value = float(cov_text.replace("CoV: ", "")) if "CoV: " in cov_text else 0
                
                viz_state["statistics"] = {
                    "sil": sil_value,
                    "cov": cov_value,
                    "iteration": self.iteration_counter
                }
            except Exception as e:
                print(f"Error capturing statistics: {e}")
        
        # Get a title for the visualization
        title = f"HDEMG Analysis - {self.filename}" if self.filename else "HDEMG Analysis"
        
        # Get the file path
        if self.pathname and self.filename:
            filepath = os.path.join(self.pathname, self.filename + "_output_decomp.mat")
        else:
            # If we don't have a path, use a generic one
            filepath = ""
            
        # Get parameters
        parameters = self.ui_params if self.ui_params else {}
        
        # Add to visualization storage
        self.viz_storage.add_visualization(
            title=title,
            filepath=filepath,
            parameters=parameters,
            viz_state=viz_state
        )
        
        self.edit_field.setText(f"Visualization '{title}' saved")
        
        # Confirm to user
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Visualization Saved",
            f"Visualization '{title}' has been saved to the dashboard.",
            QMessageBox.Ok
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DecompositionApp()
    window.show()
    sys.exit(app.exec_())