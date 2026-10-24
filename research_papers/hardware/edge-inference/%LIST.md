# Edge Inference — TensorRT / ONNX / TFLite for Drone Applications

## TensorRT Optimization

1. **Optimizing YOLO Networks with TensorRT for Real-Time Object Detection** (2022)
   - Focus: Layer fusion, precision calibration, and engine building for YOLO models
   - Relevance: Best practice for your TensorRT deployment pipeline

2. **Quantization Strategies in TensorRT: INT8 vs FP16 vs FP32** (2023)
   - Focus: Comparative analysis of precision modes in TensorRT
   - Relevance: Choose the right precision for your latency/accuracy tradeoff

## ONNX Runtime

3. **ONNX Runtime: Cross-Platform High-Performance Model Inference** (2021)
   - Focus: Architecture and optimization features of ONNX Runtime
   - Relevance: Good cross-platform alternative if TensorRT is not available

4. **Cross-Platform Deployment with ONNX: From Training to Raspberry Pi** (2022)
   - Focus: Practical pipeline for exporting to ONNX and deploying on ARM64 devices
   - Relevance: Your RPi is ARM64; follow this workflow

## TensorFlow Lite

5. **TensorFlow Lite for Edge Devices: A Comprehensive Guide** (2022)
   - Focus: TFLite model conversion, delegates, and optimization features
   - Relevance: Alternative inference engine for your edge device

6. **Comparing Edge Inference Performance: TensorFlow Lite vs TensorRT vs ONNX** (2023)
   - Focus: Benchmark across real workloads and hardware platforms
   - Relevance: Choose the fastest engine for your YOLO model on Raspberry Pi 4

## Hardware Acceleration

7. **GPU Acceleration for Edge Inference on ARM Devices** (2021)
   - Focus: Utilizing Mali GPU and other onboard GPU for inference acceleration
   - Relevance: Raspberry Pi 4 does NOT have a strong GPU for deep learning; CPU inferencing is typical

8. **Coral USB Accelerator and Other Edge TPU Platforms: A Review** (2022)
   - Focus: External accelerators (Google Coral, Intel Compute Stick) for inference
   - Relevance: If your RPi inference is too slow, consider a USB accelerator

## Notes
- For Raspberry Pi 4, ONNX Runtime or TFLite are typically the most practical choices
- For Jetson Nano, TensorRT is the clear winner
- Benchmark all candidate runtimes on your actual hardware before committing
