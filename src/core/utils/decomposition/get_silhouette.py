import numpy as np
import scipy
from sklearn.cluster import KMeans
from utils.decomposition.get_spikes import maxk


def get_silhouette(w_n, Z, fsamp):
    """
    Calculates the silhouette score for the identified spikes.

    The silhouette score measures how well the spikes are separated from noise,
    based on the difference between within-cluster and between-cluster distances.
    """

    source_pred = np.dot(np.transpose(w_n), Z).real  # element-wise square of the input to estimate the ith source
    source_pred = np.multiply(source_pred, abs(source_pred))  # keep the negatives

    peaks, _ = scipy.signal.find_peaks(np.squeeze(source_pred), distance=np.round(fsamp * 0.02) + 1)
    source_pred /= np.mean(maxk(source_pred[peaks], 1))
    if len(peaks) > 1:

        # two classes: 1) spikes 2) noise
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1).fit(source_pred[peaks].reshape(-1, 1))

        # indices of the spike and noise clusters (the spike cluster should have a larger value)
        spikes_ind = np.argmax(kmeans.cluster_centers_)
        noise_ind = np.argmin(kmeans.cluster_centers_)

        # get the points that correspond to each of these clusters
        spikes = peaks[np.where(kmeans.labels_ == spikes_ind)]

        # calculate the centroids
        spikes_centroid = kmeans.cluster_centers_[spikes_ind]
        noise_centroid = kmeans.cluster_centers_[noise_ind]

        # difference between the within-cluster sums of point-to-centroid distances
        intra_sums = ((source_pred[spikes] - spikes_centroid) ** 2).sum()
        inter_sums = ((source_pred[spikes] - noise_centroid) ** 2).sum()
        sil = (inter_sums - intra_sums) / max(intra_sums, inter_sums)

    else:
        sil = 0

    return source_pred, spikes, sil
