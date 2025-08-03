from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from typing import List, Dict, Any
import os
import asyncio
import logging
import zipfile
import tempfile
import shutil
from pathlib import Path

from .database import AudioDatabase
from .audio_processor import AudioProcessor
from .asr_model import WhisperASR
from .feature_extractor import FeatureExtractor
import uuid

app = FastAPI(title="Audio Processing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = AudioDatabase()
audio_processor = AudioProcessor()
asr_model = WhisperASR()
feature_extractor = FeatureExtractor()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "audio-processor-api"}

@app.get("/api/audio-files")
async def get_audio_files():
    """Get all processed audio files"""
    try:
        files = db.get_all_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio-files/{file_id}")
async def get_audio_file(file_id: int):
    """Get specific audio file details"""
    try:
        file_data = db.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        return file_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio-files/{file_id}/segments")
async def get_file_segments(file_id: int):
    """Get all segments for a specific file with quality metrics"""
    try:
        segments = db.get_segments_by_file_id(file_id)
        return {"segments": segments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml-ready-segments")
async def get_ml_ready_segments(min_quality: float = 0.3, limit: int = 100):
    """Get high-quality segments suitable for ML training"""
    try:
        segments = db.get_ml_ready_segments(min_quality_score=min_quality, limit=limit)
        return {"segments": segments, "count": len(segments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quality-statistics")
async def get_quality_statistics():
    """Get comprehensive quality statistics"""
    try:
        stats = db.get_quality_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio-files/{file_id}/audio")
async def get_audio_file_stream(file_id: int):
    """Stream audio file for playback"""
    try:
        file_data = db.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        audio_path = file_data.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename=f"audio_{file_id}.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-audio")
async def process_audio_file(file: UploadFile = File(...)):
    """Process uploaded audio file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a')):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save uploaded file to processed_data directory
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"/app/processed_data/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the audio file
        result = await process_audio_pipeline(file_path)
        
        return {"message": "File processed successfully", "data": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_audio_pipeline(audio_path: str) -> Dict[str, Any]:
    """Complete audio processing pipeline"""
    try:
        # Process audio (normalize, convert sample rate)
        processed_path = audio_processor.process_audio(audio_path)
        
        # Generate transcript
        transcript = asr_model.transcribe(processed_path)
        
        # Extract features
        duration = audio_processor.get_duration(processed_path)
        wpm = feature_extractor.calculate_wpm(transcript, duration)
        filler_ratio = feature_extractor.calculate_filler_ratio(transcript)
        sentiment_score = feature_extractor.calculate_sentiment(transcript)
        
        # Store in database
        file_data = {
            "filename": os.path.basename(audio_path),
            "duration": duration,
            "transcript": transcript,
            "wpm": wpm,
            "filler_ratio": filler_ratio,
            "sentiment_score": sentiment_score,
            "audio_path": processed_path
        }
        
        file_id = db.insert_audio_file(file_data)
        file_data["id"] = file_id
        
        return file_data
    
    except Exception as e:
        raise Exception(f"Processing failed: {str(e)}")

@app.post("/api/process-audio-ml")
async def process_audio_ml(file: UploadFile = File(...)):
    """Process uploaded audio file for ML training with hardcoded 60 segments maximum"""
    try:
        # Accept any audio file type
        import uuid
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"/app/processed_data/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Normalize and resample
        processed_path = audio_processor.process_audio(file_path)

        # Create ML-ready segments with hardcoded 60 segments maximum
        segments = audio_processor.create_ml_ready_segments(
            processed_path, asr_model
        )

        # Calculate features for full audio and build transcript
        full_transcript = " ".join([seg['transcript'] for seg in segments])
        duration = audio_processor.get_duration(processed_path)
        
        # Calculate features for the full audio
        full_wpm = feature_extractor.calculate_wpm(full_transcript, duration)
        full_filler_ratio = feature_extractor.calculate_filler_ratio(full_transcript)
        full_sentiment = feature_extractor.calculate_sentiment(full_transcript)

        # Store original file with calculated features
        file_id = db.insert_audio_file({
            "filename": os.path.basename(file_path),
            "duration": duration,
            "transcript": full_transcript,
            "wpm": full_wpm,
            "filler_ratio": full_filler_ratio,
            "sentiment_score": full_sentiment,
            "audio_path": processed_path
        })

        # Store segments with quality metrics
        stored_segments = []
        for segment in segments:
            # Extract features for segment
            segment_wpm = feature_extractor.calculate_wpm(
                segment['transcript'], segment['duration']
            )
            segment_filler_ratio = feature_extractor.calculate_filler_ratio(
                segment['transcript']
            )
            segment_sentiment = feature_extractor.calculate_sentiment(
                segment['transcript']
            )
            
            # Calculate training priority based on quality and content
            training_priority = segment['quality_metrics']['quality_score']
            if segment_wpm > 0 and segment_wpm < 200:  # Good speech rate
                training_priority += 0.1
            if segment_filler_ratio < 0.1:  # Low filler words
                training_priority += 0.1
            if len(segment['transcript'].split()) >= 5:  # Good length
                training_priority += 0.1
            
            # Store segment with comprehensive metrics
            segment_data = {
                "original_file_id": file_id,
                "segment_index": segment['index'],
                "start_time": segment['start_time'],
                "end_time": segment['end_time'],
                "duration": segment['duration'],
                "transcript": segment['transcript'],
                "audio_path": segment['audio_path'],
                "wpm": segment_wpm,
                "filler_ratio": segment_filler_ratio,
                "sentiment_score": segment_sentiment,
                "quality_score": segment['quality_metrics']['quality_score'],
                "volume": segment['quality_metrics']['volume'],
                "volume_db": segment['quality_metrics']['volume_db'],
                "noise_ratio": segment['quality_metrics']['noise_ratio'],
                "snr_estimate": segment['quality_metrics']['snr_estimate'],
                "zero_crossing_rate": segment['quality_metrics']['zero_crossing_rate'],
                "spectral_centroid": segment['quality_metrics']['spectral_centroid'],
                "is_ml_ready": True,
                "training_priority": min(1.0, training_priority)
            }
            
            segment_id = db.insert_segment_with_quality(segment_data)
            segment_data['id'] = segment_id
            stored_segments.append(segment_data)

        return {
            "message": "ML audio-text pairs created successfully",
            "file_id": file_id,
            "segments_created": len(stored_segments),
            "segments": stored_segments,
            "full_audio_features": {
                "wpm": full_wpm,
                "filler_ratio": full_filler_ratio,
                "sentiment_score": full_sentiment,
                "transcript": full_transcript
            },
            "quality_summary": {
                "average_quality_score": sum(s['quality_score'] for s in stored_segments) / len(stored_segments) if stored_segments else 0,
                "high_quality_segments": len([s for s in stored_segments if s['quality_score'] >= 0.7]),
                "total_segments": len(stored_segments)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-audio-advanced")
async def process_audio_advanced(file: UploadFile = File(...)):
    """Advanced audio processing with comprehensive segmentation and quality analysis"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a')):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save uploaded file
        import uuid
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"/app/processed_data/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process audio
        processed_path = audio_processor.process_audio(file_path)
        duration = audio_processor.get_duration(processed_path)
        
        # Get Whisper transcription with timestamps
        whisper_result = asr_model.transcribe_with_timestamps(processed_path)
        
        # Store original file
        file_id = db.insert_audio_file({
            "filename": os.path.basename(file_path),
            "duration": duration,
            "transcript": whisper_result['text'],
            "wpm": feature_extractor.calculate_wpm(whisper_result['text'], duration),
            "filler_ratio": feature_extractor.calculate_filler_ratio(whisper_result['text']),
            "sentiment_score": feature_extractor.calculate_sentiment(whisper_result['text']),
            "audio_path": processed_path
        })
        
        # Process segments with quality filtering
        segments = audio_processor.segment_with_whisper(processed_path, asr_model)
        
        # Store segments
        stored_segments = []
        for segment in segments:
            segment_data = {
                "original_file_id": file_id,
                "segment_index": segment['index'],
                "start_time": segment['start_time'],
                "end_time": segment['end_time'],
                "duration": segment['duration'],
                "transcript": segment['transcript'],
                "audio_path": segment['audio_path'],
                "wpm": feature_extractor.calculate_wpm(segment['transcript'], segment['duration']),
                "filler_ratio": feature_extractor.calculate_filler_ratio(segment['transcript']),
                "sentiment_score": feature_extractor.calculate_sentiment(segment['transcript']),
                "quality_score": segment['quality_metrics']['quality_score'],
                "volume": segment['quality_metrics']['volume'],
                "volume_db": segment['quality_metrics']['volume_db'],
                "noise_ratio": segment['quality_metrics']['noise_ratio'],
                "snr_estimate": segment['quality_metrics']['snr_estimate'],
                "zero_crossing_rate": segment['quality_metrics']['zero_crossing_rate'],
                "spectral_centroid": segment['quality_metrics']['spectral_centroid'],
                "is_ml_ready": segment['quality_metrics']['is_acceptable'],
                "training_priority": segment['quality_metrics']['quality_score']
            }
            
            segment_id = db.insert_segment_with_quality(segment_data)
            segment_data['id'] = segment_id
            stored_segments.append(segment_data)
        
        return {
            "message": "Advanced audio processing completed",
            "file_id": file_id,
            "total_segments": len(stored_segments),
            "quality_segments": len([s for s in stored_segments if s['is_ml_ready']]),
            "average_quality_score": sum(s['quality_score'] for s in stored_segments) / len(stored_segments) if stored_segments else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio-files/{file_id}/segments/{segment_id}/download")
async def download_segment(file_id: int, segment_id: int):
    """Download a specific audio segment"""
    try:
        # Get segment data from database
        segments = db.get_segments_by_file_id(file_id)
        segment = None
        for seg in segments:
            if seg['id'] == segment_id:
                segment = seg
                break
        
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        audio_path = segment.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Segment audio file not found")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename=f"segment_{segment_id:03d}.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio-files/{file_id}/segments/download-zip")
async def download_file_segments_zip(file_id: int):
    """Download all segments for a specific file as a zip"""
    try:
        # Get file data
        file_data = db.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get all segments for this file
        segments = db.get_segments_by_file_id(file_id)
        if not segments:
            raise HTTPException(status_code=404, detail="No segments found for this file")
        
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            # Add segments to zip
            for segment in segments:
                audio_path = segment.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    # Create filename for zip
                    segment_filename = f"segment_{segment['segment_index']:03d}.wav"
                    
                    # Add audio file to zip
                    zipf.write(audio_path, segment_filename)
                    
                    # Add transcript as text file
                    transcript_filename = f"segment_{segment['segment_index']:03d}.txt"
                    transcript_content = segment.get("transcript", "")
                    zipf.writestr(transcript_filename, transcript_content)
                    
                    # Add metadata as JSON
                    metadata_filename = f"segment_{segment['segment_index']:03d}_metadata.json"
                    metadata = {
                        "segment_index": segment['segment_index'],
                        "start_time": segment['start_time'],
                        "end_time": segment['end_time'],
                        "duration": segment['duration'],
                        "quality_score": segment['quality_score'],
                        "wpm": segment['wpm'],
                        "filler_ratio": segment['filler_ratio'],
                        "sentiment_score": segment['sentiment_score'],
                        "is_ml_ready": segment['is_ml_ready']
                    }
                    import json
                    zipf.writestr(metadata_filename, json.dumps(metadata, indent=2))
        
        # Return the zip file
        return FileResponse(
            path=temp_zip.name,
            media_type="application/zip",
            filename=f"segments_{file_id}.zip",
            background=lambda: os.unlink(temp_zip.name)  # Clean up after download
        )
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_zip' in locals() and os.path.exists(temp_zip.name):
            os.unlink(temp_zip.name)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml-ready-segments/download-zip")
async def download_ml_ready_segments_zip(min_quality: float = 0.3, limit: int = 100):
    """Download ML-ready segments as a zip file"""
    try:
        # Get ML-ready segments
        segments = db.get_ml_ready_segments(min_quality_score=min_quality, limit=limit)
        if not segments:
            raise HTTPException(status_code=404, detail="No ML-ready segments found")
        
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            # Add segments to zip
            for segment in segments:
                audio_path = segment.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    # Create filename for zip
                    segment_filename = f"ml_segment_{segment['id']:03d}.wav"
                    
                    # Add audio file to zip
                    zipf.write(audio_path, segment_filename)
                    
                    # Add transcript as text file
                    transcript_filename = f"ml_segment_{segment['id']:03d}.txt"
                    transcript_content = segment.get("transcript", "")
                    zipf.writestr(transcript_filename, transcript_content)
                    
                    # Add metadata as JSON
                    metadata_filename = f"ml_segment_{segment['id']:03d}_metadata.json"
                    metadata = {
                        "segment_id": segment['id'],
                        "original_file_id": segment['original_file_id'],
                        "segment_index": segment['segment_index'],
                        "start_time": segment['start_time'],
                        "end_time": segment['end_time'],
                        "duration": segment['duration'],
                        "quality_score": segment['quality_score'],
                        "wpm": segment['wpm'],
                        "filler_ratio": segment['filler_ratio'],
                        "sentiment_score": segment['sentiment_score'],
                        "training_priority": segment['training_priority'],
                        "volume_db": segment['volume_db'],
                        "noise_ratio": segment['noise_ratio'],
                        "snr_estimate": segment['snr_estimate']
                    }
                    import json
                    zipf.writestr(metadata_filename, json.dumps(metadata, indent=2))
        
        # Return the zip file
        return FileResponse(
            path=temp_zip.name,
            media_type="application/zip",
            filename=f"ml_ready_segments_q{min_quality}_n{len(segments)}.zip",
            background=lambda: os.unlink(temp_zip.name)  # Clean up after download
        )
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_zip' in locals() and os.path.exists(temp_zip.name):
            os.unlink(temp_zip.name)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 