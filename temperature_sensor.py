import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature


class TemperatureSensor(Node):

    def __init__(self):
        super().__init__('temperature_sensor')

        # Publisher for temperature readings
        self.publisher_ = self.create_publisher(
            Temperature,
            '/machine/temperature',
            10
        )

        # Publish every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.publish_temperature)

        # Initial simulated temperature
        self.temperature = 74.0
        self.get_logger().info('Temperature Sensor Started')

    def publish_temperature(self):

        msg = Temperature()

        # Add timestamp
        msg.header.stamp = self.get_clock().now().to_msg()

        # Temperature in Celsius
        msg.temperature = self.temperature

        # Simulated measurement variance
        msg.variance = 0.0

        self.publisher_.publish(msg)

        self.get_logger().info(
            f'Temperature: {self.temperature:.2f} °C'
        )


def main(args=None):

    rclpy.init(args=args)

    node = TemperatureSensor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
