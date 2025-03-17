from fastICA_algorithm.emg_decomposition_final import offline_EMG
import glob, os
import numpy as np
import pickle 
import pandas as pd
import json

def fastICA():
    # Convert all directories to absolute paths before any chdir
    input_dir = os.path.abspath("../data/io/input_decomposition")
    output_dir = os.path.abspath("../data/io/output_decomposition")
    
    # Initialize the EMG object with the given directory and to_paramter = 1
    emg_obj = offline_EMG(input_dir, 1)
    
    # List the .otb+ files before changing the working directory
    all_files = sorted(glob.glob(os.path.join(input_dir, '*.otb+')))
    if not all_files:
        print(f"No .otb files found in directory: {input_dir}")
        return
    
    all_dicts = []
    
    # File type options: 'otb', 'csv', 'ephys', etc.
    file_type = 'otb'
    
    # Process each file found
    for file in all_files:
        ################## FILE ORGANISATION ################################
        file_name = file.split('/')[-1]
        if file_type == 'otb':
            emg_obj.open_otb(file) 
        elif file_type == 'csv':
            print('CSV file processing to be completed')
        elif file_type == 'ephys':
            print('Ephys file processing to be completed')

        emg_obj.electrode_formatter()  # adds spatial context and additional filtering
        
        if emg_obj.check_emg:
            emg_obj.manual_rejection()

        #################### BATCHING #######################################
        if emg_obj.ref_exist:
            print('Target used for batching')
            emg_obj.batch_w_target()
        else:
            emg_obj.batch_wo_target()

        ################### CONVOLUTIVE SPHERING #############################
        emg_obj.signal_dict['diff_data'] = []
        tracker = 0
        nwins = int(len(emg_obj.plateau_coords) / 2)
        for g in range(int(emg_obj.signal_dict['nelectrodes'])):
            extension_factor = int(np.round(emg_obj.ext_factor / np.shape(emg_obj.signal_dict['batched_data'][tracker])[0]))
            
            # Arrays for extended EMG data PRIOR to removal of edges
            emg_obj.signal_dict['extend_obvs_old'] = np.zeros([
                nwins, 
                np.shape(emg_obj.signal_dict['batched_data'][tracker])[0] * extension_factor, 
                np.shape(emg_obj.signal_dict['batched_data'][tracker])[1] + extension_factor - 1 - emg_obj.differential_mode
            ])
            emg_obj.decomp_dict['whitened_obvs_old'] = emg_obj.signal_dict['extend_obvs_old'].copy()
            
            # Arrays for square and inverse of extended EMG data PRIOR to removal of edges
            emg_obj.signal_dict['sq_extend_obvs'] = np.zeros([
                nwins,
                np.shape(emg_obj.signal_dict['batched_data'][tracker])[0] * extension_factor,
                np.shape(emg_obj.signal_dict['batched_data'][tracker])[0] * extension_factor
            ])
            emg_obj.signal_dict['inv_extend_obvs'] = emg_obj.signal_dict['sq_extend_obvs'].copy()
            
            # Dewhitening and whitening matrices
            emg_obj.decomp_dict['dewhiten_mat'] = emg_obj.signal_dict['sq_extend_obvs'].copy()
            emg_obj.decomp_dict['whiten_mat'] = emg_obj.signal_dict['sq_extend_obvs'].copy()
            
            # Arrays for extended EMG data AFTER removal of edges
            fsamp = emg_obj.signal_dict['fsamp']
            edges = int(np.round(fsamp * emg_obj.edges2remove))
            emg_obj.signal_dict['extend_obvs'] = emg_obj.signal_dict['extend_obvs_old'][:, :, edges - 1:-edges].copy()
            emg_obj.decomp_dict['whitened_obvs'] = emg_obj.signal_dict['extend_obvs'].copy()

            for interval in range(nwins): 
                current_shape = np.shape(emg_obj.decomp_dict['whitened_obvs'][interval])[0]
                emg_obj.decomp_dict['B_sep_mat'] = np.zeros([current_shape, emg_obj.its])
                emg_obj.decomp_dict['w_sep_vect'] = np.zeros([current_shape, 1])
                emg_obj.decomp_dict['MU_filters'] = np.zeros([nwins, current_shape, emg_obj.its])
                emg_obj.decomp_dict['SILs'] = np.zeros([nwins, emg_obj.its])
                emg_obj.decomp_dict['CoVs'] = np.zeros([nwins, emg_obj.its])
                emg_obj.decomp_dict['tracker'] =  np.zeros([1, emg_obj.its])
                emg_obj.decomp_dict['masked_mu_filters'] = []   # reset list for each interval

                emg_obj.convul_sphering(g, interval, tracker)
                emg_obj.fast_ICA_and_CKC(g, interval, tracker)
                tracker += 1

            ##################### POSTPROCESSING #################################
            emg_obj.post_process_EMG(g)

            ####################### SAVING DECOMPOSITION OUTPUT ########################
            decomposition_dict = {
                'chan_name': emg_obj.signal_dict['electrodes'][g],
                'muscle_name': emg_obj.signal_dict['muscles'][g],
                'coordinates': [emg_obj.coordinates[g]],
                'ied': emg_obj.ied[g],
                'emg_mask': [emg_obj.rejected_channels[g]],
                'mu_filters': [emg_obj.decomp_dict['masked_mu_filters']],
                'inv_extend_obvs': [emg_obj.signal_dict['inv_extend_obvs']],
                'pulse_trains': [emg_obj.mu_dict['pulse_trains'][g]],
                'discharge_times': [emg_obj.mu_dict['discharge_times'][g]],
                'clusters': 1 
            }
            all_dicts.append(decomposition_dict)
        
        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Remove the .otb+ extension from the file name
        file_name = file_name[:-5]
        with open(os.path.join(output_dir, file_name + '.pkl'), 'wb') as file:
            pickle.dump(all_dicts, file)
            
        if emg_obj.dup_bgrids and sum(emg_obj.mus_in_array) > 0:    
            emg_obj.post_process_across_arrays()
    
        print('Completed processing of the recorded EMG signal')
        print('Reformatting file for saving...')
    
        # Save processing parameters to a pickle file in the output directory
        parameters_dict = {
            'file_path': all_files[0],
            'n_its': emg_obj.its,
            'ref_exist': emg_obj.ref_exist,
            'fsamp': emg_obj.signal_dict['fsamp'],
            'target_thres': emg_obj.target_thres,
            'nwins': nwins,
            'check_EMG': emg_obj.check_emg,
            'drawing_mode': emg_obj.drawing_mode,
            'differential_mode': emg_obj.differential_mode,
            'peel_off': emg_obj.peel_off,
            'refine_MU': emg_obj.refine_mu,
            'sil_thr': emg_obj.sil_thr,
            'ext_factor': emg_obj.ext_factor,
            'edges': emg_obj.edges2remove,
            'dup_thr': emg_obj.dup_thr,
            'cov_filter': emg_obj.cov_filter,
            'cov_thr': emg_obj.cov_thr,
            'original_data': emg_obj.signal_dict['data'],
            'path': emg_obj.signal_dict['path'],
            'target': emg_obj.signal_dict['target']
        }

        with open(os.path.join(output_dir, file_name + '_params.pkl'), 'wb') as file:
            pickle.dump(parameters_dict, file)
    
        print('Decomposed data saved.')

