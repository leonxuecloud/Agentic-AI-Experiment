#!/usr/bin/env python3
"""
Simple test to verify the file path configuration works
"""

import sys
import os
from pathlib import Path

# Test the path resolution logic
def get_test_file_path():
    """Get the test file path from arguments, environment, or default"""
    # Priority: 1) Command line arg, 2) Environment variable, 3) Default
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    env_path = os.getenv('WPLOG_TEST_FILE')
    if env_path:
        return env_path
    
    # Default to a test_data directory in the project
    default_path = Path(__file__).parent / "test_data" / "wplog2014.txt"
    return str(default_path)

if __name__ == "__main__":
    path = get_test_file_path()
    print(f"Resolved file path: {path}")
    print(f"File exists: {Path(path).exists()}")
    
    # Show which method was used
    if len(sys.argv) > 1:
        print("Source: Command line argument")
    elif os.getenv('WPLOG_TEST_FILE'):
        print("Source: WPLOG_TEST_FILE environment variable")
    else:
        print("Source: Default location (test_data/wplog2014.txt)")
