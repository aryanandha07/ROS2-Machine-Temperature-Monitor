# Presentation & Defense Guide: ROS 2 Machine Temperature Monitor
**Evaluation by:** Dr. K Ponnappa  
**Course / Level:** ROS 2 Machine Monitoring & Alarm Pipeline (P01 Specification - 100 Marks)  
**Project Domain:** Industrial Cyber-Physical Digital Twin for Precision Engine Machining Operations  

---

## Front Page Details

### Title
**MACHINE TEMPERATURE MONITORING & ALARM SYSTEM**  
*Cyber-Physical Digital Twin for Precision CNC Engine Machining Operations (Crankshaft & Piston Assembly)*

### Presented To
**Dr. K Ponnappa**  
Department of Mechanical / Robotics Engineering  

### Team Members
| No. | Student Name | Role / Roll No. | Subsystem Ownership |
|:---:|---|:---:|---|
| 1 | **Abhinav Giri** | Roll No: 01 | Verification & Acceptance Testing |
| 2 | **Akash Deep** | Roll No: 02 | Signal Filtering & Exponential Moving Average |
| 3 | **Aryanandha** | Roll No: 03 | Sensor Node, Physics Model & Fault Injection (Role A) |
| 4 | **Dhanjeet Mishra** | Roll No: 04 | Hysteresis & Alarm State Machine (Role B) |
| 5 | **Harshit Singh** | Roll No: 05 | Watchdog Timer & Stale Data Detection |
| 6 | **Lokendra** | Roll No: 06 | Safe Reset Interlock Service (`/machine/reset`) |
| 7 | **Paramjeet Kumawat** | Roll No: 07 | ROS 2 Diagnostics (`/diagnostics`) |
| 8 | **Ritesh Vivek Kumar** | Roll No: 08 | 3D RViz Digital Twin & Model Markers |
| 9 | **Sunny** | Roll No: 09 | Launch Orchestration, Evidence Logger & CI/CD (Role C) |

---

## Complete Slide-by-Slide Presentation Walkthrough

### Slide 1: Title Slide (Cover Page)
- **Visuals:** Dark blue executive aesthetic, 4-cylinder engine crankshaft & spindle CAD backdrop, team list with roll numbers, faculty supervisor callout.
- **Talking Script:**  
  *"Good morning Dr. K Ponnappa and evaluation committee. Today, our team is presenting our ROS 2 Machine Temperature Monitoring and Alarm System. Rather than building a generic textbook publisher with arbitrary numbers, we designed this project as an industrial cyber-physical digital twin directly protecting the precision machining operations of our 4-cylinder engine crankshaft and piston assembly that we analyzed in our previous manufacturing study."*

---

### Slide 2: Industrial Context & Machining Protection
- **Visuals:** Crankshaft journal finish-turning specifications (Ø50 h5, tolerance -0.011 mm, 600–900 RPM CBN cutting, 5–8 bar flood coolant).
- **Talking Script:**  
  *"In our previous SolidWorks and Fusion 360 machining study, we established that crankshaft main journals must meet an IT5 tolerance of Ø50 h5. During high-speed finish turning at 600 to 900 RPM, friction at the CNC spindle bearings generates intense thermal loads. If flood coolant pressure drops below 5 bar or bearings degrade, thermal expansion causes spindle runout exceeding 12 µm, resulting in scrapped components. Our ROS 2 pipeline provides real-time 10 Hz thermal tracking, vibration filtering, dual-threshold alarm interlocks, and sensor-failure detection to prevent catastrophic thermal runaway."*

---

### Slide 3: System Architecture & ROS 2 Computation Graph
- **Visuals:** 3-Tier ROS 2 graph: Layer 1 (Sensor & Physics), Layer 2 (Monitoring & Filtering), Layer 3 (Industrial Interfaces, GUI, RViz).
- **Talking Script:**  
  *"Our architecture is organized into three clean layers: Layer 1 is the sensor node publishing calibrated temperature readings at 10 Hz over `/machine/temperature`. Layer 2 is the core monitor node that runs the EMA filter, hysteresis state machine, and 1.0 s watchdog timer. Layer 3 includes our industrial extensions: ROS 2 diagnostics on `/diagnostics`, our 3D RViz digital twin marker, and an automated evidence logger."*

---

### Slide 4: Signal Filtering & Exponential Moving Average (EMA)
- **Visuals:** Mathematical formula $y[k] = \alpha \cdot x[k] + (1 - \alpha) \cdot y[k-1]$, table comparing noise attenuation at $\alpha=0.2$ vs pass-through at $\alpha=1.0$.
- **Talking Script:**  
  *"In CNC machining, mechanical cutting vibration and tool chatter introduce high-frequency measurement noise. A naive threshold would trigger false alarms on transient spikes. We implemented an Exponential Moving Average digital low-pass filter with a default smoothing factor of $\alpha=0.2$. This attenuates 89% of high-frequency noise while preserving the true thermodynamic trend of the machine. For automated grading and deterministic verification, $\alpha$ can be set to 1.0 to directly reflect input readings."*

---

### Slide 5: Dual-Threshold Hysteresis & Safe Reset Interlocks
- **Visuals:** Hysteresis state transition diagram: 80°C High threshold, 75°C Low threshold, deadband hold, and the `/machine/reset` service decision tree.
- **Talking Script:**  
  *"A critical requirement in machine safety is preventing 'relay chattering' near boundaries. We implemented dual-threshold hysteresis: the alarm trips at or above 80°C and only clears strictly below 75°C. In the 75°C to 80°C band, the previous alarm state is maintained. Furthermore, our `/machine/reset` service enforces a hardware safety interlock: if an operator attempts a reset at 77°C, the service rejects it. Reset is only permitted once the spindle has safely cooled below 75°C and valid telemetry is flowing."*

---

### Slide 6: Sensor Heartbeat Watchdog & Stale Data Detection
- **Visuals:** Monotonic timer logic, cable disconnect fault injection (`/sensor/set_connected false`), transition to `STALE`.
- **Talking Script:**  
  *"In real manufacturing, sensor wires can break or communication buses can hang. If a monitor continues acting on frozen data, an overheating machine could catch fire. Our monitor runs a 10 Hz watchdog timer comparing monotonic clock timestamps. If no fresh packet arrives for more than 1.0 second, the node immediately logs a warning, switches status to `STALE`, and locks out reset commands. Once the sensor re-establishes communication, normal threshold evaluation automatically resumes."*

---

### Slide 7: Industrial Standards: Diagnostics & Desktop GUI
- **Visuals:** `/diagnostics` topic structure (`DiagnosticArray`), `rqt_robot_monitor` integration, Tkinter desktop dashboard screenshot.
- **Talking Script:**  
  *"To take this project beyond academic requirements, we implemented ROS 2 standard diagnostics on `/diagnostics`, publishing `OK`, `WARN`, and `ERROR` states with structured hardware telemetry. We also built an interactive operator desktop GUI in Tkinter. It gives plant operators a live gauge, a flashing status annunciator, a safe reset button, and one-click fault injection controls for live demonstrations."*

---

### Slide 8: 3D RViz Digital Twin & Automated Evidence Logger
- **Visuals:** 3D RViz spindle marker changing colors (Green < 75°C, Amber 75–80°C, Pulsing Red ≥ 80°C, Gray STALE), 4-panel matplotlib verification plot.
- **Talking Script:**  
  *"To fulfill the project specification requirement for 'installed model files', we developed a 3D digital twin marker publisher in RViz2 that renders the CNC spindle bearing and dynamically updates its RGBA color and pulsing frequency based on machine state. In addition, our automated evidence logger records continuous 10 Hz telemetry to timestamped CSV files and automatically renders publication-grade 4-panel matplotlib charts capturing the complete test timeline."*

---

### Slide 9: Complete Verification Matrix & Boundary Testing
- **Visuals:** Full 11-test verification table with 100% PASS ratings across T01 through T11.
- **Talking Script:**  
  *"Here is our experimental verification table conducted with deterministic parameters ($\alpha=1.0$). We validated all functional behaviors: 74°C NORMAL, 80°C ALARM, 77°C Hysteresis Hold, Reset Rejection at 77°C, Safe Reset at 74°C, Stale transition after 1.0 s silence, and sensor recovery. Furthermore, we verified dynamic parameter boundary rejections: our node strictly rejects $high \le low$ (such as high=70 while low=75), non-positive timeouts, and invalid alpha values."*

---

### Slide 10: Reproducibility, Docker & GitHub Actions CI
- **Visuals:** Dockerfile, `docker compose up --build` command, GitHub Actions CI passing badge, team role mappings (Roles A, B, C).
- **Talking Script:**  
  *"To ensure maximum reproducibility—which carries 10 marks on the evaluation rubric—we containerized the entire pipeline using Docker. Any evaluator can run the system with a single `docker compose up` command. We also configured a continuous integration pipeline using GitHub Actions that automatically builds the package and executes all linters and unit tests on every commit."*

---

### Slide 11: Conclusion & Live Demonstration
- **Visuals:** Summary card, live demo command roadmap, repository link.
- **Talking Script:**  
  *"In conclusion, this project satisfies 100% of the P01 project specifications and expands them with industrial diagnostics, automated evidence generation, 3D visualization, and real-world machining context. We are now ready to demonstrate the live system. Thank you, Dr. K Ponnappa."*

---

## Probable Viva / Defense Questions from Dr. K Ponnappa & Model Answers

### Q1: "Why did you use an Exponential Moving Average (EMA) rather than a simple moving average (SMA)?"
**Answer:**  
*"An EMA requires only $O(1)$ constant memory and a single multiplication per sample ($y[k] = \alpha x[k] + (1-\alpha)y[k-1]$), whereas an SMA requires storing a window buffer of $N$ previous samples. In high-rate embedded sensor applications (10 Hz or higher), EMA minimizes memory footprint and latency while providing smooth exponential attenuation of high-frequency noise."*

### Q2: "Why does your stale watchdog use the ROS monotonic clock rather than the system wall clock?"
**Answer:**  
*"Wall clocks (`time.time()`) can jump forwards or backwards due to NTP time synchronization, leap seconds, or manual adjustments, which can cause spurious stale triggers or failure to detect a timeout. The monotonic clock (`node.get_clock().now()`) is guaranteed to be strictly non-decreasing, ensuring accurate and reliable elapsed time calculation."*

### Q3: "What prevents the reset service from succeeding when the temperature is 76°C?"
**Answer:**  
*"Our `/machine/reset` service callback evaluates `if self.filtered_temperature >= self.low: response.success = False`. Since `low = 75.0°C`, any temperature at or above 75.0°C violates the safe restart interlock. This guarantees the machine cannot be restarted until the spindle has cooled safely below the hysteresis band."*

### Q4: "How does your parameter validation callback prevent race conditions or invalid configurations at runtime?"
**Answer:**  
*"We registered `add_on_set_parameters_callback(self.validate_parameters)`. When an operator calls `ros2 param set`, ROS 2 intercepts the request before applying it. Our validator checks `high > low`, $0 < \alpha \le 1$, and $timeout > 0$. If any condition is violated, it returns `SetParametersResult(successful=False)`, and the node retains its previous valid state without crashing."*

### Q5: "How does this ROS 2 pipeline relate to the 4-cylinder engine crankshaft machining we studied earlier?"
**Answer:**  
*"In our engine assembly project, the crankshaft main journals require an IT5 tolerance fit of Ø50 h5 (-0.011 mm). During high-speed CNC turning (600–900 RPM), spindle bearing friction and potential coolant failure (dropping below 5–8 bar) induce thermal expansion. This ROS 2 system acts as an online condition-monitoring digital twin that detects thermal runaway before thermal deformation ruins the component's geometric tolerances."*
