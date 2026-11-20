#!/usr/bin/env python3
"""
Automated Test-Input and Verification Sequence Script.

Executes complete deterministic test sequence per P01 Specification:
1. Normal operation: 74 C -> Status NORMAL, Alarm False
2. Overheating: 80 C -> Status ALARM, Alarm True
3. Hysteresis hold: 77 C -> Status ALARM, Alarm True
4. Safe reset rejection: Reset at 77 C must FAIL
5. Safe reset acceptance: 74 C -> Reset must SUCCEED, Status NORMAL
6. Stale sensor detection: Stop publishing > 1.0 s -> Status STALE
7. Reset during stale: Must FAIL
8. Sensor recovery: Resume 74 C -> Status NORMAL
9. Dynamic Parameter Boundary Rejection:
   - Reject high <= low (e.g., high=70.0 while low=75.0)
   - Reject alpha <= 0 or alpha > 1
   - Reject stale_timeout <= 0
"""

import sys
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue


class TestSequenceRunner(Node):

    def __init__(self):
        super().__init__('test_sequence_runner')

        # Publisher to override sensor temperature directly
        self.publisher = self.create_publisher(
            Temperature,
            '/machine/temperature',
            10
        )

        # Service client for reset
        self.reset_client = self.create_client(
            Trigger,
            '/machine/reset'
        )

        # Parameter client to test boundary rejections
        self.param_client = self.create_client(
            SetParameters,
            '/temperature_monitor/set_parameters'
        )

        # Telemetry monitors
        self.latest_status = None
        self.latest_alarm = None
        self.create_subscription(String, '/machine/status', self._status_cb, 10)
        self.create_subscription(Bool, '/machine/alarm', self._alarm_cb, 10)

        self.test_results = []
        self.get_logger().info('Automated Test Sequence Runner initialized.')

    def _status_cb(self, msg):
        self.latest_status = msg.data

    def _alarm_cb(self, msg):
        self.latest_alarm = msg.data

    def publish_temperature(self, temperature: float, duration: float = 1.5):
        """Publish temperature at 10 Hz for specified duration."""
        self.get_logger().info(f'Publishing T = {temperature:.1f} °C for {duration:.1f}s...')
        end_time = time.monotonic() + duration
        while time.monotonic() < end_time:
            msg = Temperature()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.temperature = float(temperature)
            msg.variance = 0.0
            self.publisher.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.1)

    def call_reset(self) -> (bool, str):
        """Call /machine/reset service synchronously."""
        if not self.reset_client.wait_for_service(timeout_sec=3.0):
            return False, 'Service /machine/reset unavailable'

        req = Trigger.Request()
        future = self.reset_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)

        if future.done() and future.result() is not None:
            res = future.result()
            return res.success, res.message
        return False, 'Call failed'

    def test_parameter(self, param_name: str, value: float) -> bool:
        """Attempt to set a parameter on the monitor and return whether it succeeded."""
        if not self.param_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error('Parameter service unavailable')
            return False

        req = SetParameters.Request()
        p = Parameter()
        p.name = param_name
        p.value = ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=float(value))
        req.parameters = [p]

        future = self.param_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
        if future.done() and future.result() is not None:
            results = future.result().results
            return results[0].successful if results else False
        return False

    def record_result(self, test_id, name, expected, observed, passed):
        self.test_results.append({
            'id': test_id,
            'name': name,
            'expected': expected,
            'observed': observed,
            'passed': passed
        })
        status_str = "PASS" if passed else "FAIL"
        self.get_logger().info(f"[{status_str}] {test_id}: {name} -> Observed: {observed}")

    def run_all_tests(self):
        self.get_logger().info("================ STARTING TEST SUITE ================")
        time.sleep(1.0)  # Allow discovery

        # Ensure alpha=1.0 for deterministic evaluation
        self.test_parameter('alpha', 1.0)

        # ---------------- Test 1: 74 C -> NORMAL ----------------
        self.publish_temperature(74.0, duration=1.2)
        p1 = (self.latest_status == 'NORMAL' and self.latest_alarm is False)
        self.record_result('T01', 'Initial Nominal (74°C)', 'Status=NORMAL, Alarm=False',
                           f'Status={self.latest_status}, Alarm={self.latest_alarm}', p1)

        # ---------------- Test 2: 80 C -> ALARM ----------------
        self.publish_temperature(80.0, duration=1.2)
        p2 = (self.latest_status == 'ALARM' and self.latest_alarm is True)
        self.record_result('T02', 'High Threshold (80°C)', 'Status=ALARM, Alarm=True',
                           f'Status={self.latest_status}, Alarm={self.latest_alarm}', p2)

        # ---------------- Test 3: 77 C -> Hysteresis ALARM ----------------
        self.publish_temperature(77.0, duration=1.2)
        p3 = (self.latest_status == 'ALARM' and self.latest_alarm is True)
        self.record_result('T03', 'Hysteresis Zone (77°C)', 'Status=ALARM (Hold), Alarm=True',
                           f'Status={self.latest_status}, Alarm={self.latest_alarm}', p3)

        # ---------------- Test 4: Reset at 77 C -> Must FAIL ----------------
        succ, msg = self.call_reset()
        p4 = (succ is False)
        self.record_result('T04', 'Reset at 77°C (Must Fail)', 'success=False',
                           f'success={succ} ({msg})', p4)

        # ---------------- Test 5: 74 C -> Reset Must SUCCEED ----------------
        self.publish_temperature(74.0, duration=1.2)
        succ, msg = self.call_reset()
        p5 = (succ is True and self.latest_status == 'NORMAL' and self.latest_alarm is False)
        self.record_result('T05', 'Safe Reset at 74°C', 'success=True, Status=NORMAL',
                           f'success={succ}, Status={self.latest_status}', p5)

        # ---------------- Test 6: Stale Detection (>1.0s timeout) ----------------
        self.get_logger().info('Pausing sensor publication for 1.5 seconds...')
        time.sleep(1.5)
        # Pump callbacks to process stale timer
        rclpy.spin_once(self, timeout_sec=0.2)
        p6 = (self.latest_status == 'STALE')
        self.record_result('T06', 'Stale Sensor Timeout (>1.0s)', 'Status=STALE',
                           f'Status={self.latest_status}', p6)

        # ---------------- Test 7: Reset during STALE -> Must FAIL ----------------
        succ, msg = self.call_reset()
        p7 = (succ is False)
        self.record_result('T07', 'Reset during STALE (Must Fail)', 'success=False',
                           f'success={succ} ({msg})', p7)

        # ---------------- Test 8: Sensor Recovery ----------------
        self.publish_temperature(74.0, duration=1.2)
        p8 = (self.latest_status == 'NORMAL')
        self.record_result('T08', 'Sensor Telemetry Recovery', 'Status=NORMAL',
                           f'Status={self.latest_status}', p8)

        # ---------------- Test 9: Reject high <= low (high=70, low=75) ----------------
        succ = self.test_parameter('high', 70.0)
        p9 = (succ is False)
        self.record_result('T09', 'Reject high <= low (high=70.0)', 'Rejected (False)',
                           f'{"Accepted" if succ else "Rejected"}', p9)

        # ---------------- Test 10: Reject invalid alpha (alpha=0.0) ----------------
        succ = self.test_parameter('alpha', 0.0)
        p10 = (succ is False)
        self.record_result('T10', 'Reject invalid alpha (alpha=0.0)', 'Rejected (False)',
                           f'{"Accepted" if succ else "Rejected"}', p10)

        # ---------------- Test 11: Reject negative stale_timeout ----------------
        succ = self.test_parameter('stale_timeout', -1.0)
        p11 = (succ is False)
        self.record_result('T11', 'Reject negative stale_timeout', 'Rejected (False)',
                           f'{"Accepted" if succ else "Rejected"}', p11)

        # Print Formatted Verification Table
        print("\n" + "="*85)
        print(f"{'TEST ID':<8} | {'TEST DESCRIPTION':<32} | {'RESULT':<6} | {'OBSERVED'}")
        print("="*85)
        total_passed = 0
        for r in self.test_results:
            status_text = "PASS" if r['passed'] else "FAIL"
            if r['passed']:
                total_passed += 1
            print(f"{r['id']:<8} | {r['name']:<32} | {status_text:<6} | {r['observed']}")
        print("="*85)
        print(f"VERIFICATION SCORE: {total_passed}/{len(self.test_results)} Tests Passed ({(total_passed/len(self.test_results))*100:.1f}%)")
        print("="*85 + "\n")


def main(args=None):
    rclpy.init(args=args)
    runner = TestSequenceRunner()
    try:
        runner.run_all_tests()
    finally:
        runner.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
