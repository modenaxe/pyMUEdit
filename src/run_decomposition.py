import os
import sys
import numpy as np

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the offline_EMG class
from core.EmgDecomposition import format_results_2, offline_EMG
from core.logger import logger

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
    try:
    # Validate input file
        if not os.path.exists(input_file):
            logger.error(f"Error: Input file {input_file} does not exist")
            return None

        if not input_file.endswith(".otb+"):
            logger.error(f"Warning: Input file {input_file} does not have .otb+ extension")

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
        parameters = {
            "NITER": 10,
            "ref_exist": 1,  # if ref_signal exist ref_exist = 1; if not ref_exist = 0 and manual selection of windows
            "checkEMG": 0,  # 0 = Consider all the channels ; 1 = Visual checking
            "nwindows": 1,  # number of segmented windows over each contraction
            "differentialmode": 0,  # 0 = no; 1 = yes (filter out the smallest MU, can improve decomposition at the highest intensities
            "initialization": 0,  # 0 = max EMG; 1 = random weights
            "peeloff": 1,  # 0 = no; 1 = yes (update the residual EMG by removing the motor units with the highest SIL value)
            "covfilter": 1,  # 0 = no; 1 = yes (filter out the motor units with a coefficient of variation of their ISI > than parameters.covthr)
            "refineMU": 1,  # 0 = no; 1 = yes (refine the MU spike train over the entire signal 1-remove the discharge times that generate outliers in the discharge rate and 2- reevaluate the MU pulse train)
            "drawingmode": 0,  # 0 = Output in the command window ; 1 = Output in a figure
            "duplicatesbgrids": 1,  # 0 = do not consider duplicates between grids ; 1 = Remove duplicates between grids
            # SPECIFIC VALUES
            "thresholdtarget": 0.8,  # threshold to segment the target displayed to the participant, 1 being the maxima of the target (e.g., plateau)
            "nbextchan": 1000,  # nb of extended channels (1000 in Negro 2016, can be higher to improve the decomposition)
            "edges": 0.2,  # edges of the signal to remove after preprocessing the signal (in sec)
            "contrastfunc": "skew",  # contrast functions: 'skew', 'kurtosis', 'logcosh'
            "silthr": 0.90,  # Threshold for SIL values
            "covthr": 0.5,  # Threshold for CoV of ISI values
            "peeloffwin": 0.025,  # duration of the window (ms) for detecting the action potentials from the EMG signal
            "duplicatesthresh": 0.3,  # threshold that define the minimal percentage of common discharge times between duplicated motor units
            "CoVDR": 0.3,  # threshold that define the CoV of Discharge rate that we want to reach for cleaning the MU discharge times when refineMU is on
        }
        emg.apply_muedit_params(parameters)

        logger.debug(f"Starting decomposition of {input_file}")

        # Open the OTB+ file
        emg.open_otb_plus(input_file)

        # Format electrodes
        emg.electrode_formatter()

        # Manual rejection (automatic in this case)
        emg.manual_rejection()

        # Batch the signal
        if "target" in emg.signal_dict and emg.signal_dict["target"] is not None:
            logger.debug("Using target for batching")
            emg.batch_w_target()
        else:
            print("No target found, using automatic batching")
            emg.batch_wo_target()

        # Initialize arrays for decomposition
        emg.signal_dict["diff_data"] = []
        tracker = 0
        nwins = int(len(emg.plateau_coords) / 2)

        # Process each electrode
        for g in range(int(emg.signal_dict["ngrid"])):
            logger.debug(f"Processing electrode {g + 1}/{emg.signal_dict['ngrid']}")

            # Calculate extension factor
            extension_factor = int(
                np.round(
                    emg.ext_factor / np.shape(emg.signal_dict["batched_data"][tracker])[0]
                )
            )

            # Initialize arrays for extended EMG data
            emg.signal_dict["extend_obvs_old"] = np.zeros(
                [
                    nwins,
                    np.shape(emg.signal_dict["batched_data"][tracker])[0]
                    * (extension_factor),
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
                    np.shape(emg.signal_dict["batched_data"][tracker])[0]
                    * (extension_factor),
                    np.shape(emg.signal_dict["batched_data"][tracker])[0]
                    * (extension_factor),
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
                logger.debug(f"Processing electrode {g + 1}, interval {interval + 1}/{nwins}")

                # Initialize separation matrices and vectors
                emg.decomp_dict["B_sep_mat"] = np.zeros(
                    [np.shape(emg.decomp_dict["whitened_obvs"][interval])[0], emg.its]
                )
                emg.decomp_dict["w_sep_vect"] = np.zeros(
                    [np.shape(emg.decomp_dict["whitened_obvs"][interval])[0], 1]
                )
                emg.decomp_dict["MU_filters"] = np.zeros(
                    [
                        nwins,
                        np.shape(emg.decomp_dict["whitened_obvs"][interval])[0],
                        emg.its,
                    ]
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
                    logger.info(
                        f"Electrode {g + 1}, interval {interval + 1}: SIL={sil:.4f}, CoV={cov:.4f}"
                    )

                tracker += 1

            # Post-process this electrode
            logger.debug(f"Post-processing electrode {g + 1}...")
            emg.post_process_EMG(g)

        # Process across arrays if enabled
        if emg.dup_bgrids and sum(emg.mus_in_array) > 0:
            logger.debug("Processing across arrays...")
            emg.post_process_across_arrays()

        # Save results to .mat file
        output_file = os.path.splitext(os.path.basename(input_file))[0] + "_decomp.mat"
        output_path = os.path.join(output_dir, output_file)

        # Create a dictionary with the results
        results = {
            "signal": format_results_2(emg.format_results_1()),
            "parameters": parameters
        }

        # Save to .mat file
        import scipy.io as sio

        sio.savemat(output_path, results)
        logger.info(f"Result keys: {list(results.keys())}")
        logger.info(f"Signal shape: {np.shape(results['signal'])}")
        logger.debug(f"Decomposition complete. Results saved to {output_path}")
        return results
    except Exception as e:
        logger.exception(f"Decomposition failed for file {input_file}: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run EMG decomposition on an OTB+ file"
    )
    parser.add_argument("input_file", help="Path to the input OTB+ file")
    parser.add_argument(
        "--output-dir", help="Directory to save results (default: same as input file)"
    )
    parser.add_argument(
        "--no-intermediate",
        action="store_true",
        help="Disable saving intermediate outputs",
    )

    args = parser.parse_args()

    run_decomposition(
        args.input_file,
        output_dir=args.output_dir,
        save_intermediate=not args.no_intermediate,
    )
