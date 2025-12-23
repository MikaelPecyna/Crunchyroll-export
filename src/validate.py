#!/usr/bin/env python3
"""
Simple validation script to check if the installation is working correctly.
Run this to verify that all dependencies are installed and the CLI is functional.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.7 or higher."""
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 7):
        print("❌ Python 3.7 or higher required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    return True


def check_dependencies():
    """Check if all required packages are installed."""
    dependencies = {
        "requests": "HTTP requests library",
        "dotenv": "Environment variable management"
    }
    
    all_ok = True
    for package, description in dependencies.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✓ {package:<20} {description}")
        except ImportError:
            print(f"❌ {package:<20} {description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_project_structure():
    """Check if all project files exist."""
    required_files = [
        "main.py",
        "services.py",
        "utils.py",
        "config.py",
        ".env.example",
        "README.md",
    ]
    
    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check if .env file exists and has a token."""
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        print("   Copy .env.example to .env and add your token")
        return False
    
    with open(".env") as f:
        content = f.read()
        if "CRUNCHYROLL_TOKEN=" not in content:
            print("⚠️  CRUNCHYROLL_TOKEN not found in .env")
            return False
    
    print("✓ .env file configured")
    return True


def check_cli_help():
    """Check if CLI help works."""
    try:
        from main import main
        # This is just a basic check that the module loads
        print("✓ CLI module loads successfully")
        return True
    except ImportError as e:
        print(f"❌ CLI module import failed: {e}")
        return False


def main_validation():
    """Run all validation checks."""
    print("=" * 50)
    print("Crunchyroll Data Manager - Installation Check")
    print("=" * 50)
    print()
    
    print("Python Installation:")
    python_ok = check_python_version()
    print()
    
    print("Dependencies:")
    deps_ok = check_dependencies()
    print()
    
    print("Project Structure:")
    structure_ok = check_project_structure()
    print()
    
    print("Configuration:")
    env_ok = check_env_file()
    print()
    
    print("CLI Module:")
    cli_ok = check_cli_help()
    print()
    
    # Summary
    print("=" * 50)
    
    if python_ok and deps_ok and structure_ok and cli_ok:
        if not env_ok:
            print("✓ Installation OK (⚠️  configure token in .env)")
            print()
            print("Next steps:")
            print("1. Edit .env and add your Crunchyroll token")
            print("2. Run: python main.py show-columns")
            return 0
        else:
            print("✓ Installation complete and ready to use!")
            print()
            print("Try this command to test:")
            print("  python main.py show-columns")
            return 0
    else:
        print("❌ Installation incomplete")
        print()
        print("Please:")
        print("1. Install Python 3.7+")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Configure token: cp .env.example .env && edit .env")
        return 1


if __name__ == "__main__":
    sys.exit(main_validation())
