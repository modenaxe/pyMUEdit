from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import traceback
import os


class DecompositionWorker(QThread):
    """
    Worker thread to run EMG decomposition in the background.
    Emits signals for progress updates and plot data.
    """

    progress = pyqtSignal(str, object)
    plot_update = pyqtSignal(object, object, object, object, object, object, object, object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, signal, parameters):
        """
        Initialize the worker with signal data and decomposition parameters.
        """
        super().__init__()
        self.signal = signal
        self.parameters = parameters

        # Force non-interactive mode
        self.parameters["checkEMG"] = 0
        self.parameters["enable_plots"] = False

    def run(self):
        """Run the decomposition process in a separate thread."""
        try:
            os.environ["OMP_NUM_THREADS"] = "4"
            os.environ["MKL_NUM_THREADS"] = "4"
            os.environ["NUMEXPR_NUM_THREADS"] = "4"
            os.environ["OPENBLAS_NUM_THREADS"] = "4"
            os.environ["VECLIB_MAXIMUM_THREADS"] = "4"
            os.environ["NUMBA_NUM_THREADS"] = "4"

            # Set matplotlib to non-interactive mode
            import matplotlib

            matplotlib.use("Agg")  # Force non-interactive backend

            # Import decomposition classes
            from HDEMGdecomposition import EMGDecomposition, DecompositionResults

            # Create results object with callbacks
            results = DecompositionResults()
            results.set_progress_callback(self.emit_progress)
            results.set_plot_callback(self.emit_plot_update)

            # Prepare signal data
            self.emit_progress("Preparing signal data...")

            # Convert signal to simple dictionary structure
            signal_dict = self.convert_to_dict(self.signal)

            # Fix fsamp if it's a nested array
            if "fsamp" in signal_dict:
                if isinstance(signal_dict["fsamp"], np.ndarray) and signal_dict["fsamp"].size == 1:
                    signal_dict["fsamp"] = float(signal_dict["fsamp"].item())

            # Fix ngrid if it's a nested array
            if "ngrid" in signal_dict:
                if isinstance(signal_dict["ngrid"], np.ndarray) and signal_dict["ngrid"].size == 1:
                    signal_dict["ngrid"] = int(signal_dict["ngrid"].item())

            # Ensure data has no NaN values
            if "data" in signal_dict and isinstance(signal_dict["data"], np.ndarray):
                if np.isnan(signal_dict["data"]).any():
                    signal_dict["data"] = np.nan_to_num(signal_dict["data"])

            # Run decomposition with fault handling
            self.emit_progress("Starting decomposition...")

            # Create EMGDecomposition instance
            emg_decomp = EMGDecomposition(self.parameters, results)

            # Prepare signal data
            emg_decomp.prepare_signal_data(signal_dict)

            # Run the decomposition
            result = emg_decomp.run()
            print("DEBUG: Decomposition completed successfully")

            # Signal completion
            self.finished.emit(result)

        except Exception as e:
            print(f"DEBUG: Exception in worker thread: {str(e)}")
            traceback.print_exc()
            self.error.emit(str(e))

    def emit_progress(self, message, progress=None):
        """Emit progress update."""
        try:
            self.progress.emit(message, progress)
        except Exception as e:
            print(f"DEBUG: Error in emit_progress: {str(e)}")

    def emit_plot_update(self, time, target, plateau_coords, icasig=None, spikes=None, time2=None, sil=None, cov=None):
        """
        Emit plot data update with safety checks.
        """
        try:
            # Handle plateau coordinates
            if plateau_coords is not None:
                if isinstance(plateau_coords, np.ndarray):
                    plateau_coords = plateau_coords.tolist()

            # Handle spike indices
            if isinstance(spikes, np.ndarray):
                # Only include a subset of spikes for efficiency
                if len(spikes) > 50:
                    spikes = np.sort(np.random.choice(spikes, 50, replace=False)).tolist()
                else:
                    spikes = spikes.tolist()

            # Emit the plot update signal
            self.plot_update.emit(time, target, plateau_coords, icasig, spikes, time2, sil, cov)

        except Exception as e:
            print(f"DEBUG: Error in emit_plot_update: {str(e)}")
            self.progress.emit(
                f"Processing... SIL={sil:.4f if sil is not None else 'N/A'}, "
                f"CoV={cov:.4f if cov is not None else 'N/A'}",
                None,
            )

    def convert_to_dict(self, signal):
        """Convert signal data to a Python dictionary"""
        try:
            if isinstance(signal, dict):
                return signal

            if isinstance(signal, np.ndarray) and hasattr(signal, "dtype") and signal.dtype.names is not None:
                signal_dict = {}

                # For MATLAB imports
                if signal.shape == (1, 1):
                    for field in signal.dtype.names:
                        try:
                            field_data = signal[0, 0][field]

                            # Handle nested structures
                            if isinstance(field_data, np.ndarray) and field_data.dtype.names is not None:
                                nested_dict = {}
                                for nested_field in field_data.dtype.names:
                                    nested_dict[nested_field] = field_data[nested_field]
                                signal_dict[field] = nested_dict
                            else:
                                signal_dict[field] = field_data
                        except Exception as e:
                            print(f"DEBUG: Error processing field '{field}': {str(e)}")
                else:
                    for field in signal.dtype.names:
                        try:
                            signal_dict[field] = signal[field]
                        except Exception as e:
                            print(f"DEBUG: Error processing field '{field}': {str(e)}")

                return signal_dict
            return dict(signal)
        except Exception as e:
            print(f"DEBUG: Error in convert_to_dict: {str(e)}")
            return {}
