#!/usr/bin/env python3
"""
Simple runner script to execute the data population process.
This script can be run from the server directory.
"""

import sys
import os
from pathlib import Path

# Add the server directory to the Python path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

# Change to the server directory
os.chdir(server_dir)

# Import and run the data populator
from data.populate_models import main

if __name__ == "__main__":
    print("Starting TigerTalks data population...")
    print("This will parse JSON files and populate the database with course and semester data.")
    print("=" * 60)
    
    try:
        main()
        print("=" * 60)
        print("Data population completed successfully!")
    except Exception as e:
        print(f"Error during data population: {e}")
        sys.exit(1)
