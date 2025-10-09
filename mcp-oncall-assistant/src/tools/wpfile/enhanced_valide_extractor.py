#!/usr/bin/env python3
"""
Enhanced CaseWare File Extractor - Focus on Archives
Specifically designed to extract ALL files from CaseWare archives.

Usage:
    python enhanced_valide_extractor.py <stream_file> <output_dir>
    
Environment variables:
    CASEWARE_STREAM_FILE - Path to the stream file to process
    CASEWARE_OUTPUT_DIR - Output directory for extracted files
"""

import os
import struct
import zipfile
import lzma
import sys
from pathlib import Path

def extract_from_raw_stream(stream_path, output_dir):
    """Extract files from raw CasewareDocument stream"""
    print(f"🔍 Analyzing raw stream: {stream_path}")
    
    with open(stream_path, 'rb') as f:
        data = f.read()
    
    print(f"📊 Stream size: {len(data):,} bytes")
    
    # Look for ZIP signature at different offsets
    zip_signatures = [b'PK\x03\x04', b'PK\x01\x02', b'PK\x05\x06']
    
    zip_offsets = []
    for sig in zip_signatures:
        offset = 0
        while True:
            offset = data.find(sig, offset)
            if offset == -1:
                break
            zip_offsets.append(offset)
            print(f"✅ Found ZIP signature {sig.hex()} at offset {offset}")
            offset += 1
    
    if not zip_offsets:
        print("❌ No ZIP signatures found")
        return 0
    
    # Try extracting from each ZIP offset
    total_extracted = 0
    
    for i, offset in enumerate(sorted(set(zip_offsets))):
        try:
            print(f"\n🎯 Attempting extraction from offset {offset}")
            
            # Create temporary ZIP file from this offset
            zip_data = data[offset:]
            temp_zip = output_dir / f"temp_stream_{i}.zip"
            
            with open(temp_zip, 'wb') as f:
                f.write(zip_data)
            
            # Try to extract
            extract_dir = output_dir / f"extracted_from_offset_{offset}"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(temp_zip, 'r') as zf:
                files_in_zip = zf.namelist()
                print(f"📁 Found {len(files_in_zip)} files in ZIP at offset {offset}")
                
                for filename in files_in_zip:
                    print(f"  📄 {filename}")
                    try:
                        # Extract and decompress if needed
                        file_data = zf.read(filename)
                        
                        # Check for CaseWare LZMA2 header
                        if len(file_data) >= 12 and file_data[:4] == b'\x0c\x00\x00\x00':
                            print(f"    🔓 LZMA2 compressed: {len(file_data)} bytes")
                            try:
                                # Skip 12-byte header and decompress
                                compressed_data = file_data[12:]
                                decompressed = lzma.decompress(compressed_data, format=lzma.FORMAT_ALONE)
                                file_data = decompressed
                                print(f"    ✅ Decompressed: {len(compressed_data)} → {len(decompressed)} bytes")
                            except Exception as e:
                                print(f"    ⚠️ LZMA2 decompression failed: {e}")
                        
                        # Save file
                        output_file = extract_dir / filename
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output_file, 'wb') as f:
                            f.write(file_data)
                        
                        total_extracted += 1
                        print(f"    💾 Saved: {output_file} ({len(file_data)} bytes)")
                        
                    except Exception as e:
                        print(f"    ❌ Failed to extract {filename}: {e}")
            
            # Clean up temp file
            temp_zip.unlink()
            
        except Exception as e:
            print(f"❌ Failed to process offset {offset}: {e}")
    
    return total_extracted

def main():
    print("🔧 Enhanced Archive Extractor")
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
            print("Usage: python enhanced_valide_extractor.py <stream_file> [output_dir]")
            print("Or set CASEWARE_STREAM_FILE environment variable")
            return
    
    if not stream_file.exists():
        print(f"❌ Stream file not found: {stream_file}")
        return
    
    # Get output directory
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    elif os.getenv('CASEWARE_OUTPUT_DIR'):
        output_dir = Path(os.getenv('CASEWARE_OUTPUT_DIR'))
    else:
        output_dir = Path("03_Extracted_Data/Enhanced_Extraction")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_files = extract_from_raw_stream(stream_file, output_dir)
    
    print(f"\n🎉 EXTRACTION COMPLETE")
    print(f"Total files extracted: {total_files}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
