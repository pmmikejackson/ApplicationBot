#!/bin/bash

echo "🤖 Setting up ApplicationBot - Job Application Automation System"
echo "================================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/documents
mkdir -p database/data

# Set permissions
chmod +x setup.sh

echo ""
echo "🚀 Setup complete! Next steps:"
echo ""
echo "1. Edit the .env file with your configuration:"
echo "   - Database credentials"
echo "   - Platform login credentials (LinkedIn, Indeed)"
echo "   - OpenAI API key (optional, for AI job analysis)"
echo "   - Email settings (optional, for notifications)"
echo ""
echo "2. Start the application:"
echo "   docker-compose up -d"
echo ""
echo "3. Access the dashboard:"
echo "   http://localhost:3000"
echo ""
echo "4. API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "📚 For more information, see the README.md file."
echo ""