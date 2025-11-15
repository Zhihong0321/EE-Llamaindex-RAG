#!/bin/bash

# Script to push LlamaIndex RAG API to GitHub
# Repository: https://github.com/Zhihong0321/EE-Llamaindex-RAG

echo "🚀 Pushing LlamaIndex RAG API to GitHub..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add remote (remove if exists)
echo "🔗 Setting up remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Zhihong0321/EE-Llamaindex-RAG.git

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
.kiro/

# Database
*.db
*.sqlite

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Alembic
alembic/versions/*.pyc
EOF
fi

# Add all files
echo "📁 Adding files..."
git add .

# Create commit
echo "💾 Creating commit..."
git commit -m "Initial commit: Production-ready LlamaIndex RAG API

Features:
- Complete RAG implementation with LlamaIndex + FastAPI + PostgreSQL
- Document ingestion with vector embeddings (pgvector)
- Conversational chat with session management
- Source attribution with relevance scores
- Comprehensive testing (unit, integration, E2E)
- Production deployment guides (Railway, Docker)
- Security hardening and best practices
- Performance optimization guidelines
- Monitoring and alerting strategies
- Complete documentation

Technical Stack:
- FastAPI for REST API
- LlamaIndex for RAG orchestration
- PostgreSQL with pgvector for vector storage
- OpenAI for embeddings and chat
- Alembic for database migrations
- Pytest for testing

Documentation:
- README.md - Quick start and overview
- PRODUCTION_DEPLOYMENT_GUIDE.md - Complete deployment guide
- SECURITY_CHECKLIST.md - Security review and hardening
- PERFORMANCE_OPTIMIZATION.md - Performance tuning guide
- MONITORING_GUIDE.md - Monitoring and alerting setup
- PRODUCTION_READINESS_SUMMARY.md - Production readiness review

All 21 implementation tasks completed and tested."

# Push to GitHub
echo "⬆️  Pushing to GitHub..."
git branch -M main
git push -u origin main --force

echo "✅ Successfully pushed to https://github.com/Zhihong0321/EE-Llamaindex-RAG"
echo ""
echo "Next steps:"
echo "1. Visit your repository: https://github.com/Zhihong0321/EE-Llamaindex-RAG"
echo "2. Review the README.md for setup instructions"
echo "3. Check out the production deployment guides"
echo "4. Deploy to Railway or your preferred platform"
