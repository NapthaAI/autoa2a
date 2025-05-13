#!/usr/bin/env python
"""
Setup development environment for autoa2a.
This script creates the necessary symlinks for development.
"""
import os
import sys
import shutil
import importlib.util

def create_symlink_or_copy(source, target):
    """Create a symlink or copy files if symlinks aren't supported."""
    # Remove existing link/directory if it exists
    if os.path.exists(target):
        if os.path.islink(target):
            os.unlink(target)
        elif os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
    
    # Create link or copy files
    try:
        # Try creating a symlink first
        os.symlink(source, target, target_is_directory=os.path.isdir(source))
        print(f"Created symlink: {target} → {source}")
    except (OSError, AttributeError):
        # If symlink fails (e.g., on Windows without admin), copy instead
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        print(f"Copied: {source} → {target}")

def main():
    # Get project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Define source and target paths
    common_source = os.path.join(project_root, 'a2a', 'samples', 'python', 'common')
    common_target = os.path.join(project_root, 'common')
    
    # Create the symlink/copy for common
    create_symlink_or_copy(common_source, common_target)
    
    # Verify the setup
    try:
        # Try importing the module to verify it works
        spec = importlib.util.find_spec('common')
        if spec:
            print("✓ Verified: 'common' module is importable")
        else:
            print("⚠ Warning: 'common' module is not importable")
    except ImportError:
        print("⚠ Warning: Could not verify module imports")
    
    print("\nDevelopment environment setup complete!")
    print("You can now run:")
    print("  pip install -e .    # For pip")
    print("  uv sync             # For uv")

if __name__ == "__main__":
    main()