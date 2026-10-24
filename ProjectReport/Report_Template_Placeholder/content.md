# Project Report Input Specification & Content Guide
**KTU B.Tech Computer Science Project Report (Standard Format)**

---

## 1. Project & Department Metadata

- **Project Title:** SARAS: SEARCH AND RESCUE AUTONOMOUS SWARM
- **Report Category:** A PROJECT PHASE I REPORT / FINAL PROJECT REPORT
- **Student Details:**
  - Name: ABIN VARGHESE
  - Register Number: AJC23CS008
- **Internal Supervisor / Guide:**
  - Name: Dr. Jacob John
  - Designation: Associate Professor
- **Project Coordinator(s):**
  - Name: Dr. Jacob John
  - Designation: Associate Professor
- **Head of Department (CSE):**
  - Name: Dr. Juby Mathew
  - Designation: Head of Department, CSE
- **Institution:** Amal Jyothi College of Engineering (Autonomous), Kanjirappally
- **Affiliated University:** APJ Abdul Kalam Technological University (KTU)
- **Month & Year:** October 2026

---

## 2. Standard Chapter Outline

### Abstract (250–300 words)
- Problem: Post-disaster search and rescue in hazardous environments under tight time windows.
- Method: Search And Rescue Autonomous Swarm (SARAS) integrating edge computer vision and decentralized market auction coordination.
- Dataset: VisDrone aerial benchmark and Gazebo multi-robot disaster simulations.
- Key Results: 8-bit integer quantized YOLOv8 nano runs at 16.8 FPS with 81.6% mAP@0.5 on Raspberry Pi 4 (<6.5W); decentralized swarm achieves 100% coverage in 11.4 min with 96.6% path efficiency; dropout recovery under 420 ms.
- Significance: Bridges physical edge robotics with intelligent tactical decision support.

### Chapter 1: Introduction (3–5 pages)
- **1.1 Background:** Rapid disaster escalation, golden window criticality, limitations of manned and single-drone sweeps, emergence of autonomous swarms.
- **1.2 Motivation:** 65% fatalities occur due to delays in initial 12 hours; single drone flight time limits (20-30 min); telemetry lag and human operator fatigue.
- **1.3 Problem Statement:** Autonomous spatial partitioning, real-time edge vision inference, fault-tolerant peer reallocation, and tactical casualty triage across GPS-degraded, communication-constrained environments.
- **1.4 Objectives:** Numbered list of 5 measurable objectives mapping directly to results in Chapter 5.
- **1.5 Scope and Limitations:** What is covered (INT8 edge inference, auction bidding, SITL Gazebo simulation, RAG triage) vs out of scope (canopy penetration, multi-drone physical fleet).
- **1.6 Contributions:** Optimized INT8 pipeline, asynchronous swarm protocol, sub-second fault recovery, agentic RAG triage, comprehensive comparative study.
- **1.7 Report Organisation:** Breakdown of Chapters 2 to 6 and Back Matter.

### Chapter 2: Literature Survey (6–10 pages)
- **2.1 Overview of Problem Domain:** Autonomous aerial reconnaissance, swarms vs single drones.
- **2.2 Classical ML Approaches:** HOG + SVM, Haar Cascades + AdaBoost, Random Forest, KNN (reported accuracies 42-68%, limitations in scale, pose, clutter).
- **2.3 Deep Learning Approaches:** Faster R-CNN (two-stage, high mAP but heavy memory and latency), SSD & YOLO (single-stage, small-target challenges), Vision Transformers (DETR, Swin).
- **2.4 Recent / Hybrid Approaches:** MobileNetV3, YOLOv8/v7, INT8 Quantization, MARL (Dec-POMDP), Asynchronous market auction heuristics, RAG decision models.
- **2.5 Datasets Used in Prior Work:** VisDrone, Heridal SAR, Okutama-Action, DOTA.
- **2.6 Comparison Table:** Ref, Method, Dataset, Metric, Key Limitation.
- **2.7 Research Gap:** Disconnection between edge vision, multi-agent flight planning, and triage decision support; leads directly to Chapter 3.

### Chapter 3: Proposed Methodology (8–12 pages)
- **3.1 System Overview:** Full pipeline block diagram across Tier 1 (Edge Perception), Tier 2 (Swarm Coordination), Tier 3 (Fault Recovery), and Tier 4 (Agentic Triage).
- **3.2 Dataset Description:** VisDrone benchmark, 10,209 images, target classes, small-target and occlusion challenges.
- **3.3 Data Preprocessing:** Sanitization, adaptive letterbox resizing to $640 \times 640$, pixel normalization, class imbalance weighting, Mosaic and MixUp augmentations.
- **3.4 Feature Extraction / Representation:** CSPDarknet backbone, Path Aggregation Network (PANet) neck, multi-scale feature pyramids ($P_3, P_4, P_5$).
- **3.5 Proposed Model Architecture:** Anchor-free decoupled head, layer-wise description, 3.2M parameters, 8.7 GFLOPs, 6.4 MB INT8 footprint.
- **3.6 Loss Function and Optimisation:** CIoU loss, Distribution Focal Loss (DFL), BCE classification loss, AdamW optimizer, Cosine Annealing learning rate schedule.
- **3.7 Training Strategy:** Transfer learning from COCO, two-stage fine-tuning (frozen backbone 10 epochs, unfrozen 90 epochs), early stopping, INT8 post-training quantization.
- **3.8 Evaluation Metrics:** Equations for Precision, Recall, F1, mAP@0.5, mAP@0.5:0.95, Latency/FPS, Coverage Efficiency $\eta_{\text{cov}}$, Reallocation Latency $T_{\text{realloc}}$.

### Chapter 4: Implementation (5–8 pages)
- **4.1 Hardware and Software Requirements:** Workstation (i7-12700H, RTX 3070 Ti, 32 GB RAM, Ubuntu 22.04, CUDA 11.8) and UAV hardware (S500 quadcopter, Pixhawk 4, Raspberry Pi 4, Sony IMX219 camera, 4S LiPo).
- **4.2 Tools and Frameworks:** PyTorch, Ultralytics YOLOv8, ONNX Runtime, OpenCV, ROS 2 Humble, Gazebo Harmonic, PX4 Autopilot, MAVSDK-Python, Next.js, Leaflet, LangChain, FAISS.
- **4.3 Dataset Split:** 6,471 train (63.4%), 548 val (5.4%), 3,190 test (31.2%) with scene-stratified separation.
- **4.4 Hyperparameter Settings:** Table of learning rates, batch sizes, weight decay, loss gains, and NMS thresholds.
- **4.5 Model Training Procedure:** Step-by-step training flow, 84 epochs convergence in 3h 42m.
- **4.6 Deployment / User Interface:** Multi-threaded companion computer daemon and Next.js / Leaflet Ground Control Dashboard.

### Chapter 5: Results and Discussion (8–12 pages)
- **5.1 Experimental Setup:** VisDrone test set evaluation on Raspberry Pi 4 + Gazebo SITL simulation across $1\text{ km}^2$ disaster theater with $N=2,4,6,8$ drones.
- **5.2 Training and Validation Curves:** Loss decay and validation mAP curves.
- **5.3 Performance Metrics on Test Set:** Precision (84.9%), Recall (78.6%), F1 (81.6%), mAP@0.5 (81.6%), Latency (59.5 ms), Throughput (16.8 FPS) on Raspberry Pi 4.
- **5.4 Confusion Matrix / ROC Curves:** Analysis of True Positives, False Negatives (canopy/oblique angles), and False Positives (debris/shadows).
- **5.5 Comparison with Baseline Models:** Comparison against HOG+SVM, Faster R-CNN, SSD MobileNetV2, YOLOv5n, YOLOv7-tiny on Raspberry Pi 4.
- **5.6 Comparison with Existing Works:** Comparison table against Liu et al., Al-Haddad et al., Rodriguez et al., Miller et al.
- **5.7 Ablation Study:** Incremental impact of Mosaic augmentation, anchor-free heads, market auction, and fault recovery.
- **5.8 Error Analysis:** Occlusion, shadow artifacts, and nadir camera pitch challenges.
- **5.9 Discussion:** Trade-offs between accuracy, inference speed, thermal budget, and auction communication complexity.

### Chapter 6: Conclusion and Future Work (1–2 pages)
- **6.1 Conclusion:** Summary of findings and verification of all 5 project objectives from Section 1.4.
- **6.2 Limitations:** Single physical prototype, monocular RGB sensor limitations, thermal SBC limits, RF bandwidth scaling.
- **6.3 Future Work:** Multispectral thermal sensor fusion, decentralized LoRa mesh networking, MARL flight policies, multi-center civil defense field trials.

### Back Matter
- **References:** 25 IEEE-style citations, all referenced in the report.
- **Appendix A:** Key code snippets (Auction cost computation, embedded INT8 ONNX inference daemon).
- **Appendix B:** Additional results and flight trajectory visualizations.
