#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from asr_model import WhisperASR
from audio_processor import AudioProcessor

def test_whisper_only():
    """Test Whisper-only segmentation without any quality constraints"""
    print("🧪 Testing Whisper-Only Segmentation")
    print("=" * 50)
    
    try:
        # Initialize components
        asr_model = WhisperASR()
        audio_processor = AudioProcessor()
        
        # Test with a real audio file
        audio_path = "../audio_files/Script 1.mp3"
        
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return
        
        print(f"📁 Using audio file: {audio_path}")
        
        # Test Whisper transcription with timestamps
        print("\n🎯 Testing Whisper transcription...")
        timestamp_result = asr_model.transcribe_with_timestamps(audio_path)
        print(f"Number of Whisper segments: {len(timestamp_result['segments'])}")
        
        # Test the segmentation function
        print("\n🎯 Testing segment_with_whisper function...")
        segments = audio_processor.segment_with_whisper(audio_path, asr_model)
        print(f"Number of segments created: {len(segments)}")
        
        # Test ML-ready segments (should return all segments up to 60)
        print("\n🎯 Testing create_ml_ready_segments function...")
        ml_segments = audio_processor.create_ml_ready_segments(audio_path, asr_model)
        print(f"Number of ML-ready segments: {len(ml_segments)}")
        
        # Show first few segments
        print("\n📋 First 5 segments:")
        for i, segment in enumerate(ml_segments[:5]):
            print(f"  Segment {i+1}:")
            print(f"    Start: {segment['start_time']:.2f}s")
            print(f"    End: {segment['end_time']:.2f}s")
            print(f"    Duration: {segment['duration']:.2f}s")
            print(f"    Text: {segment['transcript'][:100]}...")
            print()
        
        print("✅ Test complete!")
        return len(ml_segments)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    test_whisper_only() 