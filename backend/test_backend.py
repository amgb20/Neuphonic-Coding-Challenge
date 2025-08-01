#!/usr/bin/env python3
"""
Comprehensive test suite for the audio processing backend
Tests all required features:
1. Sentence-Level Segmentation
2. Individual segment storage
3. Quality filtering for noisy segments
4. ML-Ready Data Structure
5. Background noise assessment
6. Quality scoring for training data selection
"""

import os
import sys
import tempfile
import shutil
import numpy as np
import soundfile as sf
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audio_processor import AudioProcessor
from asr_model import WhisperASR
from feature_extractor import FeatureExtractor
from database import AudioDatabase

def create_test_audio(duration=10.0, sample_rate=16000, filename="test_audio.wav"):
    """Create a test audio file with speech-like characteristics"""
    # Generate speech-like audio (sine wave with some variation)
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a speech-like signal (multiple frequencies)
    signal = (np.sin(2 * np.pi * 200 * t) +  # Base frequency
              0.5 * np.sin(2 * np.pi * 400 * t) +  # Harmonics
              0.3 * np.sin(2 * np.pi * 600 * t) +
              0.1 * np.random.randn(len(t)))  # Some noise
    
    # Normalize
    signal = signal / np.max(np.abs(signal))
    
    # Save to file
    sf.write(filename, signal, sample_rate)
    return filename

def test_sentence_level_segmentation():
    """Test sentence-level segmentation functionality"""
    print("Testing sentence-level segmentation...")
    
    # Create test audio
    test_file = create_test_audio(duration=15.0)
    
    try:
        # Initialize components
        audio_processor = AudioProcessor()
        
        # Mock Whisper model for testing
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.0,
                    'text': 'This is a complete sentence.'
                },
                {
                    'start': 3.5,
                    'end': 6.0,
                    'text': 'Another sentence here!'
                },
                {
                    'start': 6.5,
                    'end': 8.0,
                    'text': 'um uh'  # Incomplete sentence
                },
                {
                    'start': 8.5,
                    'end': 12.0,
                    'text': 'This is a longer sentence with more words.'
                }
            ]
        }
        
        # Test segmentation
        segments = audio_processor.segment_with_whisper(test_file, mock_whisper)
        
        # Verify results
        assert len(segments) > 0, "Should have at least one segment"
        
        # Check that incomplete sentences are filtered out
        incomplete_segments = [s for s in segments if 'um uh' in s.get('transcript', '')]
        assert len(incomplete_segments) == 0, "Incomplete sentences should be filtered out"
        
        # Check that complete sentences are included
        complete_segments = [s for s in segments if 'complete sentence' in s.get('transcript', '')]
        assert len(complete_segments) > 0, "Complete sentences should be included"
        
        print("✅ Sentence-level segmentation test passed")
        
    except Exception as e:
        print(f"❌ Sentence-level segmentation test failed: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_individual_segment_storage():
    """Test individual segment storage in database"""
    print("Testing individual segment storage...")
    
    # Create temporary database
    temp_db_path = "/tmp/test_audio_data.duckdb"
    
    try:
        db = AudioDatabase(temp_db_path)
        
        # Test data
        file_data = {
            "filename": "test_file.wav",
            "duration": 10.0,
            "transcript": "Test transcript",
            "wpm": 150.0,
            "filler_ratio": 0.05,
            "sentiment_score": 0.1,
            "audio_path": "/tmp/test.wav"
        }
        
        # Insert file
        file_id = db.insert_audio_file(file_data)
        assert file_id is not None, "File should be inserted successfully"
        
        # Insert segments
        segment_data = {
            "original_file_id": file_id,
            "segment_index": 0,
            "start_time": 0.0,
            "end_time": 3.0,
            "duration": 3.0,
            "transcript": "This is a test segment.",
            "audio_path": "/tmp/segment_0.wav",
            "wpm": 160.0,
            "filler_ratio": 0.02,
            "sentiment_score": 0.2,
            "quality_score": 0.8,
            "volume": 0.1,
            "volume_db": -20.0,
            "noise_ratio": 0.3,
            "snr_estimate": 15.0,
            "zero_crossing_rate": 0.1,
            "spectral_centroid": 2000.0,
            "is_ml_ready": True,
            "training_priority": 0.9
        }
        
        segment_id = db.insert_segment_with_quality(segment_data)
        assert segment_id is not None, "Segment should be inserted successfully"
        
        # Retrieve segments
        segments = db.get_segments_by_file_id(file_id)
        assert len(segments) == 1, "Should retrieve exactly one segment"
        
        # Verify segment data
        segment = segments[0]
        assert segment['transcript'] == "This is a test segment.", "Transcript should match"
        assert segment['quality_score'] == 0.8, "Quality score should match"
        assert segment['is_ml_ready'] == True, "ML ready flag should be set"
        
        print("✅ Individual segment storage test passed")
        
    except Exception as e:
        print(f"❌ Individual segment storage test failed: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_quality_filtering():
    """Test quality filtering for noisy segments"""
    print("Testing quality filtering...")
    
    try:
        audio_processor = AudioProcessor()
        
        # Create test audio segments with different quality levels
        sample_rate = 16000
        
        # High quality segment (clean speech)
        clean_speech = np.sin(2 * np.pi * 200 * np.linspace(0, 3, sample_rate * 3))
        clean_speech = clean_speech / np.max(np.abs(clean_speech))
        
        # Noisy segment (high noise)
        noise = 0.8 * np.random.randn(sample_rate * 3)
        noisy_speech = clean_speech + noise
        noisy_speech = noisy_speech / np.max(np.abs(noisy_speech))
        
        # Very quiet segment
        quiet_speech = 0.01 * clean_speech
        
        # Test quality assessment
        clean_quality = audio_processor.assess_segment_quality(clean_speech, sample_rate)
        noisy_quality = audio_processor.assess_segment_quality(noisy_speech, sample_rate)
        quiet_quality = audio_processor.assess_segment_quality(quiet_speech, sample_rate)
        
        # Verify quality filtering
        assert clean_quality['is_acceptable'] == True, "Clean speech should be acceptable"
        assert noisy_quality['is_acceptable'] == False, "Noisy speech should be rejected"
        assert quiet_quality['is_acceptable'] == False, "Quiet speech should be rejected"
        
        # Verify quality scores
        assert clean_quality['quality_score'] > noisy_quality['quality_score'], "Clean speech should have higher quality"
        assert clean_quality['quality_score'] > quiet_quality['quality_score'], "Clean speech should have higher quality"
        
        print("✅ Quality filtering test passed")
        
    except Exception as e:
        print(f"❌ Quality filtering test failed: {e}")
        raise

def test_background_noise_assessment():
    """Test background noise assessment per segment"""
    print("Testing background noise assessment...")
    
    try:
        audio_processor = AudioProcessor()
        sample_rate = 16000
        
        # Create segments with different noise characteristics
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Low noise segment
        low_noise = np.sin(2 * np.pi * 200 * t) + 0.1 * np.random.randn(len(t))
        low_noise = low_noise / np.max(np.abs(low_noise))
        
        # High noise segment
        high_noise = np.sin(2 * np.pi * 200 * t) + 0.8 * np.random.randn(len(t))
        high_noise = high_noise / np.max(np.abs(high_noise))
        
        # Assess noise levels
        low_noise_metrics = audio_processor.assess_segment_quality(low_noise, sample_rate)
        high_noise_metrics = audio_processor.assess_segment_quality(high_noise, sample_rate)
        
        # Verify noise assessment
        assert low_noise_metrics['noise_ratio'] < high_noise_metrics['noise_ratio'], "Low noise segment should have lower noise ratio"
        assert low_noise_metrics['snr_estimate'] > high_noise_metrics['snr_estimate'], "Low noise segment should have higher SNR"
        
        # Verify spectral characteristics
        assert low_noise_metrics['spectral_centroid'] > 0, "Spectral centroid should be positive"
        assert high_noise_metrics['spectral_centroid'] > 0, "Spectral centroid should be positive"
        
        print("✅ Background noise assessment test passed")
        
    except Exception as e:
        print(f"❌ Background noise assessment test failed: {e}")
        raise

def test_ml_ready_data_structure():
    """Test ML-ready data structure with 50+ segments"""
    print("Testing ML-ready data structure...")
    
    # Create test audio
    test_file = create_test_audio(duration=30.0)  # Longer file for more segments
    
    try:
        audio_processor = AudioProcessor()
        
        # Mock Whisper to return many segments
        mock_whisper = Mock()
        segments_data = []
        
        # Generate 60 segments (more than required 50)
        for i in range(60):
            segments_data.append({
                'start': i * 0.5,
                'end': (i + 1) * 0.5,
                'text': f'This is segment number {i}.'
            })
        
        mock_whisper.transcribe.return_value = {'segments': segments_data}
        
        # Test ML-ready segment creation
        ml_segments = audio_processor.create_ml_ready_segments(
            test_file, mock_whisper, min_segments=50
        )
        
        # Verify we get enough segments
        assert len(ml_segments) >= 50, f"Should have at least 50 segments, got {len(ml_segments)}"
        
        # Verify quality filtering
        for segment in ml_segments:
            assert 'quality_metrics' in segment, "Each segment should have quality metrics"
            assert 'quality_score' in segment['quality_metrics'], "Quality score should be present"
            assert segment['quality_metrics']['quality_score'] >= audio_processor.min_quality_score, "All segments should meet quality threshold"
        
        print("✅ ML-ready data structure test passed")
        
    except Exception as e:
        print(f"❌ ML-ready data structure test failed: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_quality_scoring_for_training():
    """Test quality scoring for training data selection"""
    print("Testing quality scoring for training data selection...")
    
    try:
        # Create temporary database
        temp_db_path = "/tmp/test_training_data.duckdb"
        db = AudioDatabase(temp_db_path)
        
        # Insert test segments with different quality levels
        test_segments = [
            {
                "original_file_id": 1,
                "segment_index": 0,
                "start_time": 0.0,
                "end_time": 3.0,
                "duration": 3.0,
                "transcript": "High quality segment with good content.",
                "audio_path": "/tmp/segment_0.wav",
                "wpm": 160.0,
                "filler_ratio": 0.02,
                "sentiment_score": 0.2,
                "quality_score": 0.9,
                "volume": 0.15,
                "volume_db": -16.0,
                "noise_ratio": 0.2,
                "snr_estimate": 18.0,
                "zero_crossing_rate": 0.08,
                "spectral_centroid": 2500.0,
                "is_ml_ready": True,
                "training_priority": 0.95
            },
            {
                "original_file_id": 1,
                "segment_index": 1,
                "start_time": 3.0,
                "end_time": 6.0,
                "duration": 3.0,
                "transcript": "Medium quality segment.",
                "audio_path": "/tmp/segment_1.wav",
                "wpm": 140.0,
                "filler_ratio": 0.08,
                "sentiment_score": 0.1,
                "quality_score": 0.6,
                "volume": 0.08,
                "volume_db": -22.0,
                "noise_ratio": 0.5,
                "snr_estimate": 12.0,
                "zero_crossing_rate": 0.15,
                "spectral_centroid": 1800.0,
                "is_ml_ready": True,
                "training_priority": 0.7
            },
            {
                "original_file_id": 1,
                "segment_index": 2,
                "start_time": 6.0,
                "end_time": 9.0,
                "duration": 3.0,
                "transcript": "Low quality segment with noise.",
                "audio_path": "/tmp/segment_2.wav",
                "wpm": 120.0,
                "filler_ratio": 0.15,
                "sentiment_score": -0.1,
                "quality_score": 0.3,
                "volume": 0.03,
                "volume_db": -30.0,
                "noise_ratio": 0.8,
                "snr_estimate": 8.0,
                "zero_crossing_rate": 0.25,
                "spectral_centroid": 1200.0,
                "is_ml_ready": False,
                "training_priority": 0.3
            }
        ]
        
        # Insert segments
        for segment_data in test_segments:
            db.insert_segment_with_quality(segment_data)
        
        # Test ML-ready segment retrieval
        ml_segments = db.get_ml_ready_segments(min_quality_score=0.5, limit=10)
        
        # Verify only high-quality segments are returned
        assert len(ml_segments) == 2, "Should return only high-quality segments"
        
        # Verify segments are sorted by training priority
        priorities = [seg['training_priority'] for seg in ml_segments]
        assert priorities == sorted(priorities, reverse=True), "Segments should be sorted by training priority"
        
        # Test quality statistics
        stats = db.get_quality_statistics()
        assert 'total_segments' in stats, "Statistics should include total segments"
        assert 'ml_ready_segments' in stats, "Statistics should include ML-ready segments"
        assert stats['ml_ready_segments'] == 2, "Should have 2 ML-ready segments"
        
        print("✅ Quality scoring for training test passed")
        
    except Exception as e:
        print(f"❌ Quality scoring for training test failed: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def test_feature_extraction():
    """Test feature extraction for segments"""
    print("Testing feature extraction...")
    
    try:
        feature_extractor = FeatureExtractor()
        
        # Test transcript
        transcript = "This is a test transcript for feature extraction. It contains multiple sentences and should provide good features for analysis."
        duration = 10.0
        
        # Extract features
        features = feature_extractor.extract_all_features(transcript, duration)
        
        # Verify all required features are present
        required_features = ['wpm', 'filler_ratio', 'sentiment_score', 'speech_rate', 'complexity']
        for feature in required_features:
            assert feature in features, f"Feature {feature} should be present"
        
        # Verify feature values are reasonable
        assert features['wpm'] > 0, "WPM should be positive"
        assert 0 <= features['filler_ratio'] <= 1, "Filler ratio should be between 0 and 1"
        assert -1 <= features['sentiment_score'] <= 1, "Sentiment score should be between -1 and 1"
        
        print("✅ Feature extraction test passed")
        
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
        raise

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting comprehensive backend feature tests...\n")
    
    tests = [
        test_sentence_level_segmentation,
        test_individual_segment_storage,
        test_quality_filtering,
        test_background_noise_assessment,
        test_ml_ready_data_structure,
        test_quality_scoring_for_training,
        test_feature_extraction
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
    
    print("📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! All required features are implemented correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 