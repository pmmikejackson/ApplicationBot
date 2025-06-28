#!/bin/bash

# ApplicationBot Development to Deployment Sync Script
# Syncs code from development folder to Docker deployment folder

echo "🔄 ApplicationBot Code Sync"
echo "=========================="

# Configuration - Auto-detect current directory as dev path
DEV_PATH="$(pwd)"
DEPLOY_PATH="/volume1/docker/ApplicationBot"

# Override paths if we're not on Synology (for development)
if [[ ! -d "/volume1" ]]; then
    echo "⚠️  Not on Synology NAS - showing files that would be synced"
    echo "📁 Current directory: $DEV_PATH"
    echo "📁 Target would be: $DEPLOY_PATH"
    echo ""
    echo "📋 Files ready for deployment:"
    echo "   - backend/app/services/email_parser_service.py (new)"
    echo "   - backend/app/api/api_v1/endpoints/email_parser.py (new)"
    echo "   - backend/app/api/api_v1/api.py (updated)"
    echo "   - backend/app/core/config.py (updated)"
    echo "   - frontend/src/services/api.ts (updated)"
    echo "   - frontend/src/pages/Dashboard.tsx (updated)"
    echo "   - CLAUDE.md (updated)"
    echo ""
    echo "✅ All email parsing code is ready!"
    echo "💡 Copy this folder to your Synology NAS and run sync.sh there"
    exit 0
fi

# Check if development path exists
if [ ! -d "$DEV_PATH" ]; then
    echo "❌ Development path not found: $DEV_PATH"
    exit 1
fi

# Create deployment directory if it doesn't exist
if [ ! -d "$DEPLOY_PATH" ]; then
    echo "📁 Creating deployment directory: $DEPLOY_PATH"
    mkdir -p "$DEPLOY_PATH"
fi

echo "📂 Source: $DEV_PATH"
echo "📂 Target: $DEPLOY_PATH"
echo ""

# Sync files (excluding .git and other development files)
echo "🚀 Syncing files..."
rsync -av \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    --exclude='.env.local' \
    --exclude='*.log' \
    "$DEV_PATH/" "$DEPLOY_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sync completed successfully!"
    echo "📊 Files synced to deployment folder"
    echo ""
    echo "🐳 Next steps:"
    echo "   1. Open Synology Container Manager"
    echo "   2. Stop ApplicationBot project"
    echo "   3. Start ApplicationBot project"
    echo "   4. Check http://192.168.1.79:9001"
    echo ""
else
    echo "❌ Sync failed!"
    exit 1
fi