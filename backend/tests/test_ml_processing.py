#!/usr/bin/env python3
"""
Test script for ML processing functionality
"""

import requests
import os
from pathlib import Path

def test_ml_processing():
    """Test the ML processing endpoint"""
    
    # Check if we have any audio files to test with
    audio_dir = Path("../audio_files")
    if not audio_dir.exists():
        print("❌ No audio_files directory found")
        return
    
    # Find audio files
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.m4a"))
    
    if not audio_files:
        print("❌ No audio files found in audio_files directory")
        return
    
    print(f"🎵 Found {len(audio_files)} audio files")
    
    # Test with the first audio file
    test_file = audio_files[1]
    print(f"🧪 Testing ML processing with: {test_file.name}")
    
    # Test the ML processing endpoint
    url = "http://localhost:8000/api/process-audio-ml"
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "audio/mpeg")}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ML processing successful!")
            print(f"📊 File ID: {result.get('file_id')}")
            print(f"🎯 Segments created: {result.get('segments_created')}")
            
            # Test getting segments
            file_id = result.get('file_id')
            if file_id:
                segments_url = f"http://localhost:8000/api/audio-files/{file_id}/segments"
                segments_response = requests.get(segments_url)
                
                if segments_response.status_code == 200:
                    segments_data = segments_response.json()
                    segments = segments_data.get('segments', [])
                    print(f"📋 Retrieved {len(segments)} segments")
                    
                    if segments:
                        # Show first few segments
                        print("\n📝 First 3 segments:")
                        for i, segment in enumerate(segments[:3]):
                            print(f"  Segment {i+1}:")
                            print(f"    Duration: {segment.get('duration', 0):.2f}s")
                            print(f"    Quality: {segment.get('quality_score', 0):.2f}")
                            print(f"    Transcript: {segment.get('transcript', '')[:50]}...")
                    
                    # Test download functionality
                    download_url = f"http://localhost:8000/api/audio-files/{file_id}/segments/download-zip"
                    download_response = requests.get(download_url)
                    
                    if download_response.status_code == 200:
                        print("✅ Segment download test successful!")
                    else:
                        print(f"❌ Segment download failed: {download_response.status_code}")
                else:
                    print(f"❌ Failed to get segments: {segments_response.status_code}")
        else:
            print(f"❌ ML processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during ML processing test: {e}")

def test_web_interface():
    """Test if the web interface is accessible"""
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("✅ Web interface is accessible")
        else:
            print(f"❌ Web interface returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Web interface not accessible: {e}")

if __name__ == "__main__":
    print("🧪 Testing ML Processing System")
    print("=" * 40)
    
    # Test web interface
    test_web_interface()
    print()
    
    # Test ML processing
    test_ml_processing()
    print()
    
    print("🎉 Testing complete!")
    print("\n📋 To test the web interface:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Click 'ML Processing' button")
    print("3. Upload an audio file")
    print("4. View the created segments")
    print("5. Download segments as needed") 