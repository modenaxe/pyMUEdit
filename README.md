Project Link:
https://unsw-my.sharepoint.com/:b:/g/personal/z5457396_ad_unsw_edu_au/EZDXEj6-KdVHhTAYwLtUpXABa6Rdv-_usMerwVv2zG88Mg?e=d67qOJ


[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=18296375&assignment_repo_type=AssignmentRepo)



# OpenHDEMG — User Manual (v1.0)

---

## 1  Introduction  
OpenHDEMG is a Python rewrite of the MATLAB application **MUedit**.  
Like the original, it separates high-density EMG (HDEMG) signals into individual motor-unit pulse trains using **Fast Independent Component Analysis (FastICA)**. In addition to automatic decomposition, the tool offers per-session configuration, channel visualisation and an interactive manual-editing workspace.

---

## 2  Quick-start Installation  

| &nbsp; | Command / Action |
|-------|------------------|
| **Prerequisites** | • Python ≥ 3.9  • git (optional)  • macOS / Linux / Windows 10+ |
| Verify Python | `python3 --version` |
| **Download** | **A** ZIP — GitHub → **Code → Download ZIP** → unzip<br>**B** git —<br>`git clone https://github.com/unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery.git` |
| Enter repo | `cd capstone-project-2025-t1-25t1-3900-w16a-celery` |
| Virtual env | `python3 -m venv venv`<br>`source venv/bin/activate` (mac/Linux)<br>`.\venv\Scripts\Activate` (Win) |
| Install reqs | `pip install -r requirements.txt` |
| Launch GUI | `cd src`<br>`python3 main.py` |

The dashboard window should appear within a few seconds.

---

## 3  Workflow Overview  

1. **Import** `.otb+ / .mat / .csv` → `open_otb.py`.  
2. **Annotate** grids & muscles → `Quattrodlg.py`.  
3. **Segment** contractions → `segmentsession.py`.  
4. **QC channels** (optional) → `electrode_formatter.py`.  
5. **Filter** → `notch_filter.py` (adaptive) + `bandpass_filter.py` (20-500 Hz surface, 100-4400 Hz intramuscular).  
6. **Extend & whiten** → `extend_emg.py`, `whiten_emg.py`.  
7. **FastICA** → `fixed_point_alg.py`.  
8. **Spike classification** → `get_spikes.py` (K-means).  
9. **Refinement** → `min_cov_isi.py` (minimise ISI-CoV).  
10. **Quality metric** → `get_silhouette.py`; accepted units can be **peeled-off** (`peel_off.py`) and the loop restarts on the residual.

---

## 4  Supported Input Formats  

* `.otb+` (OT BioLab +)  
* `.rhd` (Intan RHX “one file per channel”)  
* `.mat` / `.csv`

> **Minimum array sizes** — at least **32 surface** *or* **16 intramuscular** electrodes are required.

### 4.1 Required Signal Fields  

| Field | Description |
|-------|-------------|
| `signal.data` | `nChannels × nSamples` matrix (all grids concatenated) |
| `signal.fsamp` | Sampling frequency (Hz) |
| `signal.nChan` | Number of recorded channels |
| `signal.ngrid` | Number of grids / arrays |
| `signal.gridname` | List of grid IDs (e.g. `"GR08MM1305"`) |
| `signal.muscle` | List of muscle names |

**Optional but recommended**

| Field | Purpose |
|-------|---------|
| `signal.target` | Force / torque **target** trace |
| `signal.path` | Actual force / torque **path** trace |

### 4.2 Built-in Grid IDs  
`GR04MM1305`, `GR08MM1305`, `GR10MM0808`, `GR10MM0804`, `HD04MM1305`, `HD08MM1305`, `HD10MM0808`, `HD10MM0804`, plus **Myomatrix** arrays (CAMBER / Emory).

### 4.3 Adding Custom Arrays  

```electrode_formatter.py
elif electrode_names[i] == "MY_GRID":
    ElChannelMap.append([
        [0, 1, 2, 3],
        [7, 6, 5, 4],
        [8, 9,10,11]
    ])
    rejected_channels.append(np.zeros([12]))  # electrodes
    IED.append(8)                             # inter-electrode distance mm
    emg_obj.emgopt.append("surface")          # or "intra"
```

---

## 5  Session Segmentation  

1. Click **Segment Session**.  
2. Choose an auxiliary channel or **EMG amplitude**.  
3. Enter a **threshold** *or* specify **number of windows** and drag-select them.  
4. Click **Concatenate** (merge) or **Split** (each window to its own `.mat`).

---

## 6  Decomposition Parameters  

| Setting | Purpose |
|---------|---------|
| **Reference** | Auto segmentation on `Target`, or manual on any trace. |
| **Check EMG** | “Yes” opens per-column QC to discard noisy channels. |
| **Contrast** | `logcosh`, `skew`, `kurtosis`. |
| **Initialisation** | `EMG max` (deterministic) or `Random`. |
| **CoV filter** | Keep units with ISI-CoV below threshold. |
| **Peel-off** | Subtract accepted unit before next iteration. |
| **Refine MUs** | Automatic outlier removal & filter update. |
| **Iterations** | FastICA iterations per grid & window. |
| **Windows** | Number of ROIs. |
| **Threshold target** | Fraction (0-1) of target force. |
| **Extended channels** | Size after time-delay embedding. |
| **Duplicate thr.** | Overlap % to tag duplicates (default 0.30). |
| **SIL / CoV thresholds** | Quality cut-offs. |

---

## 7  Running Decomposition  

1. Perform channel QC if **Check EMG = Yes**.  
2. Select ROIs if manual segmentation.  
3. Progress bar reports `Grid`, `Iteration`, `SIL`, `CoV`.  
4. Output `*_output_decomp.mat` contains  

| Variable | Content |
|----------|---------|
| `signal.Pulsetrain` | Cell (units × time) per grid |
| `signal.Dischargetimes` | 2-D cell `[grid, unit]` |

---

## 8  Manual Editing  

| Action | Key | Effect |
|--------|-----|--------|
| Flag unit(s) | — | Mark unreliable trains |
| Remove outliers | **r** | Delete spikes causing extreme ISI |
| Add spikes | **a** | Box-select missed spikes |
| Delete spikes | **d** | Box-select false positives |
| Update filter | **Space** | Re-estimate separation vector (current window) |
| Extend filter | **e** | Slide window (50 % overlap) across recording |
| Lock spikes | **s** | Freeze current spikes before re-evaluation |
| Undo / Redo | Ctrl-Z / Ctrl-Y | Unlimited stack |

*Marker colours* — green (+SIL), blue, orange, red (–SIL).

Batch buttons: **Remove all outliers**, **Update all MU filters**.  
**Save** → `*_edited.mat` containing an `edition` structure (edited pulse trains & times).

---

## 9  Duplicate Check & Visualisation  

*Duplicates* — spikes aligned within ±0.5 ms; overlap ≥ `Duplicate thr.`.  
Buttons: **Remove duplicates within grid** / **across grids**.

*Visualisation* tab  
* **Plot MU spike trains** — raster per grid  
* **Plot MU firing rates** — 1 s Hanning-smoothed rate

---

## 10  Algorithmic Detail (advanced users)  

> For those who wish to extend or audit the pipeline.

```
import  → grid/muscle  → segment  → channel QC
     ↓                   ↓
filter (notch + BP)  →  extend + whiten
     ↓
FastICA (fixed_point_alg)
     ↓
K-means spike/noise  ↻  refine (min_cov_isi)
     ↓
SIL assessment  →  accept & peel-off  →  repeat until done
```

*Built with:* Python 3 · NumPy · SciPy · scikit-learn · Matplotlib/PyQtGraph · PyQt5

---
```
*Prepared by **Team W16A-CELERY** — UNSW Capstone 2025.*
```
