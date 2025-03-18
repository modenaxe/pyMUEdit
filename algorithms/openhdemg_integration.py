import openhdemg.library as emg
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import pickle
import scipy.io as sio
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Then import using the absolute path
from algorithms.algorithm_manager import fastICA

def load_decomposition_output(pickle_file_path):
    """Load the decomposition output saved by algorithm_manager.py"""
    with open(pickle_file_path, 'rb') as file:
        all_dicts = pickle.load(file)
    return all_dicts

def load_parameters(params_file_path):
    """Load the parameters saved by algorithm_manager.py"""
    with open(params_file_path, 'rb') as file:
        parameters = pickle.load(file)
    return parameters

def create_openhdemg_emgfile(all_dicts, parameters):
    """Convert decomposition results to openhdemg emgfile format"""
    # Initialize the emgfile structure
    emgfile = {
        "SOURCE": "CUSTOMCODE",
        "FILENAME": os.path.basename(parameters['file_path']),
        "RAW_SIGNAL": pd.DataFrame(parameters['original_data']),
        "REF_SIGNAL": pd.DataFrame(parameters.get('path', [])),
        "FSAMP": parameters['fsamp'],
        "IED": all_dicts[0]['ied'] if all_dicts else 0,
        "EMG_LENGTH": parameters['original_data'].shape[1],
        "NUMBER_OF_MUS": 0,  # Will calculate this below
        "EXTRAS": pd.DataFrame()
    }
    
    # Process all pulse trains
    all_pulse_trains = []
    for dict_entry in all_dicts:
        if 'pulse_trains' in dict_entry and dict_entry['pulse_trains'][0] is not None:
            for pt in dict_entry['pulse_trains'][0]:
                all_pulse_trains.append(pt)
    
    if all_pulse_trains:
        emgfile["IPTS"] = pd.DataFrame(np.vstack(all_pulse_trains).T)
    else:
        emgfile["IPTS"] = pd.DataFrame()
    
    # Create MUPULSES (discharge times)
    emgfile["MUPULSES"] = []
    for electrode_idx, dict_entry in enumerate(all_dicts):
        if 'discharge_times' in dict_entry and dict_entry['discharge_times'][0]:
            for discharge_times in dict_entry['discharge_times'][0]:
                emgfile["MUPULSES"].append(np.array(discharge_times))
    
    accuracy_values = []
    for i in range(len(emgfile["MUPULSES"])):
        # Use a default accuracy value or extract from data if available
        # Try to get SIL values from the data if they exist
        accuracy_values.append(0.9)  # Default value
    
    # Create DataFrame with explicit index matching number of MUs
    emgfile["ACCURACY"] = pd.DataFrame({0: accuracy_values}, index=range(len(emgfile["MUPULSES"])))
    emgfile["NUMBER_OF_MUS"] = len(emgfile["MUPULSES"])
    
    # Create binary MU firing representation
    if emgfile["MUPULSES"]:
        binary_mus = np.zeros((emgfile["EMG_LENGTH"], len(emgfile["MUPULSES"])))
        for i, discharge_times in enumerate(emgfile["MUPULSES"]):
            binary_mus[discharge_times, i] = 1
        emgfile["BINARY_MUS_FIRING"] = pd.DataFrame(binary_mus)
    else:
        emgfile["BINARY_MUS_FIRING"] = pd.DataFrame()
    
    return emgfile

def save_for_openhdemg(all_dicts, parameters, output_path):
    """Save decomposition results in a format compatible with openhdemg (.mat file)"""
    # Create the signal structure as expected by openhdemg
    signal = {
        'data': parameters['original_data'],
        'fsamp': parameters['fsamp'],
        'nChan': parameters['original_data'].shape[0],
        'ngrid': len(all_dicts),
        'gridname': np.array([d['chan_name'] for d in all_dicts], dtype=object),
        'muscle': np.array([d['muscle_name'] for d in all_dicts], dtype=object),
    }
    
    # Add target and path if available
    if 'target' in parameters:
        signal['target'] = parameters['target']
    if 'path' in parameters:
        signal['path'] = parameters['path']
    
    # Add pulse trains and discharge times
    pulse_trains_list = []
    discharge_times_list = []
    
    for dict_entry in all_dicts:
        if 'pulse_trains' in dict_entry and dict_entry['pulse_trains'][0] is not None:
            for pt in dict_entry['pulse_trains'][0]:
                pulse_trains_list.append(pt)
        
        if 'discharge_times' in dict_entry and dict_entry['discharge_times'][0]:
            for dt in dict_entry['discharge_times'][0]:
                discharge_times_list.append(dt)
    
    signal['Pulsetrain'] = np.array(pulse_trains_list)
    signal['Dischargetimes'] = np.array(discharge_times_list, dtype=object)
    
    # Save the structure to .mat file
    sio.savemat(output_path, {'signal': signal})
    
    return output_path

def process_decomposition_output(pickle_file_path, params_file_path, output_dir, analysis_params=None):
    # Load the decomposition results
    all_dicts = load_decomposition_output(pickle_file_path)
    parameters = load_parameters(params_file_path)
    
    # Create the emgfile for openhdemg
    emgfile = create_openhdemg_emgfile(all_dicts, parameters)
    
    # Optionally save in .mat format
    mat_file_path = os.path.join(output_dir, 'for_openhdemg.mat')
    save_for_openhdemg(all_dicts, parameters, mat_file_path)
    
    # Run openhdemg analysis
    # Sort MUs based on recruitment order
    emgfile = emg.sort_mus(emgfile=emgfile)
    
    # Filter the reference signal
    if not emgfile["REF_SIGNAL"].empty:
        emgfile = emg.filter_refsig(emgfile=emgfile)
        emgfile = emg.remove_offset(emgfile=emgfile, auto=1024)
    
    # Calculate basic properties if analysis_params is provided
    results = None
    if analysis_params is not None:  # Check if analysis_params exists
        if 'mvc' in analysis_params:
            results = emg.basic_mus_properties(emgfile=emgfile, mvc=analysis_params['mvc'])
            
        # Save the results if desired
        if results is not None and 'results_path' in analysis_params:
            results.to_csv(analysis_params['results_path'])
        
        # Save the edited emgfile
        if 'emgfile_path' in analysis_params:
            emg.asksavefile(emgfile=emgfile, filename=analysis_params['emgfile_path'])

    visualize_decomposition(emgfile)
    
    return emgfile, results

def run_decomposition_and_analyze(input_dir, output_dir, analysis_params=None):
    """Run the entire pipeline: decomposition and analysis"""
    
    # Add the path where algorithm_manager.py is located
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from algorithm_manager import fastICA
    
    # Run the decomposition
    fastICA()  # This processes files in the input directory and saves outputs
    
    # Find the generated output files
    decomp_files = [f for f in os.listdir(output_dir) if f.endswith('.pkl') and not f.endswith('_params.pkl')]
    params_files = [f for f in os.listdir(output_dir) if f.endswith('_params.pkl')]
    
    results = []
    
    # Process each decomposition file
    for i, decomp_file in enumerate(decomp_files):
        # Find corresponding parameters file
        base_name = decomp_file.split('.')[0]
        params_file = next((f for f in params_files if f.startswith(base_name)), None)
        
        if params_file:
            # Process this decomposition output
            emgfile, analysis_result = process_decomposition_output(
                os.path.join(output_dir, decomp_file),
                os.path.join(output_dir, params_file),
                output_dir,
                analysis_params
            )
            results.append((emgfile, analysis_result))
    
    return results

def visualize_decomposition(emgfile):
    """Display standard visualizations for the decomposed data"""
    
    # Create time vector based on the length of the data and sampling frequency
    time = np.arange(emgfile["EMG_LENGTH"]) / emgfile["FSAMP"]
    
    # Plot 1: Motor unit discharge patterns
    plt.figure(figsize=(12, 6))
    
    # Plot reference signal if available
    if not emgfile["REF_SIGNAL"].empty:
        ax1 = plt.subplot(2, 1, 1)
        ax1.plot(time, emgfile["REF_SIGNAL"].iloc[:, 0], 'k-')
        ax1.set_title('Reference Signal')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(time[0], time[-1])
        plt.grid(True)
    
    # Plot motor unit discharge times
    ax2 = plt.subplot(2, 1, 2)
    for i, discharges in enumerate(emgfile["MUPULSES"]):
        # Convert sample indices to time
        discharge_times = np.array(discharges) / emgfile["FSAMP"]
        # Plot as vertical lines at each discharge time
        for t in discharge_times:
            ax2.axvline(x=t, ymin=i/len(emgfile["MUPULSES"]), 
                       ymax=(i+0.8)/len(emgfile["MUPULSES"]), 
                       color='blue', linewidth=0.5)
    
    ax2.set_title('Motor Unit Discharge Patterns')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Motor Unit')
    ax2.set_yticks(np.arange(len(emgfile["MUPULSES"])))
    ax2.set_yticklabels([f'MU {i+1}' for i in range(len(emgfile["MUPULSES"]))])
    ax2.set_xlim(time[0], time[-1])
    plt.tight_layout()
    
    # Plot 2: Instantaneous discharge rates
    plt.figure(figsize=(12, 6))
    
    for i, discharges in enumerate(emgfile["MUPULSES"]):
        # Convert sample indices to time
        discharge_times = np.array(discharges) / emgfile["FSAMP"]
        
        if len(discharge_times) > 1:
            # Calculate instantaneous discharge rates (1/ISI)
            isi = np.diff(discharge_times)
            idr = 1/isi
            
            # Plot at the midpoint between consecutive discharges
            idr_times = discharge_times[:-1] + isi/2
            plt.plot(idr_times, idr, '-o', markersize=2, label=f'MU {i+1}')
    
    plt.title('Instantaneous Discharge Rates')
    plt.xlabel('Time (s)')
    plt.ylabel('Discharge Rate (Hz)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Plot 3: Raw EMG signal (sample channels)
    plt.figure(figsize=(12, 6))

    # Check the actual dimensions of the data
    raw_signal_length = len(emgfile['RAW_SIGNAL'])
    time_length = len(time)

    # Create a proper time vector that matches the raw signal length
    if raw_signal_length != time_length:
        # Create a new time vector that matches the RAW_SIGNAL length
        adjusted_time = np.arange(raw_signal_length) / emgfile["FSAMP"]
    else:
        adjusted_time = time

    # Plot a subset of channels
    channels_to_plot = min(5, emgfile['RAW_SIGNAL'].shape[1])
    for i in range(channels_to_plot):
        plt.plot(adjusted_time, emgfile['RAW_SIGNAL'].iloc[:, i], label=f'Channel {i+1}')

    plt.title(f'Raw EMG Signals (First {channels_to_plot} Channels)')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Only call plt.show() once at the end to display all figures at once
    plt.show()