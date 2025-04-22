def prepare_parameters(ui_params):
    """Convert UI parameters to algorithm parameters for emg_decomposition.py"""
    parameters = {}

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
    parameters["thresholdtarget"] = ui_params.get("threshold_target", 0.8)
    parameters["nbextchan"] = ui_params.get("extended_channels", 1000)
    parameters["duplicatesthresh"] = ui_params.get("duplicates_threshold", 0.3)
    parameters["silthr"] = ui_params.get("sil_threshold", 0.9)
    parameters["covthr"] = ui_params.get("cov_threshold", 0.5)

    # Set algorithm-specific parameters
    parameters["CoVDR"] = 0.3  # Threshold for CoV of Discharge rate
    parameters["edges"] = 0.5  # Edges to remove (in seconds)
    parameters["contrastfunc"] = ui_params.get("contrast_function", "skew")
    parameters["peeloffwin"] = 0.025  # Window duration for detecting action potentials
    parameters["differentialmode"] = 0  # Default to no differentiation
    parameters["drawingmode"] = 0  # Enable visualization
    parameters["enable_plots"] = True  # Enable plots for debugging

    return parameters
