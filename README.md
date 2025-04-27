# HDEMG Analysis Tool

A Python-based application for High-Density Electromyography (HDEMG) signal analysis with motor unit decomposition, visualization, and editing capabilities.

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
   git clone <repository-url>
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
   git clone <repository-url>
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

## Application Features

- Import and analyze HDEMG data
- Decompose EMG signals into motor units
- Edit motor units manually
- Visualize signal patterns
- Export analysis results
