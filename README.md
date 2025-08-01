# Audio Processing Pipeline

A complete audio processing system that ingests audio files, processes them through a fault-tolerant pipeline, generates transcripts using Whisper ASR, computes features, and provides a web dashboard for visualization.

## 🚀 Features

- **Audio Processing**: Normalize volume, convert sample rates, segment long files
- **Speech Recognition**: OpenAI Whisper ASR for accurate transcription
- **Feature Extraction**: WPM, filler word ratio, sentiment analysis
- **Database Storage**: DuckDB for efficient data storage
- **Web Dashboard**: React frontend with real-time audio playback
- **Docker Support**: Complete containerized environment
- **Fault Tolerance**: Error handling and retry mechanisms

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Input   │───▶│  Processing     │───▶│   Database      │
│   (.wav/.mp3)   │    │   Pipeline      │    │   (DuckDB)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Web Dashboard │
                       │   (React/TS)    │
                       └─────────────────┘
```

## 📋 Requirements

- Docker and Docker Compose
- 4GB+ RAM (for Whisper model loading)
- 2GB+ disk space

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Neuphonic-Coding-Challenge
```

### 2. Create Required Directories

```bash
mkdir -p audio_files processed_data data
```

### 3. Build and Run

```bash
# Build all services
make build

# Start all services
make run

# Or start with logs
make dev
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
neuphonic-coding-challenge/
├── backend/
│   ├── src/
│   │   ├── api.py              # FastAPI application
│   │   ├── audio_processor.py  # Audio processing logic
│   │   ├── asr_model.py        # Whisper ASR integration
│   │   ├── feature_extractor.py # Feature calculation
│   │   └── database.py         # DuckDB operations
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Backend container
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── App.tsx            # Main app component
│   │   └── index.tsx          # Entry point
│   ├── package.json           # Node.js dependencies
│   └── Dockerfile             # Frontend container
├── docker-compose.yml         # Multi-service setup
├── Makefile                   # Automation commands
└── README.md                 # This file
```

## 🎯 Usage

### Upload and Process Audio

1. **Via Web Dashboard**:
   - Navigate to http://localhost:3000
   - Click "Upload Audio" button
   - Select your audio file (.wav, .mp3, .m4a)
   - Wait for processing to complete

2. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/process-audio" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@your_audio_file.mp3"
   ```

### View Results

- **Dashboard**: See all processed files with features
- **Individual View**: Click on any file to see detailed analysis
- **Audio Player**: Play processed audio with transcript

## 🔧 Available Commands

```bash
# Main commands
make all              # Build and run everything
make build            # Build all services
make run              # Start services in background
make dev              # Start with logs

# Individual services
make build-backend    # Build backend only
make build-frontend   # Build frontend only
make dev-backend      # Start backend with logs
make dev-frontend     # Start frontend with logs

# Utility commands
make logs             # View all logs
make logs-backend     # View backend logs
make logs-frontend    # View frontend logs
make restart          # Restart all services
make stop             # Stop all services
make clean            # Stop and clean up

# Development commands
make shell-backend    # Access backend shell
make shell-frontend   # Access frontend shell
make test             # Run all tests
make health           # Check service health
```

## 🔍 API Endpoints

### Audio Processing
- `POST /api/process-audio` - Upload and process audio file
- `GET /api/audio-files` - Get all processed files
- `GET /api/audio-files/{id}` - Get specific file details

### Health Check
- `GET /health` - Service health status

## 📊 Features Extracted

### Basic Features
- **WPM (Words Per Minute)**: Speaking rate calculation
- **Filler Word Ratio**: Percentage of filler words used
- **Sentiment Score**: Text sentiment analysis (-1 to 1)

### Advanced Features
- **Speech Rate Metrics**: Syllables per minute, pause rate
- **Complexity Metrics**: Word length, vocabulary diversity
- **Quality Metrics**: Audio quality assessment

## 🐳 Docker Configuration

### Services
- **Backend**: Python FastAPI with audio processing
- **Frontend**: React development server
- **Redis**: Caching and session management

### Volumes
- `./audio_files` → `/app/audio_files` (input files)
- `./processed_data` → `/app/processed_data` (processed files)
- `./data` → `/app/data` (database files)

## 🔧 Configuration

### Environment Variables

**Backend**:
- `DATABASE_URL`: DuckDB connection string
- `WHISPER_MODEL_SIZE`: Whisper model size (tiny/base/small/medium/large)
- `ENVIRONMENT`: development/production

**Frontend**:
- `REACT_APP_API_URL`: Backend API URL

### Model Sizes

| Size | Parameters | Memory | Speed | Accuracy |
|------|------------|--------|-------|----------|
| tiny | 39M | ~1GB | Fast | Good |
| base | 74M | ~1GB | Fast | Good |
| small | 244M | ~2GB | Medium | Better |
| medium | 769M | ~5GB | Slow | Best |
| large | 1550M | ~10GB | Very Slow | Best |

## 🚨 Troubleshooting

### Common Issues

1. **Out of Memory**:
   ```bash
   # Increase Docker memory limit
   docker-compose down
   # Edit docker-compose.yml to add memory limits
   docker-compose up
   ```

2. **Whisper Model Download Issues**:
   ```bash
   # Check model download
   make shell-backend
   python -c "import whisper; whisper.load_model('base')"
   ```

3. **Audio Processing Errors**:
   ```bash
   # Check audio file format
   file your_audio.mp3
   # Ensure file is valid audio
   ```

4. **Frontend Not Loading**:
   ```bash
   # Check if frontend is running
   curl http://localhost:3000
   # Check backend API
   curl http://localhost:8000/health
   ```

### Logs and Debugging

```bash
# View all logs
make logs

# View specific service logs
make logs-backend
make logs-frontend

# Access container shells
make shell-backend
make shell-frontend
```

## 🧪 Testing

```bash
# Run backend tests
make test-backend

# Run frontend tests
make test-frontend

# Run all tests
make test
```

## 📈 Performance

### Processing Times (approximate)
- **Tiny Model**: 2-5 seconds per minute of audio
- **Base Model**: 3-7 seconds per minute of audio
- **Small Model**: 5-10 seconds per minute of audio
- **Medium Model**: 10-20 seconds per minute of audio

### Memory Usage
- **Backend**: 2-4GB (depending on model size)
- **Frontend**: 100-200MB
- **Redis**: 50-100MB

## 🔒 Security

- CORS configured for localhost only
- File upload validation
- Error handling without exposing internals
- No sensitive data in logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs: `make logs`
3. Check service health: `make health`
4. Open an issue with detailed error information
