FROM osrf/ros:humble-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install additional tools and visualization dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-tk \
    python3-matplotlib \
    ros-humble-diagnostic-updater \
    ros-humble-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

# Create ROS 2 workspace
WORKDIR /ros2_ws/src/machine_temperature_monitor

# Copy package source
COPY . .

WORKDIR /ros2_ws

# Build package
RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install --packages-select machine_temperature_monitor

# Source workspace on entry
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

ENTRYPOINT ["/bin/bash", "-c", "source /ros2_ws/install/setup.bash && exec \"$@\"", "--"]
CMD ["ros2", "launch", "machine_temperature_monitor", "machine_monitor.launch.py"]
