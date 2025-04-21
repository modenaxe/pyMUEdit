Project Link:
https://unsw-my.sharepoint.com/:b:/g/personal/z5457396_ad_unsw_edu_au/EZDXEj6-KdVHhTAYwLtUpXABa6Rdv-_usMerwVv2zG88Mg?e=d67qOJ


[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=18296375&assignment_repo_type=AssignmentRepo)

**USER MANUAL**
__Introduction__
MUedit.py is a copy of the original MUedit, translated directly from the matlab code. Just like the original, it decomposes electromyographic (EMG) signals recorded from
arrays of electrodes into individual motor unit pulse trains using fast independent
component analysis (fastICA), has customisable configurations, visualisation and manual editing features.

__Setup__ 
Software requirements.
MUedit.py requires python 3
Download all the files from https://github.com/unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery
Option 1:
Click the green 'code' button, select the ‘download zip’ option and unzip the contents
Option 2:
-	Install git
-	Run the following in your terminal: ‘git clone https://github.com/unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery.git’
Several python packages are required, before starting the application, run the following commands on your terminal
-	python -m venv venv
-	source venv/bin/activate  # or venv\Scripts\activate on Windows
-	pip install -r requirements.txt


__Overview of the decomposition algorithm and the associated functions__
Some functions have been renamed or refactored where appropriate 
1) The monopolar EMG signals collected during the experimental session are imported in
the software (open_otb.py previously openOTBplus.m, openIntan.m, openOEphys.m).
2) The configuration of the recording is updated to add the names of the arrays and the
muscles (if necessary; Quattrodlg.py, Intandlg.m, OEphysdlg.m).
3) The recording can be segmented such that you only keep the segments with contractions
(if necessary; segmentsession.py)
4) The signals are displayed on the screen such that you can remove channels with artifacts
or bad signal-to-noise ratio (if the option is selected), and reformatted
(formatsignalHDEMG.m).
5) The signals are filtered with i) an adaptive notch filter that remove the frequencies with
abnormal peaks (notch_filter.py) and ii) a band pass filter (20-500 Hz for surface EMG
and 100-4400 Hz for intramuscular EMG) (bandpass_filter.py).
6) The EMG signals are extended by adding delayed versions of each channel (extend_emg.py).
7) The EMG signals are then demeaned (demean.m) and spatially whitened (pcaesig.m;
whiten_emg.py) to make them uncorrelated and of equal power.
8) A fixed-point algorithm is applied to identify the motor unit pulse trains (fixed_point_alg.py).
In this algorithm, a contrast function is iteratively applied to estimate a separation vector
that maximised the level of sparseness of the motor unit pulse train.
9) At this stage, the motor unit pulse train contained high peaks (i.e., the spikes from the
identified motor unit) and low peaks (i.e. spikes from other motor units and noise). High
peaks are separated from low peaks and noise using peak detection and K-mean
classification with two classes: 'spikes' and 'noise' (get_spikes.py). The peaks from the class
with the highest centroid are considered as spikes of the identified motor unit.
10) A second algorithm refines the estimation of the discharge times by iteratively

recalculating the separation vector and repeating the steps with peak detection and K-
mean classification until the coefficient of variation of the inter-spike intervals is

minimised (min_cov_isi.py)
11) The accuracy of each estimated pulse train is assessed by computing the silhouette (SIL)
value between the two classes of spikes identified with K-mean classification (get_silhouette.py).
When the SIL exceeds a predetermined threshold, the motor unit is saved, and optionally
peeled-off (peel_off.py) from the signal to run the next iteration on the residual of the EMG
signals.


Structure of output?
__Format of EMG signals to import__
Similar to the original MUedit, you can import ‘.otb+’ files recorded with the software OT BioLab+ (OT
Bioelettronica), ii) ‘info.rhd’ files recorded with RHX Data Acquisition (Intan Tech), iii)
‘structure.oebin’ files recorded with Open Ephys GUI (Open Ephys), and iv) ‘.mat’ files
formatted for MUedit.
For recording from OT BioLab+, go to Acquisition, Setup, and configure electrodes type
(e.g., ‘GR08MM1305’) and the muscles (e.g., ‘Tibialis Anterior’). The sampling frequency
should be set at a minimum of 2,048 Hz. MUedit will automatically import the grid and
muscle names, the force, and the target together with the EMG signals from the ‘.otb+’ file.
However, it is worth noting that the decomposition will only work with the signals recorded
with arrays of 32 or more electrodes.
For recording from RHX Data Acquisition, click on the ‘Select File Format’ button, and select
the ‘One File Per Channel’ Format. It will generate a subdirectory with one file per channel
with raw data (.dat), a file ‘time.dat’ with time stamps, and a file ‘info.rhd’ with all the
information about the settings of the recording. You will import the file ‘info.rhd’ in MUedit
to load the data. It is worth noting that the decomposition will only work with the signals
recorded with arrays with a minimum of 16 intramuscular electrodes or 32 surface
electrodes.
For recording from Open Ephys GUI, add a record node to the signal chain. Select the binary
format. It will generate a subdirectory with a file ‘structure.oebin’ with all the information
about the recording, a folder with continuous data (‘continuous.dat’), time stamps and
sample numbers, and a folder with events. You will import the file ‘structure.oebin’ in MUedit
to load the data. It is worth noting that the decomposition will only work with the signals
recorded with arrays with a minimum of 16 intramuscular electrodes or 32 surface
electrodes.
When importing a ‘.mat’ file, create a structure called signal (Figure 4) and add the following
variables:
• signal.data is a matrix of a size nb channels × time where EMG signals from all the grids
are vertically concatenated. For example, EMG signals recorded from two grids of 64
electrodes over 10 seconds at a sampling frequency of 2,048 Hz would generate a matrix
signal.data of a size 128 × 20480.

6

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

Figure 4. Matlab structure “signal” to import data in MUedit.

If you use another system, or a custom-made grid/array of electrodes, you must also add its
configuration in the function formatsignalHDEMG.m. For this, you will need to add in the
function if contains(gridname{i}, 'nameofthearray') a condition elseif with the
name of your array (Figure 5) and the following variables:
• ElChannelMap is a matrix or a vector with the position of each channel within the
grid/array.
• discardChannelsVec is a vector of zeros of a size 1 × number of electrodes in the
grid/array.
• IED is the interelectrode distance, e.g., 4 for 4mm.
• nbelectrodes is the total number of electrodes within the grid/array.
• emgtype is the type of signals. 1 being for EMG signals recorded with surface
electrodes, 2 for EMG signals recorded with intramuscular electrodes.

7

Figure 5. Code example for the array ‘MYOMRF-4x8’ in the function formatsignalHDEMG.m.

Of note, the current version of MUedit includes the following grid names sold by
OTBioelettronica: ‘GR04MM1305’, ‘GR08MM1305’, ‘GR10MM0808’, ‘GR10MM0804’
‘HD04MM1305’, ‘HD08MM1305’, ‘HD10MM0808’, ‘HD10MM0804’. It also includes the
following Myomatrix distributed by the Center for Advanced Motor BioEngineering and
Research (CAMBER) from Emory University. See Myomatrix arrays for high-definition muscle
recording by Chung et al., published in Elife in 2023.

After recording the EMG signals from OT Biolab+, RHX Data Acquisition, Open Ephys GUI,
or creating the ‘.mat’ file with the structure signal, go to MUedit, click on Select file, and open
either the ‘.otb+’ , ‘info.rhd’, ‘structure.oebin’, or the ‘.mat’ file’.

Figure 6. Panel of EMG decomposition.
