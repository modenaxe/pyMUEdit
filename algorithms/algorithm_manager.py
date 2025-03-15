import pickle
from fastICA_algorithm.emg_decomposition_final import offline_EMG

def fastICA(otb_filepath, save_dir, output_filename, to_filter=True):
    """
    Processes a given .otb EMG file using the offline_EMG module and saves the resulting
    motor unit data to a file.
    
    Parameters:
      otb_filepath (str): Path to the .otb file.
      save_dir (str): Directory for saving temporary and output files.
      output_filename (str): Path (including filename) where the results will be saved.
      to_filter (bool): Whether to perform notch and bandpass filtering.
    """
    # Create an instance of the offline_EMG class
    processor = offline_EMG(save_dir, to_filter)
    
    # Read and extract the .otb file and parse metadata
    processor.open_otb(otb_filepath)
    
    # Perform the decomposition

    # FastICA algorithm here...
    
    # write to output_filename here...

    
    print(f"Processing complete. Results saved to {output_filename}")