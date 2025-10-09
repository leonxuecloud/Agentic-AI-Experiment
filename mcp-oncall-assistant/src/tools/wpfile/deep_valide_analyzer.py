#!/usr/bin/env python3
"""
Deep Analysis of CaseWare Archives
Find all possible files including missing files.

Usage:
    python deep_valide_analyzer.py <stream_file>
    
Environment variable:
    CASEWARE_STREAM_FILE - Path to the stream file to analyze
"""

import os
import struct
import lzma
import sys
from pathlib import Path

def find_lzma2_blocks(data):
    """Find all CaseWare LZMA2 blocks in data"""
    blocks = []
    offset = 0
    
    while offset < len(data) - 12:
        # Look for CaseWare LZMA2 header pattern: 0x0000000c + size + 0x00000000
        if data[offset:offset+4] == b'\x0c\x00\x00\x00':
            # Read the size field
            try:
                size_bytes = data[offset+4:offset+8]
                if len(size_bytes) == 4:
                    size = struct.unpack('<I', size_bytes)[0]
                    
                    # Check for the second part of header (should be 0x00000000)
                    if data[offset+8:offset+12] == b'\x00\x00\x00\x00':
                        if offset + 12 + size <= len(data):
                            blocks.append({
                                'offset': offset,
                                'header_size': 12,
                                'payload_size': size,
                                'total_size': 12 + size,
                                'payload_data': data[offset+12:offset+12+size]
                            })
                            print(f"✅ Found LZMA2 block at offset {offset}: {size} bytes payload")
                            offset += 12 + size
                            continue
            except:
                pass
        
        offset += 1
    
    return blocks

def try_decompress_lzma2(data):
    """Try different LZMA2 decompression methods"""
    methods = [
        ('FORMAT_ALONE', lzma.FORMAT_ALONE),
        ('FORMAT_XZ', lzma.FORMAT_XZ),
        ('FORMAT_RAW', lzma.FORMAT_RAW),
    ]
    
    for name, fmt in methods:
        try:
            result = lzma.decompress(data, format=fmt)
            return result, name
        except Exception as e:
            continue
    
    return None, None

def analyze_valide_stream():
    """Deep analysis of the stream"""
    print("🔬 Deep Analysis of CaseWare Archive")
    print("=" * 50)
    
    # Get stream file from command line, environment variable, or search
    if len(sys.argv) > 1:
        stream_file = Path(sys.argv[1])
    elif os.getenv('CASEWARE_STREAM_FILE'):
        stream_file = Path(os.getenv('CASEWARE_STREAM_FILE'))
    else:
        # Look for stream files in common locations
        search_dirs = [
            Path("03_Extracted_Data/Raw_Streams"),
            Path.cwd()
        ]
        stream_file = None
        for search_dir in search_dirs:
            if search_dir.exists():
                bin_files = list(search_dir.glob("*.bin"))
                if bin_files:
                    stream_file = bin_files[0]
                    break
        
        if not stream_file:
            print("❌ No stream file found.")
            print("Usage: python deep_valide_analyzer.py <stream_file>")
            print("Or set CASEWARE_STREAM_FILE environment variable")
            return
    
    if not stream_file.exists():
        print(f"❌ Stream file not found: {stream_file}")
        return
    
    with open(stream_file, 'rb') as f:
        data = f.read()
    
    print(f"📊 Stream size: {len(data):,} bytes")
    print(f"🔍 First 64 bytes: {data[:64].hex()}")
    
    # Look for LZMA2 blocks
    blocks = find_lzma2_blocks(data)
    print(f"\n📦 Found {len(blocks)} LZMA2 blocks")
    
    output_dir = Path("03_Extracted_Data/Deep_Valide_Analysis")
    output_dir.mkdir(exist_ok=True)
    
    extracted_count = 0
    
    for i, block in enumerate(blocks):
        print(f"\n🎯 Processing block {i+1}/{len(blocks)}")
        print(f"   Offset: {block['offset']}")
        print(f"   Payload size: {block['payload_size']} bytes")
        
        # Try to decompress
        decompressed, method = try_decompress_lzma2(block['payload_data'])
        
        if decompressed:
            print(f"   ✅ Decompressed with {method}: {len(decompressed)} bytes")
            
            # Save decompressed data
            output_file = output_dir / f"block_{i+1}_decompressed.bin"
            with open(output_file, 'wb') as f:
                f.write(decompressed)
            
            # Check if it looks like a known file type
            if decompressed.startswith(b'PK'):
                print(f"   📦 Looks like ZIP data")
            elif decompressed.startswith(b'\x00\x00'):
                print(f"   💾 Looks like database file")
            elif b'.ac' in decompressed[:100]:
                print(f"   🎯 Contains .ac reference!")
            
            # Look for filename patterns
            if b'Friedlander' in decompressed:
                print(f"   📄 Contains 'Friedlander' text")
            
            extracted_count += 1
        else:
            print(f"   ❌ Failed to decompress")
            
            # Save raw data anyway
            output_file = output_dir / f"block_{i+1}_raw.bin"
            with open(output_file, 'wb') as f:
                f.write(block['payload_data'])
    
    # Also look for reference .ac files
    print(f"\n🔍 Analyzing reference .ac files...")
    
    # Search for .ac files in common locations
    search_dirs = [
        Path("01_Source_Files"),
        stream_file.parent.parent / "01_Source_Files",
        Path.cwd()
    ]
    
    ref_ac_file = None
    for search_dir in search_dirs:
        if search_dir.exists():
            ac_files = list(search_dir.rglob("*.ac"))
            if ac_files:
                ref_ac_file = ac_files[0]
                break
    
    if ref_ac_file and ref_ac_file.exists():
        with open(ref_ac_file, 'rb') as f:
            ac_data = f.read()
        
        print(f"📊 Reference .ac file size: {len(ac_data)} bytes")
        print(f"🔍 First 64 bytes: {ac_data[:64].hex()}")
        
        # Look for this pattern in our extracted blocks
        ac_start = ac_data[:32]
        for i, block in enumerate(blocks):
            decompressed, _ = try_decompress_lzma2(block['payload_data'])
            if decompressed and ac_start in decompressed:
                print(f"   🎯 Found .ac file pattern in block {i+1}!")
                
                # Save as .ac file
                output_ac = output_dir / "recovered_Friedlander (GF) Prof Corp - 2024.ac"
                with open(output_ac, 'wb') as f:
                    f.write(decompressed)
                print(f"   💾 Saved as: {output_ac}")
    
    print(f"\n🎉 ANALYSIS COMPLETE")
    print(f"Extracted blocks: {extracted_count}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    analyze_valide_stream()
