#!/usr/bin/env python3
"""
Machine Temperature Monitor Node with Hysteresis and Stale-Data Detection.

Subscribes to raw machine temperature, applies Exponential Moving Average (EMA)
filtering, evaluates dual-threshold hysteresis alarms, detects communication
timeouts (stale data), publishes standard ROS 2 diagnostics, and provides a
safe reset service.
"""

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue


class TemperatureMonitor(Node):
    """Monitors machine temperature with hysteresis and sensor-failure detection."""

    def __init__(self):
        super().__init__('temperature_monitor')

        # Declare configurable parameters
        self.declare_parameter('high', 80.0)
        self.declare_parameter('low', 75.0)
        self.declare_parameter('alpha', 0.2)
        self.declare_parameter('stale_timeout', 1.0)

        self.high = float(self.get_parameter('high').value)
        self.low = float(self.get_parameter('low').value)
        self.alpha = float(self.get_parameter('alpha').value)
        self.stale_timeout = float(self.get_parameter('stale_timeout').value)

        # Validate initial configuration
        if not self.valid_config(
            self.high, self.low, self.alpha, self.stale_timeout
        ):
            raise ValueError(
                f'Invalid configuration: high={self.high}, low={self.low}, '
                f'alpha={self.alpha}, timeout={self.stale_timeout}'
            )

        # Register parameter validation callback
        self.add_on_set_parameters_callback(self.validate_parameters)

        # Internal state
        self.raw_temperature = None
        self.filtered_temperature = None
        self.last_received = None
        self.alarm_active = False
        self.status = 'STALE'  # Initially STALE until first sensor reading arrives

        # Subscription: Raw Temperature from Sensor
        self.subscription = self.create_subscription(
            Temperature,
            '/machine/temperature',
            self.temperature_callback,
            10
        )

        # Required Topic Publishers
        self.alarm_publisher = self.create_publisher(
            Bool, '/machine/alarm', 10
        )

        self.status_publisher = self.create_publisher(
            String, '/machine/status', 10
        )

        # Extraordinary Feature: Filtered Temperature Topic for Telemetry / RViz
        self.filtered_temp_publisher = self.create_publisher(
            Temperature, '/machine/filtered_temperature', 10
        )

        # Extraordinary Feature: Industrial Standard Diagnostics (/diagnostics)
        self.diag_publisher = self.create_publisher(
            DiagnosticArray, '/diagnostics', 10
        )

        # Required Service: Safe Reset
        self.reset_service = self.create_service(
            Trigger,
            '/machine/reset',
            self.reset_callback
        )

        # Periodic Timer for Stale Sensor Detection (10 Hz check)
        self.timer = self.create_timer(0.1, self.check_stale)

        # Periodic Timer for Diagnostics Publishing (1 Hz)
        self.diag_timer = self.create_timer(1.0, self.publish_diagnostics)

        self.get_logger().info(
            f'Temperature Monitor started. High: {self.high} C, Low: {self.low} C, '
            f'Alpha: {self.alpha}, Stale Timeout: {self.stale_timeout} s'
        )

    def valid_config(self, high, low, alpha, timeout):
        """Validate parameter ranges per specification: high > low, 0 < alpha <= 1, timeout > 0."""
        return (
            high > low
            and 0.0 < alpha <= 1.0
            and timeout > 0.0
        )

    def validate_parameters(self, params):
        """Dynamic parameter validation callback."""
        high = self.high
        low = self.low
        alpha = self.alpha
        timeout = self.stale_timeout

        for param in params:
            if param.name == 'high':
                high = float(param.value)
            elif param.name == 'low':
                low = float(param.value)
            elif param.name == 'alpha':
                alpha = float(param.value)
            elif param.name == 'stale_timeout':
                timeout = float(param.value)

        if not self.valid_config(high, low, alpha, timeout):
            self.get_logger().error(
                f'Rejected invalid parameter update: high={high}, low={low}, '
                f'alpha={alpha}, timeout={timeout}'
            )
            return SetParametersResult(
                successful=False,
                reason=(
                    'Invalid configuration: ensure high > low, '
                    '0.0 < alpha <= 1.0, and stale_timeout > 0.0'
                )
            )

        self.high = high
        self.low = low
        self.alpha = alpha
        self.stale_timeout = timeout

        self.get_logger().info(
            f'Parameters dynamically updated: high={high}, low={low}, '
            f'alpha={alpha}, timeout={timeout}'
        )
        return SetParametersResult(successful=True)

    def temperature_callback(self, msg):
        """Process incoming raw temperature reading."""
        self.raw_temperature = msg.temperature
        self.last_received = self.get_clock().now()

        # Exponential Moving Average (EMA) Filtering:
        # y[k] = alpha * x[k] + (1 - alpha) * y[k-1]
        if self.filtered_temperature is None:
            self.filtered_temperature = self.raw_temperature
        else:
            self.filtered_temperature = (
                self.alpha * self.raw_temperature
                + (1.0 - self.alpha) * self.filtered_temperature
            )

        temp = self.filtered_temperature

        # Dual-Threshold Hysteresis Evaluation:
        # Trigger alarm at or above high threshold (default: 80.0 C)
        # Clear alarm strictly below low threshold (default: 75.0 C)
        # Retain previous state between low and high
        if temp >= self.high:
            self.alarm_active = True
        elif temp < self.low:
            self.alarm_active = False

        self.status = 'ALARM' if self.alarm_active else 'NORMAL'
        self.publish_state()

        # Publish filtered temperature message
        filt_msg = Temperature()
        filt_msg.header.stamp = self.get_clock().now().to_msg()
        filt_msg.header.frame_id = msg.header.frame_id or 'machine_frame'
        filt_msg.temperature = float(temp)
        filt_msg.variance = msg.variance
        self.filtered_temp_publisher.publish(filt_msg)

    def publish_state(self):
        """Publish alarm state and machine status."""
        alarm_msg = Bool()
        alarm_msg.data = self.alarm_active
        self.alarm_publisher.publish(alarm_msg)

        status_msg = String()
        status_msg.data = self.status
        self.status_publisher.publish(status_msg)

    def check_stale(self):
        """Check for sensor communication timeout and transition to STALE if exceeded."""
        if self.last_received is None:
            if self.status != 'STALE':
                self.status = 'STALE'
                self.publish_state()
            return

        elapsed = (
            self.get_clock().now() - self.last_received
        ).nanoseconds / 1e9

        if elapsed > self.stale_timeout:
            if self.status != 'STALE':
                self.get_logger().warn(
                    f'Sensor communication failure: no readings received for '
                    f'{elapsed:.2f} s (> {self.stale_timeout:.1f} s). Status -> STALE'
                )
                self.status = 'STALE'
                self.publish_state()

    def reset_callback(self, request, response):
        """
        Service callback for /machine/reset (std_srvs/Trigger).

        Acceptance Criteria:
        - Succeeds ONLY when valid readings exist AND filtered temperature < 75.0 C.
        - Fails when temperature >= 75.0 C.
        - Fails when sensor data is STALE.
        """
        if self.status == 'STALE':
            response.success = False
            response.message = 'Reset rejected: sensor data is stale (communication failure)'
            self.get_logger().warn('Reset request REJECTED: sensor data is stale.')

        elif self.filtered_temperature is None:
            response.success = False
            response.message = 'Reset rejected: no temperature data received yet'
            self.get_logger().warn('Reset request REJECTED: no temperature data.')

        elif self.filtered_temperature >= self.low:
            response.success = False
            response.message = (
                f'Reset rejected: temperature ({self.filtered_temperature:.2f} C) '
                f'is not below safe threshold ({self.low:.1f} C)'
            )
            self.get_logger().warn(
                f'Reset request REJECTED: temp {self.filtered_temperature:.2f} C >= {self.low} C.'
            )

        else:
            self.alarm_active = False
            self.status = 'NORMAL'
            self.publish_state()

            response.success = True
            response.message = (
                f'Alarm reset successful: temperature is {self.filtered_temperature:.2f} C '
                f'(below safe threshold {self.low:.1f} C)'
            )
            self.get_logger().info('Reset request ACCEPTED: machine state cleared to NORMAL.')

        return response

    def publish_diagnostics(self):
        """Publish standard ROS 2 DiagnosticArray on /diagnostics."""
        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()

        status = DiagnosticStatus()
        status.name = 'Machine: Spindle Bearing Thermal Monitor'
        status.hardware_id = 'CNC_SPINDLE_BEARING_01'

        if self.status == 'STALE':
            status.level = DiagnosticStatus.ERROR
            status.message = 'Sensor data STALE: sensor timeout exceeded'
        elif self.alarm_active:
            status.level = DiagnosticStatus.ERROR
            status.message = f'Thermal OVERHEAT Alarm active (>= {self.high} C)'
        elif self.filtered_temperature is not None and self.filtered_temperature >= self.low:
            status.level = DiagnosticStatus.WARN
            status.message = f'Elevated temperature in hysteresis band ({self.low} C - {self.high} C)'
        else:
            status.level = DiagnosticStatus.OK
            status.message = 'Operating normally within safe temperature bounds'

        status.values = [
            KeyValue(key='status', value=str(self.status)),
            KeyValue(key='alarm_active', value=str(self.alarm_active)),
            KeyValue(
                key='raw_temperature_c',
                value=f'{self.raw_temperature:.2f}' if self.raw_temperature is not None else 'N/A'
            ),
            KeyValue(
                key='filtered_temperature_c',
                value=f'{self.filtered_temperature:.2f}' if self.filtered_temperature is not None else 'N/A'
            ),
            KeyValue(key='threshold_high_c', value=str(self.high)),
            KeyValue(key='threshold_low_c', value=str(self.low)),
            KeyValue(key='filter_alpha', value=str(self.alpha)),
            KeyValue(key='stale_timeout_s', value=str(self.stale_timeout)),
        ]

        diag_array.status.append(status)
        self.diag_publisher.publish(diag_array)


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = TemperatureMonitor()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
