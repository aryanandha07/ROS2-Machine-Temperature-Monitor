#!/usr/bin/env python3

import time
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_srvs.srv import Trigger


class TemperatureTester(Node):

    def __init__(self):
        super().__init__('temperature_tester')

        self.publisher = self.create_publisher(
            Temperature,
            '/machine/temperature',
            10
        )

        self.reset_client = self.create_client(
            Trigger,
            '/machine/reset'
        )

        self.get_logger().info('Temperature Test Started')

    def publish_temperature(self, temperature, duration=2.0):

        self.get_logger().info(
            f'Testing temperature: {temperature} C'
        )

        end_time = time.monotonic() + duration

        while time.monotonic() < end_time:

            msg = Temperature()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.temperature = float(temperature)
            msg.variance = 0.0

            self.publisher.publish(msg)

            # Publish at 10 Hz
            time.sleep(0.1)

    def test_reset(self):

        if not self.reset_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Reset service unavailable')
            return

        request = Trigger.Request()

        future = self.reset_client.call_async(request)

        rclpy.spin_until_future_complete(
            self,
            future,
            timeout_sec=5.0
        )

        if future.done() and future.result() is not None:

            response = future.result()

            self.get_logger().info(
                f'Reset response: {response.success} | '
                f'{response.message}'
            )

        else:
            self.get_logger().error('Reset request failed')


def main(args=None):

    rclpy.init(args=args)

    node = TemperatureTester()

    try:
        # Give ROS time to discover the publisher
        time.sleep(1.0)

        # Test 1: Normal temperature
        node.publish_temperature(74.0)

        # Test 2: Overheating
        node.publish_temperature(80.0)

        # Test 3: Hysteresis
        node.publish_temperature(77.0)

        # Reset must fail at 77 C
        node.test_reset()

        # Test 4: Cooling
        node.publish_temperature(74.0)

        # Reset must succeed at 74 C
        node.test_reset()

        # Stop publishing to test stale detection
        node.get_logger().info(
            'Stopping sensor data for 2 seconds'
        )

        time.sleep(2.0)

        node.get_logger().info('Test sequence completed')

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
