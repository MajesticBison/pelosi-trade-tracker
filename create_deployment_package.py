#!/usr/bin/env python3
"""
Create a deployment package for Windows deployment
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a zip file with all necessary files for Windows deployment."""
    
    # Files to include in the deployment package
    files_to_include = [
        'pelosi_tracker.py',
        'scraper.py', 
        'pdf_parser.py',
        'database.py',
        'discord_notifier.py',
        'requirements.txt',
        'env.example',
        'README.md',
        'WINDOWS_DEPLOYMENT.md',
        'check_status.py',
        'setup_windows_task.ps1',
        'setup_windows.bat'
    ]
    
    # Create deployment directory
    deployment_dir = Path('windows_deployment')
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    deployment_dir.mkdir()
    
    print("📦 Creating Windows deployment package...")
    print("=" * 50)
    
    # Copy files to deployment directory
    copied_files = []
    for file_name in files_to_include:
        if os.path.exists(file_name):
            shutil.copy2(file_name, deployment_dir / file_name)
            copied_files.append(file_name)
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (not found)")
    
    # Create a simple README for the deployment package
    readme_content = """# Pelosi Trade Tracker - Windows Deployment Package

## Quick Setup

1. **Extract this zip file** to a folder like `C:\\PelosiTracker\\`

2. **Run the setup script**:
   ```
   setup_windows.bat
   ```

3. **Edit the .env file** with your Discord webhook URL

4. **Set up Task Scheduler** (run as Administrator):
   ```
   PowerShell -ExecutionPolicy Bypass -File setup_windows_task.ps1
   ```

## Files Included

- `pelosi_tracker.py` - Main script
- `scraper.py` - Web scraping module
- `pdf_parser.py` - PDF parsing module  
- `database.py` - Database operations
- `discord_notifier.py` - Discord notifications
- `requirements.txt` - Python dependencies
- `env.example` - Environment template
- `setup_windows.bat` - Easy setup script
- `setup_windows_task.ps1` - Task Scheduler setup
- `check_status.py` - Status monitoring
- `WINDOWS_DEPLOYMENT.md` - Detailed instructions

## Testing

After setup, test with:
```
python pelosi_tracker.py --dry-run
python pelosi_tracker.py --test-discord
python check_status.py
```

## Support

See `WINDOWS_DEPLOYMENT.md` for detailed instructions and troubleshooting.
"""
    
    with open(deployment_dir / 'README.txt', 'w') as f:
        f.write(readme_content)
    
    # Create zip file
    zip_filename = 'pelosi_tracker_windows.zip'
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    
    print(f"\n📦 Creating zip file: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in deployment_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(deployment_dir)
                zipf.write(file_path, arcname)
    
    # Clean up deployment directory
    shutil.rmtree(deployment_dir)
    
    # Get file size
    file_size = os.path.getsize(zip_filename) / 1024 / 1024  # MB
    
    print(f"✅ Deployment package created: {zip_filename}")
    print(f"📊 Package size: {file_size:.1f} MB")
    print(f"📁 Files included: {len(copied_files)}")
    
    print("\n🚀 Deployment Instructions:")
    print("1. Copy the zip file to your Windows computer")
    print("2. Extract it to C:\\PelosiTracker\\")
    print("3. Run setup_windows.bat")
    print("4. Edit .env with your Discord webhook")
    print("5. Set up Task Scheduler with setup_windows_task.ps1")

if __name__ == "__main__":
    create_deployment_package()
