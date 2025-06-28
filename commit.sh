#!/bin/bash

# ApplicationBot Initial Commit Script

echo "🚀 Committing ApplicationBot to Git"
echo "================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Run ./git_setup.sh first"
    exit 1
fi

# Check if there are staged changes
if git diff --cached --quiet; then
    echo "📋 Staging all files..."
    git add .
fi

# Create the initial commit
echo "💾 Creating initial commit..."
git commit -m "feat: Initial ApplicationBot job automation system

- Multi-platform job scraping (LinkedIn, Indeed, BuiltIn, ZipRecruiter)
- AI-powered job matching and scoring with OpenAI integration
- Automated application system with Selenium WebDriver
- React 18 dashboard with TypeScript and Tailwind CSS
- FastAPI backend with PostgreSQL database and Alembic migrations
- Celery background task processing with Redis
- Docker containerization for easy deployment
- Email automation with SMTP integration
- JWT authentication and Fernet encryption
- Comprehensive logging and error handling
- Working deployment on Synology NAS (192.168.1.79:9001)

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

if [ $? -eq 0 ]; then
    echo "✅ Commit successful!"
    
    # Show commit details
    echo ""
    echo "📊 Commit details:"
    git log -1 --stat
    
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Create repository on GitHub/GitLab"
    echo "   2. Add remote: git remote add origin <your-repo-url>"
    echo "   3. Push: git push -u origin main"
    echo ""
    echo "📝 Or create and push in one go:"
    echo "   gh repo create ApplicationBot --public --push"
else
    echo "❌ Commit failed!"
    exit 1
fi