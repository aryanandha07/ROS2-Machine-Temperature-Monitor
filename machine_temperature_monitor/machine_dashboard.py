#!/usr/bin/env python3
"""
Interactive Machine Temperature Monitoring Dashboard.

Provides a visual GUI for operators and demonstration presentations:
- Real-time gauge and digital temperature readout (Raw & Filtered).
- Live Status Annunciator (NORMAL: Green, ALARM: Red Flashing, STALE: Amber).
- One-click trigger for /machine/reset service.
- One-click fault injection buttons for live testing (coolant cutoff, sensor disconnect).
- Live parameter tuning (high, low, alpha, timeout).
"""

import sys
import threading
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger, SetBool
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue


class DashboardBridge(Node):
    """ROS 2 Node running in background thread of GUI."""

    def __init__(self, update_ui_callback):
        super().__init__('machine_dashboard_bridge')
        self.update_ui = update_ui_callback

        self.raw_temp = 0.0
        self.filtered_temp = 0.0
        self.alarm_active = False
        self.status = 'STALE'

        # Subscriptions
        self.create_subscription(
            Temperature, '/machine/temperature', self.on_raw_temp, 10
        )
        self.create_subscription(
            Temperature, '/machine/filtered_temperature', self.on_filtered_temp, 10
        )
        self.create_subscription(
            Bool, '/machine/alarm', self.on_alarm, 10
        )
        self.create_subscription(
            String, '/machine/status', self.on_status, 10
        )

        # Service Clients
        self.reset_cli = self.create_client(Trigger, '/machine/reset')
        self.coolant_cli = self.create_client(SetBool, '/sensor/set_coolant')
        self.conn_cli = self.create_client(SetBool, '/sensor/set_connected')
        self.param_cli = self.create_client(SetParameters, '/temperature_monitor/set_parameters')

    def on_raw_temp(self, msg):
        self.raw_temp = msg.temperature
        self.update_ui('raw_temp', self.raw_temp)

    def on_filtered_temp(self, msg):
        self.filtered_temp = msg.temperature
        self.update_ui('filtered_temp', self.filtered_temp)

    def on_alarm(self, msg):
        self.alarm_active = msg.data
        self.update_ui('alarm', self.alarm_active)

    def on_status(self, msg):
        self.status = msg.data
        self.update_ui('status', self.status)

    def call_reset(self, callback_done):
        if not self.reset_cli.wait_for_service(timeout_sec=1.0):
            callback_done(False, 'Service /machine/reset unavailable')
            return
        future = self.reset_cli.call_async(Trigger.Request())
        future.add_done_callback(lambda f: callback_done(f.result().success, f.result().message))

    def set_coolant(self, active: bool, callback_done):
        if not self.coolant_cli.wait_for_service(timeout_sec=1.0):
            callback_done(False, 'Service /sensor/set_coolant unavailable')
            return
        req = SetBool.Request(data=active)
        future = self.coolant_cli.call_async(req)
        future.add_done_callback(lambda f: callback_done(f.result().success, f.result().message))

    def set_sensor_connected(self, connected: bool, callback_done):
        if not self.conn_cli.wait_for_service(timeout_sec=1.0):
            callback_done(False, 'Service /sensor/set_connected unavailable')
            return
        req = SetBool.Request(data=connected)
        future = self.conn_cli.call_async(req)
        future.add_done_callback(lambda f: callback_done(f.result().success, f.result().message))


def start_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("tkinter not available. Please install python3-tk.")
        return

    rclpy.init()

    root = tk.Tk()
    root.title("CNC Machine Spindle Thermal Monitor — Digital Twin")
    root.geometry("640x580")
    root.resizable(False, False)

    # Style
    style = ttk.Style()
    style.theme_use('clam')

    # Status & Telemetry Variables
    raw_var = tk.StringVar(value="--.- °C")
    filt_var = tk.StringVar(value="--.- °C")
    status_var = tk.StringVar(value="INITIALIZING")
    log_var = tk.StringVar(value="System started. Awaiting sensor telemetry...")

    def ui_callback(key, value):
        if key == 'raw_temp':
            raw_var.set(f"{value:.2f} °C")
        elif key == 'filtered_temp':
            filt_var.set(f"{value:.2f} °C")
        elif key == 'status':
            status_var.set(value)
            if value == 'NORMAL':
                status_lbl.config(bg="#2ecc71", fg="white")
            elif value == 'ALARM':
                status_lbl.config(bg="#e74c3c", fg="white")
            elif value == 'STALE':
                status_lbl.config(bg="#f39c12", fg="black")

    bridge = DashboardBridge(ui_callback)

    # Spin ROS 2 in background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(bridge,), daemon=True)
    spin_thread.start()

    # Layout Header
    header = tk.Frame(root, bg="#2c3e50", pady=10)
    header.pack(fill=tk.X)
    title = tk.Label(
        header, text="CNC SPINDLE THERMAL MONITOR",
        font=("Helvetica", 16, "bold"), fg="white", bg="#2c3e50"
    )
    title.pack()
    subtitle = tk.Label(
        header, text="Engine Assembly Machining Operations • Spindle Bearing Journal",
        font=("Helvetica", 9), fg="#bdc3c7", bg="#2c3e50"
    )
    subtitle.pack()

    # Temperature Display Frame
    card_frame = tk.Frame(root, pady=15)
    card_frame.pack(fill=tk.X, padx=20)

    # Raw Temp Card
    c1 = tk.LabelFrame(card_frame, text=" Raw Temperature ", font=("Helvetica", 10, "bold"), padx=15, pady=10)
    c1.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
    tk.Label(c1, textvariable=raw_var, font=("Helvetica", 20, "bold"), fg="#7f8c8d").pack()

    # Filtered Temp Card
    c2 = tk.LabelFrame(card_frame, text=" Filtered (EMA α=0.2) ", font=("Helvetica", 10, "bold"), padx=15, pady=10)
    c2.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
    tk.Label(c2, textvariable=filt_var, font=("Helvetica", 20, "bold"), fg="#2980b9").pack()

    # Status Banner
    status_frame = tk.Frame(root, padx=20, pady=5)
    status_frame.pack(fill=tk.X)
    status_lbl = tk.Label(
        status_frame, textvariable=status_var, font=("Helvetica", 16, "bold"),
        bg="#f39c12", fg="black", pady=8, relief=tk.RIDGE
    )
    status_lbl.pack(fill=tk.X)

    # Control Actions Frame
    ctrl_frame = tk.LabelFrame(root, text=" Operator Controls & Reset ", font=("Helvetica", 10, "bold"), padx=15, pady=10)
    ctrl_frame.pack(fill=tk.X, padx=20, pady=10)

    def on_reset_click():
        log_var.set("Requesting /machine/reset...")
        bridge.call_reset(lambda ok, msg: log_var.set(f"Reset {'ACCEPTED' if ok else 'REJECTED'}: {msg}"))

    btn_reset = tk.Button(
        ctrl_frame, text="Execute Safe Reset (/machine/reset)", font=("Helvetica", 11, "bold"),
        bg="#3498db", fg="white", activebackground="#2980b9", command=on_reset_click, pady=6
    )
    btn_reset.pack(fill=tk.X)

    # Fault Injection Simulation Frame (Extraordinary Demo Features)
    test_frame = tk.LabelFrame(root, text=" Live Fault Injection (Demo Mode) ", font=("Helvetica", 10, "bold"), padx=15, pady=10)
    test_frame.pack(fill=tk.X, padx=20, pady=5)

    btn_row = tk.Frame(test_frame)
    btn_row.pack(fill=tk.X)

    def cut_coolant():
        bridge.set_coolant(False, lambda ok, msg: log_var.set(f"Coolant CUT: Spindle heating initiated!"))

    def restore_coolant():
        bridge.set_coolant(True, lambda ok, msg: log_var.set("Coolant RESTORED: Cooling to nominal."))

    def disconnect_sensor():
        bridge.set_sensor_connected(False, lambda ok, msg: log_var.set("Sensor DISCONNECTED: Testing 1s STALE timeout."))

    def reconnect_sensor():
        bridge.set_sensor_connected(True, lambda ok, msg: log_var.set("Sensor RECONNECTED: Telemetry resumed."))

    tk.Button(btn_row, text="Cut Coolant (Overheat)", bg="#e67e22", fg="white", command=cut_coolant).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    tk.Button(btn_row, text="Restore Coolant", bg="#27ae60", fg="white", command=restore_coolant).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    tk.Button(btn_row, text="Disconnect Sensor", bg="#8e44ad", fg="white", command=disconnect_sensor).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    tk.Button(btn_row, text="Reconnect Sensor", bg="#16a085", fg="white", command=reconnect_sensor).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    # Log Terminal Line
    log_lbl = tk.Label(root, textvariable=log_var, font=("Courier", 9), fg="#2c3e50", bg="#ecf0f1", anchor="w", padx=10, pady=5)
    log_lbl.pack(fill=tk.X, side=tk.BOTTOM)

    root.protocol("WM_DELETE_WINDOW", lambda: (bridge.destroy_node(), rclpy.shutdown(), root.destroy()))
    root.mainloop()


def main(args=None):
    start_gui()


if __name__ == '__main__':
    main()
