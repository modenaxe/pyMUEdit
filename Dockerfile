FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1
ENV HOME=/app
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    supervisor \
    xvfb \
    x11vnc \
    xfce4 \
    xfce4-terminal \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5dbus5 \
    libqt5network5 \
    libqt5svg5-dev \
    libgl1 \
    libdbus-1-3 \
    fonts-liberation \
    net-tools \
    netcat-openbsd \
    git \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
    python3-pyqt5 \
    python3-pyqt5.qtsvg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC and websockify
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /usr/share/novnc \
    && git clone --depth 1 https://github.com/novnc/websockify /usr/share/novnc/utils/websockify \
    && chmod +x /usr/share/novnc/utils/websockify/run \
    && ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure scripts are executable
RUN chmod +x /app/src/main.py

# Setup supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose VNC and noVNC ports
EXPOSE 5900 6080

# Use tini as entrypoint to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]