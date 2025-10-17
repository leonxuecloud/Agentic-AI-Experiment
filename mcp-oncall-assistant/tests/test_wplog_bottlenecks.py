#!/usr/bin/env python3
"""
Test wplog_find_bottlenecks function with the provided test file

Usage:
    python tests/test_wplog_bottlenecks.py [path_to_wplog_file]
    
    If no path is provided, uses WPLOG_TEST_FILE environment variable
    or defaults to './test_data/wplog2014.txt'
"""

import sys
import json
import os
from pathlib import Path

# Add the project root and src directory to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

def get_test_file_path():
    """Get the test file path from arguments, environment, or default"""
    # Priority: 1) Command line arg, 2) Environment variable, 3) Default
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    env_path = os.getenv('WPLOG_TEST_FILE')
    if env_path:
        return env_path
    
    # Default to a test_data directory in the project
    default_path = PROJECT_ROOT / "test_data" / "wplog2014.txt"
    return str(default_path)

def test_wplog_find_bottlenecks():
    """Test the wplog_find_bottlenecks function with the specific test file"""
    from server import wplog_find_bottlenecks
    
    test_file_path = get_test_file_path()
    
    print(f"🧪 Testing wplog_find_bottlenecks with: {test_file_path}")
    print("=" * 60)
    
    # Check if file exists
    if not Path(test_file_path).exists():
        print(f"❌ Test file not found: {test_file_path}")
        print("Please ensure the file exists at the specified path.")
        return False
    
    # Test with default parameters
    print("📋 Test 1: Default parameters (5.0 second minimum gap)")
    result = wplog_find_bottlenecks(test_file_path)
    
    print(f"✅ Success: {result.get('success')}")
    print(f"📊 Total gaps found: {result.get('total_gaps_found', 0)}")
    print(f"🔍 Top time gaps: {len(result.get('top_time_gaps', []))}")
    print(f"🚨 Verified bottlenecks: {len(result.get('verified_bottlenecks', []))}")
    
    if result.get('primary_bottleneck'):
        primary = result['primary_bottleneck']
        print(f"🎯 Primary bottleneck: {primary.get('duration_minutes', 0):.2f} minutes")
        print(f"   Lines: {primary.get('lines', 'N/A')}")
    
    print("\n" + "=" * 60)
    
    # Test with lower threshold for more sensitive detection
    print("📋 Test 2: Lower threshold (1.0 second minimum gap)")
    result2 = wplog_find_bottlenecks(test_file_path, min_gap_seconds=1.0)
    
    print(f"✅ Success: {result2.get('success')}")
    print(f"📊 Total gaps found: {result2.get('total_gaps_found', 0)}")
    print(f"🔍 Top time gaps: {len(result2.get('top_time_gaps', []))}")
    
    # Show top 3 time gaps for detailed analysis
    if result2.get('top_time_gaps'):
        print("\n🔍 Top 3 Time Gaps:")
        for i, gap in enumerate(result2['top_time_gaps'][:3], 1):
            print(f"  {i}. Duration: {gap.get('duration_minutes', 0):.2f} minutes")
            print(f"     Lines: {gap.get('start_line')} → {gap.get('end_line')}")
            print(f"     Start: {gap.get('start_message', '')[:80]}...")
            print(f"     End: {gap.get('end_message', '')[:80]}...")
            print()
    
    # Show verified bottlenecks if any
    if result2.get('verified_bottlenecks'):
        print("🚨 Verified Bottlenecks:")
        for i, bottleneck in enumerate(result2['verified_bottlenecks'][:3], 1):
            print(f"  {i}. Type: {bottleneck.get('type', 'Unknown')}")
            print(f"     Duration: {bottleneck.get('duration_minutes', 0):.2f} minutes")
            print(f"     User: {bottleneck.get('user', 'Unknown')}")
            print(f"     Process: {bottleneck.get('process', 'Unknown')}")
            print()
    
    print("\n" + "=" * 60)
    
    # Test error handling with non-existent file
    print("📋 Test 3: Error handling (non-existent file)")
    result3 = wplog_find_bottlenecks("non_existent_file.txt")
    print(f"❌ Expected failure: {not result3.get('success')}")
    print(f"📝 Error message: {result3.get('error', 'No error message')}")
    
    return result.get('success', False) and result2.get('success', False)

def detailed_analysis():
    """Perform detailed analysis of the test file"""
    from tools.wplog.wplog_analyzer import WPLogAnalyzer
    
    test_file_path = get_test_file_path()
    
    if not Path(test_file_path).exists():
        print(f"❌ Test file not found: {test_file_path}")
        return
    
    print("\n🔬 Detailed Analysis of wplog2014.txt")
    print("=" * 60)
    
    analyzer = WPLogAnalyzer(verbose=True)
    analyzer.load_log_file(test_file_path)
    analyzer.analyze_time_gaps(min_gap_seconds=1.0)
    analyzer.analyze_errors()
    
    print(f"\n📊 Analysis Summary:")
    print(f"   Total entries: {len(analyzer.log_entries):,}")
    print(f"   Total errors: {len(analyzer.errors):,}")
    print(f"   Time gaps: {len(analyzer.time_gaps)}")
    print(f"   Duration: {analyzer._get_total_duration()}")
    
    # Show log entry types
    log_types = {}
    for entry in analyzer.log_entries:
        log_types[entry.log_type] = log_types.get(entry.log_type, 0) + 1
    
    print(f"\n📝 Log Entry Types:")
    for log_type, count in log_types.items():
        print(f"   {log_type}: {count:,} entries")
    
    # Show sample entries
    print(f"\n📄 Sample Log Entries (first 3):")
    for i, entry in enumerate(analyzer.log_entries[:3], 1):
        print(f"   {i}. [{entry.log_type}] {entry.timestamp} - {entry.message[:80]}...")
    
    return True

if __name__ == "__main__":
    try:
        success = test_wplog_find_bottlenecks()
        if success:
            print("\n✅ Basic tests passed!")
            detailed_analysis()
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n❌ Some tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)