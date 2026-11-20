# Presentation & Viva Defense Guide
### ROS 2 Based Machine Temperature Monitoring and Alarm System
**Evaluator:** Prof. Sunil Aggarwal  
**Program:** B.Tech Smart Manufacturing, IIITDM Jabalpur  
**Course Level:** P01 Intermediate Specification (100 Marks)  

---

## Front Page Details

### Title
**ROS 2 BASED MACHINE TEMPERATURE MONITORING AND ALARM SYSTEM**  
*A Python-Based Industrial Temperature Monitoring & Autonomous Fault Detection Prototype*

### Presented To
**Prof. Sunil Aggarwal**  
Department of Mechanical / Smart Manufacturing  
Indian Institute of Information Technology, Design and Manufacturing (IIITDM), Jabalpur  

### Presented By (Team of 3)
| Student Name | Roll Number | Project Role (per Spec) | Subsystem Ownership |
|---|:---:|:---:|---|
| **Aryanandha** | **24BSM013** | **Role A** | Sensor simulation node, CNC spindle physics model, fault-injection services, test sequence generator. |
| **Spoorthy** | **24BSM002** | **Role B** | EMA signal filtering, dual-threshold hysteresis state machine, watchdog stale detection, safe reset service (`/machine/reset`). |
| **Devanshu Verma** | **24BSM019** | **Role C** | ROS 2 launch orchestration, parameter management, automated evidence logger (CSV & 4-panel plots), interactive GUI dashboard, Docker & CI/CD. |

---

## Slide-by-Slide Walkthrough (Referencing Your Original PDF)

### Slide 01: Title Slide (Cover Page)
- **Reference in PDF:** Matches Slide 01 of your original PDF.
- **Talking Script:**  
  *"Good morning Prof. Sunil Aggarwal. Today, our team—Aryanandha, Spoorthy, and Devanshu Verma from B.Tech Smart Manufacturing at IIITDM Jabalpur—is presenting our project: ROS 2 Based Machine Temperature Monitoring and Alarm System. In our initial proposal, we outlined a software prototype. Today, we present not just the completed functional prototype, but an industrial digital twin where we have implemented and validated all the future work items proposed in our preliminary study."*

---

### Slide 02: Overheating Needs an Early, Stable Response (`> detect before damage.`)
- **Reference in PDF:** Matches Slide 02 of your original PDF.
- **Talking Script:**  
  *"As established in our problem statement: abnormal machine temperature can cause severe equipment damage, production interruptions, and workplace safety hazards. In precision smart manufacturing, spindle bearing thermal expansion and coolant flow loss degrade tolerances. Our objective is to monitor high-rate temperature data, trigger alarms at a high threshold, safely clear them below a low threshold, detect stale data within 1.0 second, and provide an interlocked reset service."*

---

### Slide 03: Two ROS 2 Nodes Turn Readings into Machine Status
- **Reference in PDF:** Matches Slide 03 of your original PDF.
- **Talking Script:**  
  *"Our architecture consists of two primary ROS 2 nodes connected via standard interfaces. Node 01 is the Simulated Temperature Sensor Node, publishing `sensor_msgs/Temperature` at 10 Hz over `/machine/temperature`. Node 02 is the Temperature Monitoring Node, which applies EMA filtering, evaluates thresholds, detects timeouts, and publishes machine status. The communication graph outputs `/machine/alarm` (`std_msgs/Bool`), `/machine/status` (`std_msgs/String`), and provides the `/machine/reset` (`std_srvs/Trigger`) service."*

---

### Slide 04: Hysteresis Prevents Repeated Alarm Switching
- **Reference in PDF:** Matches Slide 04 of your original PDF.
- **Talking Script:**  
  *"To eliminate contactor chattering near threshold boundaries, our node executes a 3-step pipeline: Receive, Filter, and Compare. We apply an Exponential Moving Average (EMA) low-pass filter:
  $$FilteredTemperature = \alpha \times CurrentReading + (1 - \alpha) \times PreviousFilteredTemperature$$
  At or above 80°C, the alarm activates. In the hysteresis zone between 75°C and 80°C, the system holds its previous state. Strictly below 75°C, the alarm clears. Reset requests are rejected if the machine is at or above 75°C or if telemetry is stale."*

---

### Slide 05: The Prototype is Organized for Repeatable Testing
- **Reference in PDF:** Matches Slide 05 of your original PDF.
- **Talking Script:**  
  *"In our original PDF slide, we noted: 'Intended test behaviours, not automatically verified results.' Today, we have upgraded this into a 100% automatically verified test suite. Using our test-runner script `test_sequence.py` and automated pytest suites, every single boundary condition—from 74°C normal, 80°C alarm, 77°C hysteresis hold, reset rejection, safe reset, to stale timeout and recovery—passes with zero manual intervention."*

---

### Slide 06: Delivering Future Work Today (Part 1: Live Dashboard & 3D Digital Twin)
- **Reference in PDF:** Fulfills Slide 06's bullet: *"Future: integrate a physical temperature sensor and live dashboard"*.
- **Talking Script:**  
  *"In Slide 06 of our original presentation, we identified our first future scope item: a live dashboard. We have built an interactive desktop GUI (`machine_dashboard.py`) in Tkinter. It gives operators real-time digital readouts of raw vs. filtered temperatures, colored status annunciators, a one-click safe reset button, and live fault-injection controls. Furthermore, we integrated a 3D digital twin in RViz2 with dynamic thermal color heatmapping."*

---

### Slide 07: Delivering Future Work Today (Part 2: Telemetry Logger & 4-Panel Verification Plots)
- **Reference in PDF:** Fulfills Slide 06's bullet: *"Future: store readings for history and extend monitoring"*.
- **Talking Script:**  
  *"Our second future scope item was historical data storage. We implemented `evidence_logger.py`, which records continuous 10 Hz telemetry to timestamped CSV files. On test completion, it automatically renders a publication-grade 4-panel matplotlib verification plot displaying the raw vs. filtered temperature curve with shaded alarm bands, the alarm step-function, the status timeline with stale blackout regions, and reset event markers."*

---

### Slide 08: Reproducibility, Docker & GitHub Actions CI
- **Talking Script:**  
  *"For maximum reproducibility—which carries 10 marks on the evaluation rubric—we containerized the entire pipeline using Docker (`docker compose up --build`). We also established a GitHub Actions CI pipeline running automated linting (flake8, pep257) and acceptance tests on every push. All three member roles (A, B, and C) have been strictly realized."*

---

### Slide 09: Conclusion & Live Demonstration
- **Talking Script:**  
  *"In conclusion, this project satisfies 100% of the course requirements and delivers every future enhancement proposed in our preliminary PDF. We are now ready to demonstrate the live system to Prof. Sunil Aggarwal. Thank you."*

---

## Defense & Viva Q&A for Prof. Sunil Aggarwal

### Q1: "Why is Exponential Moving Average (EMA) preferred in smart manufacturing machine monitoring over a simple moving average (SMA)?"
**Answer:**  
*"In real-time embedded sensing, an EMA requires only $O(1)$ memory and a single arithmetic operation per cycle ($y[k] = \alpha x[k] + (1-\alpha)y[k-1]$). An SMA requires maintaining a rolling buffer of $N$ previous samples. EMA achieves effective high-frequency chatter rejection with minimal memory footprint and zero buffer-shifting latency."*

### Q2: "What is the role of hysteresis in industrial machine monitoring?"
**Answer:**  
*"Without hysteresis, if the temperature hovers around 80.0°C (e.g., fluctuating between 79.9°C and 80.1°C due to sensor noise), the alarm would toggle on and off dozens of times per second. This causes relay chattering, electrical wear, and false emergency halts. Hysteresis creates a 5°C deadband (75°C to 80°C) where the current state is latched until a decisive change occurs."*

### Q3: "Why does the `/machine/reset` service reject requests at 76°C even if the alarm was triggered previously?"
**Answer:**  
*"Resetting an alarm while the temperature is at 76°C would create a dangerous false-sense of safety because the spindle is still in an elevated, thermally vulnerable state. By enforcing `filtered_temp < 75.0°C`, the service guarantees that machine restart is physically locked out until the equipment has cooled safely into its normal operating zone."*

### Q4: "How does your implementation detect a sensor disconnection, and what happens to the reset service during that time?"
**Answer:**  
*"Our monitor uses a 10 Hz periodic timer that computes elapsed time using the ROS monotonic clock: `elapsed = (now() - last_received).nanoseconds / 1e9`. If `elapsed > 1.0 s`, the node transitions `status` to `STALE`. While in `STALE`, all `/machine/reset` requests are immediately rejected (`success=False`) because the controller cannot verify physical safety on absent data."*
