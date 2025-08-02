#!/usr/bin/env python3
"""
Backend Test Script
Run this to test the audio processing backend functionality with real audio files
"""

import requests
import json
import os
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
# Fix the path to be relative to the backend directory
AUDIO_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "audio_files")

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_list_files():
    """Test listing audio files"""
    print("📋 Testing list audio files...")
    response = requests.get(f"{API_BASE_URL}/api/audio-files")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        files = response.json()["files"]
        print(f"Found {len(files)} processed files:")
        for file in files:
            print(f"  - {file['filename']} (ID: {file['id']})")
    print()

def test_get_file_details(file_id: int):
    """Test getting specific file details"""
    print(f"📄 Testing get file details for ID {file_id}...")
    response = requests.get(f"{API_BASE_URL}/api/audio-files/{file_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        file_data = response.json()
        print(f"File: {file_data['filename']}")
        print(f"Duration: {file_data['duration']:.2f}s")
        print(f"WPM: {file_data['wpm']:.1f}")
        print(f"Filler Ratio: {file_data['filler_ratio']:.3f}")
        print(f"Sentiment: {file_data['sentiment_score']:.3f}")
        print(f"Transcript preview: {file_data['transcript'][:100]}...")
    print()

def test_get_file_segments(file_id: int):
    """Test getting segments for a specific file"""
    print(f"🎵 Testing get segments for file ID {file_id}...")
    response = requests.get(f"{API_BASE_URL}/api/audio-files/{file_id}/segments")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        segments = response.json()["segments"]
        print(f"Found {len(segments)} segments:")
        for i, segment in enumerate(segments[:5]):  # Show first 5 segments
            print(f"  Segment {i+1}: {segment['transcript'][:50]}... (Quality: {segment['quality_score']:.2f})")
    print()

def test_ml_ready_segments():
    """Test getting ML-ready segments"""
    print("🤖 Testing ML-ready segments...")
    response = requests.get(f"{API_BASE_URL}/api/ml-ready-segments")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} ML-ready segments")
        if data['segments']:
            print("Sample segments:")
            for i, segment in enumerate(data['segments'][:3]):
                print(f"  {i+1}. Quality: {segment['quality_score']:.2f}, Training Priority: {segment['training_priority']:.2f}")
    print()

def test_quality_statistics():
    """Test getting quality statistics"""
    print("📊 Testing quality statistics...")
    response = requests.get(f"{API_BASE_URL}/api/quality-statistics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Total segments: {stats['total_segments']}")
        print(f"ML-ready segments: {stats['ml_ready_segments']}")
        print(f"Average quality score: {stats['quality_score']['average']:.2f}")
    print()

def test_upload_and_process(audio_file_path: str):
    """Test uploading and processing an audio file"""
    print(f"🎵 Testing upload and process: {audio_file_path}")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ File not found: {audio_file_path}")
        return
    
    with open(audio_file_path, 'rb') as f:
        files = {'file': (os.path.basename(audio_file_path), f, 'audio/mpeg')}
        response = requests.post(f"{API_BASE_URL}/api/process-audio", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ File processed successfully!")
        print(f"Data: {json.dumps(result['data'], indent=2)}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_upload_and_process_ml(audio_file_path: str):
    """Test uploading and processing an audio file for ML training"""
    print(f"🤖 Testing ML upload and process: {audio_file_path}")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ File not found: {audio_file_path}")
        return
    
    with open(audio_file_path, 'rb') as f:
        files = {'file': (os.path.basename(audio_file_path), f, 'audio/mpeg')}
        response = requests.post(f"{API_BASE_URL}/api/process-audio-ml", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ ML processing completed successfully!")
        print(f"Segments created: {result['segments_created']}")
        print(f"Quality summary: {result['quality_summary']}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_audio_streaming(file_id: int):
    """Test audio file streaming"""
    print(f"🎧 Testing audio streaming for file ID {file_id}...")
    response = requests.head(f"{API_BASE_URL}/api/audio-files/{file_id}/audio")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Audio file available for streaming")
    else:
        print(f"❌ Error: {response.status_code}")
    print()

def list_available_audio_files():
    """List available audio files for testing"""
    print("📁 Available audio files for testing:")
    audio_dir = Path(AUDIO_FILES_DIR)
    print(f"Looking for audio files in: {audio_dir.absolute()}")
    if audio_dir.exists():
        for file in audio_dir.glob("*.mp3"):
            print(f"  - {file.name}")
    else:
        print("  No audio files directory found")
    print()

def test_specific_file(filename: str):
    """Test processing a specific audio file"""
    print(f"🎵 Testing specific file: {filename}")
    file_path = Path(AUDIO_FILES_DIR) / filename
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    test_upload_and_process(str(file_path))
    test_upload_and_process_ml(str(file_path))
    return True

def test_batch_processing(max_files: int = 3):
    """Test processing multiple files"""
    print(f"🔄 Testing batch processing (max {max_files} files)...")
    audio_dir = Path(AUDIO_FILES_DIR)
    if not audio_dir.exists():
        print("❌ Audio files directory not found")
        return
    
    mp3_files = list(audio_dir.glob("*.mp3"))
    if not mp3_files:
        print("❌ No MP3 files found")
        return
    
    # Process up to max_files
    files_to_process = mp3_files[:max_files]
    print(f"Found {len(files_to_process)} files to process:")
    
    for i, file_path in enumerate(files_to_process, 1):
        print(f"\n[{i}/{len(files_to_process)}] Processing: {file_path.name}")
        test_upload_and_process(str(file_path))
        test_upload_and_process_ml(str(file_path))
        time.sleep(2)  # Small delay between uploads
    
    print(f"\n✅ Batch processing complete! Processed {len(files_to_process)} files")

def main():
    """Main test function"""
    print("🧪 Backend Testing Suite")
    print("=" * 50)
    
    # Test basic functionality
    test_health()
    test_list_files()
    test_ml_ready_segments()
    test_quality_statistics()
    
    # Test with existing files
    test_get_file_details(1)
    test_get_file_segments(1)
    test_audio_streaming(1)
    
    # List available files for upload testing
    list_available_audio_files()
    
    # Interactive testing
    print("\n🎵 Interactive Testing Options:")
    print("1. Test batch processing (automatic)")
    print("2. Test a specific file (manual input)")
    print("3. Skip file testing")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🔄 Running batch processing...")
            test_batch_processing(max_files=2)
        elif choice == "2":
            print("\n📁 Available files for testing:")
            audio_dir = Path(AUDIO_FILES_DIR)
            print(f"Looking for audio files in: {audio_dir.absolute()}")
            if audio_dir.exists():
                mp3_files = list(audio_dir.glob("*.mp3"))
                print(f"Found {len(mp3_files)} MP3 files")
                for i, file in enumerate(mp3_files, 1):
                    print(f"  {i}. {file.name}")
                
                if mp3_files:
                    try:
                        file_choice = input(f"\nEnter file number (1-{len(mp3_files)}): ").strip()
                        file_index = int(file_choice) - 1
                        if 0 <= file_index < len(mp3_files):
                            selected_file = mp3_files[file_index]
                            print(f"\n🎵 Testing file: {selected_file.name}")
                            test_specific_file(selected_file.name)
                        else:
                            print("❌ Invalid file number")
                    except ValueError:
                        print("❌ Please enter a valid number")
                else:
                    print("❌ No MP3 files found in directory")
            else:
                print(f"❌ Audio files directory not found: {audio_dir.absolute()}")
        elif choice == "3":
            print("⏭️ Skipping file testing")
        else:
            print("❌ Invalid choice, skipping file testing")
    
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    
    print("\n✅ Backend testing complete!")

if __name__ == "__main__":
    main() 