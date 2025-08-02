import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import WaveSurfer from 'wavesurfer.js';

interface AudioFile {
  id: number;
  filename: string;
  duration: number;
  transcript: string;
  wpm: number;
  filler_ratio: number;
  sentiment_score: number;
  audio_path: string;
  created_at: string;
}

interface AudioSegment {
  id: number;
  original_file_id: number;
  segment_index: number;
  start_time: number;
  end_time: number;
  duration: number;
  transcript: string;
  audio_path: string;
  wpm: number;
  filler_ratio: number;
  sentiment_score: number;
  quality_score: number;
}

const AudioPlayer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [audioFile, setAudioFile] = useState<AudioFile | null>(null);
  const [segments, setSegments] = useState<AudioSegment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [viewMode, setViewMode] = useState<'full' | 'segments'>('full');
  const [selectedSegment, setSelectedSegment] = useState<AudioSegment | null>(null);
  const [currentWordIndex, setCurrentWordIndex] = useState(-1);
  const audioRef = useRef<HTMLAudioElement>(null);
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  useEffect(() => {
    if (id) {
      fetchAudioFile();
      fetchSegments();
    }
  }, [id]);

  useEffect(() => {
    if (audioFile && waveformRef.current && !wavesurferRef.current) {
      initializeWaveSurfer();
    }
  }, [audioFile]);

  const initializeWaveSurfer = () => {
    if (!waveformRef.current || !audioFile) return;

    try {
      // Create canvas for gradients
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('Failed to get canvas context');
        return;
      }
      canvas.width = 100;
      canvas.height = 100;

      // Define the waveform gradient
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
      gradient.addColorStop(0, '#656666'); // Top color
      gradient.addColorStop((canvas.height * 0.7) / canvas.height, '#656666'); // Top color
      gradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#ffffff'); // White line
      gradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#ffffff'); // White line
      gradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#B1B1B1'); // Bottom color
      gradient.addColorStop(1, '#B1B1B1'); // Bottom color

      // Define the progress gradient
      const progressGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
      progressGradient.addColorStop(0, '#EE772F'); // Top color
      progressGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#EB4926'); // Top color
      progressGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#ffffff'); // White line
      progressGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#ffffff'); // White line
      progressGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#F6B094'); // Bottom color
      progressGradient.addColorStop(1, '#F6B094'); // Bottom color

      wavesurferRef.current = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: gradient,
        progressColor: progressGradient,
        barWidth: 2,
        barRadius: 3,
        cursorWidth: 1,
        height: 80,
        barGap: 3,
      });

      wavesurferRef.current.load(`http://localhost:8000/api/audio-files/${id}/audio`);

      wavesurferRef.current.on('ready', () => {
        console.log('WaveSurfer is ready');
      });

      wavesurferRef.current.on('audioprocess', (currentTime: number) => {
        setCurrentTime(currentTime);
        updateWordHighlighting(currentTime);
      });

      wavesurferRef.current.on('play', () => {
        setIsPlaying(true);
      });

      wavesurferRef.current.on('pause', () => {
        setIsPlaying(false);
      });

      wavesurferRef.current.on('finish', () => {
        setIsPlaying(false);
        setCurrentWordIndex(-1);
      });

      wavesurferRef.current.on('error', (error: any) => {
        console.error('WaveSurfer error:', error);
      });

      // Add interaction for play/pause on click
      wavesurferRef.current.on('interaction', () => {
        wavesurferRef.current?.playPause();
      });

      // Add hover effect
      if (waveformRef.current) {
        const hoverElement = waveformRef.current.querySelector('.hover-effect') as HTMLElement;
        if (hoverElement) {
          waveformRef.current.addEventListener('pointermove', (e) => {
            const rect = waveformRef.current?.getBoundingClientRect();
            if (rect) {
              const offsetX = e.clientX - rect.left;
              hoverElement.style.width = `${offsetX}px`;
            }
          });
        }
      }

    } catch (error) {
      console.error('Failed to initialize WaveSurfer:', error);
    }
  };

  const updateWordHighlighting = (currentTime: number) => {
    if (!audioFile?.transcript) return;

    const words = audioFile.transcript.split(' ');
    const totalDuration = audioFile.duration;
    const timePerWord = totalDuration / words.length;
    const currentWordIndex = Math.floor(currentTime / timePerWord);
    
    setCurrentWordIndex(Math.min(currentWordIndex, words.length - 1));
  };

  const fetchAudioFile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/api/audio-files/${id}`);
      setAudioFile(response.data);
    } catch (err) {
      setError('Failed to fetch audio file details');
      console.error('Error fetching audio file:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSegments = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/audio-files/${id}/segments`);
      setSegments(response.data.segments || []);
    } catch (err) {
      console.error('Error fetching segments:', err);
    }
  };

  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  };

  const handleSegmentPlay = async (segment: AudioSegment) => {
    setSelectedSegment(segment);
    // For now, we'll just show the segment info
    // In a full implementation, you'd want to stream the segment audio
  };

  const downloadSegment = async (segment: AudioSegment) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/audio-files/${id}/segments/${segment.id}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `segment_${segment.segment_index}.mp3`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading segment:', err);
    }
  };

  const downloadFullAudio = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/audio-files/${id}/audio`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${audioFile?.filename || 'audio'}.mp3`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading full audio:', err);
    }
  };

  const downloadAllSegments = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/audio-files/${id}/segments/download-zip`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${audioFile?.filename || 'audio'}_segments.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading segments:', err);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.1) return 'text-green-600';
    if (score < -0.1) return 'text-red-600';
    return 'text-gray-600';
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.1) return 'Positive';
    if (score < -0.1) return 'Negative';
    return 'Neutral';
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityLabel = (score: number) => {
    if (score >= 0.7) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };

  const getSegmentMetrics = () => {
    if (segments.length === 0) return null;

    const avgWpm = segments.reduce((sum, seg) => sum + seg.wpm, 0) / segments.length;
    const avgFillerRatio = segments.reduce((sum, seg) => sum + seg.filler_ratio, 0) / segments.length;
    const avgSentiment = segments.reduce((sum, seg) => sum + seg.sentiment_score, 0) / segments.length;
    const avgQuality = segments.reduce((sum, seg) => sum + seg.quality_score, 0) / segments.length;

    return {
      avgWpm: avgWpm.toFixed(2),
      avgFillerRatio: (avgFillerRatio * 100).toFixed(2),
      avgSentiment: avgSentiment.toFixed(3),
      avgQuality: (avgQuality * 100).toFixed(2)
    };
  };

  const renderTranscriptWithHighlighting = () => {
    if (!audioFile?.transcript) return null;

    const words = audioFile.transcript.split(' ');
    
    return (
      <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
        <h3 className="text-lg font-semibold mb-3">Transcript with Word Highlighting</h3>
        <div className="text-gray-800 leading-relaxed">
          {words.map((word, index) => (
            <span
              key={index}
              className={`inline-block mr-1 px-1 rounded ${
                index === currentWordIndex 
                  ? 'bg-blue-200 text-blue-800 font-medium' 
                  : ''
              }`}
            >
              {word}
            </span>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="loading-spinner"></div>
        <span className="ml-3 text-gray-600">Loading audio file...</span>
      </div>
    );
  }

  if (error || !audioFile) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error loading audio file</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <Link
          to="/"
          className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors duration-200"
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const segmentMetrics = getSegmentMetrics();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-primary-600 hover:text-primary-700 mb-2 inline-block">
            ← Back to Dashboard
          </Link>
          <h2 className="text-2xl font-bold text-gray-900">{audioFile.filename}</h2>
          <p className="text-gray-600">
            {formatTime(audioFile.duration)} • {new Date(audioFile.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={downloadFullAudio}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            Download Full Audio
          </button>
          {segments.length > 0 && (
            <button
              onClick={downloadAllSegments}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200"
            >
              Download All Segments
            </button>
          )}
        </div>
      </div>

      {/* View Mode Toggle */}
      {segments.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex space-x-4">
            <button
              onClick={() => setViewMode('full')}
              className={`px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
                viewMode === 'full' 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Full Audio
            </button>
            <button
              onClick={() => setViewMode('segments')}
              className={`px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
                viewMode === 'segments' 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Segments ({segments.length})
            </button>
          </div>
        </div>
      )}

      {/* Full Audio View */}
      {viewMode === 'full' && (
        <>
          {/* Audio Player */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="audio-player rounded-lg p-6 mb-6">
              <div className="flex items-center justify-center mb-4">
                <button
                  onClick={handlePlayPause}
                  className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow duration-200"
                >
                  {isPlaying ? (
                    <svg className="w-8 h-8 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-8 h-8 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Soundcloud-style Waveform */}
              <div className="relative">
                <div ref={waveformRef} className="cursor-pointer relative hover:bg-gray-50 rounded" style={{ background: 'transparent' }}>
                  <div className="absolute top-1/2 left-0 transform -translate-y-1/2 z-10 text-xs bg-black bg-opacity-75 text-gray-300 px-2 py-1 rounded">
                    {formatTime(currentTime)}
                  </div>
                  <div className="absolute top-1/2 right-0 transform -translate-y-1/2 z-10 text-xs bg-black bg-opacity-75 text-gray-300 px-2 py-1 rounded">
                    {formatTime(duration)}
                  </div>
                  <div className="hover-effect absolute left-0 top-0 z-10 pointer-events-none h-full w-0 mix-blend-overlay bg-white bg-opacity-50 opacity-0 transition-opacity duration-200" 
                       style={{ width: '0px' }}></div>
                </div>
              </div>

              {/* Hidden Audio Element */}
              <audio
                ref={audioRef}
                style={{ display: 'none' }}
              >
                <source src={`http://localhost:8000/api/audio-files/${audioFile.id}/audio`} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900 mb-2">{audioFile.wpm.toFixed(2)}</div>
                <div className="text-sm text-gray-600">Words Per Minute</div>
                <div className="mt-2 text-xs text-gray-500">
                  {audioFile.wpm < 120 ? 'Slow' : audioFile.wpm > 160 ? 'Fast' : 'Normal'} pace
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {(audioFile.filler_ratio * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Filler Words</div>
                <div className="mt-2 text-xs text-gray-500">
                  {audioFile.filler_ratio < 0.05 ? 'Low' : audioFile.filler_ratio > 0.15 ? 'High' : 'Moderate'} usage
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center">
                <div className={`text-3xl font-bold mb-2 ${getSentimentColor(audioFile.sentiment_score)}`}>
                  {getSentimentLabel(audioFile.sentiment_score)}
                </div>
                <div className="text-sm text-gray-600">Sentiment</div>
                <div className="mt-2 text-xs text-gray-500">
                  Score: {audioFile.sentiment_score.toFixed(3)}
                </div>
              </div>
            </div>
          </div>

          {/* Transcript with Word Highlighting */}
          {renderTranscriptWithHighlighting()}
        </>
      )}

      {/* Segments View */}
      {viewMode === 'segments' && segments.length > 0 && (
        <>
          {/* Segment Metrics */}
          {segmentMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900 mb-2">{segmentMetrics.avgWpm}</div>
                  <div className="text-sm text-gray-600">Avg WPM</div>
                  <div className="mt-2 text-xs text-gray-500">Across all segments</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    {segmentMetrics.avgFillerRatio}%
                  </div>
                  <div className="text-sm text-gray-600">Avg Filler Words</div>
                  <div className="mt-2 text-xs text-gray-500">Across all segments</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center">
                  <div className={`text-3xl font-bold mb-2 ${getSentimentColor(parseFloat(segmentMetrics.avgSentiment))}`}>
                    {getSentimentLabel(parseFloat(segmentMetrics.avgSentiment))}
                  </div>
                  <div className="text-sm text-gray-600">Avg Sentiment</div>
                  <div className="mt-2 text-xs text-gray-500">
                    Score: {segmentMetrics.avgSentiment}
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center">
                  <div className={`text-3xl font-bold mb-2 ${getQualityColor(parseFloat(segmentMetrics.avgQuality))}`}>
                    {getQualityLabel(parseFloat(segmentMetrics.avgQuality))}
                  </div>
                  <div className="text-sm text-gray-600">Avg Quality</div>
                  <div className="mt-2 text-xs text-gray-500">
                    {segmentMetrics.avgQuality}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Segments Grid */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Audio Segments ({segments.length} segments)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {segments.map((segment) => (
                <div key={segment.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      Segment {segment.segment_index}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${getQualityColor(segment.quality_score)}`}>
                      Quality: {getQualityLabel(segment.quality_score)} ({(segment.quality_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    {formatTime(segment.start_time)} - {formatTime(segment.end_time)} 
                    ({formatTime(segment.duration)})
                  </div>
                  <p className="text-sm text-gray-700 mb-3 line-clamp-3">
                    {segment.transcript}
                  </p>
                  <div className="flex justify-between text-xs text-gray-500 mb-3">
                    <span>WPM: {segment.wpm.toFixed(2)}</span>
                    <span>Sentiment: {segment.sentiment_score.toFixed(2)}</span>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleSegmentPlay(segment)}
                      className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs hover:bg-blue-200"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => downloadSegment(segment)}
                      className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs hover:bg-green-200"
                    >
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AudioPlayer; 