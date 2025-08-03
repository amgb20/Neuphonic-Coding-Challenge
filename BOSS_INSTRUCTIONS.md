# 🚀 Quick Start Guide for Boss

## Prerequisites
- Docker Desktop installed and running
- Git installed

## Step-by-Step Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Neuphonic-Coding-Challenge
```

### 2. Start the Application
```bash
# Build and start all services
docker-compose up --build
```

**Note**: The first time you run this, it will take a few minutes to download and build everything. Subsequent runs will be much faster.

### 3. Access the Web Application
Once you see messages like "Application startup complete" and "Compiled successfully", open your web browser and go to:

**🌐 Main Dashboard**: http://localhost:3000

### 4. Test the Application
1. Click the "Upload Audio" button
2. Select any audio file (.wav, .mp3, .m4a)
3. Wait for processing (usually 1-3 minutes depending on file size)
4. View the results in the dashboard

### 5. Stop the Application
When you're done testing, press `Ctrl+C` in the terminal to stop all services.

## Troubleshooting

### If the application doesn't start:
```bash
# Check if Docker is running
docker --version

# Check if ports are available
lsof -i :3000
lsof -i :8000
```

### If you get permission errors:
```bash
# On macOS/Linux, you might need to run with sudo
sudo docker-compose up --build
```

### To view logs:
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

## What's Running

- **Frontend**: React web app on http://localhost:3000
- **Backend**: Python API on http://localhost:8000  
- **Database**: DuckDB (embedded, no external setup needed)
- **Cache**: Redis (for performance)

## Features to Test

1. **Audio Upload**: Try uploading different audio files
2. **Transcription**: See how accurately it transcribes speech
3. **Feature Analysis**: View WPM, sentiment, and quality metrics
4. **Audio Playback**: Listen to processed audio segments
5. **Dashboard**: Browse through all processed files

## Need Help?

If something doesn't work, check:
1. Docker Desktop is running
2. Ports 3000 and 8000 are not in use by other applications
3. You have at least 4GB of available RAM
4. Your internet connection is stable (for initial downloads)

The application is designed to be self-contained and should work out of the box! 🎉 