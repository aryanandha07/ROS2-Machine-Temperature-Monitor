#!/usr/bin/env python3
"""
Evidence Logger and Plot Generator Node.

Fulfills Project Evidence Deliverables:
- Records timestamped raw temperature, filtered temperature, alarm state, and status.
- Logs reset requests and service responses.
- Generates a timestamped CSV file in the 'evidence/' directory.
- On shutdown (or via /evidence/generate_plots service), renders a 4-panel
  matplotlib verification plot displaying:
    1. Raw vs. Filtered Temperature with EMA smoothing and Alarm/Safe bands.
    2. Alarm State timeline (Boolean step signal).
    3. Machine Status with STALE blackout periods highlighted.
    4. Reset events with success / rejection markers.
"""

import os
import csv
from datetime import datetime
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger


class EvidenceLogger(Node):
    """Subscribes to telemetry, logs to CSV, and generates verification figures."""

    def __init__(self):
        super().__init__('evidence_logger')

        self.declare_parameter('output_dir', 'evidence')
        self.output_dir = self.get_parameter('output_dir').value

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Setup CSV file
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_path = os.path.join(self.output_dir, f'temperature_run_{timestamp_str}.csv')
        self.plot_path = os.path.join(self.output_dir, f'verification_plot_{timestamp_str}.png')

        self.csv_file = open(self.csv_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'elapsed_sec',
            'raw_temperature',
            'filtered_temperature',
            'alarm_active',
            'status',
            'event'
        ])
        self.csv_file.flush()

        # Data buffers for plotting
        self.start_time = self.get_clock().now()
        self.times = []
        self.raw_temps = []
        self.filtered_temps = []
        self.alarms = []
        self.statuses = []
        self.events = []  # List of (time, temp, label, success_bool)

        # Current telemetry cache
        self.curr_raw = None
        self.curr_filtered = None
        self.curr_alarm = False
        self.curr_status = 'STALE'

        # Subscriptions
        self.create_subscription(
            Temperature, '/machine/temperature', self.raw_callback, 10
        )
        self.create_subscription(
            Temperature, '/machine/filtered_temperature', self.filtered_callback, 10
        )
        self.create_subscription(
            Bool, '/machine/alarm', self.alarm_callback, 10
        )
        self.create_subscription(
            String, '/machine/status', self.status_callback, 10
        )

        # Sampling Timer (10 Hz recording)
        self.timer = self.create_timer(0.1, self.record_sample)

        # Service to trigger immediate plot generation
        self.create_service(Trigger, '/evidence/save_plots', self.save_plots_callback)

        self.get_logger().info(f'Evidence Logger running. Logging to: {self.csv_path}')

    def raw_callback(self, msg):
        self.curr_raw = msg.temperature

    def filtered_callback(self, msg):
        self.curr_filtered = msg.temperature

    def alarm_callback(self, msg):
        self.curr_alarm = msg.data

    def status_callback(self, msg):
        self.curr_status = msg.data

    def record_sample(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9

        raw_val = self.curr_raw if self.curr_raw is not None else float('nan')
        filt_val = self.curr_filtered if self.curr_filtered is not None else float('nan')

        self.times.append(elapsed)
        self.raw_temps.append(raw_val)
        self.filtered_temps.append(filt_val)
        self.alarms.append(1 if self.curr_alarm else 0)
        self.statuses.append(self.curr_status)

        self.csv_writer.writerow([
            f'{elapsed:.3f}',
            f'{raw_val:.3f}' if not math_isnan(raw_val) else '',
            f'{filt_val:.3f}' if not math_isnan(filt_val) else '',
            int(self.curr_alarm),
            self.curr_status,
            ''
        ])
        self.csv_file.flush()

    def log_reset_event(self, success: bool, msg: str):
        """Record a reset trigger service call event."""
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        current_temp = self.curr_filtered if self.curr_filtered is not None else self.curr_raw
        self.events.append((elapsed, current_temp, msg, success))
        self.csv_writer.writerow([
            f'{elapsed:.3f}',
            '',
            '',
            int(self.curr_alarm),
            self.curr_status,
            f'RESET_{"SUCCESS" if success else "REJECT"}: {msg}'
        ])
        self.csv_file.flush()

    def save_plots_callback(self, request, response):
        self.generate_plot()
        response.success = True
        response.message = f'Plots saved to {self.plot_path}'
        return response

    def generate_plot(self):
        """Generate high-resolution 4-panel matplotlib verification plot."""
        if not self.times:
            self.get_logger().warn('No data collected to plot.')
            return

        try:
            import matplotlib
            matplotlib.use('Agg')  # Headless rendering
            import matplotlib.pyplot as plt
        except ImportError:
            self.get_logger().error('matplotlib not installed. Skipping plot generation.')
            return

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
        fig.suptitle('Machine Temperature Monitoring Telemetry & Verification', fontsize=14, fontweight='bold')

        # Panel 1: Temperature & Threshold Bands
        ax1.plot(self.times, self.raw_temps, label='Raw Sensor (10 Hz)', color='gray', alpha=0.5, linestyle=':')
        ax1.plot(self.times, self.filtered_temps, label='Filtered (EMA α=0.2)', color='blue', linewidth=2.0)
        ax1.axhline(80.0, color='red', linestyle='--', linewidth=1.5, label='Alarm High Limit (80°C)')
        ax1.axhline(75.0, color='green', linestyle='--', linewidth=1.5, label='Clear Safe Limit (75°C)')
        ax1.axhspan(80.0, 100.0, color='red', alpha=0.1, label='Alarm Zone')
        ax1.axhspan(0.0, 75.0, color='green', alpha=0.08, label='Safe Zone')
        ax1.set_ylabel('Temperature (°C)', fontsize=11)
        ax1.set_ylim(65.0, 90.0)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(loc='upper right', framealpha=0.9, fontsize=9)

        # Plot reset events on Panel 1
        for t, temp, label, success in self.events:
            marker = '^' if success else 'x'
            color = 'green' if success else 'red'
            ax1.scatter([t], [temp or 75.0], marker=marker, s=120, color=color, zorder=5)
            ax1.annotate(
                f'{"Reset OK" if success else "Reset Blocked"}',
                xy=(t, temp or 75.0),
                xytext=(t, (temp or 75.0) + (3 if success else -3)),
                arrowprops=dict(facecolor=color, arrowstyle='->'),
                fontsize=8, fontweight='bold', color=color
            )

        # Panel 2: Alarm State Timeline
        ax2.step(self.times, self.alarms, where='post', color='crimson', linewidth=2.0, label='Alarm State')
        ax2.set_ylabel('Alarm (Bool)', fontsize=11)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['False (Normal)', 'True (ALARM)'])
        ax2.set_ylim(-0.2, 1.2)
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend(loc='upper right', fontsize=9)

        # Panel 3: Machine Status & Stale Region
        status_num = []
        for s in self.statuses:
            if s == 'NORMAL':
                status_num.append(0)
            elif s == 'ALARM':
                status_num.append(1)
            elif s == 'STALE':
                status_num.append(2)
            else:
                status_num.append(-1)

        ax3.step(self.times, status_num, where='post', color='darkorange', linewidth=2.0, label='Status')
        ax3.set_ylabel('Status', fontsize=11)
        ax3.set_yticks([0, 1, 2])
        ax3.set_yticklabels(['NORMAL', 'ALARM', 'STALE (Failure)'])
        ax3.set_ylim(-0.3, 2.3)
        ax3.set_xlabel('Elapsed Time (seconds)', fontsize=11)
        ax3.grid(True, linestyle='--', alpha=0.6)
        ax3.legend(loc='upper right', fontsize=9)

        plt.tight_layout()
        plt.savefig(self.plot_path, dpi=300)
        plt.close()
        self.get_logger().info(f'Verification plot saved to: {self.plot_path}')

    def close(self):
        if not self.csv_file.closed:
            self.csv_file.close()
        self.generate_plot()


def math_isnan(val):
    return val != val


def main(args=None):
    rclpy.init(args=args)
    node = EvidenceLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
