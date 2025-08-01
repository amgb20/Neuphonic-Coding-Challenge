import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface AudioFile {
  id: number;
  filename: string;
  duration: number;
  transcript: string;
  wpm: number;
  filler_ratio: number;
  sentiment_score: number;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchAudioFiles();
  }, []);

  const fetchAudioFiles = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/audio-files');
      setAudioFiles(response.data.files || []);
    } catch (err) {
      setError('Failed to fetch audio files');
      console.error('Error fetching audio files:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      await axios.post('http://localhost:8000/api/process-audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Refresh the list after upload
      await fetchAudioFiles();
    } catch (err) {
      setError('Failed to upload and process audio file');
      console.error('Error uploading file:', err);
    } finally {
      setUploading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-green-600';
    if (score < -0.3) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.3) return 'Positive';
    if (score < -0.3) return 'Negative';
    return 'Neutral';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="loading-spinner"></div>
        <span className="ml-3 text-gray-600">Loading audio files...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Audio Files</h2>
          <p className="text-gray-600">Processed audio files and their analysis</p>
        </div>
        
        <label className="cursor-pointer bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors duration-200">
          {uploading ? 'Processing...' : 'Upload Audio'}
          <input
            type="file"
            accept=".wav,.mp3,.m4a"
            onChange={handleFileUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Statistics */}
      {audioFiles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{audioFiles.length}</div>
            <div className="text-sm text-gray-600">Total Files</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(audioFiles.reduce((sum, file) => sum + file.duration, 0) / 60)}m
            </div>
            <div className="text-sm text-gray-600">Total Duration</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(audioFiles.reduce((sum, file) => sum + file.wpm, 0) / audioFiles.length)}
            </div>
            <div className="text-sm text-gray-600">Avg WPM</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">
              {audioFiles.filter(f => f.sentiment_score > 0.3).length}
            </div>
            <div className="text-sm text-gray-600">Positive Files</div>
          </div>
        </div>
      )}

      {/* Audio Files List */}
      {audioFiles.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No audio files yet</h3>
          <p className="text-gray-600 mb-4">Upload your first audio file to get started</p>
          <label className="cursor-pointer bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors duration-200">
            Upload Audio File
            <input
              type="file"
              accept=".wav,.mp3,.m4a"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {audioFiles.map((file) => (
            <div key={file.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {file.filename}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {formatDuration(file.duration)} • {new Date(file.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Link
                    to={`/audio/${file.id}`}
                    className="bg-primary-100 text-primary-700 px-3 py-1 rounded-md text-sm font-medium hover:bg-primary-200 transition-colors duration-200"
                  >
                    View Details
                  </Link>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{file.wpm}</div>
                    <div className="text-xs text-gray-500">WPM</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {(file.filler_ratio * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">Filler Words</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-lg font-semibold ${getSentimentColor(file.sentiment_score)}`}>
                      {getSentimentLabel(file.sentiment_score)}
                    </div>
                    <div className="text-xs text-gray-500">Sentiment</div>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4">
                  <p className="text-sm text-gray-600 line-clamp-3">
                    {file.transcript || 'No transcript available'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard; 