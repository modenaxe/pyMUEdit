Project Link:
https://unsw-my.sharepoint.com/:b:/g/personal/z5457396_ad_unsw_edu_au/EZDXEj6-KdVHhTAYwLtUpXABa6Rdv-_usMerwVv2zG88Mg?e=d67qOJ


[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=18296375&assignment_repo_type=AssignmentRepo)

__Introduction__
OpenHDEMG is a python translation of MUedit. Just like the original, it decomposes electromyographic (EMG) signals recorded from
arrays of electrodes into individual motor unit pulse trains using fast independent
component analysis (fastICA), has customisable configurations, visualisation and manual editing features.


__Setup__
OpenHDEMG requires python 3. To check if you have python 3 installed, enter the following command in your terminal:
‘python3 --version’

Next, download all the files from https://github.com/unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery
Option 1:
Click the green code button, select the ‘download zip’ option and unzip the contents
Option 2:
1.	Install git
2.	Run the following in your terminal: ‘git clone https://github.com/unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery.git’

Several python packages needs to be installed before running the application
Step1: Create a python virtue environment: 
python -m venv venv
Step 2: activate the virtue environment (to exit the virtue environment type ‘deactivate’ once done):
source venv/bin/activate  
(or venv\Scripts\activate on Windows)
Step 3: install required packages
pip install -r requirements.txt


__Overview of the decomposition algorithm and the associated functions__
Some functions have been renamed or refactored where appropriate so may differ from the original 
1.	The monopolar EMG signals collected during the experimental session are imported in (open_otb.py previously openOTBplus.m).
2.	The configuration of the recording is updated to add the names of the arrays and the muscles (if necessary; Quattrodlg.py).
3.	The recording can be segmented such that you only keep the segments with contractions (segmentsession.py)
4.	The signals are displayed on the screen such that you can remove channels with artifacts or bad signal-to-noise ratio (if the option is selected), and reformatted (electrode_formatter.py).
5.	The signals are filtered with i) an adaptive notch filter that remove the frequencies with abnormal peaks (notch_filter.py) and ii) a band pass filter (20-500 Hz for surface EMG and 100-4400 Hz for intramuscular EMG) (bandpass_filter.py).
6.	The EMG signals are extended by adding delayed versions of each channel (extend_emg.py).
7.	The EMG signals are then demeaned and spatially whitened (whiten_emg.py) to make them uncorrelated and of equal power.
8.	A fixed-point algorithm is applied to identify the motor unit pulse trains (fixed_point_alg.py). In this algorithm, a contrast function is iteratively applied to estimate a separation vector that maximised the level of sparseness of the motor unit pulse train.
9.	At this stage, the motor unit pulse train contained high peaks (i.e., the spikes from the identified motor unit) and low peaks (i.e. spikes from other motor units and noise). High peaks are separated from low peaks and noise using peak detection and K-mean classification with two classes: 'spikes' and 'noise' (get_spikes.py). The peaks from the class with the highest centroid are considered as spikes of the identified motor unit.
10.	A second algorithm refines the estimation of the discharge times by iteratively recalculating the separation vector and repeating the steps with peak detection and K-mean classification until the coefficient of variation of the inter-spike intervals is minimised (min_cov_isi.py)
11.	The accuracy of each estimated pulse train is assessed by computing the silhouette (SIL) value between the two classes of spikes identified with K-mean classification (get_silhouette.py). When the SIL exceeds a predetermined threshold, the motor unit is saved, and optionally peeled-off (peel_off.py) from the signal to run the next iteration on the residual of the EMG signals.


Structure of output?
Format of EMG signals to import
Similar to the original MUedit, you can import ‘.otb+’ files recorded with the software OT BioLab+ (OTBioelettronica. For recording from OT BioLab+, go to Acquisition, Setup, and configure electrodes type)
(e.g., ‘GR08MM1305’) and the muscles (e.g., ‘Tibialis Anterior’). The sampling frequency
should be set at a minimum of 2,048 Hz. MUedit will automatically import the grid and
muscle names, the force, and the target together with the EMG signals from the ‘.otb+’ file.
However, it is worth noting that the decomposition will only work with signals recorded with arrays of 32 or more electrodes.
For recording from RHX Data Acquisition, click on the ‘Select File Format’ button, and select the ‘One File Per Channel’ Format. It will generate a subdirectory with one file per channel with raw data (.dat), a file ‘time.dat’ with time stamps, and a file ‘info.rhd’ with all the information about the settings of the recording. You will import the file ‘info.rhd’ in MUedit to load the data. It is worth noting that the decomposition will only work with the signals recorded with arrays with a minimum of 16 intramuscular electrodes or 32 surface electrodes.
When importing a ‘.mat’ file, create a structure called signal (Figure 4) and add the following
variables:
• signal.data is a matrix of a size nb channels × time where EMG signals from all the grids are vertically concatenated. For example, EMG signals recorded from two grids of 64 electrodes over 10 seconds at a sampling frequency of 2,048 Hz would generate a matrix signal.data of a size 128 × 20480.
• signal.fsamp is the sampling frequency.
• signal.nChan is the number of recorded channels.
• signal.ngrid is the number of grids/arrays used to record EMG signals.
• signal.gridname is an array of cells containing the names of the grids as strings. For
example, EMG signals recorded with 2 grids of 64 electrodes, 13 × 5, interelectrode
distance 8mm from OT Bioelettronica would generate an array of two cells, with
‘GR08MM1305’ in each cell. If you used different grids or your own system, you must
create a name of grids here, and add the configuration of the grid in the function
formatsignalHDEMG.m (see below)
• signal.muscle is an array of cells containing the names of the muscles as strings. For
example, EMG signals recorded with 2 grids from the tibialis anterior and the soleus
would generate an array of two cells, with ‘Tibialis Anterior’ and ‘Soleus’ in each cell.
Optional:
• signal.target is a vector of a size 1 × time containing the force/torque target displayed
to the participant.
• signal.path is a vector of a size 1 × time containing the force/torque produced by the
participant.

If you use another system, or a custom-made grid/array of electrodes, you must also add its
configuration in the file electrode_formatter.py. For this, you will need to add in the following to the *electrode_formatter(emg_obj: “offline_EMG”) -> None:* function:
# Replace the electrode name with your electrode name
elif electrode_names[i] == "electrode name":
            print(f"Configuring {electrode_names[i]} (non-mapped EMG)")
            # replace the matrix below with your matrix
     ElChannelMap.append(
                [
                    [0, 0, 1, 2, 3],
                    [15, 7, 6, 5, 4],
                    [14, 13, 12, 11, 10],
                    [18, 17, 16, 8, 9],
                    [19, 20, 21, 22, 23],
                    [27, 28, 29, 30, 31],
                    [24, 25, 26, 32, 33],
                    [34, 35, 36, 37, 38],
                    [44, 45, 46, 47, 39],
                    [43, 42, 41, 40, 38],
                    [53, 52, 51, 50, 49],
                    [54, 55, 63, 62, 61],
                    [56, 57, 58, 59, 60],
                ]
            )

         # replace 65 below with the number of electrodes in your matrix
            rejected_channels.append(np.zeros([65]))
         # replace 8 below with the interelectrode distance, eg 8 for 8mm
            IED.append(8)
            ElChannelMap[i] = np.squeeze(np.array(ElChannelMap[i]))
            chans_per_electrode.append((np.shape(ElChannelMap[i])[0] * np.shape(ElChannelMap[i])[1]) - 1)
            emg_obj.emgopt.append("surface")
• ElChannelMap is a matrix or a vector with the position of each channel within the
grid/array.
• rejected_channels is a vector of zeros of a size 1 × number of electrodes in the
grid/array.
• IED is the interelectrode distance, e.g., 4 for 4mm.
• emgt_obj.emgopt is the type of signals. “surface” being EMG signals recorded with surface electrodes, “intra” being EMG signals recorded with intramuscular electrodes.

Of note, the current version of MUedit includes the following grid names sold by
OTBioelettronica: ‘GR04MM1305’, ‘GR08MM1305’, ‘GR10MM0808’, ‘GR10MM0804’
‘HD04MM1305’, ‘HD08MM1305’, ‘HD10MM0808’, ‘HD10MM0804’. It also includes the
following Myomatrix distributed by the Center for Advanced Motor BioEngineering and
Research (CAMBER) from Emory University. See Myomatrix arrays for high-definition muscle recording by Chung et al., published in Elife in 2023.


__Segment the session__
If you have recorded multiple contractions in the same file, you can either decide to select these segments and concatenate them, or to split them in different ‘mat’ files. For this, click
on the ‘Segment Session’ button.
First, select the auxiliary channel you want to display to segment the data. Then, set a
threshold to automatically segment the session or set a number of windows to manually
select the regions of interest. Two lines of the same colour appear to delineate the borders
of each window (Figure 8). If you click on the ‘Concatenate’ button, the selected windows are
concatenated while the data between windows are deleted. If you click on the ‘Split’ button,
each selected window is saved in a separated ‘mat’ file, and the file with the first segment is
automatically loaded for the decomposition. At the end, click on the ‘OK’ button.


__Parameters of the decomposition__
You can adjust a few options and parameters to optimise the performance of the algorithm.

• Reference: if you used the trapezoidal feedback from OT Biolab+ or imported your
target and force signals in the structure signal as signal.target and signal.path (see
section ‘Format of EMG signals to import’), you can select ‘Target’. The algorithm will
automatically segment the EMG signals to decompose the section(s) for which the actual force is above a threshold that you can freely chose (“Threshold target” in the parameters for decomposition). For example, if you have a plateau set at 10% of the maximal force, and you want to automatically decompose the EMG signals above 9% of the maximal force, set the value of Threshold target to 0.9 as 90% of the level of the target. Alternatively, if you want to manually select the sections of the signals to decompose, select any other auxiliary signal recorded during your session or ‘EMG amplitude’. At the beginning of the decomposition, you will be asked to select a region interest over a plot displaying auxiliary signal or the rectified EMG signal of half the channels and its average value.
• Check EMG: if you want to visually check the EMG signals and manually remove channels with low signal-to-noise ratio and/or artifacts, select ‘Yes’. If you want to automatically decompose all the channels, select ‘No’.
• Contrast function: you can select the contrast function used in the fixed-point algorithm that optimise separation vectors for each motor unit. You have three choices: ‘logcosh’, ‘skew’, and ‘kurtosis’.
• Initialisation: you can choose how to initialise the separation vectors in the fixed-point
algorithm. If you select ‘EMG max’, the separation vectors will be initialised as the EMG
values at the time instance where the sum of the squared EMG values over all the channels is maximal. If you select ‘Random’, the separation vectors will be initialised with random values.
• CoV filter: If you want to only keep motor unit pulse trains with stable and constant
discharge times, you can select ‘Yes’ and add a threshold to keep motor units which
exhibit a coefficient of variation of their inter-spike intervals below the fixed COV
threshold. If not, select ‘No’.
• Peeloff: If you want to remove the trains of action potentials of reliable identified motor units from the EMG signals and run the following iteration on the residual EMG, Select ‘Yes’. If not, select ‘No’. Reliable identified motor units have pulse trains above the silhouette threshold.
• Refine MUs: you can choose to automatically “clean” the identified motor unit pulse
trains. If you select ‘Yes’, the algorithm iteratively deletes discharge times such that
discharge rates above a threshold (mean + 3 standard deviations) are removed. This loop stops once the coefficient of variation of the inter-spike intervals is below 0.3. After this, the separation vector is updated based on the new discharge times and applied over the entire signal. The algorithm finally iteratively deletes discharge times to remove
discharge rates above the threshold for a second time.
• Number of iterations: Number of iterations performed by the decomposition algorithm
per grid and window (see below).
• Number of windows: Number of windows for which the signal is decomposed. If you
selected ‘Force’ as reference, the number of windows corresponds to the number of
segments above the threshold. If you selected ‘EMG amplitude as reference, this is the
number of regions of interest that you want to select/analyse.
• Threshold target: Threshold to automatically segment the target of force displayed to
the participant. This value is only used if you selected ‘Force’ as reference.
• Nb of extended channels: Number of channels after signal extension.
• Duplicate threshold: Percentage of common discharge times for two motor units to be
considered as duplicates. 0.3 means 30% of the total number of discharge times from
the motor unit with the highest number of discharge times.
• SIL threshold: Only motor unit pulses trains with a silhouette value above this threshold will be retained.
• COV threshold: If you selected ‘Yes’ to COV filter, only motor unit pulses trains with a
coefficient of variation of their inter-spike intervals below this threshold will be retained.


__EMG decomposition__
After clicking on ‘Start’, a few manual steps may be completed to visually check EMG signals or select regions of interests for the decomposition (see above).
If you selected ‘Yes’ to the option “Check EMG”, columns of EMG signals will successively appear on the screen. Enter the number of the rows to be removed (if multiple rows, use space in between) and hit ‘Ok’. If you want to keep all the rows, hit ‘Ok’. This step ends once all the columns from all the grids have been checked.
If you selected ‘EMG amplitude’ or another auxiliary channel as reference, you must select as many regions of interest as the number of windows set in the EMG decomposition panel. For this, drag and drop the rectangle box over the segment of the displayed data on the upper plot.

After these steps, the EMG decomposition starts. The app displays on the upper plot the segment selected with the reference. It also displays the pulse train and the identified discharge times on the bottom plots. Information about the number of the grid, the number of the iteration, the silhouette value, and the coefficient of variation of the inter-spike intervals is displayed on the top of the app and is refreshing at each iteration.
At the end of the decomposition, a ‘.mat’ file is automatically saved with a structure
“parameters” which contains all the parameters of the decomposition and a structure “signal” which contains all the data. In addition of the initial variables gathered in “signal”, two variables with the output of the decomposition are added:
• signal.Pulsetrain is an array of cells containing the motor unit pulse trains for each
grid/array of electrodes. The size of each cell is nb motor units × time.
• signal.Dischargetimes is a set of cells of a size nb grids × nb motor units containing the discharge times of each identified motor unit.
