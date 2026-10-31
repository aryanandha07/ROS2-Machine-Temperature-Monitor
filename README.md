# Machine Temperature Monitoring and Alarm System

## 1. Project Overview

This project implements a machine temperature monitoring and alarm system using ROS 2 Humble and Python.

The system monitors temperature readings, filters sensor data, detects overheating, and generates an alarm when the temperature reaches a predefined limit. It also detects sensor communication failures and provides a reset service.

A simulated temperature sensor is used to demonstrate the system without requiring physical hardware.

## 2. Objectives

- Monitor machine temperature using ROS 2.
- Filter temperature readings using an Exponential Moving Average (EMA).
- Detect overheating using configurable temperature thresholds.
- Implement hysteresis to prevent frequent alarm switching.
- Detect missing sensor data.
- Provide a service to reset the alarm safely.
- Validate system parameters to prevent invalid configurations.

## 3. Technologies Used

- Operating System: Ubuntu 22.04
- Middleware: ROS 2 Humble
- Programming Language: Python
- Communication: ROS 2 Topics and Services
- Development Environment: Visual Studio Code
- Simulation: Software-based temperature sensor

## 4. System Architecture

The system consists of two main nodes.

### Temperature Sensor Node

The sensor node simulates a machine temperature sensor and publishes temperature readings at 10 Hz.

Topic:
`/machine/temperature`

Message type:
`sensor_msgs/msg/Temperature`

### Temperature Monitor Node

The monitor node subscribes to temperature readings, filters incoming data, evaluates alarm conditions, and publishes the machine status.

It also provides a service to reset the alarm when the temperature is safe.

### Data Flow

Simulated Temperature Sensor  
↓  
`/machine/temperature`  
↓  
Temperature Monitor and EMA Filter  
↓  
Alarm Evaluation  
↓  
`/machine/alarm` and `/machine/status`

## 5. ROS 2 Communication Interfaces

| Interface | Name | Message/Service Type | Purpose |
|---|---|---|---|
| Topic | `/machine/temperature` | `sensor_msgs/msg/Temperature` | Publishes temperature readings |
| Topic | `/machine/alarm` | `std_msgs/msg/Bool` | Publishes alarm state |
| Topic | `/machine/status` | `std_msgs/msg/String` | Publishes machine status |
| Service | `/machine/reset` | `std_srvs/srv/Trigger` | Requests a safe alarm reset |

## 6. Temperature Monitoring Logic

### Exponential Moving Average

The system uses an Exponential Moving Average (EMA) to smooth temperature readings.

Formula:

Filtered Temperature = α × Current Temperature + (1 − α) × Previous Filtered Temperature

Where:

- α is the smoothing factor.
- A larger α responds more quickly to changes.
- A smaller α produces smoother readings.

The default smoothing factor is 0.2.

For deterministic threshold tests, α can be set to 1.0 so that the filtered temperature follows the latest reading directly.

### Alarm Thresholds

Default parameters:

| Parameter | Default Value | Description |
|---|---:|---|
| High temperature | 80°C | Activates the alarm |
| Low temperature | 75°C | Clears the alarm when the temperature falls below this limit |
| EMA factor | 0.2 | Controls filtering |
| Stale timeout | 1.0 second | Maximum time without a received reading before the data is considered stale |

### Hysteresis

Hysteresis prevents the alarm from switching repeatedly when the temperature fluctuates near the threshold.

- At or above 80°C: the alarm activates.
- Between 75°C and 80°C: the previous alarm state is maintained.
- Below 75°C: the alarm clears.

### Stale Sensor Detection

If no temperature reading is received for more than the configured timeout, the monitor reports the status as `STALE`.

When readings resume, the monitor evaluates the new readings and updates the status and alarm accordingly.

### Safe Alarm Reset

The `/machine/reset` service allows an alarm reset request.

The reset is rejected when the temperature is at or above 75°C. It is also rejected when sensor data is stale.

A reset is accepted when valid temperature data is available and the filtered temperature is below 75°C.

## 7. Installation and Execution

### Prerequisites

Install ROS 2 Humble on Ubuntu 22.04 and ensure that Python and the ROS 2 build tools are available.

### Build the Package

Open a terminal and execute:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select machine_temperature_monitor
source ~/ros2_ws/install/setup.bash
```

### Run the Complete System

Launch both the simulated sensor and the temperature monitor:

```bash
ros2 launch machine_temperature_monitor machine_monitor.launch.py
```

### Observe the Alarm

In another terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /machine/alarm
```

### Observe the Machine Status

```bash
ros2 topic echo /machine/status
```

### Inspect Temperature Readings

```bash
ros2 topic echo /machine/temperature
```

### Check the Reset Service

```bash
ros2 service call /machine/reset std_srvs/srv/Trigger "{}"
```

The reset response indicates whether the request was accepted.

## 8. Testing and Validation

The following tests were performed during development with the monitor configured for deterministic threshold testing using α = 1.0.

| Test | Input or Condition | Expected Result | Observed Result |
|---|---|---|---|
| Normal operation | 74°C | Alarm OFF;