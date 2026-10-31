import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'machine_temperature_monitor'

    config_file = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'parameters.yaml'
    )

    temperature_sensor = Node(
        package=package_name,
        executable='temperature_sensor',
        name='temperature_sensor',
        output='screen'
    )

    temperature_monitor = Node(
        package=package_name,
        executable='temperature_monitor',
        name='temperature_monitor',
        parameters=[config_file],
        output='screen'
    )

    return LaunchDescription([
        temperature_monitor,
        temperature_sensor
    ])
