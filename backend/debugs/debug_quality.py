#!/usr/bin/env python3
"""
Debug script to test quality assessment
"""

import sys
import os
sys.path.append('../src')

from audio_processor import AudioProcessor
import librosa
import numpy as np

def test_quality_assessment():
    """Test the quality assessment with sample audio"""
    
    # Initialize audio processor
    processor = AudioProcessor()
    
    print("🔧 Testing Quality Assessment with New Thresholds")
    print("=" * 50)
    
    # Test with a simple audio segment (sine wave)
    sr = 16000
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(sr * duration))
    
    # Create a simple sine wave (clean audio)
    clean_audio = 0.1 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    
    # Create noisy audio
    noisy_audio = clean_audio + 0.05 * np.random.randn(len(clean_audio))
    
    print("📊 Testing Clean Audio:")
    clean_metrics = processor.assess_segment_quality(clean_audio, sr)
    print(f"  Volume: {clean_metrics['volume']:.6f}")
    print(f"  Volume dB: {clean_metrics['volume_db']:.2f}")
    print(f"  Noise Ratio: {clean_metrics['noise_ratio']:.6f}")
    print(f"  SNR Estimate: {clean_metrics['snr_estimate']:.6f}")
    print(f"  Zero Crossing Rate: {clean_metrics['zero_crossing_rate']:.6f}")
    print(f"  Spectral Centroid: {clean_metrics['spectral_centroid']:.2f}")
    print(f"  Quality Score: {clean_metrics['quality_score']:.6f}")
    print(f"  Is Acceptable: {clean_metrics['is_acceptable']}")
    
    print("\n📊 Testing Noisy Audio:")
    noisy_metrics = processor.assess_segment_quality(noisy_audio, sr)
    print(f"  Volume: {noisy_metrics['volume']:.6f}")
    print(f"  Volume dB: {noisy_metrics['volume_db']:.2f}")
    print(f"  Noise Ratio: {noisy_metrics['noise_ratio']:.6f}")
    print(f"  SNR Estimate: {noisy_metrics['snr_estimate']:.6f}")
    print(f"  Zero Crossing Rate: {noisy_metrics['zero_crossing_rate']:.6f}")
    print(f"  Spectral Centroid: {noisy_metrics['spectral_centroid']:.2f}")
    print(f"  Quality Score: {noisy_metrics['quality_score']:.6f}")
    print(f"  Is Acceptable: {noisy_metrics['is_acceptable']}")
    
    print("\n🔧 Current Thresholds:")
    print(f"  Min Volume Threshold: {processor.min_volume_threshold}")
    print(f"  Max Noise Ratio: {processor.max_noise_ratio}")
    print(f"  Min SNR Threshold: {processor.min_snr_threshold}")
    print(f"  Min Quality Score: {processor.min_quality_score}")

if __name__ == "__main__":
    test_quality_assessment() 