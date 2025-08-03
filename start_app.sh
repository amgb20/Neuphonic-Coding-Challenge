#!/bin/bash

echo "🚀 Starting Neuphonic Audio Processing Application..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed!"
    echo "Please install Docker Compose and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create required directories if they don't exist
mkdir -p audio_files processed_data data

echo "📦 Building and starting services..."
echo "⏳ This may take a few minutes on first run..."
echo ""

# Build and start the application
docker-compose up --build

echo ""
echo "🎉 Application stopped!" 