import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'machine_temperature_monitor'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Aryanandha',
    maintainer_email='aryanandha633@gmail.com',
    description='ROS 2 machine temperature monitoring with alarm and stale sensor detection',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'temperature_sensor = machine_temperature_monitor.temperature_sensor:main',
            'temperature_monitor = machine_temperature_monitor.temperature_monitor:main',
        ],
    },
)