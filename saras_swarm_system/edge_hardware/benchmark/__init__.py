"""SARAS Benchmark Package."""

from edge_hardware.benchmark.benchmark_inference import (
    BenchmarkMetric,
    run_benchmark_for_config,
)

__all__ = ["BenchmarkMetric", "run_benchmark_for_config"]
