#!/usr/bin/env python3
"""
3D RViz Digital Twin Marker Publisher.

Fulfills 'model files' specification requirement by rendering a 3D visual model
of the CNC machine spindle and crankshaft journal bearing in RViz2 with dynamic
thermal color heatmapping:
- Safe (< 75 C): Cyan / Emerald Green
- Hysteresis band (75 - 80 C): Amber Warning
- Overheat Alarm (>= 80 C): Pulsing Crimson Red
- Stale Sensor: Translucent Gray
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point


class RvizMarkerPublisher(Node):
    """Publishes 3D RViz markers representing the machine spindle thermal state."""

    def __init__(self):
        super().__init__('rviz_marker_publisher')

        self.marker_pub = self.create_publisher(Marker, '/machine/model_marker', 10)

        self.temperature = 74.0
        self.alarm_active = False
        self.status = 'STALE'
        self.pulse_phase = 0.0

        # Subscriptions
        self.create_subscription(
            Temperature, '/machine/filtered_temperature', self.temp_cb, 10
        )
        self.create_subscription(
            Bool, '/machine/alarm', self.alarm_cb, 10
        )
        self.create_subscription(
            String, '/machine/status', self.status_cb, 10
        )

        # Publish marker at 10 Hz
        self.timer = self.create_timer(0.1, self.publish_marker)
        self.get_logger().info('3D RViz Spindle Digital Twin Marker Publisher active.')

    def temp_cb(self, msg):
        self.temperature = msg.temperature

    def alarm_cb(self, msg):
        self.alarm_active = msg.data

    def status_cb(self, msg):
        self.status = msg.data

    def publish_marker(self):
        self.pulse_phase += 0.2

        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'cnc_spindle_bearing'
        marker.id = 0
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        # Dimensions of Spindle Journal (scaled for visualization: 0.5m dia, 1.2m length)
        marker.pose.position.x = 0.0
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.6
        marker.pose.orientation.x = 0.7071
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = 0.7071

        marker.scale.x = 0.5
        marker.scale.y = 0.5
        marker.scale.z = 1.2

        # Dynamic Color Heatmapping
        if self.status == 'STALE':
            marker.color.r = 0.6
            marker.color.g = 0.6
            marker.color.b = 0.6
            marker.color.a = 0.5
        elif self.alarm_active:
            # Pulsing red
            pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0
            marker.color.r = 1.0
            marker.color.g = 0.1 * pulse
            marker.color.b = 0.1 * pulse
            marker.color.a = 0.85 + 0.15 * pulse
        elif self.temperature >= 75.0:
            # Warning amber
            marker.color.r = 1.0
            marker.color.g = 0.6
            marker.color.b = 0.0
            marker.color.a = 0.9
        else:
            # Normal safe green/cyan
            marker.color.r = 0.1
            marker.color.g = 0.8
            marker.color.b = 0.4
            marker.color.a = 0.9

        self.marker_pub.publish(marker)

        # Publish text label above spindle
        text_marker = Marker()
        text_marker.header.frame_id = 'map'
        text_marker.header.stamp = marker.header.stamp
        text_marker.ns = 'spindle_text'
        text_marker.id = 1
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD
        text_marker.pose.position.x = 0.0
        text_marker.pose.position.y = 0.0
        text_marker.pose.position.z = 1.4
        text_marker.scale.z = 0.18
        text_marker.color.r = 1.0
        text_marker.color.g = 1.0
        text_marker.color.b = 1.0
        text_marker.color.a = 1.0
        text_marker.text = (
            f"CNC Spindle Bearing (Ø50 h5)\n"
            f"Temp: {self.temperature:.1f} °C | Status: {self.status}"
        )
        self.marker_pub.publish(text_marker)


def main(args=None):
    rclpy.init(args=args)
    node = RvizMarkerPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
