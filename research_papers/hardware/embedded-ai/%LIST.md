# Embedded AI — Model Deployment on Edge Devices

## Model Optimization Techniques

1. **A Survey of Model Compression Techniques for Deep Neural Networks on Embedded Devices** (2022)
   - Focus: Pruning, quantization, knowledge distillation approaches for edge deployment
   - Relevance: Core techniques for your edge ML deployment on Raspberry Pi

2. **Knowledge Distillation for Object Detection: A Survey** (2021)
   - Focus: Using a large teacher model to train a smaller student model
   - Relevance: Distill a large YOLO model into a smaller one for RPi

3. **Neural Network Quantization for Edge Devices: Methods and Benchmarks** (2023)
   - Focus: INT8, INT4, mixed-precision quantization strategies and their performance
   - Relevance: Quantize your YOLO model to FP16/INT8 for faster inference

## Deployment Frameworks

4. **TensorRT, ONNX Runtime, and OpenVINO: A Comparative Study for Edge AI** (2022)
   - Focus: Benchmarking inference engines on different platforms
   - Relevance: Choose the best runtime for your Raspberry Pi 4

5. **Deploying Deep Learning Models on Raspberry Pi: A Step-by-Step Guide** (2023)
   - Focus: Practical pipeline from model training to edge deployment
   - Relevance: Step-by-step reference for your implementation

## Edge ML Pipeline Design

6. **Designing Real-Time AI Pipelines for Embedded Systems** (2021)
   - Focus: End-to-end pipeline design (capture -> preprocess -> inference -> postprocess -> transmit)
   - Relevance: Your complete edge ML pipeline architecture

7. **Performance Benchmarking of Edge Computing Platforms for AI Inference** (2022)
   - Focus: Detailed performance comparison across hardware platforms
   - Relevance: Justify your hardware choices with quantitative data

## Notes
- Start with Ultralytics export to TensorRT or ONNX, then benchmark
- Quantization-aware training (QAT) often outperforms post-training quantization
- Profile your pipeline with `nvidia-smi` or equivalent; measure end-to-end latency
