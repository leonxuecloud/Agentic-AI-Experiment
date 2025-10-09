#!/usr/bin/env python3
"""
CaseWare Universal File Recovery Tool
Comprehensive solution for extracting and recovering all files from CaseWare .ac_ archives

Features:
- OLE compound document parsing
- CaseWare LZMA2 decompression
- ZIP archive extraction
- Recursive directory scanning for .ac_ files
- Multiple recovery methods
- Comprehensive error handling
- Progress reporting
- Command-line interface with flexible input/output options

Usage Examples:
    python caseware_universal_extractor.py
    python caseware_universal_extractor.py --help
    python caseware_universal_extractor.py "path/to/file.ac_"
    python caseware_universal_extractor.py "input.ac_" "output_folder"
    python caseware_universal_extractor.py -i "input_folder" -o "output_folder"  # Recursively processes all .ac_ files
"""

import struct
import os
import zlib
import lzma
import zipfile
import shutil
import argparse
import sys
import hashlib
from pathlib import Path

class CaseWareExtractor:
    def __init__(self, input_path=None, output_path=None):
        self.base_dir = Path(__file__).parent.parent
        
        # Set input directory/file
        if input_path:
            self.input_path = Path(input_path).resolve()
        else:
            self.input_path = self.base_dir / "01_Source_Files"
        
        # Set output directory
        if output_path:
            self.output_dir = Path(output_path).resolve()
        else:
            self.output_dir = self.base_dir / "03_Extracted_Data" / "Decompressed_Files"
        
        self.stats = {
            'files_processed': 0,
            'files_extracted': 0,
            'files_failed': 0,
            'checksum_errors': 0,
            'checksum_warnings': 0,
            'total_size_in': 0,
            'total_size_out': 0
        }
        
        # Track extraction issues for reporting
        self.extraction_log = []

    def verify_checksum(self, data, expected_crc32, filename):
        """Verify CRC32 checksum of extracted data"""
        try:
            calculated_crc = zlib.crc32(data) & 0xffffffff
            if calculated_crc != expected_crc32:
                error_msg = f"Checksum mismatch for {filename}: expected {expected_crc32:08x}, got {calculated_crc:08x}"
                self.log(f"⚠️ {error_msg}", "WARNING")
                self.extraction_log.append(f"CHECKSUM_ERROR: {error_msg}")
                self.stats['checksum_errors'] += 1
                return False
            return True
        except Exception as e:
            warning_msg = f"Checksum verification failed for {filename}: {e}"
            self.log(f"⚠️ {warning_msg}", "WARNING")
            self.extraction_log.append(f"CHECKSUM_WARNING: {warning_msg}")
            self.stats['checksum_warnings'] += 1
            return False

    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of extracted file for verification"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def log(self, message, level="INFO"):
        """Enhanced logging with levels"""
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROGRESS": "🔄", "CHECKSUM": "🔐"}
        print(f"{symbols.get(level, 'ℹ️')} {message}")

    def parse_ole_compound_document(self, data):
        """Parse OLE compound document and extract CasewareDocument stream"""
        try:
            if len(data) < 512 or data[0:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                return None
                
            self.log("OLE compound document detected")
            
            # Get sector size
            sector_shift = struct.unpack('<H', data[30:32])[0]
            sector_size = 1 << sector_shift
            self.log(f"Sector size: {sector_size} bytes")
            
            # Get directory first sector
            dir_first_sector = struct.unpack('<I', data[48:52])[0]
            dir_offset = 512 + (dir_first_sector * sector_size)
            
            # Search for CasewareDocument stream
            entries_per_sector = sector_size // 128
            max_sectors = 10
            
            for sector in range(max_sectors):
                current_dir_offset = dir_offset + (sector * sector_size)
                
                if current_dir_offset + sector_size > len(data):
                    break
                
                for entry_idx in range(entries_per_sector):
                    entry_offset = current_dir_offset + (entry_idx * 128)
                    
                    if entry_offset + 128 > len(data):
                        continue
                    
                    entry_data = data[entry_offset:entry_offset + 128]
                    
                    # Parse directory entry
                    try:
                        name_bytes = entry_data[0:64]
                        null_pos = name_bytes.find(b'\x00\x00')
                        if null_pos > 0 and null_pos % 2 == 0:
                            name = name_bytes[:null_pos].decode('utf-16le')
                        else:
                            name = name_bytes.decode('utf-16le').rstrip('\x00')
                        
                        entry_type = entry_data[66]
                        start_sector = struct.unpack('<I', entry_data[116:120])[0]
                        stream_size = struct.unpack('<Q', entry_data[120:128])[0]
                        
                        if name.lower() == 'casewaredocument' and entry_type == 2:
                            self.log(f"Found CasewareDocument stream: {stream_size} bytes", "SUCCESS")
                            
                            # Extract stream data
                            stream_offset = 512 + (start_sector * sector_size)
                            if stream_offset + stream_size <= len(data):
                                return data[stream_offset:stream_offset + stream_size]
                    except:
                        continue
            
            return None
            
        except Exception as e:
            self.log(f"OLE parsing error: {e}", "ERROR")
            return None

    def decompress_caseware_file(self, data):
        """Decompress CaseWare LZMA2 compressed data"""
        try:
            # Check for CaseWare header pattern
            if data.startswith(b'\x0c\x00\x00\x00'):
                # Standard CaseWare header: 12 bytes
                payload = data[12:]
                self.log(f"CaseWare LZMA2 header found, payload: {len(payload)} bytes")
            else:
                # Direct LZMA2 data
                payload = data
                self.log(f"Direct LZMA2 data: {len(payload)} bytes")
            
            # Try LZMA2 decompression
            result = lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=[
                {"id": lzma.FILTER_LZMA2, "preset": 0}
            ])
            
            self.log(f"LZMA2 decompression successful: {len(payload)} → {len(result)} bytes", "SUCCESS")
            return result
            
        except Exception as e:
            self.log(f"LZMA2 decompression failed: {e}", "WARNING")
            return data  # Return original if decompression fails

    def extract_zip_archive(self, data, output_path):
        """Extract ZIP archive from decompressed data"""
        try:
            # Find ZIP signature
            zip_offset = 0
            if not data.startswith(b'PK\x03\x04'):
                zip_offset = data.find(b'PK\x03\x04')
                if zip_offset == -1:
                    self.log("No ZIP signature found", "WARNING")
                    return False
                self.log(f"ZIP signature found at offset {zip_offset}")
            
            zip_data = data[zip_offset:]
            
            # Save ZIP data to temporary file
            temp_zip = output_path.parent / f"temp_{output_path.name}.zip"
            with open(temp_zip, 'wb') as f:
                f.write(zip_data)
            
            # Extract ZIP
            try:
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(output_path)
                    file_count = len(zip_ref.namelist())
                    self.log(f"Extracted {file_count} files from ZIP archive", "SUCCESS")
                
                # Clean up temp file
                temp_zip.unlink()
                return True
                
            except zipfile.BadZipFile:
                self.log("Invalid ZIP file format", "ERROR")
                temp_zip.unlink()
                return False
                
        except Exception as e:
            self.log(f"ZIP extraction error: {e}", "ERROR")
            return False

    def extract_damaged_zip(self, data, output_path):
        """Extract files from potentially damaged ZIP using manual parsing"""
        try:
            extracted_count = 0
            offset = 0
            
            while offset < len(data) - 30:
                # Look for local file header signature
                if data[offset:offset+4] != b'\x50\x4B\x03\x04':
                    offset += 1
                    continue
                
                try:
                    # Parse ZIP local file header
                    header = struct.unpack('<4sBB4H3I2H', data[offset:offset+30])
                    signature, ver_needed, ver_made, flags, method, time, date, crc32, comp_size, uncomp_size, name_len, extra_len = header
                    
                    # Basic validation
                    if name_len > 1000 or extra_len > 50000:
                        offset += 4
                        continue
                    
                    # Extract filename
                    name_start = offset + 30
                    name_end = name_start + name_len
                    if name_end > len(data):
                        break
                    
                    filename = data[name_start:name_end].decode('utf-8', errors='replace')
                    
                    # Extract file data
                    data_start = name_end + extra_len
                    data_end = data_start + comp_size
                    
                    if data_end > len(data):
                        break
                    
                    file_data = data[data_start:data_end]
                    
                    # Decompress if needed
                    if method == 8:  # Deflate
                        try:
                            file_data = zlib.decompress(file_data, -15)
                        except:
                            pass
                    elif method == 14:  # LZMA2 (CaseWare custom)
                        file_data = self.decompress_caseware_file(file_data)
                    
                    # Verify checksum if we have expected CRC32
                    checksum_valid = True
                    if crc32 != 0 and len(file_data) > 0:
                        checksum_valid = self.verify_checksum(file_data, crc32, filename)
                        if not checksum_valid:
                            # Still extract the file but log the checksum error
                            self.extraction_log.append(f"EXTRACTED_WITH_CHECKSUM_ERROR: {filename}")
                    
                    # Save file
                    file_path = output_path / filename.replace('\\', os.sep)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Calculate and log file hash for verification
                    file_hash = self.calculate_file_hash(file_path)
                    checksum_status = "✅" if checksum_valid else "⚠️"
                    hash_info = f" [MD5: {file_hash[:8]}...]" if file_hash else ""
                    
                    extracted_count += 1
                    self.log(f"{checksum_status} Extracted: {filename} ({len(file_data)} bytes){hash_info}")
                    
                    offset = data_end
                    
                except Exception as e:
                    offset += 4
                    continue
            
            if extracted_count > 0:
                self.log(f"Manual ZIP extraction completed: {extracted_count} files", "SUCCESS")
                return True
            else:
                self.log("No files extracted via manual parsing", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Manual ZIP extraction error: {e}", "ERROR")
            return False

    def process_file(self, file_path):
        """Process a single .ac_ file with all recovery methods"""
        self.log(f"\n🎯 Processing: {file_path.name}", "PROGRESS")
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            self.stats['files_processed'] += 1
            self.stats['total_size_in'] += len(data)
            
            # Create output directory
            output_path = self.output_dir / file_path.stem
            output_path.mkdir(parents=True, exist_ok=True)
            
            success = False
            
            # Method 1: Parse as OLE compound document
            self.log("Method 1: OLE compound document parsing")
            ole_stream = self.parse_ole_compound_document(data)
            
            if ole_stream:
                # Decompress the stream
                decompressed = self.decompress_caseware_file(ole_stream)
                
                # Try to extract as ZIP
                if self.extract_zip_archive(decompressed, output_path):
                    success = True
                elif self.extract_damaged_zip(decompressed, output_path):
                    success = True
            
            # Method 2: Direct ZIP extraction (if OLE method failed)
            if not success:
                self.log("Method 2: Direct ZIP extraction")
                if self.extract_damaged_zip(data, output_path):
                    success = True
            
            # Method 3: Search for embedded ZIP signatures
            if not success:
                self.log("Method 3: ZIP signature search")
                zip_found = False
                offset = 0
                while offset < len(data):
                    zip_pos = data.find(b'PK\x03\x04', offset)
                    if zip_pos == -1:
                        break
                    
                    # Try extracting from this position
                    remaining_data = data[zip_pos:]
                    if self.extract_damaged_zip(remaining_data, output_path):
                        zip_found = True
                        break
                    
                    offset = zip_pos + 1
                
                if zip_found:
                    success = True
            
            # Update statistics
            if success:
                self.stats['files_extracted'] += 1
                # Calculate output size
                total_out = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
                self.stats['total_size_out'] += total_out
                self.log(f"✅ Successfully processed {file_path.name}", "SUCCESS")
            else:
                self.stats['files_failed'] += 1
                self.log(f"❌ Failed to extract files from {file_path.name}", "ERROR")
            
            # Write extraction log if there were any issues
            if self.extraction_log:
                log_file = output_path / f"{file_path.stem}_extraction_log.txt"
                with open(log_file, 'w') as f:
                    f.write(f"Extraction Log for: {file_path.name}\n")
                    f.write(f"Processed: {file_path}\n")
                    f.write(f"Output: {output_path}\n")
                    f.write("=" * 50 + "\n\n")
                    for entry in self.extraction_log:
                        f.write(f"{entry}\n")
                    f.write(f"\nSummary:\n")
                    f.write(f"Checksum Errors: {self.stats['checksum_errors']}\n")
                    f.write(f"Checksum Warnings: {self.stats['checksum_warnings']}\n")
                self.log(f"📝 Extraction log written: {log_file}", "INFO")
                # Clear log for next file
                self.extraction_log = []
            
            return success
            
        except Exception as e:
            self.log(f"Processing error for {file_path.name}: {e}", "ERROR")
            self.stats['files_failed'] += 1
            return False

    def get_files_to_process(self):
        """Get list of files to process based on input path"""
        files_to_process = []
        
        if self.input_path.is_file():
            # Single file
            if self.input_path.suffix.lower() in ['.ac_', '.ac', '.bin']:
                files_to_process.append(self.input_path)
            else:
                self.log(f"Unsupported file type: {self.input_path.suffix}", "WARNING")
        elif self.input_path.is_dir():
            # Directory - perform recursive search for all supported files
            self.log(f"🔍 Performing recursive search in: {self.input_path}", "PROGRESS")
            patterns = ["*.ac_", "*.ac", "*.bin"]
            for pattern in patterns:
                # Use rglob for recursive search instead of glob
                found_files = list(self.input_path.rglob(pattern))
                if found_files:
                    self.log(f"Found {len(found_files)} {pattern} file(s)", "INFO")
                    files_to_process.extend(found_files)
                    # Show the found files for user awareness
                    for file_path in found_files:
                        relative_path = file_path.relative_to(self.input_path)
                        self.log(f"  📁 {relative_path}", "INFO")
            
            if not files_to_process:
                self.log(f"No supported files found in directory tree", "INFO")
        else:
            self.log(f"Input path does not exist: {self.input_path}", "ERROR")
        
        return files_to_process

    def run(self):
        """Main execution function"""
        self.log("🚀 CaseWare Universal File Recovery Tool", "PROGRESS")
        self.log("=" * 50)
        
        # Show input/output paths
        self.log(f"Input: {self.input_path}")
        self.log(f"Output: {self.output_dir}")
        
        # Find files to process
        files_to_process = self.get_files_to_process()
        
        if not files_to_process:
            self.log(f"No supported files found in {self.input_path}", "ERROR")
            self.log("Supported formats: .ac_, .ac, .bin", "INFO")
            return
        
        self.log(f"Found {len(files_to_process)} file(s) to process")
        
        # Process each file
        for file_path in files_to_process:
            self.process_file(file_path)
        
        # Print final statistics
        self.log("\n📊 PROCESSING COMPLETE", "SUCCESS")
        self.log("=" * 50)
        self.log(f"Files processed: {self.stats['files_processed']}")
        self.log(f"Files extracted: {self.stats['files_extracted']}")
        self.log(f"Files failed: {self.stats['files_failed']}")
        
        if self.stats['checksum_errors'] > 0 or self.stats['checksum_warnings'] > 0:
            self.log(f"🔐 Checksum errors: {self.stats['checksum_errors']}", "WARNING")
            self.log(f"🔐 Checksum warnings: {self.stats['checksum_warnings']}", "WARNING")
        
        if self.stats['files_processed'] > 0:
            success_rate = (self.stats['files_extracted'] / self.stats['files_processed']) * 100
            self.log(f"Success rate: {success_rate:.1f}%")
        
        if self.stats['total_size_in'] > 0:
            self.log(f"Total input: {self.stats['total_size_in']:,} bytes")
            self.log(f"Total output: {self.stats['total_size_out']:,} bytes")
        
        self.log(f"Results saved to: {self.output_dir}", "SUCCESS")
        
        if self.stats['checksum_errors'] > 0:
            self.log("⚠️ Some files have checksum errors - check extraction logs for details", "WARNING")

def create_argument_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="CaseWare Universal File Recovery Tool - Extract files from CaseWare archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Process all .ac_ files in default source directory:
    python caseware_universal_extractor.py

  Process a specific file:
    python caseware_universal_extractor.py "Friedlander.ac_"

  Process a file with custom output directory:
    python caseware_universal_extractor.py "input.ac_" "output_folder"

  Process all files in a directory:
    python caseware_universal_extractor.py -i "input_folder" -o "output_folder"

  Process a raw binary stream:
    python caseware_universal_extractor.py "stream.bin" "extracted_files"

Supported file formats:
  .ac_  - CaseWare archive files
  .ac   - CaseWare data files
  .bin  - Raw binary streams (from stream extractor)
        """
    )
    
    parser.add_argument(
        'input', 
        nargs='?', 
        help='Input file or directory path (default: ../01_Source_Files/)'
    )
    
    parser.add_argument(
        'output', 
        nargs='?', 
        help='Output directory path (default: ../03_Extracted_Data/Decompressed_Files/)'
    )
    
    parser.add_argument(
        '-i', '--input-dir',
        help='Input directory containing files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for extracted files'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='CaseWare Universal Extractor v2.2 - Now with recursive directory scanning'
    )
    
    return parser

def main():
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Determine input and output paths
    input_path = None
    output_path = None
    
    if args.input_dir:
        input_path = args.input_dir
    elif args.input:
        input_path = args.input
    
    if args.output_dir:
        output_path = args.output_dir
    elif args.output:
        output_path = args.output
    
    # Create and run extractor
    try:
        extractor = CaseWareExtractor(input_path, output_path)
        extractor.run()
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
