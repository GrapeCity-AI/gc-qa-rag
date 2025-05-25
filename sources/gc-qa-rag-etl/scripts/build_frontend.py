import os
import shutil
import subprocess
from pathlib import Path

def build_and_deploy_frontend():
    # Get the root directory
    root_dir = Path(__file__).parent.parent
    frontend_dir = root_dir / "etlapp-web"
    static_dir = root_dir / "static"

    # Build frontend
    print("Building frontend...")
    subprocess.run(["pnpm", "install"], cwd=frontend_dir, check=True)
    subprocess.run(["pnpm", "build"], cwd=frontend_dir, check=True)

    # Clear existing static directory
    if static_dir.exists():
        shutil.rmtree(static_dir)
    
    # Copy build output to static directory
    dist_dir = frontend_dir / "dist"
    shutil.copytree(dist_dir, static_dir)
    print(f"Frontend build deployed to {static_dir}")

if __name__ == "__main__":
    build_and_deploy_frontend() 