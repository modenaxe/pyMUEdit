import os
import sys
import numpy as np

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the offline_EMG class
from core.EmgDecomposition import offline_EMG

def run_decomposition(input_file, output_dir=None, save_intermediate=True):
    """
    Run the EMG decomposition process on an input OTB+ file.
    
    Args:
        input_file (str): Path to the input OTB+ file
        output_dir (str, optional): Directory to save results. If None, uses the same directory as input_file
        save_intermediate (bool): Whether to save intermediate outputs for debugging
    
    Returns:
        dict: The decomposition results
    """
    # Validate input file
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        return None
    
    if not input_file.endswith('.otb+'):
        print(f"Warning: Input file {input_file} does not have .otb+ extension")
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_file))
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize the EMG object
    emg = offline_EMG(save_dir=output_dir, to_filter=True)
    emg.save_intermediate = save_intermediate
    
    # Set decomposition parameters
    emg.its = 20  # Number of iterations for fixed point algorithm
    emg.check_emg = 0  # Automatic selection of EMG channels
    emg.sil_thr = 0.9  # Silhouette threshold
    emg.cov_thr = 0.5  # Coefficient of variation threshold
    emg.dup_thr = 0.3  # Duplicate threshold
    emg.dup_bgrids = 1  # Enable duplicate removal between grids
    
    print(f"Starting decomposition of {input_file}")
    
    # Open the OTB+ file
    emg.open_otb(input_file)
    
    # Format electrodes
    emg.electrode_formatter()
    
    # Manual rejection (automatic in this case)
    emg.manual_rejection()
    
    # Batch the signal
    if "target" in emg.signal_dict and emg.signal_dict["target"] is not None:
        print("Using target for batching")
        emg.batch_w_target()
    else:
        print("No target found, using automatic batching")
        emg.batch_wo_target()
    
    # Initialize arrays for decomposition
    emg.signal_dict["diff_data"] = []
    tracker = 0
    nwins = int(len(emg.plateau_coords) / 2)
    
    # Process each electrode
    for g in range(int(emg.signal_dict["nelectrodes"])):
        print(f"Processing electrode {g+1}/{emg.signal_dict['nelectrodes']}")
        
        # Calculate extension factor
        extension_factor = int(
            np.round(emg.ext_factor / np.shape(emg.signal_dict["batched_data"][tracker])[0])
        )
        
        # Initialize arrays for extended EMG data
        emg.signal_dict["extend_obvs_old"] = np.zeros(
            [
                nwins,
                np.shape(emg.signal_dict["batched_data"][tracker])[0] * (extension_factor),
                np.shape(emg.signal_dict["batched_data"][tracker])[1]
                + extension_factor
                - 1
                - emg.differential_mode,
            ]
        )
        emg.decomp_dict["whitened_obvs_old"] = emg.signal_dict["extend_obvs_old"].copy()
        
        # Initialize arrays for square and inverse of extended EMG data
        emg.signal_dict["sq_extend_obvs"] = np.zeros(
            [
                nwins,
                np.shape(emg.signal_dict["batched_data"][tracker])[0] * (extension_factor),
                np.shape(emg.signal_dict["batched_data"][tracker])[0] * (extension_factor),
            ]
        )
        emg.signal_dict["inv_extend_obvs"] = emg.signal_dict["sq_extend_obvs"].copy()
        
        # Dewhitening and whitening matrices
        emg.decomp_dict["dewhiten_mat"] = emg.signal_dict["sq_extend_obvs"].copy()
        emg.decomp_dict["whiten_mat"] = emg.signal_dict["sq_extend_obvs"].copy()
        
        # Extended EMG data AFTER removal of edges
        emg.signal_dict["extend_obvs"] = emg.signal_dict["extend_obvs_old"][
            :,
            :,
            int(np.round(emg.signal_dict["fsamp"] * emg.edges2remove) - 1) : -int(
                np.round(emg.signal_dict["fsamp"] * emg.edges2remove)
            ),
        ].copy()
        emg.decomp_dict["whitened_obvs"] = emg.signal_dict["extend_obvs"].copy()
        
        # Process each window interval
        for interval in range(nwins):
            print(f"Processing electrode {g+1}, interval {interval+1}/{nwins}")
            
            # Initialize separation matrices and vectors
            emg.decomp_dict["B_sep_mat"] = np.zeros(
                [np.shape(emg.decomp_dict["whitened_obvs"][interval])[0], emg.its]
            )
            emg.decomp_dict["w_sep_vect"] = np.zeros(
                [np.shape(emg.decomp_dict["whitened_obvs"][interval])[0], 1]
            )
            emg.decomp_dict["MU_filters"] = np.zeros(
                [nwins, np.shape(emg.decomp_dict["whitened_obvs"][interval])[0], emg.its]
            )
            emg.decomp_dict["SILs"] = np.zeros([nwins, emg.its])
            emg.decomp_dict["CoVs"] = np.zeros([nwins, emg.its])
            emg.decomp_dict["tracker"] = np.zeros([1, emg.its])
            emg.decomp_dict["masked_mu_filters"] = []
            
            # Run convolutive sphering
            emg.convul_sphering(g, interval, tracker)
            
            # Run FastICA and CKC
            emg.fast_ICA_and_CKC(g, interval, tracker, cf_type="skew")
            
            # Print SIL/CoV information
            if "SILs" in emg.decomp_dict and "CoVs" in emg.decomp_dict:
                sil = np.max(emg.decomp_dict["SILs"][interval, :])
                cov = np.min(emg.decomp_dict["CoVs"][interval, :])
                print(f"Electrode {g+1}, interval {interval+1}: SIL={sil:.4f}, CoV={cov:.4f}")
            
            tracker += 1
        
        # Post-process this electrode
        print(f"Post-processing electrode {g+1}...")
        emg.post_process_EMG(g)
    
    # Process across arrays if enabled
    if emg.dup_bgrids and sum(emg.mus_in_array) > 0:
        print("Processing across arrays...")
        emg.post_process_across_arrays()
    
    # Save results to .mat file
    output_file = os.path.splitext(os.path.basename(input_file))[0] + "_decomp.mat"
    output_path = os.path.join(output_dir, output_file)
    
    # Create a dictionary with the results
    results = {
        "mu_dict": emg.mu_dict,
        "signal_dict": emg.signal_dict,
        "decomp_dict": emg.decomp_dict
    }
    
    # Save to .mat file
    import scipy.io as sio
    sio.savemat(output_path, results)
    
    print(f"Decomposition complete. Results saved to {output_path}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run EMG decomposition on an OTB+ file")
    parser.add_argument("input_file", help="Path to the input OTB+ file")
    parser.add_argument("--output-dir", help="Directory to save results (default: same as input file)")
    parser.add_argument("--no-intermediate", action="store_true", help="Disable saving intermediate outputs")
    
    args = parser.parse_args()
    
    run_decomposition(
        args.input_file, 
        output_dir=args.output_dir, 
        save_intermediate=not args.no_intermediate
    )