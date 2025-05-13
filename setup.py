from setuptools import setup, find_packages, Command
import os
import sys
import subprocess

class DevelopCommand(Command):
    """Custom develop command to set up symlinks before installation."""
    description = 'Set up development environment with symlinks'
    user_options = []
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        # Run the setup_dev.py script
        setup_dev_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'setup_dev.py')
        subprocess.check_call([sys.executable, setup_dev_path])

packages = find_packages()
packages.append('a2a.samples.python')
packages.append('common')  # Add common as a top-level package

setup(
    name="autoa2a",
    version="0.0.1",
    description="Converts any agent into A2A server",
    packages=packages,
    package_dir={
        'a2a.samples.python': 'a2a/samples/python',
        'common': 'a2a/samples/python/common',  # Map common directly
    },
    package_data={
        'a2a.samples.python': ['**/*.py'],
        'common': ['**/*.py'],
    },
    cmdclass={
        'develop': DevelopCommand,
    },
)