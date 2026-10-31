import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger


class TemperatureMonitor(Node):

    def __init__(self):
        super().__init__('temperature_monitor')

        # Declare configurable parameters
        self.declare_parameter('high', 80.0)
        self.declare_parameter('low', 75.0)
        self.declare_parameter('alpha', 0.2)
        self.declare_parameter('stale_timeout', 1.0)

        self.high = self.get_parameter('high').value
        self.low = self.get_parameter('low').value
        self.alpha = self.get_parameter('alpha').value
        self.stale_timeout = self.get_parameter('stale_timeout').value

        # Validate initial configuration
        if not self.valid_config(
            self.high, self.low, self.alpha, self.stale_timeout
        ):
            raise ValueError('Invalid temperature monitor configuration')

        # Register parameter validation callback
        self.add_on_set_parameters_callback(self.validate_parameters)

        # Internal state
        self.filtered_temperature = None
        self.last_received = None
        self.alarm_active = False
        self.status = 'STALE'

        # Subscribe to temperature sensor
        self.subscription = self.create_subscription(
            Temperature,
            '/machine/temperature',
            self.temperature_callback,
            10
        )

        # Publishers
        self.alarm_publisher = self.create_publisher(
            Bool, '/machine/alarm', 10
        )

        self.status_publisher = self.create_publisher(
            String, '/machine/status', 10
        )

        # Reset service
        self.reset_service = self.create_service(
            Trigger,
            '/machine/reset',
            self.reset_callback
        )

        # Periodically check for stale sensor data
        self.timer = self.create_timer(0.1, self.check_stale)

        self.get_logger().info('Temperature Monitor Started')

    def valid_config(self, high, low, alpha, timeout):
        return (
            high > low
            and 0.0 < alpha <= 1.0
            and timeout > 0.0
        )

    def validate_parameters(self, params):
        high = self.high
        low = self.low
        alpha = self.alpha
        timeout = self.stale_timeout

        for param in params:
            if param.name == 'high':
                high = param.value
            elif param.name == 'low':
                low = param.value
            elif param.name == 'alpha':
                alpha = param.value
            elif param.name == 'stale_timeout':
                timeout = param.value

        if not self.valid_config(high, low, alpha, timeout):
            return SetParametersResult(
                successful=False,
                reason='Invalid configuration values'
            )

        self.high = high
        self.low = low
        self.alpha = alpha
        self.stale_timeout = timeout

        return SetParametersResult(successful=True)

    def temperature_callback(self, msg):
        current_temperature = msg.temperature

        # Record arrival time using monotonic clock
        self.last_received = self.get_clock().now()

        # Exponential moving average filtering
        if self.filtered_temperature is None:
            self.filtered_temperature = current_temperature
        else:
            self.filtered_temperature = (
                self.alpha * current_temperature
                + (1.0 - self.alpha) * self.filtered_temperature
            )

        temperature = self.filtered_temperature

        # Hysteresis-based alarm logic
        if temperature >= self.high:
            self.alarm_active = True
        elif temperature < self.low:
            self.alarm_active = False

        self.status = 'ALARM' if self.alarm_active else 'NORMAL'
        self.publish_state()

        self.get_logger().info(
            f'Raw: {current_temperature:.2f} C | '
            f'Filtered: {temperature:.2f} C | '
            f'Status: {self.status}'
        )

    def publish_state(self):
        alarm_msg = Bool()
        alarm_msg.data = self.alarm_active
        self.alarm_publisher.publish(alarm_msg)

        status_msg = String()
        status_msg.data = self.status
        self.status_publisher.publish(status_msg)

    def check_stale(self):
        if self.last_received is None:
            self.status = 'STALE'
            self.publish_state()
            return

        elapsed = (
            self.get_clock().now() - self.last_received
        ).nanoseconds / 1e9

        if elapsed > self.stale_timeout:
            if self.status != 'STALE':
                self.get_logger().warn(
                    'Sensor data stale! No readings received.'
                )

            self.status = 'STALE'
            self.publish_state()

    def reset_callback(self, request, response):
        if self.status == 'STALE':
            response.success = False
            response.message = 'Reset rejected: sensor data is stale'

        elif self.filtered_temperature is None:
            response.success = False
            response.message = 'Reset rejected: no temperature data'

        elif self.filtered_temperature >= self.low:
            response.success = False
            response.message = 'Reset rejected: temperature is not below 75 C'

        else:
            self.alarm_active = False
            self.status = 'NORMAL'
            self.publish_state()

            response.success = True
            response.message = 'Alarm reset successful'

        return response


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
