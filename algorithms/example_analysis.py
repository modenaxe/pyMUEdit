import sys
import os
from pathlib import Path

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the root of the project (assuming your script is in /algorithms directory)
project_root = os.path.dirname(os.path.dirname(current_dir))

# Create paths relative to the project root
input_dir = os.path.join(project_root, "data", "io", "input_decomposition")
output_dir = os.path.join(project_root, "data", "io", "output_decomposition")

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from openhdemg_integration import run_decomposition_and_analyze, process_decomposition_output


# Define input/output directories and analysis parameters
input_dir = "../data/io/input_decomposition"
output_dir = "../data/io/output_decomposition"

# Convert backslashes to forward slashes for the open_otb function
input_dir = input_dir.replace("\\", "/")
output_dir = output_dir.replace("\\", "/")

# Run the complete pipeline
results = run_decomposition_and_analyze(input_dir, output_dir)

# Or just process previously decomposed data
pickle_file = "../data/io/input_decomposition/trial1_20MVC.pkl"
params_file = "../data/io/input_decomposition/trial1_20MVC_params.pkl"
emgfile, analysis = process_decomposition_output(pickle_file, params_file, output_dir) # we can add analysis params later