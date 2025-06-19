# HDEMG Analysis Tool 🛑

⚠️ This project is a complete work in progress and should not be used for research until the first official release ⚠️

A Python-based application for High-Density Electromyography (HDEMG) signal analysis with motor unit decomposition, visualization, and editing capabilities.

Original matlab code the application is based off:
https://github.com/simonavrillon/MUedit 
Drive containing data files used for testing:
https://drive.google.com/drive/folders/1nIpH1ksYWE-vQplEtilz843h2BuCuDmy

## Dockerized Application

This application has been dockerized to allow for easy deployment and use on any system with Docker installed, eliminating the need to install dependencies locally. The application runs entirely inside the container and is accessed through your web browser or a VNC client.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (optional but recommended)
- A web browser or VNC client

### Quick Start Guide

#### The Easy Way (Using the Scripts)

1. Clone this repository:

   ```bash
   git clone git@github.com:unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery.git
   cd capstone-project-2025-11-25t1-3900-w16a-celery
   ```

2. Run the application:

   - **Linux/macOS**: Make the script executable and run it
     ```bash
     chmod +x run-hdemg.sh
     ./run-hdemg.sh
     ```
   - **Windows**: Double-click on `run-hdemg.bat`

3. Access the application:
   - Open your web browser and navigate to: http://localhost:6080/vnc.html
   - Click the "Connect" button
   - You'll see the HDEMG Analysis Tool running in your browser

#### Manual Setup

1. Clone this repository:

   ```bash
   git clone git@github.com:unsw-cse-comp99-3900/capstone-project-2025-t1-25t1-3900-w16a-celery.git
   cd capstone-project-2025-11-25t1-3900-w16a-celery
   ```

2. Create a data directory:

   ```bash
   mkdir -p data
   ```

3. Build and start the Docker container:

   ```bash
   # With Docker Compose (recommended)
   docker-compose up -d

   # Or with Docker only
   docker build -t hdemg-analysis-tool .
   docker run -d --name hdemg-analysis-tool -p 5900:5900 -p 6080:6080 -v $(pwd)/data:/app/data hdemg-analysis-tool
   ```

4. Access the application:
   - **Web Browser**: Navigate to http://localhost:6080/vnc.html and click "Connect"
   - **VNC Client**: Connect to localhost:5900

### Accessing the Application

You have two options to access the application:

1. **Web Browser (Recommended)**:

   - Open http://localhost:6080/vnc.html in your web browser
   - Click the "Connect" button
   - No additional software needed

2. **VNC Client**:
   - Install any VNC client (like [RealVNC Viewer](https://www.realvnc.com/en/connect/download/viewer/))
   - Connect to `localhost:5900`
   - No password is required

### Persisting Data

The Docker setup mounts a `data` directory from your host machine to `/app/data` inside the container. Use this directory to store and access your HDEMG data files.

### Project Structure

```
capstone-project-2025-11-25t1-3900-w16a-celery/
├── data/                  # Data directory mounted into the container
├── docs/                  # Documentation
├── src/                   # Source code
│   ├── app/               # Main application modules
│   │   ├── DecompositionApp.py
│   │   ├── DownloadConfirmation.py
│   │   ├── ExportConfirm.py
│   │   ├── ExportResults.py
│   │   ├── HDEMGDashboard.py
│   │   ├── ImportDataWindow.py
│   │   └── MUeditManual.py
│   ├── core/              # Core functionality
│   ├── public/            # Static resources
│   ├── ui/                # UI components
│   ├── workers/           # Background worker threads
│   └── main.py            # Main entry point
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker container definition
├── requirements.txt       # Python dependencies
├── run-hdemg.bat          # Windows run script
├── run-hdemg.sh           # Linux/macOS run script
└── supervisord.conf       # Supervisor configuration
```

### Stopping the Application

- **With Docker Compose**:

  ```bash
  docker-compose down
  ```

- **With Docker only**:
  ```bash
  docker stop hdemg-analysis-tool
  docker rm hdemg-analysis-tool
  ```

### Application Features

- Import and analyze HDEMG data
- Decompose EMG signals into motor units
- Edit motor units manually
- Visualize signal patterns
- Export analysis results

---

### Supported Input Formats  

* `.otb+` (OT BioLab +)  
* `.rhd` (Intan RHX “one file per channel”)  
* `.mat` / `.csv`

> **Minimum array sizes** — at least **32 surface** *or* **16 intramuscular** electrodes are required.

### Session Segmentation  

1. Click **Segment Session**.  
2. Choose an auxiliary channel or **EMG amplitude**.  
3. Enter a **threshold** *or* specify **number of windows** and drag-select them.  
4. Click **Concatenate** (merge) or **Split** (each window to its own `.mat`).

---

### Decomposition Parameters  

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

### Running Decomposition  

1. Perform channel QC if **Check EMG = Yes**.  
2. Select ROIs if manual segmentation.  
3. Progress bar reports `Grid`, `Iteration`, `SIL`, `CoV`.  
4. Output `*_output_decomp.mat` contains  

| Variable | Content |
|----------|---------|
| `signal.Pulsetrain` | Cell (units × time) per grid |
| `signal.Dischargetimes` | 2-D cell `[grid, unit]` |

---

### Manual Editing  

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

### Duplicate Check & Visualisation  

*Duplicates* — spikes aligned within ±0.5 ms; overlap ≥ `Duplicate thr.`.  
Buttons: **Remove duplicates within grid** / **across grids**.

*Visualisation* tab  
* **Plot MU spike trains** — raster per grid  
* **Plot MU firing rates** — 1 s Hanning-smoothed rate

---

## Algorithmic Detail (advanced users)  

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

### Troubleshooting

If you encounter issues:

1. **Application doesn't appear in the browser**:

   - Make sure ports 5900 and 6080 aren't being used by other applications
   - Try running `docker logs hdemg-analysis-tool` to see if there are any error messages

2. **Application is slow**:

   - Increase the memory allocated to Docker in Docker Desktop settings
   - You can adjust screen resolution in the supervisord.conf file if needed

3. **Data files not visible in the application**:

   - Make sure you're placing your files in the `data` directory of your project
   - Check that the volume mount is working with `docker inspect hdemg-analysis-tool`

4. **Python module not found errors**:
   - If you encounter missing module errors, you may need to add them to requirements.txt
   - Rebuild the Docker image after updating: `docker-compose build` or `docker build -t hdemg-analysis-tool .`

```
*Prepared by **Team W16A-CELERY** — UNSW Capstone 2025.*
```
