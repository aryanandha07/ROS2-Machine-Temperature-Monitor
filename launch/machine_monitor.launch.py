import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node


def generate_launch_description():
    package_name = 'machine_temperature_monitor'
    pkg_share = get_package_share_directory(package_name)

    default_config = os.path.join(pkg_share, 'config', 'parameters.yaml')

    # Launch Arguments
    config_arg = DeclareLaunchArgument(
        'config_file',
        default_value=default_config,
        description='Path to YAML configuration file'
    )

    enable_logger_arg = DeclareLaunchArgument(
        'enable_logger',
        default_value='true',
        description='Enable automated CSV evidence logging and plotting'
    )

    # Core Nodes
    temperature_sensor_node = Node(
        package=package_name,
        executable='temperature_sensor',
        name='temperature_sensor',
        parameters=[LaunchConfiguration('config_file')],
        output='screen'
    )

    temperature_monitor_node = Node(
        package=package_name,
        executable='temperature_monitor',
        name='temperature_monitor',
        parameters=[LaunchConfiguration('config_file')],
        output='screen'
    )

    evidence_logger_node = Node(
        package=package_name,
        executable='evidence_logger',
        name='evidence_logger',
        parameters=[LaunchConfiguration('config_file')],
        condition=IfCondition(LaunchConfiguration('enable_logger')),
        output='screen'
    )

    return LaunchDescription([
        config_arg,
        enable_logger_arg,
        temperature_sensor_node,
        temperature_monitor_node,
        evidence_logger_node
    ])
