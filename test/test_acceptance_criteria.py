"""Unit and Acceptance Tests for TemperatureMonitor."""

import pytest
import rclpy
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from sensor_msgs.msg import Temperature
from std_srvs.srv import Trigger
from machine_temperature_monitor.temperature_monitor import TemperatureMonitor


@pytest.fixture(scope='module')
def rclpy_init():
    rclpy.init()
    yield
    if rclpy.ok():
        rclpy.shutdown()


def test_initial_configuration(rclpy_init):
    """Test initial parameters and valid configuration checks."""
    node = TemperatureMonitor()
    assert node.high == 80.0
    assert node.low == 75.0
    assert node.alpha == 0.2
    assert node.stale_timeout == 1.0
    assert node.status == 'STALE'
    node.destroy_node()


def test_deterministic_acceptance_sequence(rclpy_init):
    """
    Test deterministic sequence with alpha=1.0 per specification:
    74 -> NORMAL; 80 -> ALARM; 77 -> ALARM (hysteresis); 74 -> NORMAL.
    At 77 reset must fail, at 74 it must succeed.
    """
    node = TemperatureMonitor()
    node.alpha = 1.0  # Set alpha=1.0 for deterministic evaluation

    # Step 1: 74 C -> NORMAL
    msg1 = Temperature()
    msg1.temperature = 74.0
    node.temperature_callback(msg1)
    assert node.status == 'NORMAL'
    assert node.alarm_active is False

    # Step 2: 80 C -> ALARM
    msg2 = Temperature()
    msg2.temperature = 80.0
    node.temperature_callback(msg2)
    assert node.status == 'ALARM'
    assert node.alarm_active is True

    # Step 3: 77 C -> ALARM (Hysteresis hold)
    msg3 = Temperature()
    msg3.temperature = 77.0
    node.temperature_callback(msg3)
    assert node.status == 'ALARM'
    assert node.alarm_active is True

    # Step 4: Reset at 77 C must fail
    res_fail = node.reset_callback(Trigger.Request(), Trigger.Response())
    assert res_fail.success is False
    assert node.alarm_active is True

    # Step 5: 74 C -> ALARM clears
    msg4 = Temperature()
    msg4.temperature = 74.0
    node.temperature_callback(msg4)
    assert node.status == 'NORMAL'
    assert node.alarm_active is False

    # Step 6: Reset at 74 C must succeed
    res_succ = node.reset_callback(Trigger.Request(), Trigger.Response())
    assert res_succ.success is True

    node.destroy_node()


def test_parameter_boundary_rejection(rclpy_init):
    """Test rejection of invalid parameter updates (high <= low, alpha invalid, timeout <= 0)."""
    node = TemperatureMonitor()

    # Reject high <= low (e.g., high=70 while low=75)
    p_high = Parameter()
    p_high.name = 'high'
    p_high.value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=70.0)
    res = node.validate_parameters([p_high])
    assert res.successful is False

    # Reject alpha outside (0, 1]
    p_alpha = Parameter()
    p_alpha.name = 'alpha'
    p_alpha.value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=0.0)
    res_alpha = node.validate_parameters([p_alpha])
    assert res_alpha.successful is False

    # Reject nonpositive stale timeout
    p_timeout = Parameter()
    p_timeout.name = 'stale_timeout'
    p_timeout.value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=-1.0)
    res_timeout = node.validate_parameters([p_timeout])
    assert res_timeout.successful is False

    node.destroy_node()
