from algorithm_manager import fastICA

# Example usage:
# Note paths are relative to current working directory
otb_filepath = "../data/io/input_decomposition" # Path to .otb files
result_file = "../data/io/output_decomposition/trial1_20MVC.pkl" # Path to result file
save_directory = "../data/io/saved_files" # Directory for saving output files
    
# Run the algorithm
fastICA(otb_filepath, save_directory, result_file, to_filter=True)