import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(project_root))

from src.run_decomposition import run_decomposition

# Example usage of the run_decomposition function

def main():
    # Path to the sample OTB+ file
    # Using a sample file from the data directory
    sample_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data1', 'trial1_20MVC.otb+')
    
    # Check if the sample file exists
    if not os.path.exists(sample_file):
        print(f"Sample file {sample_file} not found.")
        print("Please update the path to point to a valid OTB+ file.")
        return
    
    # Create an output directory for the results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data1', 'decomp_output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Running decomposition on {sample_file}")
    print(f"Results will be saved to {output_dir}")
    
    # Run the decomposition
    results = run_decomposition(
        input_file=sample_file,
        output_dir=output_dir,
        save_intermediate=True  # Set to False to disable intermediate outputs
    )
    
    # Check if decomposition was successful
    if results is None:
        print("Decomposition failed. Check the console output for errors.")
        return
    
    # Print some information about the results
    mu_dict = results["mu_dict"]
    signal_dict = results["signal_dict"]
    
    # Print information about the signal
    print("\nSignal Information:")
    print(f"Sampling frequency: {signal_dict['fsamp']} Hz")
    print(f"Number of electrodes: {signal_dict['ngrid']}")
    print(f"Signal duration: {signal_dict['target'].shape[0] / signal_dict['fsamp']:.2f} seconds")
    
    # Print information about the motor units
    print("\nMotor Unit Information:")
    total_mus = 0
    for i, discharge_times in enumerate(mu_dict["discharge_times"]):
        n_mus = len(discharge_times)
        total_mus += n_mus
        print(f"Electrode {i+1}: {n_mus} motor units")
    
    print(f"Total motor units found: {total_mus}")
    
    # Print the output file path
    output_file = os.path.join(output_dir, os.path.basename(sample_file).split('.')[0] + "_decomp.mat")
    print(f"\nResults saved to: {output_file}")
    print("You can load this file in MATLAB or Python using scipy.io.loadmat()")

if __name__ == "__main__":
    main()