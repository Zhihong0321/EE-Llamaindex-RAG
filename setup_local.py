"""Local deployment setup and verification script."""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, check=True, capture=True):
    """Run a shell command and return result."""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return result.returncode == 0, "", ""
    except subprocess.CalledProcessError as e:
        return False, e.stdout if hasattr(e, 'stdout') else "", e.stderr if hasattr(e, 'stderr') else str(e)

def print_step(step_num, total, message):
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}/{total}: {message}")
    print('='*60)

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message."""
    print(f"⚠️  {message}")

def check_docker():
    """Check if Docker is installed and running."""
    print_step(1, 8, "Checking Docker Installation")
    
    # Check Docker version
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print_error("Docker is not installed or not in PATH")
        return False
    
    print_success(f"Docker installed: {stdout.strip()}")
    
    # Check if Docker daemon is running
    success, stdout, stderr = run_command("docker ps")
    if not success:
        print_error("Docker daemon is not running")
        print("Please start Docker Desktop or Docker service")
        return False
    
    print_success("Docker daemon is running")
    
    # Check Docker Compose
    success, stdout, stderr = run_command("docker compose version")
    if not success:
        # Try with hyphen
        success, stdout, stderr = run_command("docker-compose version")
        if not success:
            print_warning("Docker Compose not found, but may not be needed")
        else:
            print_success(f"Docker Compose installed: {stdout.strip()}")
    else:
        print_success(f"Docker Compose installed: {stdout.strip()}")
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    print_step(2, 8, "Checking Configuration Files")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error(".env file not found")
        return False
    
    print_success(".env file exists")
    
    # Read and check required variables
    required_vars = [
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "DB_URL",
        "CHAT_MODEL",
        "EMBEDDING_MODEL"
    ]
    
    env_content = env_path.read_text()
    missing_vars = []
    
    for var in required_vars:
        if var not in env_content or f"{var}=" not in env_content:
            missing_vars.append(var)
        else:
            # Extract value
            for line in env_content.split('\n'):
                if line.startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if value and not value.startswith('#'):
                        print_success(f"{var} is set")
                    else:
                        missing_vars.append(var)
                    break
    
    if missing_vars:
        print_error(f"Missing or empty environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def check_python_deps():
    """Check if Python dependencies are installed."""
    print_step(3, 8, "Checking Python Dependencies")
    
    try:
        import fastapi
        print_success(f"FastAPI installed: {fastapi.__version__}")
    except ImportError:
        print_error("FastAPI not installed")
        print("Run: pip install -r requirements.txt")
        return False
    
    try:
        import llama_index
        print_success("LlamaIndex installed")
    except ImportError:
        print_error("LlamaIndex not installed")
        print("Run: pip install -r requirements.txt")
        return False
    
    try:
        import asyncpg
        print_success("asyncpg installed")
    except ImportError:
        print_error("asyncpg not installed")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_config_loading():
    """Test if configuration can be loaded."""
    print_step(4, 8, "Testing Configuration Loading")
    
    try:
        from app.config import load_config
        config = load_config()
        
        print_success(f"Configuration loaded successfully")
        print(f"  - API Base: {config.openai_api_base}")
        print(f"  - Chat Model: {config.chat_model}")
        print(f"  - Embedding Model: {config.embedding_model}")
        print(f"  - Database URL: {config.db_url[:30]}...")
        
        return True
    except Exception as e:
        print_error(f"Failed to load configuration: {str(e)}")
        return False

def start_postgres():
    """Start PostgreSQL container."""
    print_step(5, 8, "Starting PostgreSQL Container")
    
    # Check if container already exists
    success, stdout, stderr = run_command("docker ps -a --filter name=llamaindex_postgres --format '{{.Names}}'")
    
    if "llamaindex_postgres" in stdout:
        print_warning("PostgreSQL container already exists")
        
        # Check if it's running
        success, stdout, stderr = run_command("docker ps --filter name=llamaindex_postgres --format '{{.Names}}'")
        if "llamaindex_postgres" in stdout:
            print_success("PostgreSQL container is already running")
            return True
        else:
            print("Starting existing container...")
            success, stdout, stderr = run_command("docker start llamaindex_postgres")
            if success:
                print_success("PostgreSQL container started")
                time.sleep(3)
                return True
            else:
                print_error(f"Failed to start container: {stderr}")
                return False
    
    # Start new container
    print("Starting PostgreSQL container with docker compose...")
    success, stdout, stderr = run_command("docker compose up postgres -d", capture=False)
    
    if not success:
        print_error("Failed to start PostgreSQL container")
        print(f"Error: {stderr}")
        return False
    
    print_success("PostgreSQL container started")
    print("Waiting for PostgreSQL to be ready...")
    time.sleep(5)
    
    return True

def verify_postgres():
    """Verify PostgreSQL is accessible."""
    print_step(6, 8, "Verifying PostgreSQL Connection")
    
    # Check if container is healthy
    success, stdout, stderr = run_command(
        "docker exec llamaindex_postgres pg_isready -U llamaindex"
    )
    
    if not success:
        print_error("PostgreSQL is not ready")
        print("Check logs with: docker logs llamaindex_postgres")
        return False
    
    print_success("PostgreSQL is ready and accepting connections")
    
    # Check pgvector extension
    success, stdout, stderr = run_command(
        'docker exec llamaindex_postgres psql -U llamaindex -d llamaindex_rag -c "CREATE EXTENSION IF NOT EXISTS vector"'
    )
    
    if success:
        print_success("pgvector extension is available")
    else:
        print_warning("Could not verify pgvector extension")
    
    return True

def run_migrations():
    """Run database migrations."""
    print_step(7, 8, "Running Database Migrations")
    
    print("Running alembic upgrade head...")
    success, stdout, stderr = run_command("alembic upgrade head", capture=False)
    
    if not success:
        print_error("Failed to run migrations")
        print(f"Error: {stderr}")
        return False
    
    print_success("Database migrations completed")
    
    # Verify tables were created
    success, stdout, stderr = run_command(
        'docker exec llamaindex_postgres psql -U llamaindex -d llamaindex_rag -c "\\dt"'
    )
    
    if success and "sessions" in stdout and "messages" in stdout and "documents" in stdout:
        print_success("Database tables created successfully")
        print(stdout)
    else:
        print_warning("Could not verify table creation")
    
    return True

def print_next_steps():
    """Print next steps for the user."""
    print_step(8, 8, "Setup Complete!")
    
    print("\n" + "="*60)
    print("✅ Local environment is ready for testing!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("\n1. Start the API server:")
    print("   uvicorn app.main:app --reload")
    print("\n   OR with Docker Compose:")
    print("   docker compose up --build")
    
    print("\n2. In a new terminal, test the API:")
    print("   python test_api.py")
    
    print("\n3. Or test manually:")
    print("   curl http://localhost:8000/health")
    
    print("\n4. View API documentation:")
    print("   http://localhost:8000/docs")
    
    print("\n5. Check logs:")
    print("   docker logs llamaindex_postgres")
    print("   docker logs llamaindex_api  (if using docker compose)")
    
    print("\n" + "="*60)

def main():
    """Main setup flow."""
    print("\n" + "="*60)
    print("LlamaIndex RAG API - Local Deployment Setup")
    print("="*60)
    
    # Run all checks
    checks = [
        ("Docker", check_docker),
        ("Environment", check_env_file),
        ("Python Dependencies", check_python_deps),
        ("Configuration", test_config_loading),
        ("PostgreSQL Start", start_postgres),
        ("PostgreSQL Verify", verify_postgres),
        ("Migrations", run_migrations),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                failed_checks.append(check_name)
                print_error(f"{check_name} check failed")
                
                # Stop on critical failures
                if check_name in ["Docker", "Environment"]:
                    print("\n❌ Critical check failed. Please fix the issues and run again.")
                    sys.exit(1)
        except Exception as e:
            print_error(f"{check_name} check failed with exception: {str(e)}")
            failed_checks.append(check_name)
            
            if check_name in ["Docker", "Environment"]:
                sys.exit(1)
    
    if failed_checks:
        print("\n" + "="*60)
        print(f"⚠️  Setup completed with {len(failed_checks)} warning(s)")
        print(f"Failed checks: {', '.join(failed_checks)}")
        print("="*60)
        print("\nYou may still be able to proceed, but some features might not work.")
    
    print_next_steps()

if __name__ == "__main__":
    main()
