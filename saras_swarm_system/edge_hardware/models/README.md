# SARAS Edge Model Repository

This directory hosts lightweight object detection models deployed on the physical companion computer (Raspberry Pi 4 / 5):

- `yolov8n.onnx`: ONNX Runtime FP32/FP16 optimized weights for fast ARM Cortex CPU inference.
- `yolov8n.pt`: Ultralytics PyTorch reference baseline weights.
- `yolov8n_int8.onnx`: Post-Training Quantized (PTQ) INT8 model for embedded execution.

## Export Instructions
To regenerate or re-export:
```bash
# Export ONNX from PyTorch with dynamic axes and slimming:
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); model.export(format='onnx', imgsz=640, simplify=True)"
```
