from PyQt5.QtCore import QObject, QThread, pyqtSignal
import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import KMeans

from core.utils.decomposition.extend_emg import extend_emg
from core.utils.decomposition.whiten_emg import whiten_emg

class BatchFilterWorker(QObject):
    progress_changed = pyqtSignal(int)
    progress_label = pyqtSignal(str)
    finished = pyqtSignal()
    canceled = pyqtSignal()
    
    def __init__(self, MUedition, original_pulsetrain, original_dischargetimes, original_silval, original_silvalcon):
        super().__init__()
        self.MUedition = MUedition
        self.original_pulsetrain = original_pulsetrain
        self.original_dischargetimes = original_dischargetimes
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        total_mus = sum(
            [pt.shape[0] for pt in self.MUedition["edition"]["Pulsetrain"]]
        )
        processed_mus = 0

        for array_idx in range(len(self.MUedition["edition"]["Pulsetrain"])):
            emg_data = self.MUedition["signal"]["data"][
                self.MUedition["edition"]["arraynb"] == array_idx, :
            ]
            emg_mask = self.MUedition["signal"]["EMGmask"][0, array_idx].squeeze()
            emg_data = emg_data[emg_mask == 0, :]

            num_mus = self.MUedition["edition"]["Pulsetrain"][array_idx].shape[0]

            for mu_idx in range(num_mus):
                if self._cancelled:
                    self.canceled.emit()
                    return

                self.progress_changed.emit(int(processed_mus / total_mus * 100))
                self.progress_label.emit(f"Updating filter for Array #{array_idx+1} MU #{mu_idx+1}")

                discharge_times = self.MUedition["edition"]["Dischargetimes"].get((array_idx, mu_idx), np.array([]))

                if len(discharge_times) > 1:
                    extension_factor = min(1000 // emg_data.shape[0], 25)
                    extended_emg = np.zeros(
                        [emg_data.shape[0] * extension_factor, emg_data.shape[1] + extension_factor - 1]
                    )
                    extended_emg = extend_emg(extended_emg, emg_data, extension_factor)

                    covariance = extended_emg @ extended_emg.T / extended_emg.shape[1]
                    inverse_cov = np.linalg.pinv(covariance)
                    _, _, dewhitening_matrix = whiten_emg(extended_emg)
                    mu_filter = np.sum(extended_emg[:, discharge_times], axis=1, keepdims=True)

                    pulse_train = ((dewhitening_matrix @ mu_filter).T @ inverse_cov) @ extended_emg
                    pulse_train = pulse_train[0, : emg_data.shape[1]]
                    pulse_train = pulse_train * np.abs(pulse_train)

                    peaks, _ = find_peaks(
                        pulse_train,
                        distance=round(0.005 * self.MUedition["signal"]["fsamp"][0, 0])
                    )

                    if len(peaks) >= 10:
                        top_values = np.sort(pulse_train[peaks])[-10:]
                        pulse_train = pulse_train / np.mean(top_values)
                    elif len(peaks) > 0:
                        pulse_train = pulse_train / np.mean(pulse_train[peaks])

                    if len(peaks) >= 2:
                        kmeans = KMeans(n_clusters=2, random_state=0).fit(pulse_train[peaks].reshape(-1, 1))
                        labels = kmeans.labels_
                        centroids = kmeans.cluster_centers_

                        high_centroid_idx = np.argmax(centroids)
                        spikes = peaks[labels == high_centroid_idx]

                        threshold = np.mean(pulse_train[spikes]) + 3 * np.std(pulse_train[spikes])
                        spikes = spikes[pulse_train[spikes] <= threshold]
                    else:
                        spikes = peaks

                    self.MUedition["edition"]["Pulsetrain"][array_idx][mu_idx, :] = pulse_train
                    self.MUedition["edition"]["Dischargetimes"][(array_idx, mu_idx)] = spikes

                processed_mus += 1

        self.progress_changed.emit(100)
        self.finished.emit()
