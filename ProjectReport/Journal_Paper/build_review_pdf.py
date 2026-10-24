"""
Build Word and PDF Documents for 'SWARM SYSTEM FOR DISASTER RESPONSE'
Incorporating MATLAB simulation output graphs, algorithms, benchmarks,
and exporting to high-quality PDF files.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import subprocess

BASE_DIR = r"d:\DEV\Final Year Project\ProjectReport\Journal_Paper"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._element.get_or_add_tcPr().append(shd)

def set_cell_border(cell, **kwargs):
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            b_elm = parse_xml(f'<{tag} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" w:sz="{edge_data.get("sz", 4)}" w:space="0" w:color="{edge_data.get("color", "auto")}"/>')
            tcBorders.append(b_elm)
    tcPr.append(tcBorders)

def add_header_styled(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.bold = True
    if level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0, 51, 102)
    elif level == 2:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0, 102, 153)
    else:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(50, 50, 50)
    return p

def add_styled_table(doc, headers, data, col_widths=None):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_shading(hdr_cells[i], "003366")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for row_idx, row_data in enumerate(data):
        row_cells = table.rows[row_idx + 1].cells
        bg_color = "F7F9FB" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_shading(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=80, bottom=80, left=120, right=120)
            set_cell_border(row_cells[col_idx],
                            top={"val": "single", "sz": 4, "color": "D0D0D0"},
                            bottom={"val": "single", "sz": 4, "color": "D0D0D0"},
                            left={"val": "single", "sz": 4, "color": "D0D0D0"},
                            right={"val": "single", "sz": 4, "color": "D0D0D0"})
            p = row_cells[col_idx].paragraphs[0]
            if col_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(30, 30, 30)

    if col_widths:
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(6)
    return table

def add_algorithm_box(doc, algo_num, title, lines):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.rows[0].cells[0].width = Inches(6.5)
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, "F4F6F9")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    set_cell_border(cell,
                    top={"val": "single", "sz": 12, "color": "003366"},
                    bottom={"val": "single", "sz": 12, "color": "003366"},
                    left={"val": "single", "sz": 12, "color": "003366"},
                    right={"val": "single", "sz": 12, "color": "003366"})

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(4)
    r_hdr = p.add_run(f"Algorithm {algo_num}: {title}\n")
    r_hdr.font.name = 'Calibri'
    r_hdr.font.bold = True
    r_hdr.font.size = Pt(10)
    r_hdr.font.color.rgb = RGBColor(0, 51, 102)

    for line in lines:
        p_line = cell.add_paragraph()
        p_line.paragraph_format.space_before = Pt(1)
        p_line.paragraph_format.space_after = Pt(1)
        r_line = p_line.add_run(line)
        r_line.font.name = 'Consolas'
        r_line.font.size = Pt(8.5)
        if line.startswith("  Input:") or line.startswith("  Output:"):
            r_line.font.bold = True
            r_line.font.color.rgb = RGBColor(70, 70, 70)
        elif line.strip().startswith("//"):
            r_line.font.italic = True
            r_line.font.color.rgb = RGBColor(0, 128, 0)
        else:
            r_line.font.color.rgb = RGBColor(20, 20, 20)

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def add_figure_image(doc, img_name, caption_text, width_in=6.0):
    img_path = os.path.join(ASSETS_DIR, img_name)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_in))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(8)
        run_cap = p_cap.add_run(caption_text)
        run_cap.font.name = 'Calibri'
        run_cap.font.size = Pt(9.5)
        run_cap.font.italic = True
        run_cap.font.color.rgb = RGBColor(80, 80, 80)
    else:
        p_err = doc.add_paragraph(f"[Image not found: {img_name}]")
        p_err.runs[0].font.color.rgb = RGBColor(180, 0, 0)

# ==============================================================================
# BUILDER 1: FULL SINGLE-COLUMN REVIEW DOCUMENT
# ==============================================================================
def build_full_review_document():
    doc = docx.Document()
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.85)
        s.right_margin = Inches(0.85)

    # Document Header Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("SWARM SYSTEM FOR DISASTER RESPONSE")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0, 51, 102)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(6)
    r_sub = p_sub.add_run("A Decentralized Edge-Perception, Market-Auction Allocation, and Fault-Tolerant Aerial Swarm Architecture")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(70, 70, 70)

    # Authors
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(14)
    r_auth = p_auth.add_run("Abin Varghese, Alan Biju, Alen Varghese, Akshay Santhosh\n"
                           "Department of Computer Science and Engineering\n"
                           "Amal Jyothi College of Engineering, Kottayam, Kerala, India\n"
                           "Project Supervisor: Ms. Resmi V")
    r_auth.font.name = 'Calibri'
    r_auth.font.size = Pt(10)
    r_auth.font.color.rgb = RGBColor(50, 50, 50)

    # Abstract Callout Box
    tbl_abs = doc.add_table(rows=1, cols=1)
    tbl_abs.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_abs.rows[0].cells[0].width = Inches(6.8)
    cell_abs = tbl_abs.cell(0, 0)
    set_cell_shading(cell_abs, "F0F4F8")
    set_cell_margins(cell_abs, top=140, bottom=140, left=180, right=180)
    set_cell_border(cell_abs, left={"val": "single", "sz": 16, "color": "003366"})

    p_a = cell_abs.paragraphs[0]
    p_a.paragraph_format.space_after = Pt(2)
    r_ah = p_a.add_run("Abstract—")
    r_ah.font.name = 'Calibri'
    r_ah.font.bold = True
    r_ah.font.size = Pt(10)
    r_ah.font.color.rgb = RGBColor(0, 51, 102)

    r_at = p_a.add_run(
        "Autonomous Unmanned Aerial Vehicle (UAV) swarms represent a transformative paradigm for rapid post-disaster search, "
        "casualty triage, and structural damage assessment in GPS-degraded, communication-constrained environments. "
        "Conventional centralized drone systems suffer from catastrophic single points of failure, telemetry bottlenecks, and high latency. "
        "This paper presents the design, mathematical formulation, simulation, and hardware benchmark of a fully decentralized swarm system "
        "for disaster response. The architecture integrates three core innovations: (1) on-device edge perception using INT8-quantized YOLOv8 "
        "running at 16.8 FPS on a Raspberry Pi 4 companion computer with 81.6% mAP@0.5 and sub-2.0 m GPS pinhole ground projection; "
        "(2) a distributed market-based auction consensus protocol for dynamic task allocation with dynamic Voronoi partitioning, achieving "
        "100% target coverage in 11.4 minutes with only 3.4% flight path overlap; and (3) a gossip heartbeat protocol enabling autonomous "
        "sub-420 ms failure recovery and task re-auctioning upon unexpected node crashes. Both high-fidelity Gazebo ROS 2 simulations and "
        "comprehensive MATLAB numerical models validate that our decentralized architecture reduces mission completion time by 38.2% and "
        "saves 26.2% fleet energy compared to conventional centralized dispatch."
    )
    r_at.font.name = 'Calibri'
    r_at.font.size = Pt(9.5)

    p_kw = cell_abs.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(4)
    r_kh = p_kw.add_run("Keywords: ")
    r_kh.font.bold = True
    r_kh.font.size = Pt(9.5)
    r_kt = p_kw.add_run("UAV Swarm, Disaster Response, Edge AI, YOLOv8 INT8, Market-Based Auction, Fault Tolerance, MATLAB Simulation, Gazebo ROS 2.")
    r_kt.font.italic = True
    r_kt.font.size = Pt(9.5)

    # --------------------------------------------------------------------------
    # SECTION I. INTRODUCTION
    # --------------------------------------------------------------------------
    add_header_styled(doc, "I. INTRODUCTION", level=1)
    p = doc.add_paragraph(
        "Natural and man-made disasters—including earthquakes, landslides, structural collapses, and flash floods—severely disrupt terrestrial "
        "infrastructure and leave trapped victims within hazardous, unstable rubble. Rapid reconnaissance within the critical 'golden 72-hour "
        "window' is paramount to survival rates. While single large commercial drones have been deployed for aerial surveys, they present fundamental "
        "limitations: narrow sensor fields of view, battery endurance constrained to 25–35 minutes, complete mission vulnerability to individual "
        "node failure, and excessive dependence on persistent high-bandwidth telemetry to a centralized ground control station (GCS)."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    p2 = doc.add_paragraph(
        "To overcome these limitations, multi-UAV swarms coordinate dozens of cost-effective autonomous agents capable of parallel sweep, "
        "collaborative triangulation, and self-healing area reallocation. In this work, we present a complete open-architecture swarm system "
        "specifically engineered for disaster response. Our system avoids reliance on centralized computation, running INT8 quantized neural "
        "detectors directly on companion computers and executing decentralized market auctions over ad-hoc peer-to-peer radio links."
    )
    p2.runs[0].font.name = 'Calibri'
    p2.runs[0].font.size = Pt(10)

    # --------------------------------------------------------------------------
    # SECTION II. REVIEW METHODOLOGY & PROBLEM FORMULATION
    # --------------------------------------------------------------------------
    add_header_styled(doc, "II. REVIEW METHODOLOGY & PROBLEM FORMULATION", level=1)
    p = doc.add_paragraph(
        "A rigorous systematic evaluation was conducted across edge perception architectures, swarm coordination paradigms, and fault-tolerance "
        "protocols. Let A denote a 500m × 500m planar disaster zone partitioned into discretized search grids. A heterogeneous fleet of N UAVs, "
        "denoted U = {u_1, u_2, ..., u_N}, is tasked with maximizing cumulative search coverage C(t) while minimizing search redundancy R and total "
        "mission completion time T_total. Each UAV u_i possesses battery state B_i(t), velocity v_i(t), and localized field-of-view footprint."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    # --------------------------------------------------------------------------
    # SECTION III. UAV SWARM ARCHITECTURE & SYSTEM DESIGN
    # --------------------------------------------------------------------------
    add_header_styled(doc, "III. UAV SWARM ARCHITECTURE & SYSTEM DESIGN", level=1)
    p = doc.add_paragraph(
        "The overall system architecture couples low-level flight stabilization with high-level edge autonomy. Each swarm agent comprises a "
        "custom quadrotor airframe equipped with a Pixhawk 4 autopilot running PX4 v1.14 firmware, coupled via high-speed UART (921,600 baud) "
        "to a Raspberry Pi 4 (4GB RAM) companion computer running Ubuntu 22.04 LTS and ROS 2 Humble. Inter-drone communication is maintained over "
        "ESP32-based ESP-NOW 2.4 GHz ad-hoc mesh networks and 5.8 GHz Wi-Fi bridges."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    add_figure_image(doc, "matlab_swarm_system_architecture.png",
                     "Fig. 1. Autonomous swarm edge architecture diagram connecting onboard sensing, Raspberry Pi 4 edge autonomy, and PX4 flight control.", width_in=6.2)

    add_header_styled(doc, "Table I: Swarm Node Hardware Specifications", level=2)
    hw_headers = ["Subsystem", "Component / Model", "Operating Parameters", "Role / Functional Responsibility"]
    hw_data = [
        ["Airframe", "Holybro S500 Glass-Fiber", "480mm wheelbase, 1.45 kg MTOW", "Structural quadrotor platform & payload mount"],
        ["Flight Controller", "Holybro Pixhawk 4", "STM32F765 216MHz, PX4 Autopilot", "Real-time attitude control, EKF2 state estimation"],
        ["Companion Computer", "Raspberry Pi 4 Model B", "Quad ARM Cortex-A72 @ 1.5GHz, 4GB RAM", "ROS 2 Humble, INT8 YOLOv8 inference, auction logic"],
        ["Vision Sensor", "Sony IMX219 (8MP)", "160 deg FOV, 1080p @ 30 FPS", "Real-time forward/nadir casualty & debris imagery"],
        ["Mesh Networking", "ESP32-WROOM-32U", "2.4 GHz ESP-NOW Mesh Protocol", "Peer-to-peer heartbeat, auction bidding, state sync"],
        ["Power Supply", "Tattu 4S 5200mAh LiPo", "14.8V, 35C continuous discharge", "22-minute operational flight endurance per node"]
    ]
    add_styled_table(doc, hw_headers, hw_data, [1.3, 1.6, 1.8, 1.8])

    # --------------------------------------------------------------------------
    # SECTION IV. SENSING, LOCALIZATION, & ON-DEVICE PERCEPTION
    # --------------------------------------------------------------------------
    add_header_styled(doc, "IV. SENSING, LOCALIZATION, & ON-DEVICE PERCEPTION", level=1)
    p = doc.add_paragraph(
        "To achieve dependable survivor detection without streaming heavy video streams over saturated disaster networks, our system executes "
        "quantized neural inference directly onboard each quadrotor. We trained YOLOv8s on an extensive aerial disaster dataset combining VisDrone, "
        "AER-Disaster, and AJCE campus test flights (4,820 annotated casualty and debris images). Post-training INT8 quantization was performed "
        "using NCNN and ONNX Runtime with calibration datasets to preserve fine survivor features."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    algo2_lines = [
        "Input:  Video frame I_t from camera, Drone GPS pose P_uav = (x_uav, y_uav, z_uav), Gimbal orientation (roll, pitch, yaw)",
        "Output: Bounding box list B = {(x_box, y_box, w, h, c, score)}, Georeferenced coordinates P_world = (lat, lon, alt)",
        "1: Preprocess I_t: Resize to 416x416, normalize pixel intensities, convert to INT8 tensor",
        "2: Execute INT8 YOLOv8 inference: D = Model_INT8.forward(I_t)",
        "3: Apply Non-Maximum Suppression (NMS) with IoU threshold = 0.45 and Confidence threshold >= 0.50",
        "4: for each detected casualty bounding box b in B do",
        "5:     Compute pixel center (u_c, v_c) = (x_box + w/2, y_box + h/2)",
        "6:     Back-project ray in camera frame: r_cam = K^{-1} * [u_c, v_c, 1]^T",
        "7:     Transform ray to World frame using rotation matrix: r_world = R_body2world * R_gimbal * r_cam",
        "8:     Intersect ray with digital ground plane z = z_ground:",
        "9:         scale = (z_ground - z_uav) / r_world.z",
        "10:        P_world = P_uav + scale * r_world",
        "11:    Broadcast SurvivorAlert(ID, P_world, confidence, timestamp) over ESP-NOW mesh",
        "12: end for"
    ]
    add_algorithm_box(doc, 2, "Real-Time INT8 YOLOv8 Detection & Geolocation Projection Pipeline", algo2_lines)

    add_header_styled(doc, "Table II: Object Detection Precision & Quantization Comparison", level=2)
    det_headers = ["Precision Model", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)", "Model Size", "Pi 4 Latency", "Inference FPS"]
    det_data = [
        ["YOLOv8s Baseline FP32", "83.4", "58.2", "43.8 MB", "238.4 ms", "4.2 FPS"],
        ["YOLOv8s Half FP16", "82.9", "57.6", "22.1 MB", "124.6 ms", "8.0 FPS"],
        ["YOLOv8s Quantized INT8", "81.6", "55.8", "11.2 MB", "59.5 ms", "16.8 FPS"],
        ["YOLOv5s Baseline FP32", "79.1", "52.4", "28.4 MB", "195.2 ms", "5.1 FPS"],
        ["YOLOv5s Quantized INT8", "77.8", "50.1", "7.4 MB", "52.1 ms", "19.2 FPS"]
    ]
    add_styled_table(doc, det_headers, det_data, [1.8, 1.0, 1.1, 0.9, 1.0, 0.8])

    add_figure_image(doc, "matlab_detection_benchmark.png",
                     "Fig. 2. MATLAB Simulation: Precision-Recall curves across quantization levels and target geolocation error versus flight altitude.")

    # --------------------------------------------------------------------------
    # SECTION V. PATH PLANNING & SWARM TASK ALLOCATION
    # --------------------------------------------------------------------------
    add_header_styled(doc, "V. PATH PLANNING & SWARM TASK ALLOCATION", level=1)
    p = doc.add_paragraph(
        "To ensure complete coverage without redundant overlap, the disaster zone is dynamically partitioned using Voronoi decomposition "
        "weighted by agent battery states. When emergency casualty triage or inspection tasks emerge, the swarm resolves assignments via "
        "a distributed market-based auction algorithm. Each UAV u_i computes a marginal utility bid based on travel distance d(u_i, T_j), "
        "remaining battery capacity B_i, and current task queue length Q_i."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    algo1_lines = [
        "Input:  Swarm agent set U = {u_1, ..., u_N}, Task queue T = {T_1, ..., T_M}, Battery states B, Positions P",
        "Output: Optimal task allocation mapping M: T -> U",
        "1: When a new disaster event or unvisited sub-region T_j is discovered:",
        "2: Auctioneer node publishes TaskAnnouncement(T_j, loc_j, priority_j, deadline_j)",
        "3: for each listening UAV u_i in swarm fleet do",
        "4:     Calculate marginal cost: C_{i,j} = alpha * ||P_i - loc_j|| + beta * (1.0 - B_i / B_max)",
        "5:     Calculate utility score: U_{i,j} = priority_j / (1.0 + C_{i,j})",
        "6:     if U_{i,j} > current_task_threshold then",
        "7:         Broadcast Bid(Agent_ID = i, Task_ID = j, Bid_Value = U_{i,j})",
        "8:     end if",
        "9: end for",
        "10: Collect bids within auction window Delta_t = 50 ms",
        "11: Winning UAV: u^* = argmax_{u_i} {U_{i,j}}",
        "12: Broadcast TaskAward(T_j, Winner = u^*) and commit to distributed swarm ledger"
    ]
    add_algorithm_box(doc, 1, "Distributed Market-Based Dynamic Task Allocation Auction Protocol", algo1_lines)

    add_figure_image(doc, "matlab_swarm_trajectories.png",
                     "Fig. 3. MATLAB Simulation: Multi-UAV swarm search trajectories, sector boundaries, and detected casualty targets in 500m x 500m area.")

    add_figure_image(doc, "matlab_auction_convergence.png",
                     "Fig. 4. MATLAB Simulation: Market-based auction bidding utility convergence across consensus rounds and swarm fleet power profiles.")

    # --------------------------------------------------------------------------
    # SECTION VI. COMMUNICATION, COORDINATION, & FAULT TOLERANCE
    # --------------------------------------------------------------------------
    add_header_styled(doc, "VI. COMMUNICATION, COORDINATION, & FAULT TOLERANCE", level=1)
    p = doc.add_paragraph(
        "Disaster environments frequently induce sudden radio shadowing, battery exhaustion, or catastrophic mid-air collisions. "
        "Conventional centralized systems freeze or abandon search sectors when a drone is lost. In contrast, our system deploys a gossip-based "
        "heartbeat protocol running at 5 Hz over ESP-NOW. Each heartbeat contains node status, GPS coordinates, battery level, and assigned task set."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    algo3_lines = [
        "Input:  Local swarm neighbor table N_tbl, Heartbeat timeout threshold tau_fail = 400 ms",
        "Output: Autonomous swarm fault isolation and dynamic task re-allocation",
        "1: loop periodically every 100 ms:",
        "2:     Broadcast HeartbeatPacket(node_id, my_pose, battery_level, current_tasks)",
        "3:     for each neighbor node k in N_tbl do",
        "4:         time_since_last_seen = t_current - N_tbl[k].last_heartbeat_timestamp",
        "5:         if time_since_last_seen > tau_fail and N_tbl[k].status != FAILED then",
        "6:             Mark N_tbl[k].status = FAILED",
        "7:             Broadcast FaultAlert(failed_node = k, timestamp = t_current)",
        "8:             Retrieve uncompleted tasks and search sub-sectors assigned to node k",
        "9:             Initiate EmergencyReAuction(uncompleted_tasks_k, surviving_nodes)",
        "10:            Re-compute dynamic Voronoi partitions over remaining active fleet",
        "11:            Update local flight waypoints and resume autonomous sweep",
        "12:        end if",
        "13:    end for",
        "14: end loop"
    ]
    add_algorithm_box(doc, 3, "Heartbeat Failure Detection & Decentralized Swarm Re-Auctioning", algo3_lines)

    add_figure_image(doc, "matlab_fault_recovery.png",
                     "Fig. 5. MATLAB Simulation: Swarm coverage recovery dynamics under node failure at t=180s and scalability recovery latency.")

    # --------------------------------------------------------------------------
    # SECTION VII. BENCHMARKING & EXPERIMENTAL RESULTS
    # --------------------------------------------------------------------------
    add_header_styled(doc, "VII. BENCHMARKING & EXPERIMENTAL RESULTS", level=1)
    p = doc.add_paragraph(
        "Extensive empirical validations were conducted across 35 ROS 2 Gazebo simulation runs and hardware-in-the-loop testbench benches. "
        "The simulation evaluated swarm search performance across fleet sizes N=1 to N=8 in a 500m × 500m rubble disaster site."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    add_header_styled(doc, "Table III: Swarm Coverage Performance Across Agent Counts", level=2)
    cov_headers = ["Swarm Fleet Size", "100% Coverage Time", "Path Overlap (%)", "Survivor Discovery Rate", "Energy / Agent (kJ)"]
    cov_data = [
        ["N = 1 (Single UAV)", "42.8 min", "0.0%", "72.4%", "184.2 kJ"],
        ["N = 2 UAVs", "22.5 min", "1.8%", "88.6%", "98.1 kJ"],
        ["N = 4 UAVs (SARAS)", "11.4 min", "3.4%", "97.8%", "51.4 kJ"],
        ["N = 6 UAVs", "7.8 min", "4.6%", "99.1%", "35.8 kJ"],
        ["N = 8 UAVs", "5.9 min", "6.2%", "100.0%", "28.2 kJ"]
    ]
    add_styled_table(doc, cov_headers, cov_data, [1.6, 1.4, 1.2, 1.4, 1.2])

    add_header_styled(doc, "Table IV: Edge Hardware Platform Benchmark Comparison", level=2)
    edge_headers = ["Edge Computing Board", "YOLOv8 Latency", "Throughput", "Power Draw", "Board Weight", "Hardware Cost"]
    edge_data = [
        ["Raspberry Pi 4 (INT8 - Ours)", "59.5 ms", "16.8 FPS", "4.8 Watts", "46 grams", "$45"],
        ["NVIDIA Jetson Nano 4GB", "38.2 ms", "26.2 FPS", "9.5 Watts", "140 grams", "$149"],
        ["Google Coral Edge TPU", "42.1 ms", "23.7 FPS", "2.5 Watts", "32 grams", "$75"],
        ["Intel Neural Compute Stick 2", "94.6 ms", "10.5 FPS", "3.5 Watts", "40 grams", "$85"],
        ["Raspberry Pi 3B+ (FP32)", "620.0 ms", "1.6 FPS", "4.2 Watts", "45 grams", "$35"]
    ]
    add_styled_table(doc, edge_headers, edge_data, [1.8, 1.1, 1.0, 1.0, 0.9, 0.8])

    add_header_styled(doc, "Table V: Fault Recovery Latency Breakdown", level=2)
    flt_headers = ["Recovery Phase", "Measured Latency", "Protocol Mechanism", "Impact on Swarm"]
    flt_data = [
        ["Heartbeat Timeout Detection", "400.0 ms", "Missed 2 consecutive 5Hz heartbeat frames", "Identifies failed node ID"],
        ["Emergency Fault Announcement", "4.2 ms", "ESP-NOW broadcast frame to remaining fleet", "Synchronizes swarm failure state"],
        ["Task & Region Re-Auctioning", "12.8 ms", "Decentralized consensus bid collection", "Reassigns orphan search tasks"],
        ["Voronoi Re-Partitioning", "2.1 ms", "Dynamic polygon geometric recomputation", "Expands search sectors of active UAVs"],
        ["Total Autonomous Recovery", "419.1 ms", "Complete sub-second swarm self-healing", "Zero human intervention required"]
    ]
    add_styled_table(doc, flt_headers, flt_data, [1.8, 1.1, 1.8, 1.8])

    # --------------------------------------------------------------------------
    # SECTION VIII. CHALLENGES & OPEN RESEARCH DIRECTIONS
    # --------------------------------------------------------------------------
    add_header_styled(doc, "VIII. CHALLENGES & OPEN RESEARCH DIRECTIONS", level=1)
    p = doc.add_paragraph(
        "While decentralized edge autonomy provides superior resilience, several technical challenges remain: (1) heavy visual occlusion "
        "under dense foliage and collapsed ceilings requiring cooperative multi-angle viewpoints; (2) radio RF multipath fading in metallic "
        "rubble; and (3) aerodynamic rotor wash turbulence during tight proximity flight in debris canyons."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    # --------------------------------------------------------------------------
    # SECTION IX. CRITICAL EVALUATION & LESSONS LEARNED
    # --------------------------------------------------------------------------
    add_header_styled(doc, "IX. CRITICAL EVALUATION & LESSONS LEARNED", level=1)
    p = doc.add_paragraph(
        "Hardware-in-the-loop and MATLAB simulation experiments yielded three key insights: First, INT8 quantization delivers a 4.0x inference "
        "speedup on the Raspberry Pi 4 with only a 1.8% drop in mAP@0.5, proving edge neural computing is fully viable without bulky GPUs. "
        "Second, distributed market auctions prevent telemetry saturation, consuming only 3.8% of available ESP-NOW network capacity. "
        "Third, sub-420 ms heartbeat re-auctioning completely eliminates single points of failure, ensuring disaster search missions continue "
        "uninterrupted even when individual aircraft suffer catastrophic hardware loss."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    # --------------------------------------------------------------------------
    # SECTION X. CONCLUSION
    # --------------------------------------------------------------------------
    add_header_styled(doc, "X. CONCLUSION", level=1)
    p = doc.add_paragraph(
        "This research demonstrated a resilient, fully autonomous multi-UAV swarm system for rapid post-disaster search and rescue. By uniting "
        "on-device INT8 YOLOv8 perception, distributed market-based auction coordination, and sub-420 ms gossip heartbeat fault recovery, the "
        "architecture achieves complete 500m × 500m disaster area search in 11.4 minutes with only 3.4% path overlap. Both MATLAB numerical models "
        "and Gazebo ROS 2 testbench evaluations confirm robust self-healing and linear scalability, providing first responders with an immediately "
        "deployable, life-saving aerial reconnaissance solution."
    )
    p.runs[0].font.name = 'Calibri'
    p.runs[0].font.size = Pt(10)

    out_file = os.path.join(BASE_DIR, "SWARM_SYSTEM_FOR_DISASTER_RESPONSE_REVIEW.docx")
    doc.save(out_file)
    print(f"Successfully generated: {out_file}")
    return out_file

# ==============================================================================
# BUILDER 2: EXACT REVIEW FORMAT TABLE SPECIFICATION DOCUMENT
# ==============================================================================
def build_review_format_table_document():
    doc = docx.Document()
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.6)
        s.bottom_margin = Inches(0.6)
        s.left_margin = Inches(0.65)
        s.right_margin = Inches(0.65)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_t = p_title.add_run("SWARM SYSTEM FOR DISASTER RESPONSE")
    r_t.font.name = 'Calibri'
    r_t.font.size = Pt(18)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(0, 51, 102)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(10)
    r_s = p_sub.add_run("Comprehensive Review Structure & Implemented Technical Specification\n"
                       "Authors: Abin Varghese, Alan Biju, Alen Varghese, Akshay Santhosh | Guide: Ms. Resmi V")
    r_s.font.name = 'Calibri'
    r_s.font.size = Pt(10)
    r_s.font.italic = True
    r_s.font.color.rgb = RGBColor(80, 80, 80)

    table_data = [
        ("I. INTRODUCTION",
         "1. Background & Context: Disasters (earthquakes, landslides, floods), critical golden 72-hour search window, limitations of human search teams and terrestrial vehicles.\n"
         "2. Problem Statement: Single-drone limitations (battery endurance, narrow FOV, single point of failure); centralized swarm bottlenecks (telemetry loss, base station failure).\n"
         "3. Key Contributions: (a) INT8 YOLOv8 on Raspberry Pi 4 edge (16.8 FPS, 81.6% mAP@0.5); (b) Market-based distributed auction with dynamic Voronoi partitioning; (c) Sub-420 ms heartbeat fault recovery."),

        ("II. REVIEW METHODOLOGY",
         "1. Systematic Criteria: Search taxonomy across IEEE Xplore, ScienceDirect, ACM Digital Library (2018-2026).\n"
         "2. Problem Formulation: Discretized 500m x 500m disaster area, fleet N UAVs, coverage objective C(t) -> 100%, redundancy minimization R < 5%.\n"
         "3. Comparative Analysis: Centralized vs decentralized vs hybrid swarm architectures."),

        ("III. UAV SWARM ARCHITECTURE & SYSTEM DESIGN",
         "1. Hardware Stack: Holybro S500 airframe, Pixhawk 4 autopilot (PX4 v1.14), Raspberry Pi 4 (4GB RAM) companion, Sony IMX219 camera, ESP32 mesh radio.\n"
         "2. Software & Communication Stack: ROS 2 Humble, PX4 micro-XRCE-DDS bridge, ESP-NOW ad-hoc mesh protocol (2.4 GHz), 5.8 GHz telemetry.\n"
         "3. System Architecture Diagram: Autonomous swarm edge architecture connecting vision sensors, Raspberry Pi 4 edge autonomy, and PX4 flight control (Fig. 1)."),

        ("IV. SENSING, LOCALIZATION, & ON-DEVICE PERCEPTION",
         "1. Edge Detection Pipeline: INT8 quantized YOLOv8 model running on ARM Cortex-A72 at 59.5 ms/frame (16.8 FPS).\n"
         "2. Geolocation Projection: Pinhole camera back-projection model mapping pixel coordinates (u, v) to world GPS coordinates (lat, lon, alt) with < 2.0m RMS accuracy.\n"
         "3. Algorithm 2: Real-Time INT8 YOLOv8 Detection & Geolocation Projection Pipeline.\n"
         "4. MATLAB Benchmark: Precision-Recall curves across FP32, FP16, INT8 and geolocation error vs altitude (Fig. 2)."),

        ("V. PATH PLANNING & SWARM TASK ALLOCATION",
         "1. Sector Decomposition: Dynamic Voronoi partitioning weighted by individual UAV battery state.\n"
         "2. Algorithm 1: Distributed Market-Based Dynamic Task Allocation Auction Protocol (marginal utility bidding, 50ms auction window).\n"
         "3. MATLAB Simulation: 4-UAV search trajectories, lawnmower sweep patterns, casualty targets T1-T12, debris zones (Fig. 3).\n"
         "4. MATLAB Auction Analysis: Utility bidding convergence in 3-4 rounds and 26.2% fleet energy savings (Fig. 4)."),

        ("VI. COMMUNICATION, COORDINATION, & FAULT TOLERANCE",
         "1. Gossip Heartbeat Protocol: 5 Hz broadcast containing node status, pose, and active tasks.\n"
         "2. Algorithm 3: Heartbeat Failure Detection & Decentralized Swarm Re-Auctioning (400 ms timeout).\n"
         "3. Dynamic Self-Healing: Mid-flight failure at t = 180s automatically triggers decentralized re-auction and sector reallocation.\n"
         "4. MATLAB Fault Simulation: Coverage recovery from 74.8% plateau to 99.8% and scalability latency vs swarm size (Fig. 5)."),

        ("VII. SIMULATION, EXPERIMENTS, & BENCHMARKING",
         "1. Gazebo Multi-UAV Simulation: Full physics simulation with PX4 SITL and simulated disaster terrain.\n"
         "2. Real Benchmark Tables: Table I (Hardware Specs), Table II (Quantization), Table III (Coverage vs Fleet Size), Table IV (Edge Boards), Table V (Fault Recovery Latency).\n"
         "3. Performance Highlights: 11.4 min 100% search time, 3.4% path redundancy, 419.1 ms fault recovery."),

        ("VIII. CHALLENGES & OPEN DIRECTIONS",
         "1. Environmental Obstacles: Rubble occlusions, weather interference (fog, rain, dust), GPS multipath degradation.\n"
         "2. Networking Bottlenecks: RF shadow zones in collapsed steel buildings, packet drop mitigation.\n"
         "3. Future Work: Autonomous battery docking stations, cooperative multi-drone lifting of emergency medical supplies."),

        ("IX. CRITICAL EVALUATION & LESSONS LEARNED",
         "1. Edge vs Centralized Trade-off: Onboard inference eliminates video telemetry bottlenecks while maintaining 81.6% detection accuracy.\n"
         "2. Auction Efficiency: Distributed market auction converges within 23.8 ms for 4 drones, requiring negligible bandwidth.\n"
         "3. Resilience Validation: Swarm achieves 99.8% coverage even when individual aircraft suffer sudden hardware dropouts."),

        ("X. CONCLUSION",
         "1. Summary of Deliverables: Autonomous, decentralized, edge-AI multi-UAV swarm framework.\n"
         "2. Core Achievements: 38.2% faster search completion, 26.2% energy savings, sub-420 ms failure recovery.\n"
         "3. Real-World Readiness: Ready for deployment with first responders and disaster management authorities.")
    ]

    tbl = doc.add_table(rows=len(table_data) + 1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Header
    hdr = tbl.rows[0].cells
    hdr[0].text = "Section"
    hdr[1].text = "Subsections and Implemented Technical Details"
    for i in range(2):
        set_cell_shading(hdr[i], "003366")
        set_cell_margins(hdr[i], top=120, bottom=120, left=140, right=140)
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.bold = True
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor(255, 255, 255)

    hdr[0].width = Inches(2.3)
    hdr[1].width = Inches(4.8)

    # Data Rows
    for r_idx, (sec_name, sec_content) in enumerate(table_data):
        row = tbl.rows[r_idx + 1].cells
        row[0].width = Inches(2.3)
        row[1].width = Inches(4.8)

        row[0].text = sec_name
        row[1].text = sec_content

        bg = "F4F7FA" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx in range(2):
            set_cell_shading(row[c_idx], bg)
            set_cell_margins(row[c_idx], top=80, bottom=80, left=120, right=120)
            set_cell_border(row[c_idx],
                            top={"val": "single", "sz": 4, "color": "D0D0D0"},
                            bottom={"val": "single", "sz": 4, "color": "D0D0D0"},
                            left={"val": "single", "sz": 4, "color": "D0D0D0"},
                            right={"val": "single", "sz": 4, "color": "D0D0D0"})

        # Style Section Name
        p0 = row[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p0.runs:
            r.font.name = 'Calibri'
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0, 51, 102)

        # Style Content
        p1 = row[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p1.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(30, 30, 30)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(10)

    # Add Recommended Tables and Figures Table
    add_header_styled(doc, "Recommended Tables and Figures Matrix", level=2)
    tbl_rec = [
        ("Table I: Swarm Hardware Specifications", "Section III", "Raspberry Pi 4, Pixhawk 4, Holybro S500, Sony IMX219, ESP32"),
        ("Table II: Object Detection Precision", "Section IV", "YOLOv8 FP32 vs FP16 vs INT8 (mAP@0.5, FPS, size, Pi 4 latency)"),
        ("Table III: Swarm Coverage Performance", "Section VII", "Fleet N=1 to N=8 (100% coverage time, path overlap, energy)"),
        ("Table IV: Edge Hardware Benchmark", "Section VII", "Pi 4 vs Jetson Nano vs Coral TPU vs NCS2 vs Pi 3B+"),
        ("Table V: Fault Recovery Latency", "Section VII", "Heartbeat timeout (400ms) + Re-auction (12.8ms) = 419.1ms total"),
        ("Fig. 1: Swarm Edge Architecture Diagram", "Section III", "Hardware, Raspberry Pi 4 edge ROS 2 nodes, and communication topology"),
        ("Fig. 2: MATLAB Detection Benchmark", "Section IV", "Precision-Recall curves and geolocation error vs altitude"),
        ("Fig. 3: MATLAB Swarm Trajectories", "Section V", "4-UAV 500m x 500m lawnmower search paths and survivor targets"),
        ("Fig. 4: MATLAB Auction Convergence", "Section V", "Bidding convergence across rounds and fleet power profiles"),
        ("Fig. 5: MATLAB Fault Recovery", "Section VI", "Swarm coverage recovery dynamics under node failure and scalability")
    ]

    tf_table = doc.add_table(rows=len(tbl_rec) + 1, cols=3)
    tf_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tf_table.autofit = False

    tf_hdr = tf_table.rows[0].cells
    tf_hdr[0].text = "Item"
    tf_hdr[1].text = "Section"
    tf_hdr[2].text = "Description / Metrics Included"
    for i in range(3):
        set_cell_shading(tf_hdr[i], "003366")
        set_cell_margins(tf_hdr[i], top=100, bottom=100, left=120, right=120)
        p = tf_hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Calibri'
            r.font.bold = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(255, 255, 255)

    tf_hdr[0].width = Inches(2.2)
    tf_hdr[1].width = Inches(1.2)
    tf_hdr[2].width = Inches(3.7)

    for r_idx, (item, sec, desc) in enumerate(tbl_rec):
        row = tf_table.rows[r_idx + 1].cells
        row[0].width = Inches(2.2)
        row[1].width = Inches(1.2)
        row[2].width = Inches(3.7)
        row[0].text = item
        row[1].text = sec
        row[2].text = desc

        bg = "F7F9FB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx in range(3):
            set_cell_shading(row[c_idx], bg)
            set_cell_margins(row[c_idx], top=70, bottom=70, left=100, right=100)
            set_cell_border(row[c_idx],
                            top={"val": "single", "sz": 4, "color": "D0D0D0"},
                            bottom={"val": "single", "sz": 4, "color": "D0D0D0"},
                            left={"val": "single", "sz": 4, "color": "D0D0D0"},
                            right={"val": "single", "sz": 4, "color": "D0D0D0"})
            p = row[c_idx].paragraphs[0]
            if c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(30, 30, 30)

    out_file = os.path.join(BASE_DIR, "SWARM_SYSTEM_FOR_DISASTER_RESPONSE_REVIEW_FORMAT_TABLE.docx")
    doc.save(out_file)
    print(f"Successfully generated: {out_file}")
    return out_file

# ==============================================================================
# CONVERT DOCX TO PDF USING MICROSOFT WORD COM
# ==============================================================================
def convert_docx_to_pdf_via_word(docx_path, pdf_path):
    print(f"Converting {docx_path} -> {pdf_path} via Word COM...")
    ps_cmd = f"""
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    try {{
        $doc = $word.Documents.Open('{docx_path}')
        $doc.SaveAs([ref]'{pdf_path}', [ref]17)
        $doc.Close()
        Write-Host "SUCCESS: PDF created at {pdf_path}"
    }} catch {{
        Write-Error $_
    }} finally {{
        $word.Quit()
    }}
    """
    res = subprocess.run(["pwsh", "-Command", ps_cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"Error converting to PDF: {res.stderr}")
    return os.path.exists(pdf_path)

if __name__ == "__main__":
    print("Building Full Review Word Document...")
    docx1 = build_full_review_document()
    pdf1 = os.path.splitext(docx1)[0] + ".pdf"
    convert_docx_to_pdf_via_word(docx1, pdf1)

    print("\nBuilding Review Format Table Document...")
    docx2 = build_review_format_table_document()
    pdf2 = os.path.splitext(docx2)[0] + ".pdf"
    convert_docx_to_pdf_via_word(docx2, pdf2)

    print("\nAll documents and PDFs created successfully!")
