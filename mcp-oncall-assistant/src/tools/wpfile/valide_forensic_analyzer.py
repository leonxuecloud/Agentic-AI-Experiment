#!/usr/bin/env python3
"""
CaseWare Valide Archive Forensic Analyzer
==========================================
Performs byte-level forensic analysis of the Valide archive to understand
extraction issues and locate missing files.

Analysis Strategy:
1. Compare Valide vs Full archive structures
2. Search for all possible data patterns
3. Attempt recovery from fragmented data
4. Generate detailed forensic report

Usage:
    python valide_forensic_analyzer.py <valide_file>
    python valide_forensic_analyzer.py <valide_file> --reference <reference_file>
    python valide_forensic_analyzer.py --input-dir <directory>
"""

import struct
import os
import sys
import argparse
from pathlib import Path

# Constants
VALIDE_FILE_PATTERNS = ["*valide*", "*Valide*", "*.ac_"]

def hex_dump(data, offset=0, width=16):
    """Generate a hex dump of data"""
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        lines.append(f'{offset+i:08x}: {hex_str:<48} |{ascii_str}|')
    return '\n'.join(lines)

def search_patterns(data):
    """Search for various file format signatures and patterns"""
    patterns = {
        'ZIP Local': b'PK\x03\x04',
        'ZIP Central': b'PK\x01\x02', 
        'ZIP End': b'PK\x05\x06',
        'OLE Document': b'\xd0\xcf\x11\xe0',
        'LZMA2 Header': b'\x00\x00\x00\x0c',
        'CaseWare Stream': b'CasewareDocument',
        'AC File Pattern': b'.ac',
        'Friedlander': b'Friedlander',
        'GF Prof Corp': b'GF Prof Corp',
        '2024': b'2024'
    }
    
    found = {}
    for name, pattern in patterns.items():
        positions = []
        start = 0
        while True:
            pos = data.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        if positions:
            found[name] = positions
    
    return found

def analyze_ole_structure(data):
    """Analyze OLE compound document structure"""
    if len(data) < 512:
        return None
    
    try:
        # Read OLE header
        header = struct.unpack('<8s16sHHHHHHII4s2s2sII4sII', data[:76])
        
        return {
            'signature': header[0],
            'minor_version': header[2],
            'major_version': header[3],
            'byte_order': header[4],
            'sector_size': 2 ** header[5],
            'mini_sector_size': 2 ** header[6],
            'num_dir_sectors': header[7],
            'num_fat_sectors': header[8],
            'dir_first_sector': header[9],
            'mini_stream_cutoff': header[12],
            'mini_fat_first_sector': header[13],
            'num_mini_fat_sectors': header[14],
            'difat_first_sector': header[15],
            'num_difat_sectors': header[16]
        }
    except:
        return None

def find_valide_file(input_dir=None):
    """Find Valide archive file in the specified directory or default locations"""
    if input_dir:
        input_dir = Path(input_dir)
        for pattern in VALIDE_FILE_PATTERNS:
            files = list(input_dir.glob(pattern))
            if files:
                return files[0]
        return None
    
    # Default search locations
    base_dir = Path(__file__).parent.parent.parent
    possible_paths = [
        base_dir / "01_Source_Files" / "Valide.ac_",
        base_dir / "01_Source_Files" / "valide.ac_", 
        Path("Valide.ac_"),
        Path("valide.ac_"),
        Path("sss")  # Keep original as fallback
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def find_reference_file(valide_path=None):
    """Find reference file in common locations"""
    base_dir = Path(__file__).parent.parent.parent
    
    # Look for any .ac file in source directories
    possible_dirs = [
        base_dir / "01_Source_Files",
        Path.cwd()
    ]
    
    if valide_path:
        possible_dirs.insert(0, valide_path.parent)
    
    for search_dir in possible_dirs:
        if search_dir.exists():
            ac_files = list(search_dir.glob("*.ac"))
            if ac_files:
                return ac_files[0]
    
    return None

def perform_forensic_analysis(valide_data):
    """Perform the main forensic analysis"""
    print("\n🔍 STRUCTURAL ANALYSIS")
    print("-" * 30)
    
    # OLE structure analysis
    ole_info = analyze_ole_structure(valide_data)
    if ole_info:
        print("✅ Valid OLE compound document detected")
        print(f"   Sector size: {ole_info['sector_size']} bytes")
        print(f"   Directory sectors: {ole_info['num_dir_sectors']}")
        print(f"   FAT sectors: {ole_info['num_fat_sectors']}")
        print(f"   First directory sector: {ole_info['dir_first_sector']}")
    else:
        print("❌ Invalid or corrupt OLE structure")
    
    print("\n🔍 PATTERN SEARCH ANALYSIS")
    print("-" * 30)
    
    patterns = search_patterns(valide_data)
    for name, positions in patterns.items():
        print(f"📍 {name}: {len(positions)} occurrences at {positions[:10]}")
        if len(positions) > 10:
            print(f"   ... and {len(positions) - 10} more")
    
    return patterns

def show_hex_analysis(valide_data, patterns):
    """Show hex dump analysis"""
    print("\n🔍 HEX DUMP ANALYSIS")
    print("-" * 30)
    
    # Show first 512 bytes (OLE header)
    print("📄 First 512 bytes (OLE Header):")
    print(hex_dump(valide_data[:512]))
    
    # Show last 512 bytes
    print("\n📄 Last 512 bytes:")
    print(hex_dump(valide_data[-512:], len(valide_data) - 512))
    
    # If we found interesting patterns, show context around them
    if 'Friedlander' in patterns:
        print("\n📄 Context around 'Friedlander' patterns:")
        for pos in patterns['Friedlander'][:3]:  # Show first 3
            start = max(0, pos - 64)
            end = min(len(valide_data), pos + 64)
            print(f"\nAt offset {pos}:")
            print(hex_dump(valide_data[start:end], start))

def analyze_compression(valide_data):
    """Analyze compression signatures"""
    print("\n🔍 COMPRESSION ANALYSIS")
    print("-" * 30)
    
    # Look for LZMA2 headers more broadly
    lzma2_sigs = []
    for i in range(len(valide_data) - 12):
        if valide_data[i:i+4] == b'\x00\x00\x00\x0c':
            # Check if this looks like a valid LZMA2 header
            size_bytes = valide_data[i+4:i+12]
            if len(size_bytes) == 8:
                size1, size2 = struct.unpack('<II', size_bytes)
                lzma2_sigs.append((i, size1, size2))
    
    print(f"🔍 Found {len(lzma2_sigs)} potential LZMA2 headers:")
    for pos, size1, size2 in lzma2_sigs:
        print(f"   Offset {pos}: sizes {size1}, {size2}")
        
        # Show context
        start = max(0, pos - 32)
        end = min(len(valide_data), pos + 64)
        print("   Context:")
        print(hex_dump(valide_data[start:end], start))
        print()

def compare_with_reference(valide_data, ref_data):
    """Compare with reference file if available"""
    print("\n🔍 SIZE COMPARISON")
    print("-" * 30)
    
    if ref_data:
        print(f"Valide archive: {len(valide_data):,} bytes")
        print(f"Reference .ac:  {len(ref_data):,} bytes")
        print(f"Size ratio:     {len(valide_data) / len(ref_data):.1%}")
        
        # Check if Valide data appears anywhere in reference
        if valide_data in ref_data:
            pos = ref_data.find(valide_data)
            print(f"✅ Valide data found as subset at offset {pos} in reference")
        else:
            print("❌ Valide data not found as complete subset in reference")

def generate_forensic_conclusion(valide_data, patterns):
    """Generate forensic conclusion"""
    print("\n🎯 FORENSIC CONCLUSION")
    print("-" * 30)
    
    # Determine the nature of this archive
    if len(valide_data) < 10000:  # Less than 10KB
        print("📋 VERDICT: Valide appears to be a partial/stub archive")
        print("   - Extremely small size suggests incomplete data")
        print("   - May contain only index/metadata")
        print("   - Missing actual file content")
        
        if 'LZMA2 Header' in patterns:
            print("   - Contains LZMA2 headers but minimal payload")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. This Valide archive is likely just metadata/index")
        print("   2. The actual files may be in separate archives")
        print("   3. Need to locate the full archive containing all 60 files")
        print("   4. The reference .ac file is not in this stub")

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="CaseWare Valide Archive Forensic Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python valide_forensic_analyzer.py valide.ac_
  python valide_forensic_analyzer.py valide.ac_ --reference "Friedlander (GF) Prof Corp - 2024.ac"
  python valide_forensic_analyzer.py --input-dir "./archives"
        """
    )
    
    parser.add_argument(
        'valide_file', 
        nargs='?',
        help='Path to the Valide archive file to analyze'
    )
    
    parser.add_argument(
        '--reference', '-r',
        help='Path to reference .ac file for comparison'
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        help='Input directory to search for Valide files'
    )
    
    args = parser.parse_args()
    
    # Find the valide file
    if args.valide_file:
        valide_path = Path(args.valide_file)
    elif args.input_dir:
        valide_path = find_valide_file(args.input_dir)
        if not valide_path:
            print(f"❌ No Valide archive files found in: {args.input_dir}")
            return
        print(f"🔍 Found Valide file: {valide_path}")
    else:
        valide_path = find_valide_file()
        if not valide_path:
            print("❌ Valide archive not found. Please specify path with:")
            print("   python valide_forensic_analyzer.py <path_to_valide_file>")
            return
    
    # Find reference file
    if args.reference:
        ref_ac_path = Path(args.reference)
    else:
        ref_ac_path = find_reference_file(valide_path)
    
    print("🔬 CaseWare Valide Archive Forensic Analysis")
    print("=" * 60)
    print(f"📂 Analyzing: {valide_path}")
    if ref_ac_path and ref_ac_path.exists():
        print(f"📂 Reference: {ref_ac_path}")
    
    # Load files
    if not valide_path.exists():
        print(f"❌ Valide archive not found: {valide_path}")
        return
    
    valide_data = valide_path.read_bytes()
    print(f"📊 Valide archive size: {len(valide_data):,} bytes")
    
    # Load reference if available
    ref_data = None
    if ref_ac_path and ref_ac_path.exists():
        ref_data = ref_ac_path.read_bytes()
        print(f"📊 Reference .ac file size: {len(ref_data):,} bytes")
    
    # Perform analysis
    patterns = perform_forensic_analysis(valide_data)
    show_hex_analysis(valide_data, patterns)
    analyze_compression(valide_data)
    compare_with_reference(valide_data, ref_data)
    generate_forensic_conclusion(valide_data, patterns)
    
    print("\n🏁 Analysis complete")

if __name__ == "__main__":
    main()
