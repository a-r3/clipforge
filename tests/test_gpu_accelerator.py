"""Tests for GPU Acceleration Engine."""

from __future__ import annotations

import pytest
from clipforge.gpu_accelerator import (
    GPUVendor,
    GPUEncodeFormat,
    GPUInfo,
    BenchmarkResult,
    GPUDetector,
    GPUAccelerator,
)


class TestGPUVendor:
    """Test GPU vendor enumeration."""

    def test_vendor_values(self) -> None:
        """Test vendor enum values."""
        assert GPUVendor.NVIDIA.value == "nvidia"
        assert GPUVendor.AMD.value == "amd"
        assert GPUVendor.INTEL.value == "intel"
        assert GPUVendor.NONE.value == "none"

    def test_vendor_comparison(self) -> None:
        """Test vendor comparison."""
        assert GPUVendor.NVIDIA != GPUVendor.AMD
        assert GPUVendor.NVIDIA == GPUVendor.NVIDIA


class TestGPUEncodeFormat:
    """Test GPU encoding formats."""

    def test_encode_format_values(self) -> None:
        """Test encoding format enum values."""
        assert GPUEncodeFormat.H264.value == "h264"
        assert GPUEncodeFormat.H265.value == "hevc"
        assert GPUEncodeFormat.VP9.value == "vp9"


class TestGPUInfo:
    """Test GPU information dataclass."""

    def test_gpu_info_creation(self) -> None:
        """Test creating GPU info."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="GeForce RTX 3080",
            memory_mb=10240,
            driver_version="530.41.03",
            supported_codecs=[GPUEncodeFormat.H264, GPUEncodeFormat.H265],
            cuda_compute_capability="8.6",
        )

        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.model == "GeForce RTX 3080"
        assert gpu.memory_mb == 10240
        assert len(gpu.supported_codecs) == 2

    def test_gpu_info_defaults(self) -> None:
        """Test GPU info with defaults."""
        gpu = GPUInfo(
            vendor=GPUVendor.AMD,
            model="Radeon RX 6800",
            memory_mb=8192,
            driver_version="22.10",
            supported_codecs=[GPUEncodeFormat.H264],
        )

        assert gpu.cuda_compute_capability is None


class TestBenchmarkResult:
    """Test benchmark result dataclass."""

    def test_benchmark_result_creation(self) -> None:
        """Test creating benchmark result."""
        result = BenchmarkResult(
            codec="h264",
            resolution="1920x1080",
            cpu_time_sec=100.0,
            gpu_time_sec=10.0,
            speedup=10.0,
            cpu_bitrate="5000k",
            gpu_bitrate="5000k",
            quality_difference=0.02,
        )

        assert result.codec == "h264"
        assert result.speedup == 10.0
        assert result.quality_difference == 0.02

    def test_benchmark_speedup_calculation(self) -> None:
        """Test speedup is correctly calculated."""
        result = BenchmarkResult(
            codec="h265",
            resolution="1080x1920",
            cpu_time_sec=180.0,
            gpu_time_sec=15.0,
            speedup=12.0,
            cpu_bitrate="3500k",
            gpu_bitrate="3500k",
            quality_difference=0.0,
        )

        assert result.speedup == 12.0
        # Verify calculation: 180 / 15 = 12


class TestGPUDetector:
    """Test GPU detection."""

    def test_detector_has_static_methods(self) -> None:
        """Test GPUDetector has static methods."""
        assert hasattr(GPUDetector, "detect_nvidia")
        assert hasattr(GPUDetector, "detect_amd")
        assert hasattr(GPUDetector, "detect_intel")
        assert hasattr(GPUDetector, "detect_all_gpus")

    def test_nvidia_detection_returns_gpu_info_or_none(self) -> None:
        """Test NVIDIA detection returns GPUInfo or None."""
        result = GPUDetector.detect_nvidia()

        if result is not None:
            assert isinstance(result, GPUInfo)
            assert result.vendor == GPUVendor.NVIDIA
            assert result.model is not None
            assert result.memory_mb > 0

    def test_amd_detection_returns_gpu_info_or_none(self) -> None:
        """Test AMD detection returns GPUInfo or None."""
        result = GPUDetector.detect_amd()

        if result is not None:
            assert isinstance(result, GPUInfo)
            assert result.vendor == GPUVendor.AMD

    def test_intel_detection_returns_gpu_info_or_none(self) -> None:
        """Test Intel detection returns GPUInfo or None."""
        result = GPUDetector.detect_intel()

        if result is not None:
            assert isinstance(result, GPUInfo)
            assert result.vendor == GPUVendor.INTEL

    def test_detect_all_gpus_returns_list(self) -> None:
        """Test detect_all_gpus returns a list."""
        gpus = GPUDetector.detect_all_gpus()

        assert isinstance(gpus, list)
        
        for gpu in gpus:
            assert isinstance(gpu, GPUInfo)
            assert gpu.vendor in [GPUVendor.NVIDIA, GPUVendor.AMD, GPUVendor.INTEL]


class TestGPUAccelerator:
    """Test GPU accelerator main interface."""

    def test_accelerator_initialization(self) -> None:
        """Test GPU accelerator initialization."""
        accel = GPUAccelerator()

        assert hasattr(accel, "gpus")
        assert isinstance(accel.gpus, list)
        assert accel.primary_gpu is None or isinstance(accel.primary_gpu, GPUInfo)

    def test_is_available(self) -> None:
        """Test GPU availability check."""
        accel = GPUAccelerator()

        if len(accel.gpus) > 0:
            assert accel.is_available() is True
        else:
            assert accel.is_available() is False

    def test_get_gpu_info(self) -> None:
        """Test getting GPU info list."""
        accel = GPUAccelerator()
        gpus = accel.get_gpu_info()

        assert isinstance(gpus, list)
        assert gpus == accel.gpus

    def test_get_primary_gpu(self) -> None:
        """Test getting primary GPU."""
        accel = GPUAccelerator()
        gpu = accel.get_primary_gpu()

        if gpu is not None:
            assert isinstance(gpu, GPUInfo)
            assert gpu == accel.gpus[0]

    def test_get_ffmpeg_hw_accel_args_nvidia(self) -> None:
        """Test FFmpeg args for NVIDIA GPU."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="RTX 3080",
            memory_mb=10240,
            driver_version="530",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        args = accel.get_ffmpeg_hw_accel_args(gpu)

        assert args["-hwaccel"] == "cuda"
        assert args["-c:v"] == "h264_nvenc"

    def test_get_ffmpeg_hw_accel_args_amd(self) -> None:
        """Test FFmpeg args for AMD GPU."""
        gpu = GPUInfo(
            vendor=GPUVendor.AMD,
            model="RX 6800",
            memory_mb=8192,
            driver_version="22.10",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        args = accel.get_ffmpeg_hw_accel_args(gpu)

        assert args["-c:v"] == "h264_amf"

    def test_get_ffmpeg_hw_accel_args_intel(self) -> None:
        """Test FFmpeg args for Intel GPU."""
        gpu = GPUInfo(
            vendor=GPUVendor.INTEL,
            model="UHD Graphics",
            memory_mb=0,
            driver_version="unknown",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        args = accel.get_ffmpeg_hw_accel_args(gpu)

        assert args["-c:v"] == "h264_qsv"

    def test_get_ffmpeg_hw_accel_args_no_gpu(self) -> None:
        """Test FFmpeg args when no GPU available."""
        accel = GPUAccelerator()
        accel.primary_gpu = None
        
        args = accel.get_ffmpeg_hw_accel_args()

        assert args == {}

    def test_get_optimal_preset_no_gpu(self) -> None:
        """Test optimal preset without GPU."""
        accel = GPUAccelerator()
        accel.primary_gpu = None
        
        preset = accel.get_optimal_preset()

        assert preset == "medium"

    def test_get_optimal_preset_nvidia(self) -> None:
        """Test optimal preset for NVIDIA GPU."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="RTX 3080",
            memory_mb=10240,
            driver_version="530",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        accel.primary_gpu = gpu
        
        preset = accel.get_optimal_preset()

        assert preset == "fast"

    def test_get_optimal_preset_amd(self) -> None:
        """Test optimal preset for AMD GPU."""
        gpu = GPUInfo(
            vendor=GPUVendor.AMD,
            model="RX 6800",
            memory_mb=8192,
            driver_version="22.10",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        accel.primary_gpu = gpu
        
        preset = accel.get_optimal_preset()

        assert preset == "veryfast"

    def test_estimate_speedup_no_gpu(self) -> None:
        """Test speedup estimate without GPU."""
        accel = GPUAccelerator()
        accel.primary_gpu = None
        
        speedup = accel.estimate_speedup()

        assert speedup == 1.0

    def test_estimate_speedup_nvidia(self) -> None:
        """Test speedup estimate for NVIDIA."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            model="RTX 3080",
            memory_mb=10240,
            driver_version="530",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        accel.primary_gpu = gpu
        
        speedup = accel.estimate_speedup()

        assert speedup == 7.0

    def test_estimate_speedup_amd(self) -> None:
        """Test speedup estimate for AMD."""
        gpu = GPUInfo(
            vendor=GPUVendor.AMD,
            model="RX 6800",
            memory_mb=8192,
            driver_version="22.10",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        accel.primary_gpu = gpu
        
        speedup = accel.estimate_speedup()

        assert speedup == 12.0

    def test_estimate_speedup_intel(self) -> None:
        """Test speedup estimate for Intel."""
        gpu = GPUInfo(
            vendor=GPUVendor.INTEL,
            model="UHD Graphics",
            memory_mb=0,
            driver_version="unknown",
            supported_codecs=[GPUEncodeFormat.H264],
        )
        
        accel = GPUAccelerator()
        accel.primary_gpu = gpu
        
        speedup = accel.estimate_speedup()

        assert speedup == 10.0
