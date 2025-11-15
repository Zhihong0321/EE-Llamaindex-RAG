@echo off
REM Script to push LlamaIndex RAG API to GitHub
REM Repository: https://github.com/Zhihong0321/EE-Llamaindex-RAG

echo 🚀 Pushing LlamaIndex RAG API to GitHub...

REM Check if git is initialized
if not exist .git (
    echo 📦 Initializing git repository...
    git init
)

REM Add remote (remove if exists)
echo 🔗 Setting up remote...
git remote remove origin 2>nul
git remote add origin https://github.com/Zhihong0321/EE-Llamaindex-RAG.git

REM Create .gitignore if it doesn't exist
if not exist .gitignore (
    echo 📝 Creating .gitignore...
    (
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo *.so
        echo .Python
        echo env/
        echo venv/
        echo ENV/
        echo build/
        echo dist/
        echo *.egg-info/
        echo .pytest_cache/
        echo .coverage
        echo htmlcov/
        echo.
        echo # Environment variables
        echo .env
        echo .env.local
        echo.
        echo # IDE
        echo .vscode/
        echo .idea/
        echo *.swp
        echo *.swo
        echo .kiro/
        echo.
        echo # Database
        echo *.db
        echo *.sqlite
        echo.
        echo # Logs
        echo *.log
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
        echo.
        echo # Alembic
        echo alembic/versions/*.pyc
    ) > .gitignore
)

REM Add all files
echo 📁 Adding files...
git add .

REM Create commit
echo 💾 Creating commit...
git commit -m "Initial commit: Production-ready LlamaIndex RAG API" -m "Features:" -m "- Complete RAG implementation with LlamaIndex + FastAPI + PostgreSQL" -m "- Document ingestion with vector embeddings (pgvector)" -m "- Conversational chat with session management" -m "- Source attribution with relevance scores" -m "- Comprehensive testing (unit, integration, E2E)" -m "- Production deployment guides (Railway, Docker)" -m "- Security hardening and best practices" -m "- Performance optimization guidelines" -m "- Monitoring and alerting strategies" -m "- Complete documentation"

REM Push to GitHub
echo ⬆️  Pushing to GitHub...
git branch -M main
git push -u origin main --force

echo ✅ Successfully pushed to https://github.com/Zhihong0321/EE-Llamaindex-RAG
echo.
echo Next steps:
echo 1. Visit your repository: https://github.com/Zhihong0321/EE-Llamaindex-RAG
echo 2. Review the README.md for setup instructions
echo 3. Check out the production deployment guides
echo 4. Deploy to Railway or your preferred platform

pause
