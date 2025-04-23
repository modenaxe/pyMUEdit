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

Several python packages need to be installed before running the application
Step1: Create a python virtue environment: 
python -m venv venv
Step 2: activate the virtue environment (to exit the virtue environment type ‘deactivate’ once done):
source venv/bin/activate  
(or venv\Scripts\activate on Windows)
Step 3: install required packages
pip install -r requirements.txt

Lastly, go to the src folder and run HDEMGDashboard.py. This can be done with the command:
python3 main.py



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



__Format of EMG signals to import__
Similar to the original MUedit, you can import ‘.otb+’ files recorded with the software OT BioLab+ (OTBioelettronica. For recording from OT BioLab+, go to Acquisition, Setup, and configure electrodes type)
(e.g., ‘GR08MM1305’) and the muscles (e.g., ‘Tibialis Anterior’). The sampling frequency
should be set at a minimum of 2,048 Hz. MUedit will automatically import the grid and
muscle names, the force, and the target together with the EMG signals from the ‘.otb+’ file.
However, it is worth noting that the decomposition will only work with signals recorded with arrays of 32 or more electrodes.
For recording from RHX Data Acquisition, click on the ‘Select File Format’ button, and select the ‘One File Per Channel’ Format. It will generate a subdirectory with one file per channel with raw data (.dat), a file ‘time.dat’ with time stamps, and a file ‘info.rhd’ with all the information about the settings of the recording. You will import the file ‘info.rhd’ in MUedit to load the data. It is worth noting that the decomposition will only work with the signals recorded with arrays with a minimum of 16 intramuscular electrodes or 32 surface electrodes.
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
If you have recorded multiple contractions in the same file, you can either decide to select these segments and concatenate them, or to split them in different ‘mat’ files. For this, click on the ‘Segment Session’ button.
First, select the auxiliary channel you want to display to segment the data. Then, set a
threshold to automatically segment the session or set the number of windows to manually select the regions of interest. Two lines of the same colour will appear to delineate the borders of each window. If you click on the ‘Concatenate’ button, the selected windows are concatenated while the data between windows are deleted. If you click on the ‘Split’ button, each selected window is saved in a separated ‘mat’ file, and the file with the first segment is automatically loaded for the decomposition. 



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



__Manual editing of motor unit pulse trains__
It is recommended to visually check and manually edit the motor unit pulse trains and the identified discharge times. The manual editing aims to correct errors from the peak
separation between the two classes (spikes and noise) using K-mean classification.
Specifically, the following steps are performed:
• identifying and removing the spikes of lower quality.
• updating the motor unit separation vector and re-applying it over a portion of the
signal.
• adding the new spikes recognized as motor unit discharge times.
It is worth noting that the manual identification of potential missed spikes and false positives is never arbitrarily accepted. Indeed, it is always followed by the update and the reapplication of the separation vector of the motor unit, which reveals whether the manual editing should be accepted or rejected based on the change in silhouette value. For additional information, you can follow the guidelines reported in Hug et al. (2021) and Del Vecchio et al., (2020).

To start with manual editing, go to the manual editing tab on the left, select the desired output file. To navigate through the recording, you can use the four buttons on the bottom of the app, or drag and scroll with the mouse.
Below are the functions of the buttons dedicated to manual editing. Keyboard shortcuts have been added between brackets [] for a selection of functions:
• Flag selected MU(s) for deletion: if the motor unit pulse train is not reliable and need to be deleted, click on this button.
• Remove outliers [r]: identify the instantaneous discharge rates above a threshold (mean discharge rate + 3 standard deviation) and remove the discharge times causing this discharge rate with the lowest height.
• Undo: cancel the last action of manual editing.
• Add spikes [a]: drag and drop a region of interest around the spikes you want to select.
You can select multiple spikes at the same time.
• Delete spikes [d]: drag and drop a region of interest around the spikes you want to
remove. You can remove multiple spikes at the same time.
• Delete DR: drag and drop a region of interest around the instantaneous discharge rates you want to remove. It will remove the discharge time causing this discharge rate with the lowest height. You can remove multiple instantaneous discharge rates at the same time.
• Update filter [space]: update the motor unit separation vector based on the identified
discharge times within the window displayed on the screen and reapply it over the
extended and whitened EMG signals of the same window. It is worth noting that the
identification of the discharge times will be updated using K-mean classification.
• Extend filter [e]: update the motor unit separation vector based on moving windows of
the same size of the displayed motor unit pulse train moving forward and backward until reaching the boundaries of the signal. Each window has a 50% overlap with the previous window. The identified discharge times within each window is used to dynamically update the motor unit separation vector and reapply it over the extended EMG signals of the same window. It is worth noting that the identification of the discharge times will be updated using K-mean classification.
• Lock spikes [s]: If you want to re-evaluate the separation vectors without an automatic
selection of the discharge times, click on this button. It will lock the identified discharge
times such that they won’t be removed in the re-evaluation process. You will need to click on this button every time you want to lock the discharge times and re-evaluate. Of note, using this option leads to a more subjective manual editing.

Typically, manual editing starts by identifying missed spikes or potential false positives by looking at the variation in discharge rate on the upper plot. You can use the button ‘Add spikes’ to drag and drop a region of interest around the missed spikes and repeat this for all the spikes. After this, you can click on ‘Update MU filter’
to update the motor unit separation vector and apply it over the EMG signals within the
window. The colour of the scatters will depend on the changes in silhouette value. Red
means that the silhouette value changes by more than -0.4, orange by between -0.4 and -0.2, blue by between 0 and +0.2, and green above 0.2. Generally, manual editing should improve the silhouette value (green scatters).

Successive steps of manual editing. 
1) identification of the missed spikes (discharge rates drop). 
2) Click on ‘Add spikes’ and drag and drop a region of interest around the spikes to select. 
3) Motor unit pulse train and discharge rates with all the spikes selected. 4) Update the motor unit separation vector and apply it over the
entire EMG signals. The green scatters mean that the silhouette value improved with manual editing.

To speed up manual editing, you can batch process some processing steps, such as
removing the discharge rates considered as outliers, or updating all the motor unit
separation vectors and reapplying them all at once. For this, click on ‘Remove all the outliers’ or ‘Update all MU filters’ on the left panel and this will be applied on all motor units.

At the end of the editing, it is recommended to check for duplicates between motor units
within the grids (if you used one grid per muscle) and between grids (if you used multiple
grids on the same muscles). We consider two or more motor units as duplicates when they
have at a significant percentage of their identified discharge times in common. This
percentage is set as ‘Duplicate threshold’ in the panel of the decomposition tab, with 0.3
being 30% of discharge times in common. The motor unit pulse trains are first aligned using
a cross-correlation function to account for a potential delay due to the conduction time along
the fibres. Then, two discharge times are considered as common when they occurred within
a time window of 0.5 ms. When a duplicate is found, the motor unit kept in the analysis is the one with the lowest coefficient of variation of inter-spike intervals. The buttons for removing the duplicates are in the left panel.

You can visualise the all the motor units with two types of plots. In the visualisation tab of MU editing there are two buttons, the first one is labelled ‘plot MU spike trains’ above a second labelled ‘Plot MU firing rates’.  The first button will display the raster plots of each grid with ticks for each discharge time. The second one will display the motor unit discharge rates smoothed with a Hanning window of one second.

At the end of the session, click on ‘Save’ to save a ‘.mat’ file with the edited motor unit pulse
trains and discharge times. It will keep the same file name with the addition of ‘_edited’ at
the end. In the file, a new structure named edition will appear with the same variables as in
signal, but with the edited pulse trains (edition.Pulsetrain) and discharge times
(edition.Dischargetimes). To further process the same file, you can load this edited file. You
will automatically resume the editing where you stopped it.
