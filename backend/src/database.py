import duckdb
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class AudioDatabase:
    def __init__(self, db_path: str = "/app/data/audio_data.duckdb"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize database tables with enhanced schema for ML-ready data"""
        with duckdb.connect(self.db_path) as conn:
            # Drop existing tables to ensure clean schema
            conn.execute("DROP TABLE IF EXISTS quality_metrics")
            conn.execute("DROP TABLE IF EXISTS audio_segments")
            conn.execute("DROP TABLE IF EXISTS audio_files")
            
            # Create audio_files table with proper auto-increment
            conn.execute("""
                CREATE TABLE audio_files (
                    id INTEGER PRIMARY KEY,
                    filename VARCHAR NOT NULL,
                    duration REAL,
                    transcript TEXT,
                    wpm REAL,
                    filler_ratio REAL,
                    sentiment_score REAL,
                    audio_path VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create enhanced audio_segments table for ML-ready data
            conn.execute("""
                CREATE TABLE audio_segments (
                    id INTEGER PRIMARY KEY,
                    original_file_id INTEGER,
                    segment_index INTEGER,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    transcript TEXT,
                    audio_path VARCHAR,
                    wpm REAL,
                    filler_ratio REAL,
                    sentiment_score REAL,
                    quality_score REAL,
                    -- Enhanced quality metrics
                    volume REAL,
                    volume_db REAL,
                    noise_ratio REAL,
                    snr_estimate REAL,
                    zero_crossing_rate REAL,
                    spectral_centroid REAL,
                    -- ML training metadata
                    is_ml_ready BOOLEAN DEFAULT FALSE,
                    training_priority REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create quality_metrics table for detailed analysis
            conn.execute("""
                CREATE TABLE quality_metrics (
                    id INTEGER PRIMARY KEY,
                    segment_id INTEGER,
                    metric_name VARCHAR,
                    metric_value REAL,
                    metric_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def insert_audio_file(self, file_data: Dict[str, Any]) -> int:
        """Insert audio file data and return the ID"""
        with duckdb.connect(self.db_path) as conn:
            # Get the next ID manually since DuckDB doesn't auto-increment
            result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM audio_files").fetchone()
            next_id = result[0] if result else 1
            
            # Insert with the next ID
            conn.execute("""
                INSERT INTO audio_files 
                (id, filename, duration, transcript, wpm, filler_ratio, sentiment_score, audio_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                next_id,
                file_data["filename"],
                file_data["duration"],
                file_data["transcript"],
                file_data["wpm"],
                file_data["filler_ratio"],
                file_data["sentiment_score"],
                file_data["audio_path"]
            ])
            
            return next_id
    
    def insert_segment_with_quality(self, segment_data: Dict[str, Any]) -> int:
        """Insert audio segment data with comprehensive quality metrics"""
        with duckdb.connect(self.db_path) as conn:
            # Get the next ID manually
            result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM audio_segments").fetchone()
            next_id = result[0] if result else 1
            
            conn.execute("""
                INSERT INTO audio_segments 
                (id, original_file_id, segment_index, start_time, end_time, duration,
                 transcript, audio_path, wpm, filler_ratio, sentiment_score, quality_score,
                 volume, volume_db, noise_ratio, snr_estimate, zero_crossing_rate, 
                 spectral_centroid, is_ml_ready, training_priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                next_id,
                segment_data["original_file_id"],
                segment_data["segment_index"],
                segment_data["start_time"],
                segment_data["end_time"],
                segment_data["duration"],
                segment_data["transcript"],
                segment_data["audio_path"],
                segment_data.get("wpm", 0.0),
                segment_data.get("filler_ratio", 0.0),
                segment_data.get("sentiment_score", 0.0),
                segment_data.get("quality_score", 0.0),
                segment_data.get("volume", 0.0),
                segment_data.get("volume_db", -60.0),
                segment_data.get("noise_ratio", 1.0),
                segment_data.get("snr_estimate", 0.0),
                segment_data.get("zero_crossing_rate", 0.0),
                segment_data.get("spectral_centroid", 0.0),
                segment_data.get("is_ml_ready", False),
                segment_data.get("training_priority", 0.0)
            ])
            
            return next_id
    
    def get_ml_ready_segments(self, min_quality_score: float = 0.3, 
                             limit: int = 1000) -> List[Dict[str, Any]]:
        """Get high-quality segments suitable for ML training"""
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT id, original_file_id, segment_index, start_time, end_time, 
                       duration, transcript, audio_path, wpm, filler_ratio, 
                       sentiment_score, quality_score, volume, volume_db, noise_ratio,
                       snr_estimate, zero_crossing_rate, spectral_centroid,
                       is_ml_ready, training_priority, created_at
                FROM audio_segments
                WHERE quality_score >= ? AND is_ml_ready = TRUE
                ORDER BY training_priority DESC, quality_score DESC
                LIMIT ?
            """, [min_quality_score, limit]).fetchall()
            
            columns = ["id", "original_file_id", "segment_index", "start_time", "end_time",
                      "duration", "transcript", "audio_path", "wpm", "filler_ratio",
                      "sentiment_score", "quality_score", "volume", "volume_db", "noise_ratio",
                      "snr_estimate", "zero_crossing_rate", "spectral_centroid",
                      "is_ml_ready", "training_priority", "created_at"]
            
            return [dict(zip(columns, row)) for row in result]
    
    def get_segments_by_file_id(self, file_id: int) -> List[Dict[str, Any]]:
        """Get all segments for a specific file with quality metrics"""
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT id, segment_index, start_time, end_time, duration, 
                       transcript, audio_path, wpm, filler_ratio, sentiment_score, 
                       quality_score, volume, volume_db, noise_ratio, snr_estimate,
                       zero_crossing_rate, spectral_centroid, is_ml_ready,
                       training_priority, created_at
                FROM audio_segments
                WHERE original_file_id = ?
                ORDER BY segment_index
            """, [file_id]).fetchall()
            
            columns = ["id", "segment_index", "start_time", "end_time", "duration",
                      "transcript", "audio_path", "wpm", "filler_ratio", 
                      "sentiment_score", "quality_score", "volume", "volume_db",
                      "noise_ratio", "snr_estimate", "zero_crossing_rate",
                      "spectral_centroid", "is_ml_ready", "training_priority", "created_at"]
            
            return [dict(zip(columns, row)) for row in result]
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get comprehensive quality statistics for segments"""
        with duckdb.connect(self.db_path) as conn:
            # Basic counts
            total_segments = conn.execute("SELECT COUNT(*) FROM audio_segments").fetchone()[0]
            ml_ready_segments = conn.execute("SELECT COUNT(*) FROM audio_segments WHERE is_ml_ready = TRUE").fetchone()[0]
            
            # Quality score statistics
            quality_stats = conn.execute("""
                SELECT 
                    AVG(quality_score) as avg_quality,
                    MIN(quality_score) as min_quality,
                    MAX(quality_score) as max_quality,
                    STDDEV(quality_score) as std_quality
                FROM audio_segments
            """).fetchone()
            
            # Volume statistics
            volume_stats = conn.execute("""
                SELECT 
                    AVG(volume) as avg_volume,
                    AVG(volume_db) as avg_volume_db,
                    AVG(noise_ratio) as avg_noise_ratio
                FROM audio_segments
            """).fetchone()
            
            return {
                "total_segments": total_segments,
                "ml_ready_segments": ml_ready_segments,
                "quality_score": {
                    "average": quality_stats[0] or 0.0,
                    "minimum": quality_stats[1] or 0.0,
                    "maximum": quality_stats[2] or 0.0,
                    "standard_deviation": quality_stats[3] or 0.0
                },
                "volume_metrics": {
                    "average_volume": volume_stats[0] or 0.0,
                    "average_volume_db": volume_stats[1] or -60.0,
                    "average_noise_ratio": volume_stats[2] or 1.0
                }
            }
    
    def update_segment_ml_status(self, segment_id: int, is_ml_ready: bool, 
                                training_priority: float = 0.0):
        """Update ML readiness status and training priority for a segment"""
        with duckdb.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE audio_segments 
                SET is_ml_ready = ?, training_priority = ?
                WHERE id = ?
            """, [is_ml_ready, training_priority, segment_id])
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all audio files"""
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT id, filename, duration, transcript, wpm, filler_ratio, 
                       sentiment_score, audio_path, created_at
                FROM audio_files
                ORDER BY created_at DESC
            """).fetchall()
            
            columns = ["id", "filename", "duration", "transcript", "wpm", 
                      "filler_ratio", "sentiment_score", "audio_path", "created_at"]
            
            return [dict(zip(columns, row)) for row in result]
    
    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get audio file by ID"""
        with duckdb.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT id, filename, duration, transcript, wpm, filler_ratio, 
                       sentiment_score, audio_path, created_at
                FROM audio_files
                WHERE id = ?
            """, [file_id]).fetchone()
            
            if result:
                columns = ["id", "filename", "duration", "transcript", "wpm", 
                          "filler_ratio", "sentiment_score", "audio_path", "created_at"]
                return dict(zip(columns, result))
            
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics with enhanced metrics"""
        with duckdb.connect(self.db_path) as conn:
            # Total files processed
            total_files = conn.execute("SELECT COUNT(*) FROM audio_files").fetchone()[0]
            
            # Average duration
            avg_duration = conn.execute("SELECT AVG(duration) FROM audio_files").fetchone()[0]
            
            # Average WPM
            avg_wpm = conn.execute("SELECT AVG(wpm) FROM audio_files").fetchone()[0]
            
            # Total segments
            total_segments = conn.execute("SELECT COUNT(*) FROM audio_segments").fetchone()[0]
            
            # ML-ready segments
            ml_ready_segments = conn.execute("SELECT COUNT(*) FROM audio_segments WHERE is_ml_ready = TRUE").fetchone()[0]
            
            # Average quality score
            avg_quality = conn.execute("SELECT AVG(quality_score) FROM audio_segments").fetchone()[0]
            
            return {
                "total_files": total_files,
                "total_segments": total_segments,
                "ml_ready_segments": ml_ready_segments,
                "average_duration": avg_duration or 0.0,
                "average_wpm": avg_wpm or 0.0,
                "average_quality_score": avg_quality or 0.0
            } 