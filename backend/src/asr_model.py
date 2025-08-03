import whisper
import os
from typing import Dict, Any, Optional

# TODO: Add support for other languages
# TODO: From the transcribed with timestamps, save the audio segments and their corresponding timestamps and text to a database but also online
# TODO: Add a way to download the audio segments and their corresponding timestamps and text

class WhisperASR:
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper ASR model
        
        Args:
            model_size: Size of Whisper model ('tiny', 'base', 'small', 'medium', 'large', 'turbo')
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            print(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded successfully")
        except Exception as e:
            raise Exception(f"Failed to load Whisper model: {str(e)}")
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional, auto-detect if None)
        
        Returns:
            Transcribed text
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Transcribe with Whisper
            if language:
                result = self.model.transcribe(audio_path, language=language)
            else:
                result = self.model.transcribe(audio_path)
            
            return result["text"].strip()
        
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_with_timestamps(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio with timestamps and segments
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
        
        Returns:
            Dictionary with transcription and segments
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Use transcription with segment-level timestamps
            if language:
                result = self.model.transcribe(audio_path, language=language)
            else:
                result = self.model.transcribe(audio_path)
            
            # Extract segments from the result
            segments = []
            if 'segments' in result:
                segments = result['segments']
            else:
                # If no segments, create a single segment from the full text
                segments = [{
                    'text': result['text'],
                    'start': 0.0,
                    'end': 0.0  # We'll need to estimate this
                }]
            
            return {
                'text': result['text'],
                'segments': segments
            }
        
        except Exception as e:
            raise Exception(f"Transcription with timestamps failed: {str(e)}")
    
    def get_available_languages(self) -> list:
        """Get list of supported language codes"""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", 
            "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", 
            "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", 
            "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", 
            "et", "mk", "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", 
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc", "ka", "be", 
            "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo", "ht", "ps", "tk", "nn", 
            "mt", "sa", "lb", "my", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", 
            "ba", "jw", "su"
        ]
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect the language of the audio file
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Language code
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Load audio and detect language
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Log mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            return detected_lang
        
        except Exception as e:
            raise Exception(f"Language detection failed: {str(e)}")
    
    def transcribe_segment(self, audio_path: str, start_time: float, end_time: float) -> str:
        """
        Transcribe a specific segment of audio
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds
        
        Returns:
            Transcribed text for the segment
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Load audio
            audio = whisper.load_audio(audio_path)
            
            # Extract segment
            sr = 16000  # Whisper uses 16kHz
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            if start_sample >= len(audio):
                return ""
            
            end_sample = min(end_sample, len(audio))
            segment_audio = audio[start_sample:end_sample]
            
            # Pad if too short
            if len(segment_audio) < sr * 0.5:  # Less than 0.5 seconds
                return ""
            
            # Transcribe segment
            result = self.model.transcribe(segment_audio)
            return result["text"].strip()
        
        except Exception as e:
            raise Exception(f"Segment transcription failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_size": self.model_size,
            "device": str(self.model.device) if self.model else None,
            "parameters": sum(p.numel() for p in self.model.parameters()) if self.model else None
        } 