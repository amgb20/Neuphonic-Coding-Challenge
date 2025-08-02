#!/usr/bin/env python3
"""
Debug script to test volume calculation
"""

import sys
import os
sys.path.append('../src')

import librosa
import numpy as np
import soundfile as sf

def test_volume_calculation():
    """Test volume calculation with real audio"""
    
    print("🔧 Testing Volume Calculation")
    print("=" * 40)
    
    # Load a real audio file
    audio_path = "../../audio_files/Script 1.mp3"
    print(f"Loading audio file: {audio_path}")
    
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        print(f"Audio loaded: {len(y)} samples, {sr} Hz")
        print(f"Audio range: {np.min(y):.6f} to {np.max(y):.6f}")
        
        # Test different volume calculations
        segment = y[:16000]  # First second
        
        print("\n📊 Volume Calculations:")
        
        # Method 1: Mean absolute value
        volume_abs = float(np.mean(np.abs(segment)))
        print(f"  Mean absolute: {volume_abs:.6f}")
        
        # Method 2: RMS
        volume_rms = float(np.sqrt(np.mean(segment**2)))
        print(f"  RMS: {volume_rms:.6f}")
        
        # Method 3: Peak
        volume_peak = float(np.max(np.abs(segment)))
        print(f"  Peak: {volume_peak:.6f}")
        
        # Volume in dB
        volume_db_abs = 20 * np.log10(volume_abs + 1e-10)
        volume_db_rms = 20 * np.log10(volume_rms + 1e-10)
        print(f"  Volume dB (abs): {volume_db_abs:.2f}")
        print(f"  Volume dB (RMS): {volume_db_rms:.2f}")
        
        # Test quality assessment
        from audio_processor import AudioProcessor
        processor = AudioProcessor()
        
        print("\n📊 Quality Assessment:")
        metrics = processor.assess_segment_quality(segment, sr)
        print(f"  Volume: {metrics['volume']:.6f}")
        print(f"  Volume dB: {metrics['volume_db']:.2f}")
        print(f"  Quality Score: {metrics['quality_score']:.6f}")
        print(f"  Is Acceptable: {metrics['is_acceptable']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volume_calculation() 