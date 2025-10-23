from PyQt5.QtCore import QThread, pyqtSignal, QObject
from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg
import numpy as np
from core.logger import logger

class batch_filter_worker(QThread):
    progress_changed = pyqtSignal(int, str) 
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, muedition, original_data, parent_instance):
        super().__init__()
        self.MUedition = muedition
        self.original_data = original_data
        self.parent_instance = parent_instance
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            # Count total MUs
            total_mus = 0
            for i in range(len(self.MUedition["edition"]["Pulsetrain"])):
                total_mus += self.MUedition["edition"]["Pulsetrain"][i].shape[0]

            # Process each MU
            processed_mus = 0
            for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
                # Get EMG data for this array
                emg_data = self.MUedition["signal"]["data"][
                    self.MUedition["edition"]["arraynb"] == array_idx, :
                ]
                emg_mask = self.MUedition["signal"]["EMGmask"][0, array_idx].squeeze()
                emg_data = emg_data[emg_mask == 0, :] # Use only non-rejected channels

                num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

                for mu_idx in range(num_mus):
                    if self._cancelled:
                        self.MUedition["edition"]["Pulsetrain"] = self.original_data[0]
                        self.MUedition["edition"]["Dischargetimes"] = self.original_data[1]
                        self.MUedition["edition"]["silval"] = self.original_data[2]
                        self.MUedition["edition"]["silvalcon"] = self.original_data[3]
                        print("Batch processing interruption!")
                        return

                    percent = int(processed_mus / total_mus * 100)
                    self.progress_changed.emit(
                        percent,
                        f"Updating filter for Array #{array_idx+1} MU #{mu_idx+1}"
                    )

                    discharge_times = self.MUedition["edition"]["Dischargetimes"].get(
                        (array_idx, mu_idx), np.array([])
                    )

                    if len(discharge_times) > 1:
                        self.process_single_mu(emg_data, array_idx, mu_idx, discharge_times)

                    processed_mus += 1

            self.progress_changed.emit(100, "Done")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def process_single_mu(self, emg_data, array_idx, mu_idx, discharge_times):
        # Create extension factor
        extension_factor = min(1000 // emg_data.shape[0], 25)

        # Extend the EMG signal
        extended_emg = np.zeros(
            [emg_data.shape[0] * extension_factor, emg_data.shape[1] + extension_factor - 1]
        )
        extended_emg = extend_emg(extended_emg, emg_data, extension_factor)

        # Calculate covariance and pseudo-inverse
        covariance = extended_emg @ extended_emg.T / extended_emg.shape[1]
        inverse_cov = np.linalg.pinv(covariance)

        # Get whitened signal
        _, _, dewhitening_matrix = whiten_emg(extended_emg)

        # Calculate motor unit filter
        mu_filter = np.sum(extended_emg[:, discharge_times], axis=1, keepdims=True)

        # Calculate pulse train
        pulse_train = ((dewhitening_matrix @ mu_filter).T @ inverse_cov) @ extended_emg
        pulse_train = pulse_train[0, : emg_data.shape[1]]

        # Square and rectify
        pulse_train = pulse_train * np.abs(pulse_train)

        # Find peaks
        from scipy.signal import find_peaks

        peaks, _ = find_peaks(pulse_train, distance=round(0.005 * self.MUedition["signal"]["fsamp"][0, 0]))

        # Normalize using top peaks
        if len(peaks) >= 10:
            top_values = np.sort(pulse_train[peaks])[-10:]
            pulse_train = pulse_train / np.mean(top_values)
        elif len(peaks) > 0:
            pulse_train = pulse_train / np.mean(pulse_train[peaks])

        # Cluster peaks to find spikes
        if len(peaks) >= 2:
            from sklearn.cluster import KMeans

            kmeans = KMeans(n_clusters=2, random_state=0).fit(pulse_train[peaks].reshape(-1, 1))
            labels = kmeans.labels_
            centroids = kmeans.cluster_centers_

            # Find class with highest centroid
            high_centroid_idx = np.argmax(centroids)
            spikes = peaks[labels == high_centroid_idx]

            # Remove outliers
            threshold = np.mean(pulse_train[spikes]) + 3 * np.std(pulse_train[spikes])
            spikes = spikes[pulse_train[spikes] <= threshold]
        else:
            spikes = peaks

        # Update the pulse train and discharge times
        self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = pulse_train
        self.MUedition["edition"]["Dischargetimes"][array_idx, mu_idx] = spikes 
        # Recalculate SIL
        self.parent_instance.calculate_silval(array_idx, mu_idx)
