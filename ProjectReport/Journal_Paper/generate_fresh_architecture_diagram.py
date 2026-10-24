"""
Generate a 100% fresh, publication-quality System Architecture Diagram for
'SWARM SYSTEM FOR DISASTER RESPONSE' using MATLAB design aesthetics.
Zero assets from previous papers.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

output_dir = r"d:\DEV\Final Year Project\ProjectReport\Journal_Paper\assets"
os.makedirs(output_dir, exist_ok=True)

fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Background container
bg = patches.FancyBboxPatch((1, 1), 98, 98, boxstyle="round,pad=0.5",
                            facecolor='#FAFBFC', edgecolor='#C0C8D0', linewidth=1.5)
ax.add_patch(bg)

# Title Banner
title_box = patches.FancyBboxPatch((3, 90), 94, 8, boxstyle="round,pad=0.3",
                                  facecolor='#003366', edgecolor='none')
ax.add_patch(title_box)
ax.text(50, 94, "SWARM SYSTEM FOR DISASTER RESPONSE: AUTONOMOUS EDGE ARCHITECTURE",
        ha='center', va='center', color='white', fontsize=12, fontweight='bold', fontname='sans-serif')

# Column 1: Onboard Hardware & Sensory Layer
c1 = patches.FancyBboxPatch((3, 8), 28, 78, boxstyle="round,pad=0.4",
                            facecolor='#EEF3F8', edgecolor='#0072BD', linewidth=1.8)
ax.add_patch(c1)
ax.text(17, 82, "1. HARDWARE & SENSING", ha='center', va='center',
        color='#003366', fontsize=10.5, fontweight='bold')

items_c1 = [
    ("Holybro S500 Quadrotor", "480mm carbon frame, 14.8V 5200mAh LiPo"),
    ("Holybro Pixhawk 4", "STM32F765 216MHz, PX4 v1.14 Autopilot"),
    ("Sony IMX219 Camera", "8MP 1080p@30FPS, Nadir/Oblique Mount"),
    ("U-blox M8N GNSS & IMU", "Dual EKF2 position, velocity & attitude"),
    ("ESP32-WROOM-32U", "2.4 GHz ESP-NOW Ad-Hoc Peer-to-Peer Mesh")
]
y_pos = 71
for title, desc in items_c1:
    b = patches.FancyBboxPatch((4.5, y_pos - 4.5), 25, 9.5, boxstyle="round,pad=0.2",
                               facecolor='#FFFFFF', edgecolor='#B0C4DE', linewidth=1.2)
    ax.add_patch(b)
    ax.text(6, y_pos + 2, title, ha='left', va='center', color='#003366', fontsize=8.5, fontweight='bold')
    ax.text(6, y_pos - 2, desc, ha='left', va='center', color='#555555', fontsize=7.2)
    y_pos -= 14

# Column 2: Companion Computer (ROS 2 Humble & Edge AI)
c2 = patches.FancyBboxPatch((34, 8), 34, 78, boxstyle="round,pad=0.4",
                            facecolor='#FFF6EE', edgecolor='#D9531F', linewidth=1.8)
ax.add_patch(c2)
ax.text(51, 82, "2. EDGE AUTONOMY (Raspberry Pi 4)", ha='center', va='center',
        color='#B23C00', fontsize=10.5, fontweight='bold')

items_c2 = [
    ("INT8 YOLOv8 Inference Engine", "Quantized ONNX/NCNN (16.8 FPS, 81.6% mAP@0.5)"),
    ("Pinhole Geolocation Projection", "Pixel-to-World camera ray intersection (< 2.0m RMS)"),
    ("Distributed Market Auctioneer", "Utility bidding consensus, dynamic Voronoi sectoring"),
    ("Gossip Heartbeat Protocol", "5 Hz neighbor state broadcast, 400ms crash timeout")
]
y_pos = 71
for title, desc in items_c2:
    b = patches.FancyBboxPatch((35.5, y_pos - 4.5), 31, 10.5, boxstyle="round,pad=0.2",
                               facecolor='#FFFFFF', edgecolor='#F0C29F', linewidth=1.2)
    ax.add_patch(b)
    ax.text(37, y_pos + 2.2, title, ha='left', va='center', color='#B23C00', fontsize=8.5, fontweight='bold')
    ax.text(37, y_pos - 2.2, desc, ha='left', va='center', color='#555555', fontsize=7.2)
    y_pos -= 15.5

# Column 3: Swarm Communication & Mission Execution
c3 = patches.FancyBboxPatch((71, 8), 26, 78, boxstyle="round,pad=0.4",
                            facecolor='#F3EEF8', edgecolor='#7E2F8E', linewidth=1.8)
ax.add_patch(c3)
ax.text(84, 82, "3. SWARM COLLABORATION", ha='center', va='center',
        color='#5C1D6B', fontsize=10.5, fontweight='bold')

items_c3 = [
    ("Ad-Hoc Swarm Mesh", "Decentralized P2P packet exchange, zero single-point failure"),
    ("Dynamic Task Allocation", "Parallel lawnmower sweeps, 3.4% path overlap in 500x500m"),
    ("Self-Healing Fault Recovery", "Sub-420 ms re-auction upon node crash, 99.8% recovery"),
    ("PX4 Offboard Control", "micro-XRCE-DDS velocity & trajectory setpoints")
]
y_pos = 71
for title, desc in items_c3:
    b = patches.FancyBboxPatch((72.5, y_pos - 4.5), 23, 10.5, boxstyle="round,pad=0.2",
                               facecolor='#FFFFFF', edgecolor='#D5BDE5', linewidth=1.2)
    ax.add_patch(b)
    ax.text(74, y_pos + 2.2, title, ha='left', va='center', color='#5C1D6B', fontsize=8.5, fontweight='bold')
    ax.text(74, y_pos - 2.2, desc, ha='left', va='center', color='#555555', fontsize=7.2)
    y_pos -= 15.5

# Connecting Flow Arrows
arrow_style = dict(facecolor='#003366', edgecolor='#003366', width=2, head_width=6, head_length=5)
ax.annotate('', xy=(34, 50), xytext=(31, 50),
            arrowprops=dict(facecolor='#0072BD', edgecolor='#0072BD', arrowstyle="->", lw=2.5))
ax.annotate('', xy=(71, 50), xytext=(68, 50),
            arrowprops=dict(facecolor='#D9531F', edgecolor='#D9531F', arrowstyle="->", lw=2.5))

# Footer metadata
ax.text(50, 4, "SARAS Swarm System Framework | 100% Custom Implementation | AJCE B.Tech Computer Science & Engineering",
        ha='center', va='center', color='#777777', fontsize=8, fontname='sans-serif')

out_path = os.path.join(output_dir, "matlab_swarm_system_architecture.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Fresh system architecture generated at: {out_path}")
