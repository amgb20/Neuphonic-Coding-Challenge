import re
import nltk
from textblob import TextBlob
from typing import List, Dict, Any
import string

class FeatureExtractor:
    def __init__(self):
        """Initialize feature extractor with NLTK data"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass  # NLTK data might already be downloaded
        
        # Common filler words in English
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 'basically',
            'actually', 'literally', 'honestly', 'frankly', 'obviously',
            'clearly', 'simply', 'just', 'sort of', 'kind of', 'right',
            'well', 'so', 'okay', 'ok', 'yeah', 'yep', 'nope', 'no',
            'anyway', 'anyways', 'whatever', 'you see', 'i guess',
            'i think', 'i believe', 'i suppose', 'i mean', 'i say'
        }
    
    def calculate_wpm(self, transcript: str, duration: float) -> float:
        """
        Calculate words per minute (WPM)
        
        Args:
            transcript: Text transcript
            duration: Audio duration in seconds
        
        Returns:
            Words per minute
        """
        try:
            if not transcript or duration <= 0:
                return 0.0
            
            # Clean transcript and count words
            words = self._extract_words(transcript)
            word_count = len(words)
            
            # Calculate WPM
            minutes = duration / 60.0
            wpm = word_count / minutes if minutes > 0 else 0.0
            
            return round(wpm, 2)
        
        except Exception as e:
            print(f"Error calculating WPM: {str(e)}")
            return 0.0
    
    def calculate_filler_ratio(self, transcript: str) -> float:
        """
        Calculate the ratio of filler words to total words
        
        Args:
            transcript: Text transcript
        
        Returns:
            Ratio of filler words (0.0 to 1.0)
        """
        try:
            if not transcript:
                return 0.0
            
            # Extract words
            words = self._extract_words(transcript.lower())
            total_words = len(words)
            
            if total_words == 0:
                return 0.0
            
            # Count filler words
            filler_count = 0
            for i, word in enumerate(words):
                # Check single word fillers
                if word in self.filler_words:
                    filler_count += 1
                # Check multi-word fillers
                elif i < len(words) - 1:
                    bigram = f"{word} {words[i + 1]}"
                    if bigram in self.filler_words:
                        filler_count += 1
            
            ratio = filler_count / total_words
            return round(ratio, 4)
        
        except Exception as e:
            print(f"Error calculating filler ratio: {str(e)}")
            return 0.0
    
    def calculate_sentiment(self, transcript: str) -> float:
        """
        Calculate sentiment score using TextBlob
        
        Args:
            transcript: Text transcript
        
        Returns:
            Sentiment score (-1.0 to 1.0, where -1 is very negative, 1 is very positive)
        """
        try:
            if not transcript:
                return 0.0
            
            # Clean transcript
            cleaned_text = self._clean_text(transcript)
            
            # Calculate sentiment
            blob = TextBlob(cleaned_text)
            sentiment_score = blob.sentiment.polarity
            
            return round(sentiment_score, 3)
        
        except Exception as e:
            print(f"Error calculating sentiment: {str(e)}")
            return 0.0
    
    def calculate_speech_rate(self, transcript: str, duration: float) -> Dict[str, float]:
        """
        Calculate comprehensive speech rate metrics
        
        Args:
            transcript: Text transcript
            duration: Audio duration in seconds
        
        Returns:
            Dictionary with various speech rate metrics
        """
        try:
            words = self._extract_words(transcript)
            word_count = len(words)
            
            # Calculate various metrics
            minutes = duration / 60.0
            wpm = word_count / minutes if minutes > 0 else 0.0
            
            # Syllables per minute (approximate)
            syllable_count = self._count_syllables(transcript)
            spm = syllable_count / minutes if minutes > 0 else 0.0
            
            # Pauses (estimated from punctuation)
            pause_count = transcript.count('.') + transcript.count('!') + transcript.count('?')
            pause_rate = pause_count / minutes if minutes > 0 else 0.0
            
            return {
                'wpm': round(wpm, 2),
                'spm': round(spm, 2),
                'pause_rate': round(pause_rate, 2),
                'word_count': word_count,
                'syllable_count': syllable_count,
                'duration_minutes': round(minutes, 2)
            }
        
        except Exception as e:
            print(f"Error calculating speech rate: {str(e)}")
            return {
                'wpm': 0.0,
                'spm': 0.0,
                'pause_rate': 0.0,
                'word_count': 0,
                'syllable_count': 0,
                'duration_minutes': 0.0
            }
    
    def calculate_complexity_metrics(self, transcript: str) -> Dict[str, Any]:
        """
        Calculate text complexity metrics
        
        Args:
            transcript: Text transcript
        
        Returns:
            Dictionary with complexity metrics
        """
        try:
            if not transcript:
                return {
                    'avg_word_length': 0.0,
                    'unique_word_ratio': 0.0,
                    'sentence_count': 0,
                    'avg_sentence_length': 0.0,
                    'readability_score': 0.0
                }
            
            words = self._extract_words(transcript)
            sentences = self._extract_sentences(transcript)
            
            # Average word length
            total_characters = sum(len(word) for word in words)
            avg_word_length = total_characters / len(words) if words else 0.0
            
            # Unique word ratio
            unique_words = set(words)
            unique_word_ratio = len(unique_words) / len(words) if words else 0.0
            
            # Sentence metrics
            sentence_count = len(sentences)
            avg_sentence_length = len(words) / sentence_count if sentence_count > 0 else 0.0
            
            # Simple readability score (Flesch Reading Ease approximation)
            readability_score = self._calculate_readability(words, sentences)
            
            return {
                'avg_word_length': round(avg_word_length, 2),
                'unique_word_ratio': round(unique_word_ratio, 3),
                'sentence_count': sentence_count,
                'avg_sentence_length': round(avg_sentence_length, 2),
                'readability_score': round(readability_score, 2)
            }
        
        except Exception as e:
            print(f"Error calculating complexity metrics: {str(e)}")
            return {
                'avg_word_length': 0.0,
                'unique_word_ratio': 0.0,
                'sentence_count': 0,
                'avg_sentence_length': 0.0,
                'readability_score': 0.0
            }
    
    def extract_all_features(self, transcript: str, duration: float) -> Dict[str, Any]:
        """
        Extract all features from transcript
        
        Args:
            transcript: Text transcript
            duration: Audio duration in seconds
        
        Returns:
            Dictionary with all extracted features
        """
        try:
            # Basic features
            wpm = self.calculate_wpm(transcript, duration)
            filler_ratio = self.calculate_filler_ratio(transcript)
            sentiment_score = self.calculate_sentiment(transcript)
            
            # Advanced features
            speech_rate = self.calculate_speech_rate(transcript, duration)
            complexity = self.calculate_complexity_metrics(transcript)
            
            return {
                'wpm': wpm,
                'filler_ratio': filler_ratio,
                'sentiment_score': sentiment_score,
                'speech_rate': speech_rate,
                'complexity': complexity,
                'word_count': speech_rate['word_count'],
                'duration_seconds': duration,
                'duration_minutes': speech_rate['duration_minutes']
            }
        
        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return {
                'wpm': 0.0,
                'filler_ratio': 0.0,
                'sentiment_score': 0.0,
                'speech_rate': {},
                'complexity': {},
                'word_count': 0,
                'duration_seconds': duration,
                'duration_minutes': duration / 60.0
            }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        return [word.lower() for word in words if word.strip()]
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _count_syllables(self, text: str) -> int:
        """Approximate syllable count"""
        text = text.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
        
        return max(count, 1)  # At least 1 syllable per word
    
    def _calculate_readability(self, words: List[str], sentences: List[str]) -> float:
        """Calculate simple readability score"""
        if not words or not sentences:
            return 0.0
        
        # Simple Flesch Reading Ease approximation
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simplified formula
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        return max(0.0, min(100.0, readability)) 