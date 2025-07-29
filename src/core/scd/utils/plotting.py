"""Matplotlib functions for plotting decomposition outputs"""

from typing import List, Optional
import torch
import numpy as np

from ..config.structures import set_random_seed

set_random_seed(seed=42)

# plot_sources function is removed, available in original repository if needed

def plot_accepted_source(source, best_timestamps, sil=None, cov=None, plot_callback=None):
    source = source.cpu().detach().numpy()
    best_timestamps = best_timestamps.cpu().detach().numpy()
    if plot_callback: plot_callback(source, best_timestamps, None, sil, cov)
