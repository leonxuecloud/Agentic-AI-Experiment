#!/usr/bin/env python3
"""
Test the fixed caseware_analyze_file function
"""

import sys
from pathlib import Path
import tempfile

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_caseware_analyze_file():
    """Test the caseware_analyze_file function with a sample file"""
    from server import caseware_analyze_file
    
    # Create a temporary test file with OLE header
    ole_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'TESTDATA' * 100
    
    with tempfile.NamedTemporaryFile(suffix='.ac_', delete=False) as temp_file:
        temp_file.write(ole_header)
        temp_file.flush()
        
        # Test the analyze function
        print(f"🧪 Testing caseware_analyze_file with: {temp_file.name}")
        result = caseware_analyze_file(temp_file.name)
        
        print("📋 Analysis Result:")
        print(f"  Success: {result.get('success')}")
        print(f"  File Type: {result.get('file_type')}")
        print(f"  File Size: {result.get('file_size')} bytes")
        print(f"  File Hash: {result.get('file_hash')}")
        
        if 'ole_structure' in result:
            ole = result['ole_structure']
            print(f"  OLE Valid: {ole.get('valid_ole_header')}")
            print(f"  Sector Size: {ole.get('sector_size')}")
        
        if 'ole_analysis_error' in result:
            print(f"  OLE Error: {result['ole_analysis_error']}")
        
        # Clean up
        try:
            Path(temp_file.name).unlink()
        except OSError:
            pass  # File might still be in use, ignore cleanup error
        
        return result.get('success', False)

if __name__ == "__main__":
    try:
        success = test_caseware_analyze_file()
        if success:
            print("\n✅ Test passed! The caseware_analyze_file function is working correctly.")
        else:
            print("\n❌ Test failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        sys.exit(1)