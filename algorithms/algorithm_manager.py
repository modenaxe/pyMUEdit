import pickle
from fastICA_algorithm.emg_decomposition_final import offline_EMG

def fastICA(otb_filepath, save_dir, output_filename, to_filter=True):
    """
    Processes a given .otb EMG file using the offline_EMG module and saves the resulting
    motor unit data to a file.
    
    Parameters:
      otb_filepath (str): Path to the .otb file.
      save_dir (str): directory at which final discharges will be saved
      output_filename (str): output file name
      to_filter (bool): whether or not you notch and butter filter the data
    """
    # Create an instance of the offline_EMG class
    processor = offline_EMG(save_dir, to_filter)
    
    # Read and extract the .otb file and parse metadata
    processor.open_otb(otb_filepath)
    
    # Perform the decomposition here...

    # FastICA algorithm here...

    # write to output_filename here...

    # Save results to save_dir here ...