# SARAS Edge Hardware & Inference Pipeline
**Search And Rescue Autonomous Swarm (SARAS) — Companion Computer Subsystem**  
*Lead: Member 1 (Hardware & Edge ML Lead)*

---

## 1. Overview

This subsystem is the onboard intelligence running directly on the physical quadrotor's companion computer (**Raspberry Pi 4 Model B (4GB/8GB)** or **Raspberry Pi 5 (8GB)**). It interfaces with:
1. **The Physical Flight Controller (Pixhawk 4 / 6C)** via serial MAVLink UART/USB.
2. **The Aerial Perception Sensor (Raspberry Pi Camera Module 3 / HQ or USB V4L2)**.
3. **The Ground Mission Command Server (FastAPI)** over 5GHz Wi-Fi / LTE telemetry uplink.

```
+-------------------------------------------------------------+
|                      PHYSICAL DRONE                         |
|                                                             |
|  +-------------------+              +--------------------+  |
|  | Pixhawk FCU       |  UART MAVLink| Raspberry Pi 4/5   |  |
|  | (PX4 / ArduPilot) |<------------>| Companion Computer |  |
|  +-------------------+  TELEM2      +---------+----------+  |
|                                               ^             |
|                                     CSI/V4L2  |             |
|                             +-----------------+----------+  |
|                             | RPi Camera Module 3 (Sony) |  |
|                             +----------------------------+  |
+-------------------------------------------|-----------------+
                                            | Wi-Fi / Telemetry (HTTP/WS)
                                            v
                              +----------------------------+
                              | SARAS Ground Command Base  |
                              | FastAPI + Swarm Allocation |
                              +----------------------------+
```

---

## 2. Hardware Wiring: Pixhawk to Raspberry Pi

### Pixhawk `TELEM2` to Raspberry Pi GPIO UART Pinout

| Pixhawk TELEM2 Pin | Signal | Raspberry Pi 4/5 Header | RPi Physical Pin |
| :--- | :--- | :--- | :--- |
| **Pin 1 (Red)** | `VCC (+5V)` | *Do NOT connect if powering RPi via dedicated BEC* | — |
| **Pin 2 (Tx)** | `Pixhawk TX` | `GPIO 15 (UART0 RXD)` | **Pin 10** |
| **Pin 3 (Rx)** | `Pixhawk RX` | `GPIO 14 (UART0 TXD)` | **Pin 8** |
| **Pin 4 (CTS)** | `CTS` | *Not connected (flow control disabled)* | — |
| **Pin 5 (RTS)** | `RTS` | *Not connected* | — |
| **Pin 6 (Black)** | `GND` | `Ground` | **Pin 6 or Pin 14** |

> [!IMPORTANT]
> **Logic Level Notice**: Pixhawk TELEM2 operates at 3.3V logic levels, perfectly matching Raspberry Pi GPIO pins. Never connect 5V directly to Raspberry Pi GPIO. Ensure the ground reference (GND) is firmly shared.

### Pixhawk USB Alternative
Alternatively, connect the Pixhawk Micro-USB / Type-C telemetry port directly to a Raspberry Pi USB port. The device will enumerate as `/dev/ttyACM0` with zero wiring complexity.

### Flight Controller Parameter Settings
In **QGroundControl** or **Mission Planner**, verify:
- **PX4**:
  - `MAV_1_CONFIG` = `TELEM2` (or `TELEM 1`)
  - `SER_TEL2_BAUD` = `57600 8N1` (or `921600` for high-rate streams)
  - `MAV_1_MODE` = `Onboard`
  - `MAV_1_RATE` = `10000 B/s`
- **ArduPilot**:
  - `SERIAL2_PROTOCOL` = `2` (MAVLink2)
  - `SERIAL2_BAUD` = `57` (57600 baud)

---

## 3. Raspberry Pi Software Setup (Debian Bookworm 64-bit)

### Step 1: Enable Serial Port & Camera on Raspberry Pi
Run Raspberry Pi Configuration tool:
```bash
sudo raspi-config
```
1. Navigate to **Interface Options -> Serial Port**:
   - *Would you like a login shell to be accessible over serial?* -> **No**
   - *Would you like the serial port hardware to be enabled?* -> **Yes**
2. Navigate to **Interface Options -> Camera** and enable CSI camera.
3. Reboot:
```bash
sudo reboot
```

### Step 2: Install System Dependencies
```bash
sudo apt update && sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-opencv \
    libcamera-dev \
    libatlas-base-dev \
    git
```

### Step 3: Set Up Python Virtual Environment
```bash
python3 -m venv ~/saras_env
source ~/saras_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Running the Subsystems

### A. Run Edge Companion Node (Autonomous Loop)
Executes camera acquisition -> ONNX inference -> MAVLink telemetry fusion -> backend alert push:

```bash
# Using ONNX Runtime on CPU with synthetic camera fallback
python run_edge_node.py --format onnx --camera synthetic

# Using physical USB camera on /dev/video0 and Pixhawk on TELEM2 (/dev/ttyAMA0)
python run_edge_node.py \
    --camera 0 \
    --format onnx \
    --model-path models/yolov8n.onnx \
    --mavlink /dev/ttyAMA0 \
    --baud 57600 \
    --backend http://192.168.1.100:8000
```

### B. Run Empirical Edge ML Benchmark (for IEEE Paper)
Profiles latency distributions, real-time FPS, and memory overhead across runtimes:

```bash
python benchmark/benchmark_inference.py --iterations 100 --threads 4 --format all
```
Outputs:
- **`benchmark/BENCHMARK_REPORT.md`**: Complete Markdown document with IEEE LaTeX tables ready for submission.
- **`benchmark/benchmark_results.csv`**: Raw sample latency timeseries data.

---

## 5. Systemd Auto-Start on Drone Boot

To ensure the companion computer starts detecting and publishing immediately when the drone battery is connected:

Create service file:
```bash
sudo nano /etc/systemd/system/saras-edge.service
```

Paste:
```ini
[Unit]
Description=SARAS Swarm Edge Companion Node
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/saras_swarm_system/edge_hardware
ExecStart=/home/pi/saras_env/bin/python run_edge_node.py --format onnx --mavlink /dev/ttyAMA0 --baud 57600 --backend http://192.168.1.100:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable saras-edge.service
sudo systemctl start saras-edge.service
sudo systemctl status saras-edge.service
```

---

## 6. Directory Structure

```
edge_hardware/
├── config/
│   ├── __init__.py
│   └── edge_config.py            # Centralized edge settings dataclass & env parser
├── inference/
│   ├── __init__.py
│   └── detector.py               # EdgeDetector with ONNX Runtime & Ultralytics YOLOv8
├── camera/
│   ├── __init__.py
│   └── capture.py                # Thread-safe zero-lag CameraStream with auto-reconnect
├── telemetry/
│   ├── __init__.py
│   └── mavlink_client.py         # MAVLink reader, Pixhawk sim, & georeferenced alert packer
├── benchmark/
│   ├── __init__.py
│   ├── benchmark_inference.py    # Empirical latency, FPS, and memory profiling suite
│   ├── BENCHMARK_REPORT.md       # Generated IEEE publication report
│   └── benchmark_results.csv     # Raw profiling dataset
├── models/
│   ├── README.md
│   ├── yolov8n.onnx              # Exported ONNX model
│   └── yolov8n.pt                # PyTorch baseline
├── run_edge_node.py              # Main executable for companion computer
├── requirements.txt              # Companion Python dependencies
└── README.md                     # Hardware & deployment documentation
```
