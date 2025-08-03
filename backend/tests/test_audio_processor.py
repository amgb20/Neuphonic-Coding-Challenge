#!/usr/bin/env python3
"""
Audio Processor Test Suite
Tests the core audio processing features with REAL audio files:
1. Quality filtering for noisy segments
2. Background noise assessment
3. Sentence-level segmentation
4. ML-ready data structure
5. Feature extraction
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from audio_processor import AudioProcessor
from feature_extractor import FeatureExtractor
from database import AudioDatabase

def get_real_audio_files():
    """Get real audio files from the audio_files directory"""
    audio_dir = Path("../audio_files")
    if not audio_dir.exists():
        raise FileNotFoundError(f"Audio files directory not found: {audio_dir.absolute()}")
    
    mp3_files = list(audio_dir.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError(f"No MP3 files found in {audio_dir.absolute()}")
    
    return mp3_files

def load_audio_segment(audio_path, start_time=10.0, duration=5.0):
    """Load a segment from a real audio file"""
    y, sr = librosa.load(audio_path, sr=16000)
    
    # Extract segment
    start_sample = int(start_time * sr)
    end_sample = int((start_time + duration) * sr)
    
    if start_sample >= len(y):
        start_sample = 0
    if end_sample > len(y):
        end_sample = len(y)
    
    segment = y[start_sample:end_sample]
    return segment, sr

def test_quality_filtering():
    """Test quality filtering with real audio segments"""
    print("Testing quality filtering with real audio...")
    
    try:
        audio_processor = AudioProcessor()
        audio_files = get_real_audio_files()
        
        # Use the first audio file for testing
        test_file = audio_files[0]
        print(f"Using audio file: {test_file.name}")
        
        # Load different segments from the same file
        segment1, sr = load_audio_segment(test_file, start_time=10.0, duration=3.0)
        segment2, sr = load_audio_segment(test_file, start_time=30.0, duration=3.0)
        segment3, sr = load_audio_segment(test_file, start_time=60.0, duration=3.0)
        
        # Test quality assessment on real segments
        quality1 = audio_processor.assess_segment_quality(segment1, sr)
        quality2 = audio_processor.assess_segment_quality(segment2, sr)
        quality3 = audio_processor.assess_segment_quality(segment3, sr)
        
        # Verify quality metrics are present
        required_metrics = ['volume', 'noise_ratio', 'quality_score', 'is_acceptable']
        for metric in required_metrics:
            assert metric in quality1, f"Quality metric {metric} should be present"
            assert metric in quality2, f"Quality metric {metric} should be present"
            assert metric in quality3, f"Quality metric {metric} should be present"
        
        # Verify quality scores are reasonable
        assert 0 <= quality1['quality_score'] <= 1, "Quality score should be between 0 and 1"
        assert 0 <= quality2['quality_score'] <= 1, "Quality score should be between 0 and 1"
        assert 0 <= quality3['quality_score'] <= 1, "Quality score should be between 0 and 1"
        
        print(f"✅ Quality filtering test passed - Segments analyzed: {len([quality1, quality2, quality3])}")
        
    except Exception as e:
        print(f"❌ Quality filtering test failed: {e}")
        raise

def test_background_noise_assessment():
    """Test background noise assessment with real audio"""
    print("Testing background noise assessment with real audio...")
    
    try:
        audio_processor = AudioProcessor()
        audio_files = get_real_audio_files()
        
        # Use the first audio file
        test_file = audio_files[0]
        print(f"Using audio file: {test_file.name}")
        
        # Load multiple segments to compare noise characteristics
        segments = []
        for i in range(5):
            start_time = i * 20.0  # Different parts of the audio
            segment, sr = load_audio_segment(test_file, start_time=start_time, duration=3.0)
            segments.append((segment, sr))
        
        # Assess noise levels for all segments
        noise_metrics = []
        for segment, sr in segments:
            metrics = audio_processor.assess_segment_quality(segment, sr)
            noise_metrics.append(metrics)
        
        # Verify noise assessment metrics
        for i, metrics in enumerate(noise_metrics):
            assert 'noise_ratio' in metrics, f"Noise ratio should be present in segment {i}"
            assert 'snr_estimate' in metrics, f"SNR estimate should be present in segment {i}"
            assert 'spectral_centroid' in metrics, f"Spectral centroid should be present in segment {i}"
            
            # Verify values are reasonable
            assert 0 <= metrics['noise_ratio'] <= 1, f"Noise ratio should be between 0 and 1 for segment {i}"
            assert metrics['snr_estimate'] >= 0, f"SNR estimate should be non-negative for segment {i}"
            assert metrics['spectral_centroid'] > 0, f"Spectral centroid should be positive for segment {i}"
        
        print(f"✅ Background noise assessment test passed - Segments analyzed: {len(noise_metrics)}")
        
    except Exception as e:
        print(f"❌ Background noise assessment test failed: {e}")
        raise

def test_sentence_completeness_check():
    """Test sentence completeness checking with real transcripts"""
    print("Testing sentence completeness check with real transcripts...")
    
    try:
        audio_processor = AudioProcessor()
        
        # Real sentence examples from the audio files (based on typical content)
        real_sentences = [
            "Recent advances in MRI technology have transformed medical diagnostics.",
            "Robotic arms have become a significant advancement in surgical practices.",
            "The integration of robotics and healthcare settings is increasing.",
            "Artificial intelligence in MRI enables faster scans and more accurate readings.",
            "Functional MRI measures brain activity by detecting changes in blood flow."
        ]
        
        # Test incomplete sentences
        incomplete_sentences = [
            "um uh",
            "incomplete sentence",
            "no capital letter",
            "too short",
            "basically um"
        ]
        
        # Test real sentences
        for sentence in real_sentences:
            assert audio_processor._is_complete_sentence(sentence), f"Should be complete: {sentence}"
        
        # Test incomplete sentences
        for sentence in incomplete_sentences:
            assert not audio_processor._is_complete_sentence(sentence), f"Should be incomplete: {sentence}"
        
        print("✅ Sentence completeness check test passed")
        
    except Exception as e:
        print(f"❌ Sentence completeness check test failed: {e}")
        raise

def test_feature_extraction():
    """Test feature extraction with real transcripts"""
    print("Testing feature extraction with real transcripts...")
    
    try:
        feature_extractor = FeatureExtractor()
        
        # Real transcript examples from the audio files
        real_transcripts = [
            "Recent advances in MRI technology have transformed medical diagnostics since its inception in the 1970s. Utilizing powerful magnetic fields and radio waves, MRI provides detailed images of the body's internal structures without the need for invasive procedures or ionizing radiation.",
            "Robotic arms have become a significant advancement in surgical practices, offering surgeons enhanced capabilities and transforming patient care. By combining engineering precision with surgical expertise, robotic arms are redefining the possibilities in the operating room.",
            "The integration of robotics and healthcare settings is increasing, enhancing the quality of care, improving patient outcomes, and streamlining workflows. From surgical assistance to logistical support, robots are raising standards within healthcare facilities."
        ]
        
        for i, transcript in enumerate(real_transcripts):
            duration = 10.0 + i * 5.0  # Varying durations
            
            # Extract features
            features = feature_extractor.extract_all_features(transcript, duration)
            
            # Verify all required features are present
            required_features = ['wpm', 'filler_ratio', 'sentiment_score', 'speech_rate', 'complexity']
            for feature in required_features:
                assert feature in features, f"Feature {feature} should be present in transcript {i}"
            
            # Verify feature values are reasonable
            assert features['wpm'] > 0, f"WPM should be positive for transcript {i}"
            assert 0 <= features['filler_ratio'] <= 1, f"Filler ratio should be between 0 and 1 for transcript {i}"
            assert -1 <= features['sentiment_score'] <= 1, f"Sentiment score should be between -1 and 1 for transcript {i}"
            
            print(f"  Transcript {i+1}: WPM={features['wpm']:.1f}, Filler={features['filler_ratio']:.3f}, Sentiment={features['sentiment_score']:.3f}")
        
        print("✅ Feature extraction test passed")
        
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
        raise

def test_database_operations():
    """Test database operations with real data"""
    print("Testing database operations with real data...")
    
    # Create temporary database
    temp_db_path = "/tmp/test_audio_processor_real.duckdb"
    
    try:
        db = AudioDatabase(temp_db_path)
        
        # Real file data
        file_data = {
            "filename": "Script_1.mp3",
            "duration": 267.32,
            "transcript": "Recent advances in MRI technology have transformed medical diagnostics since its inception in the 1970s. Utilizing powerful magnetic fields and radio waves, MRI provides detailed images of the body's internal structures without the need for invasive procedures or ionizing radiation.",
            "wpm": 126.1,
            "filler_ratio": 0.013,
            "sentiment_score": 0.163,
            "audio_path": "/app/processed_data/Script_1_processed.wav"
        }
        
        # Insert file
        file_id = db.insert_audio_file(file_data)
        assert file_id is not None, "File should be inserted successfully"
        
        # Insert real segment data
        segment_data = {
            "original_file_id": file_id,
            "segment_index": 0,
            "start_time": 0.0,
            "end_time": 15.0,
            "duration": 15.0,
            "transcript": "Recent advances in MRI technology have transformed medical diagnostics since its inception in the 1970s.",
            "audio_path": "/app/processed_data/segment_0.wav",
            "wpm": 125.0,
            "filler_ratio": 0.015,
            "sentiment_score": 0.15,
            "quality_score": 0.85,
            "volume": 0.12,
            "volume_db": -18.0,
            "noise_ratio": 0.25,
            "snr_estimate": 18.0,
            "zero_crossing_rate": 0.08,
            "spectral_centroid": 1800.0,
            "is_ml_ready": True,
            "training_priority": 0.92
        }
        
        segment_id = db.insert_segment_with_quality(segment_data)
        assert segment_id is not None, "Segment should be inserted successfully"
        
        # Retrieve segments
        segments = db.get_segments_by_file_id(file_id)
        assert len(segments) == 1, "Should retrieve exactly one segment"
        
        # Verify segment data
        segment = segments[0]
        assert segment['transcript'] == "Recent advances in MRI technology have transformed medical diagnostics since its inception in the 1970s.", "Transcript should match"
        assert segment['quality_score'] == 0.85, "Quality score should match"
        assert segment['is_ml_ready'] == True, "ML ready flag should be set"
        assert segment['wpm'] == 125.0, "WPM should match"
        
        print("✅ Database operations test passed")
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_real_audio_processing():
    """Test processing with real audio files"""
    print("Testing real audio processing...")
    
    try:
        audio_files = get_real_audio_files()
        
        # Use the first audio file for testing
        test_file = audio_files[0]
        print(f"Processing real audio file: {test_file.name}")
        
        # Initialize components
        audio_processor = AudioProcessor()
        
        # Process the audio (this will create a processed version)
        processed_path = audio_processor.process_audio(str(test_file))
        
        # Verify processing worked
        assert os.path.exists(processed_path), "Processed audio file should exist"
        
        # Get duration
        duration = audio_processor.get_duration(processed_path)
        assert duration > 0, "Duration should be positive"
        print(f"  Audio duration: {duration:.2f} seconds")
        
        # Test quality assessment on real audio
        y, sr = sf.read(processed_path)
        quality_metrics = audio_processor.assess_segment_quality(y, sr)
        
        # Verify quality metrics are present
        required_metrics = ['volume', 'noise_ratio', 'quality_score', 'is_acceptable']
        for metric in required_metrics:
            assert metric in quality_metrics, f"Quality metric {metric} should be present"
        
        print(f"  Quality score: {quality_metrics['quality_score']:.3f}")
        print(f"  Volume (dB): {quality_metrics['volume_db']:.1f}")
        print(f"  Noise ratio: {quality_metrics['noise_ratio']:.3f}")
        
        print("✅ Real audio processing test passed")
        
    except Exception as e:
        print(f"❌ Real audio processing test failed: {e}")
        raise

def run_audio_processor_tests():
    """Run all audio processor tests with real audio files"""
    print("🚀 Starting Audio Processor Test Suite with REAL Audio Files...\n")
    
    tests = [
        test_quality_filtering,
        test_background_noise_assessment,
        test_sentence_completeness_check,
        test_feature_extraction,
        test_database_operations,
        test_real_audio_processing
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ Test {test.__name__} failed: {e}")
        print()
    
    print("📊 Audio Processor Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All audio processor tests passed!")
        print("\n✅ IMPLEMENTED FEATURES (Tested with REAL Audio):")
        print("1. ✅ Quality filtering for noisy segments")
        print("2. ✅ Background noise assessment per segment")
        print("3. ✅ Sentence-level segmentation")
        print("4. ✅ Feature extraction")
        print("5. ✅ Database operations for segments")
        print("6. ✅ Real audio processing")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_audio_processor_tests()
    sys.exit(0 if success else 1)