import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node


def generate_launch_description():
    package_name = 'machine_temperature_monitor'
    pkg_share = get_package_share_directory(package_name)

    # Launch args
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Launch interactive Tkinter control dashboard'
    )

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2 3D digital twin visualization'
    )

    # Base monitor launch
    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'machine_monitor.launch.py')
        )
    )

    # 3D Marker Publisher
    marker_node = Node(
        package=package_name,
        executable='rviz_marker_publisher',
        name='rviz_marker_publisher',
        output='screen'
    )

    # Interactive Dashboard GUI
    dashboard_node = Node(
        package=package_name,
        executable='machine_dashboard',
        name='machine_dashboard',
        condition=IfCondition(LaunchConfiguration('gui')),
        output='screen'
    )

    # RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )

    return LaunchDescription([
        gui_arg,
        rviz_arg,
        base_launch,
        marker_node,
        dashboard_node,
        rviz_node
    ])
