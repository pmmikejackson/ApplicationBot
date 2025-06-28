#!/bin/bash

# ApplicationBot Git Setup Script
# Prepares the repository for initial commit and push

echo "🚀 ApplicationBot Git Setup"
echo "=========================="

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "📁 Git repository already exists"
fi

# Configure git user (update these with your details)
echo "👤 Configuring Git user..."
git config user.name "ApplicationBot Developer"
git config user.email "developer@applicationbot.com"
echo "✅ Git user configured"

# Add all files to staging
echo "📋 Adding files to staging area..."
git add .
echo "✅ Files staged for commit"

# Show status
echo "📊 Repository status:"
git status --short

# Show what will be committed
echo ""
echo "📦 Files ready for commit:"
git diff --cached --name-only

# Check if .env exists and warn
if [ -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file detected!"
    echo "   This file contains sensitive information and should NOT be committed."
    echo "   It's already in .gitignore, but please verify it's not staged:"
    git status | grep -q ".env" && echo "   ❌ .env is staged - please unstage it!" || echo "   ✅ .env is properly ignored"
fi

# Count files to be committed
file_count=$(git diff --cached --name-only | wc -l)
echo ""
echo "📈 Summary:"
echo "   Files to commit: $file_count"
echo "   Repository size: $(du -sh . | cut -f1)"

echo ""
echo "🎯 Next steps:"
echo "   1. Review the files above"
echo "   2. Run: git commit -m 'Initial ApplicationBot implementation'"
echo "   3. Add remote: git remote add origin <your-repo-url>"
echo "   4. Push: git push -u origin main"

echo ""
echo "📝 Recommended commit message:"
echo "   'feat: Initial ApplicationBot job automation system"
echo ""
echo "   - Multi-platform job scraping (LinkedIn, Indeed, BuiltIn, ZipRecruiter)"
echo "   - AI-powered job matching and scoring"
echo "   - Automated application system with Selenium"
echo "   - React dashboard with real-time analytics"
echo "   - FastAPI backend with PostgreSQL and Celery"
echo "   - Docker containerization for easy deployment"
echo "   - Working deployment on Synology NAS'"

echo ""
echo "✨ Repository ready for commit!"