import librosa
import soundfile as sf
import numpy as np
import os
from typing import List, Tuple, Dict, Any
from pydub import AudioSegment
import wave
import contextlib

class AudioProcessor:
    def __init__(self, target_sr: int = 16000, target_channels: int = 1):
        self.target_sr = target_sr
        self.target_channels = target_channels
        self.silence_threshold = 0.5  # seconds
        self.min_segment_length = 1.0  # seconds
        self.max_segment_length = 30.0  # seconds
        # Quality thresholds - made more lenient for user's audio files
        self.min_volume_threshold = 0.0005  # Lowered further for more tolerance
        self.max_noise_ratio = 0.9  # Increased tolerance for background noise
        self.min_snr_threshold = 3.0  # Lowered threshold for SNR
        self.min_quality_score = 0.05  # Much lower threshold for acceptance
    
    def process_audio(self, audio_path: str) -> str:
        """Process audio file: normalize, convert sample rate, etc."""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Convert to mono if stereo
            if len(y.shape) > 1:
                y = np.mean(y, axis=1)
            
            # Resample if needed
            if sr != self.target_sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.target_sr)
            
            # Normalize volume with less aggressive normalization
            # Use peak normalization instead of RMS normalization
            max_val = np.max(np.abs(y))
            if max_val > 0:
                y = y / max_val * 0.8  # Scale to 80% of max to avoid clipping
            
            # Save processed audio
            output_path = audio_path.replace('.mp3', '_processed.wav').replace('.wav', '_processed.wav')
            sf.write(output_path, y, self.target_sr)
            
            return output_path
        
        except Exception as e:
            raise Exception(f"Audio processing failed: {str(e)}")
    
    def get_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            return len(y) / sr
        except Exception as e:
            raise Exception(f"Failed to get duration: {str(e)}")
    
    def assess_segment_quality(self, audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Comprehensive quality assessment for audio segments
        
        Args:
            audio_segment: Audio segment as numpy array
            sr: Sample rate
        
        Returns:
            Dictionary with quality metrics
        """
        try:
            # Volume assessment - use RMS for better volume detection
            volume = float(np.sqrt(np.mean(audio_segment**2)))
            volume_db = 20 * np.log10(volume + 1e-10)
            
            # Background noise assessment
            spectral_flatness = librosa.feature.spectral_flatness(y=audio_segment, sr=sr)
            noise_ratio = float(np.mean(spectral_flatness))
            
            # Signal-to-noise ratio estimation
            # Use spectral contrast as a proxy for SNR
            spectral_contrast = librosa.feature.spectral_contrast(y=audio_segment, sr=sr)
            snr_estimate = float(np.mean(spectral_contrast))
            
            # Zero crossing rate (indicates noise level)
            zcr = float(librosa.feature.zero_crossing_rate(audio_segment).mean())
            
            # Spectral centroid (indicates frequency content)
            spectral_centroid = float(librosa.feature.spectral_centroid(y=audio_segment, sr=sr).mean())
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                volume, noise_ratio, snr_estimate, zcr, spectral_centroid
            )
            
            return {
                'volume': volume,
                'volume_db': volume_db,
                'noise_ratio': noise_ratio,
                'snr_estimate': snr_estimate,
                'zero_crossing_rate': zcr,
                'spectral_centroid': spectral_centroid,
                'quality_score': quality_score,
                'is_acceptable': quality_score >= self.min_quality_score
            }
        
        except Exception as e:
            print(f"Quality assessment error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'volume': 0.0,
                'volume_db': -60.0,
                'noise_ratio': 1.0,
                'snr_estimate': 0.0,
                'zero_crossing_rate': 0.0,
                'spectral_centroid': 0.0,
                'quality_score': 0.0,
                'is_acceptable': False
            }
    
    def _calculate_quality_score(self, volume: float, noise_ratio: float, 
                                snr_estimate: float, zcr: float, spectral_centroid: float) -> float:
        """
        Calculate comprehensive quality score for audio segment
        
        Args:
            volume: Average volume
            noise_ratio: Background noise ratio
            snr_estimate: Signal-to-noise ratio estimate
            zcr: Zero crossing rate
            spectral_centroid: Spectral centroid frequency
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Volume component (0-0.3) - adjusted for RMS volume calculation
        volume_score = min(1.0, volume / 0.1) * 0.3  # Adjusted for RMS calculation
        
        # Noise component (0-0.3) - more tolerant of background noise
        noise_score = max(0.0, 1.0 - noise_ratio * 0.8) * 0.3  # More tolerant scaling
        
        # SNR component (0-0.2) - much more lenient
        snr_score = min(1.0, snr_estimate / 2.0) * 0.2  # Lowered threshold from 5.0 to 2.0
        
        # Frequency content component (0-0.1) - wider range
        freq_score = 0.0
        if 30 <= spectral_centroid <= 15000:  # Much wider range (was 50-10000)
            freq_score = 0.1
        
        # Zero crossing rate component (0-0.1) - more tolerant
        zcr_score = max(0.0, 1.0 - zcr * 2.0) * 0.1  # More tolerant scaling (was 3.0)
        
        total_score = volume_score + noise_score + snr_score + freq_score + zcr_score
        return min(1.0, total_score)
    
    def segment_audio_by_silence(self, audio_path: str) -> List[Dict[str, Any]]:
        """Segment audio based on silence detection using energy threshold"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Convert to mono
            if len(y.shape) > 1:
                y = np.mean(y, axis=1)
            
            # Resample to 16kHz
            if sr != 16000:
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            
            # Find speech segments using energy threshold
            segments = self._find_speech_segments_energy(y, 16000)
            
            # Process segments
            processed_segments = []
            for i, (start, end) in enumerate(segments):
                segment_duration = end - start
                
                # Filter by duration
                if self.min_segment_length <= segment_duration <= self.max_segment_length:
                    # Extract segment
                    start_sample = int(start * 16000)
                    end_sample = int(end * 16000)
                    segment_audio = y[start_sample:end_sample]
                    
                    # Quality assessment
                    quality_metrics = self.assess_segment_quality(segment_audio, 16000)
                    
                    # Only include high-quality segments
                    if quality_metrics['is_acceptable']:
                        # Save segment
                        segment_path = f"{audio_path}_segment_{i:03d}.wav"
                        sf.write(segment_path, segment_audio, 16000)
                        
                        processed_segments.append({
                            'index': i,
                            'start_time': start,
                            'end_time': end,
                            'duration': segment_duration,
                            'audio_path': segment_path,
                            'quality_metrics': quality_metrics
                        })
            
            return processed_segments
        
        except Exception as e:
            raise Exception(f"Audio segmentation failed: {str(e)}")
    
    def _find_speech_segments_energy(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Find speech segments using energy threshold"""
        # Calculate energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            energy.append(np.sum(frame ** 2))
        
        energy = np.array(energy)
        
        # Normalize energy
        energy = (energy - np.mean(energy)) / np.std(energy)
        
        # Threshold for speech detection
        threshold = 0.5
        speech_frames = energy > threshold
        
        # Find segments
        segments = []
        is_speech = False
        speech_start = 0
        
        for i, is_speech_frame in enumerate(speech_frames):
            time = i * hop_length / sr
            
            if is_speech_frame and not is_speech:
                # Speech started
                speech_start = time
                is_speech = True
            elif not is_speech_frame and is_speech:
                # Speech ended
                speech_end = time
                if speech_end - speech_start >= self.min_segment_length:
                    segments.append((speech_start, speech_end))
                is_speech = False
        
        # Handle case where speech continues to end
        if is_speech:
            speech_end = len(audio) / sr
            if speech_end - speech_start >= self.min_segment_length:
                segments.append((speech_start, speech_end))
        
        return segments
    
    def segment_with_whisper(self, audio_path: str, whisper_model) -> List[Dict[str, Any]]:
        """Segment audio using Whisper timestamps with enhanced quality filtering"""
        try:
            # Use Whisper to get transcription with timestamps
            result = whisper_model.transcribe_with_timestamps(audio_path)
            
            segments = []
            if 'segments' in result and result['segments']:
                # Process each segment from Whisper
                for i, segment in enumerate(result['segments']):
                    if isinstance(segment, dict) and 'text' in segment:
                        # Extract segment audio and assess quality
                        start_time = segment.get('start', 0.0)
                        end_time = segment.get('end', start_time + 10.0)
                        duration = end_time - start_time
                        
                        # Only process segments with reasonable duration
                        if duration >= 1.0 and duration <= 30.0:
                            # Load audio for this segment
                            y, sr = librosa.load(audio_path, sr=None)
                            start_sample = int(start_time * sr)
                            end_sample = int(end_time * sr)
                            
                            if start_sample < len(y) and end_sample <= len(y):
                                segment_audio = y[start_sample:end_sample]
                                
                                # Assess quality
                                quality_metrics = self.assess_segment_quality(segment_audio, sr)
                                
                                # Save segment audio
                                segment_filename = f"{audio_path}_segment_{i:03d}.wav"
                                sf.write(segment_filename, segment_audio, sr)
                                
                                segments.append({
                                    'index': i,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'duration': duration,
                                    'transcript': segment['text'].strip(),
                                    'audio_path': segment_filename,
                                    'quality_metrics': quality_metrics
                                })
            
            # If no segments from Whisper, fall back to sentence-based approach
            if not segments:
                # Use basic transcription and split into sentences
                basic_result = whisper_model.transcribe(audio_path)
                text = basic_result['text']
                sentences = self._split_into_sentences(text)
                
                # Estimate timing for sentences
                total_duration = self.get_duration(audio_path)
                time_per_sentence = total_duration / max(len(sentences), 1)
                
                for i, sentence in enumerate(sentences):
                    if self._is_complete_sentence(sentence):
                        start_time = i * time_per_sentence
                        end_time = (i + 1) * time_per_sentence
                        duration = time_per_sentence
                        
                        # Load audio for this segment
                        y, sr = librosa.load(audio_path, sr=None)
                        start_sample = int(start_time * sr)
                        end_sample = int(end_time * sr)
                        
                        if start_sample < len(y) and end_sample <= len(y):
                            segment_audio = y[start_sample:end_sample]
                            
                            # Assess quality
                            quality_metrics = self.assess_segment_quality(segment_audio, sr)
                            
                            # Save segment audio
                            segment_filename = f"{audio_path}_segment_{i:03d}.wav"
                            sf.write(segment_filename, segment_audio, sr)
                            
                            segments.append({
                                'index': i,
                                'start_time': start_time,
                                'end_time': end_time,
                                'duration': duration,
                                'transcript': sentence.strip(),
                                'audio_path': segment_filename,
                                'quality_metrics': quality_metrics
                            })
            
            return segments
        
        except Exception as e:
            raise Exception(f"Whisper segmentation failed: {str(e)}")
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting based on punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_complete_sentence(self, text: str) -> bool:
        """Enhanced sentence completeness check"""
        text = text.strip()
        
        # Basic checks
        if len(text) < 10:  # Too short
            return False
        
        if not text[0].isupper():  # Doesn't start with capital
            return False
        
        # Check for sentence endings
        sentence_endings = ['.', '!', '?']
        if not any(text.endswith(ending) for ending in sentence_endings):
            return False
        
        # Check for minimum word count
        words = text.split()
        if len(words) < 3:  # Too few words
            return False
        
        # Check for common incomplete patterns
        incomplete_patterns = [
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean',
            'basically', 'actually', 'literally'
        ]
        
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in incomplete_patterns):
            # If it's just a filler word, reject
            if len(words) <= 2:
                return False
        
        return True
    
    def create_ml_ready_segments(self, audio_path: str, whisper_model, 
                                min_segments: int = 50) -> List[Dict[str, Any]]:
        """
        Create ML-ready segments with comprehensive quality filtering
        
        Args:
            audio_path: Path to audio file
            whisper_model: Whisper model instance
            min_segments: Minimum number of segments to generate
        
        Returns:
            List of high-quality segments suitable for ML training
        """
        try:
            # Get all potential segments
            all_segments = self.segment_with_whisper(audio_path, whisper_model)
            
            # Sort by quality score
            all_segments.sort(key=lambda x: x['quality_metrics']['quality_score'], reverse=True)
            
            # Filter for minimum quality threshold
            high_quality_segments = [
                seg for seg in all_segments 
                if seg['quality_metrics']['quality_score'] >= self.min_quality_score
            ]
            
            # Ensure we have enough segments
            if len(high_quality_segments) < min_segments:
                # Lower quality threshold if needed
                quality_scores = [seg['quality_metrics']['quality_score'] for seg in all_segments]
                if quality_scores:
                    # Use 25th percentile as new threshold
                    new_threshold = np.percentile(quality_scores, 25)
                    high_quality_segments = [
                        seg for seg in all_segments 
                        if seg['quality_metrics']['quality_score'] >= new_threshold
                    ]
            
            # Return top segments (up to min_segments)
            return high_quality_segments[:min_segments]
        
        except Exception as e:
            raise Exception(f"ML-ready segment creation failed: {str(e)}")
    
    def normalize_audio(self, audio_path: str) -> str:
        """Normalize audio volume"""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            y_normalized = librosa.util.normalize(y)
            
            output_path = audio_path.replace('.wav', '_normalized.wav')
            sf.write(output_path, y_normalized, sr)
            
            return output_path
        
        except Exception as e:
            raise Exception(f"Audio normalization failed: {str(e)}")
    
    def convert_format(self, audio_path: str, target_format: str = 'wav') -> str:
        """Convert audio to target format"""
        try:
            audio = AudioSegment.from_file(audio_path)
            output_path = audio_path.rsplit('.', 1)[0] + f'.{target_format}'
            audio.export(output_path, format=target_format)
            
            return output_path
        
        except Exception as e:
            raise Exception(f"Format conversion failed: {str(e)}") 