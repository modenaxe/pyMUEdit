import numpy as np
import torch
import traceback
import time

from .config.structures import set_random_seed, Config
from .models.scd import SwarmContrastiveDecomposition
from .processing.postprocess import save_results
from PyQt5.QtCore import QThread, pyqtSignal
from core.logger import logger

set_random_seed(seed=42)

class SCDDecompositionWorker(QThread):
    """
    Worker thread to run EMG decomposition in the background.
    Directly implements the SCD algorithm made by Agnese Grison.
    """

    progress = pyqtSignal(str, object)
    plot_update = pyqtSignal(object, object, object, object, object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress_val = 0.1

    def __init__(self, emg_obj, parameters):
        """
        Initialize the worker with an emg_obj instance and parameters.

        Args:
            emg_obj: An instance of offline_EMG that has already loaded a file
            parameters: Dictionary of algorithm parameters
        """
        super().__init__()
        self.emg_obj = emg_obj
        self.parameters = parameters
        self.progress_val = 0.1

    def run(self) -> None:
        try:
            self.emg_obj.electrode_formatter()  # adds spatial context, and additional filtering
            
            # Get parameters from parameters object
            device = self.parameters["device"]
            acceptance_silhouette = self.parameters["acceptance_silhouette"]
            extension_factor = self.parameters["extension_factor"]
            time_differentiate = False
            notch_params = [
                self.parameters["powerline_frequency"], 
                self.parameters["bandwidth"], 
                self.parameters["filt_harms"]
            ] # powerline frequency, bandwidth, filter harmonics
            low_pass_cutoff = self.parameters["low_pass_cutoff"]
            high_pass_cutoff = self.parameters["high_pass_cutoff"]
            start_time = 0
            end_time = -1
            max_iterations = self.parameters["iterations"]
            sampling_frequency = self.emg_obj.signal_dict["fsamp"]
            peel_off_window_size_ms = self.parameters["peel_off_window_size"]   # ms
            output_final_source_plot = True
            use_coeff_var_fitness = self.parameters["use_coeff_var_fitness"]
            remove_bad_fr = self.parameters["remove_bad_fr"]
            clamp_percentile = 0.999  

            # Get data from EMG object
            data_array = np.array(self.emg_obj.signal_dict["data"].astype(float))
            print(f"Number of channels: {data_array.shape[0]}, number of values per channel: {data_array.shape[1]}")
            print(data_array)
            neural_data = (
                torch.from_numpy(data_array).t().to(device=device, dtype=torch.float32)
            )  # time, channels

            config = Config(
                device=device,
                acceptance_silhouette=acceptance_silhouette,
                extension_factor=extension_factor,
                time_differentiate=time_differentiate,
                notch_params=notch_params,
                low_pass_cutoff=low_pass_cutoff,
                high_pass_cutoff=high_pass_cutoff,
                sampling_frequency=sampling_frequency,
                start_time=start_time,
                end_time=end_time,
                max_iterations=max_iterations,
                peel_off_window_size_ms=peel_off_window_size_ms,
                output_final_source_plot=output_final_source_plot,
                use_coeff_var_fitness=use_coeff_var_fitness,
                remove_bad_fr=remove_bad_fr,
                clamp_percentile=clamp_percentile,
            )

            if config.end_time == -1:
                neural_data = neural_data[config.start_time * sampling_frequency : , :]
            else:
                neural_data = neural_data[config.start_time * sampling_frequency : config.end_time * sampling_frequency, :]

            # Initiate the model and run
            model = SwarmContrastiveDecomposition(self.send_plot_update, self.send_progress_update)
            predicted_timestamps, dictionary = model.run(neural_data, config)

            self.decomp = dictionary
            # print("---------------DICTIONARY---------------")
            # print(len(dictionary["timestamps"][0]))
            # print(dictionary)
            # print("---------------END DICTIONARY---------------")
            # print()
            # print("---------------PREDICTED TIMESTAMPS---------------")
            # print(predicted_timestamps)
            # print("---------------END PREDICTED TIMESTAMPS---------------")

            self.progress.emit("Formatting results...", 0.9)
            print(self.decomp)
            #TODO: Figure out formatting results and saving
            result = self.format_results()
            self.finished.emit(result)

        except Exception as e:
            logger.exception(f"Exception in SCDDecompositionWorker: {str(e)}")
            self.error.emit(str(e))
    
    def send_plot_update(self, fICA_source, spikes, time2, sil, cov):
        """Send plot update signals to the main UI thread"""
        # Throttle updates to avoid overwhelming the UI
        self.plot_update.emit(fICA_source, spikes, time2, sil, cov)
        # Process events to keep the UI responsive during long computations
        time.sleep(0.01)  # Small delay to prevent UI freezing

    def send_progress_update(self, message):
        self.progress_val += 0.8 / self.parameters["iterations"]
        self.progress.emit(message, self.progress_val)

    
    def format_results(self):
        """Format results from offline_EMG to match MUedit's expected format."""
        # Create a clean output structure
        result = {}

        # Copy essential fields from the original signal
        for field in self.emg_obj.signal_dict:
            if field not in [
                "batched_data",
                "extend_obvs",
                "extend_obvs_old",
                "filtered_data",
                "sq_extend_obvs",
                "inv_extend_obvs",
                "diff_data",
            ]:
                result[field] = self.emg_obj.signal_dict[field]

        # Add spatial information
        if hasattr(self.emg_obj, "coordinates"):
            result["coordinates"] = self.emg_obj.coordinates
        if hasattr(self.emg_obj, "ied"):
            result["IED"] = self.emg_obj.ied
        if hasattr(self.emg_obj, "rejected_channels"):
            result["EMGmask"] = self.emg_obj.rejected_channels

        # Format pulse trains and discharge times using the exact format expected by MUedit
        result["Pulsetrain"] = {}
        result["Dischargetimes"] = {}

        #TODO: map pulse trains and discharge times from results of SCD algorithm
        # want to use self.decomp["source"] here for pulse trains, and self.decomp["timestamps"] for discharge times
        pulse_trains_array = np.array([[source[t] for t in timestamps] for source, timestamps in zip(self.decomp["source"], self.decomp["timestamps"])])
        if len(pulse_trains_array) > 0:
            for electrode, pulse_trains in enumerate(pulse_trains_array):
                if isinstance(pulse_trains, np.ndarray) and pulse_trains.shape[0] > 0:
                    result["Pulsetrain"][electrode] = pulse_trains

                    # Check if discharge_times is available for this electrode
                    if electrode < len(self.decomp["timestamps"]):
                        for mu, discharge_times in enumerate(self.decomp["timestamps"]):
                            if discharge_times is not None and len(discharge_times) > 0:
                                result["Dischargetimes"][(electrode, mu)] = discharge_times

        return result