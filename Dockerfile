FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1
ENV HOME=/app
ENV QT_X11_NO_MITSHM=1
ENV QT_QPA_PLATFORM=xcb
ENV XDG_RUNTIME_DIR=/tmp
ENV MPLBACKEND=Qt5Agg
ENV LIBGL_ALWAYS_INDIRECT=1
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies (no Python libs here)
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-recommended \
        python3-pyqt5 \
        tk-dev \
        xorg \
        x11-utils \
        libgl1 \
        libdbus-1-3 \
        xvfb \
        dbus-x11 \
        ca-certificates \
        fonts-liberation \
        tini \
        supervisor \
        x11vnc \
        xfce4 \
        xfce4-terminal \
        openbox \
        net-tools \
        netcat-openbsd \
        tk-dev \
        git \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

        # libqt5gui5 \
        # libqt5widgets5 \
        # libqt5dbus5 \
        # libqt5network5 \
        # libqt5svg5-dev \

# Install noVNC and websockify
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /usr/share/novnc \
    && git clone --depth 1 https://github.com/novnc/websockify /usr/share/novnc/utils/websockify \
    && chmod +x /usr/share/novnc/utils/websockify/run \
    && ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Upgrade pip + install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

WORKDIR /app/src

# # Setup Fluxbox configuration for proper window decorations
# RUN mkdir -p /root/.fluxbox && \
#     echo "session.screen0.toolbar.visible: true" > /root/.fluxbox/init && \
#     echo "session.screen0.toolbar.placement: TopCenter" >> /root/.fluxbox/init && \
#     echo "session.screen0.workspaces: 1" >> /root/.fluxbox/init && \
#     echo "session.screen0.focusModel: ClickToFocus" >> /root/.fluxbox/init && \
#     echo "session.screen0.windowPlacement: RowSmartPlacement" >> /root/.fluxbox/init && \
#     echo "session.screen0.decorateTransient: true" >> /root/.fluxbox/init && \
#     echo "session.ignoreBorder: false" >> /root/.fluxbox/init && \
#     echo "session.screen0.defaultDeco: NORMAL" >> /root/.fluxbox/init && \
#     echo "session.screen0.titlebar.left: Stick" >> /root/.fluxbox/init && \
#     echo "session.screen0.titlebar.right: Minimize Maximize Close" >> /root/.fluxbox/init && \
#     echo "session.styleFile: /usr/share/fluxbox/styles/Emerge" >> /root/.fluxbox/init && \
#     mkdir -p /usr/share/fluxbox/nls/C.UTF-8 && \
#     touch /usr/share/fluxbox/nls/C.UTF-8/fluxbox.cat

# Fix icon paths - create symbolic link from /app/public to /app/src/public
RUN ln -sf /app/src/public /app/public

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