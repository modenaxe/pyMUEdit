# EMG Decomposition Script

This script allows you to run the EMG decomposition process on an OTB+ file without using the GUI application.

## Prerequisites

- Python 3.7 or higher
- All dependencies installed (see `requirements.txt` in the main project)

## Usage

### Basic Usage

Run the script with the path to your OTB+ file:

```bash
python run_decomposition.py path/to/your/file.otb+
```

This will:
1. Run the decomposition process on the specified file
2. Save the results in the same directory as the input file
3. Save intermediate outputs for debugging purposes

### Advanced Options

```bash
python run_decomposition.py path/to/your/file.otb+ --output-dir path/to/output/directory --no-intermediate
```

- `--output-dir`: Specify a custom directory to save the results
- `--no-intermediate`: Disable saving intermediate outputs (reduces disk usage)

## Output

The script generates a MATLAB (.mat) file with the decomposition results. The output file will be named `[input_filename]_decomp.mat` and will contain:

- `mu_dict`: Motor unit dictionary with discharge times, pulse trains, etc.
- `signal_dict`: Signal information including raw data, processed data, etc.
- `decomp_dict`: Decomposition information including whitened observations, separation matrices, etc.

If intermediate outputs are enabled (default), debug files will be saved in a `debug_outputs` subdirectory.

## Using as a Module

You can also import the `run_decomposition` function in your own Python code:

```python
from run_decomposition import run_decomposition

# Run decomposition and get results
results = run_decomposition(
    input_file="path/to/your/file.otb+",
    output_dir="path/to/output/directory",  # Optional
    save_intermediate=True  # Optional
)

# Access results
mu_dict = results["mu_dict"]
print(f"Found {len(mu_dict['discharge_times'])} electrode arrays with motor units")
```

## Troubleshooting

- If you encounter memory errors, try disabling intermediate outputs with `--no-intermediate`
- Make sure your OTB+ file is valid and contains the expected data
- Check the console output for detailed progress and error messages