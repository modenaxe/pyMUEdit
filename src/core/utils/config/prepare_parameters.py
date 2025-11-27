def prepare_parameters(ui_params, algo_choice):
    """Convert UI parameters to algorithm parameters for emg_decomposition.py"""
    parameters = {}

    match algo_choice:
        case "Fast ICA":
            # Convert UI dropdown values to numeric flags
            parameters["checkEMG"] = 1 if ui_params.get("check_emg") == "Yes" else 0
            parameters["peeloff"] = 1 if ui_params.get("peeloff") == "Yes" else 0
            parameters["covfilter"] = 1 if ui_params.get("cov_filter") == "Yes" else 0
            parameters["initialization"] = 0 if ui_params.get("initialization") == "EMG max" else 1
            parameters["refineMU"] = 1 if ui_params.get("refine_mu") == "Yes" else 0
            parameters["duplicatesbgrids"] = 1 if ui_params.get("duplicates_bgrids", "Yes") == "Yes" else 0

            # Set numeric parameters
            parameters["NITER"] = ui_params.get("iterations", 75)
            parameters["nwindows"] = ui_params.get("windows", 1)
            use_threshold = ui_params.get("use_threshold", True)
            if use_threshold:
                parameters["thresholdtarget"] = ui_params.get("threshold_target", 0.8)
            else:
                parameters["thresholdtarget"] = 0
            parameters["nbextchan"] = ui_params.get("extended_channels", 1000)
            parameters["duplicatesthresh"] = ui_params.get("duplicates_threshold", 0.3)
            parameters["silthr"] = ui_params.get("sil_threshold", 0.9)
            parameters["covthr"] = ui_params.get("cov_threshold", 0.5)

            # Set algorithm-specific parameters
            parameters["CoVDR"] = 0.3  # Threshold for CoV of Discharge rate
            parameters["edges"] = 0.2  # Edges to remove (in seconds)
            parameters["contrastfunc"] = ui_params.get("contrast_function", "skew")
            parameters["peeloffwin"] = 0.025  # Window duration for detecting action potentials
            parameters["differentialmode"] = 0  # Default to no differentiation
            parameters["drawingmode"] = 0  # Enable visualization
            parameters["enable_plots"] = True  # Enable plots for debugging
        case "SCD":
            # Convert UI dropdown values to text or booleans
            parameters["device"] = "cpu" if ui_params.get("device") == "CPU" else "cuda"
            parameters["filt_harms"] = True if ui_params.get("filt_harms") == "Yes" else False
            parameters["use_coeff_var_fitness"] = True if ui_params.get("use_coeff_var_fitness") == "Yes" else False
            parameters["remove_bad_fr"] = True if ui_params.get("remove_bad_fr") == "Yes" else False

            # Get numeric values from UI spinbox values
            parameters["iterations"] = ui_params.get("iterations", 75)
            parameters["acceptance_silhouette"] = ui_params.get("acceptance_silhouette", 0.85)
            parameters["extension_factor"] = ui_params.get("extension_factor", 10)
            parameters["low_pass_cutoff"] = ui_params.get("low_pass_cutoff", 1000)
            parameters["high_pass_cutoff"] = ui_params.get("high_pass_cutoff", 10)
            parameters["powerline_frequency"] = ui_params.get("powerline_frequency", 50)
            parameters["peel_off_window_size"] = ui_params.get("peel_off_window_size", 20)
            parameters["bandwidth"] = ui_params.get("bandwidth", 1.0)

    return parameters
    
