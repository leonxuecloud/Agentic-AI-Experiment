#!/usr/bin/env python3
"""
CaseWare Document Stream Extractor
Specialized tool for extracting complete CasewareDocument streams as .bin files

Features:
- OLE compound document parsing with robust error handling
- Complete stream extraction (not individual files)
- Multiple extraction strategies for corrupted files
- Stream validation and analysis
- Professional logging and progress reporting

Usage: python caseware_stream_extractor.py
Processes all .ac_ files in ../01_Source_Files/ and outputs .bin files to ../03_Extracted_Data/Raw_Streams/
"""

import struct
import os
from pathlib import Path

class CaseWareStreamExtractor:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.source_dir = self.base_dir / "01_Source_Files"
        self.output_dir = self.base_dir / "03_Extracted_Data" / "Raw_Streams"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'files_processed': 0,
            'streams_extracted': 0,
            'streams_failed': 0,
            'total_stream_size': 0
        }

    def log(self, message, level="INFO"):
        """Enhanced logging with levels"""
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROGRESS": "🔄"}
        print(f"{symbols.get(level, 'ℹ️')} {message}")

    def parse_ole_directory_entry(self, entry_data):
        """Parse a single OLE directory entry"""
        try:
            # Parse name (UTF-16LE, up to 64 bytes)
            name_bytes = entry_data[0:64]
            null_pos = name_bytes.find(b'\x00\x00')
            if null_pos > 0 and null_pos % 2 == 0:
                name = name_bytes[:null_pos].decode('utf-16le')
            else:
                name = name_bytes.decode('utf-16le').rstrip('\x00')
            
            # Parse other fields
            name_len = struct.unpack('<H', entry_data[64:66])[0]
            entry_type = entry_data[66]  # 0=empty, 1=storage, 2=stream, 5=root
            start_sector = struct.unpack('<I', entry_data[116:120])[0]
            stream_size = struct.unpack('<Q', entry_data[120:128])[0]
            
            return {
                'name': name,
                'name_len': name_len,
                'type': entry_type,
                'start_sector': start_sector,
                'stream_size': stream_size
            }
        except Exception:
            return None

    def read_fat_chain(self, ole_data, start_sector, sector_size, fat_sectors):
        """Read a chain of sectors following the FAT"""
        sectors = []
        current_sector = start_sector
        
        # Build FAT table
        fat_table = []
        for fat_sector in fat_sectors:
            if fat_sector == 0xFFFFFFFE:  # FREESECT
                continue
            fat_offset = 512 + (fat_sector * sector_size)
            if fat_offset + sector_size <= len(ole_data):
                fat_data = ole_data[fat_offset:fat_offset + sector_size]
                entries_per_sector = sector_size // 4
                for i in range(entries_per_sector):
                    entry = struct.unpack('<I', fat_data[i*4:(i+1)*4])[0]
                    fat_table.append(entry)
        
        # Follow the chain
        visited = set()
        while current_sector != 0xFFFFFFFE and current_sector < len(fat_table):
            if current_sector in visited:
                break
            visited.add(current_sector)
            sectors.append(current_sector)
            current_sector = fat_table[current_sector]
            if current_sector == 0xFFFFFFFF:  # ENDOFCHAIN
                break
        
        return sectors

    def extract_stream_data(self, ole_data, start_sector, stream_size, sector_size, fat_sectors):
        """Extract complete stream data following sector chains"""
        if stream_size == 0:
            return b''
        
        # Get sector chain
        sectors = self.read_fat_chain(ole_data, start_sector, sector_size, fat_sectors)
        
        if not sectors:
            return b''
        
        # Read all sectors in the chain
        stream_data = b''
        for sector_num in sectors:
            sector_offset = 512 + (sector_num * sector_size)
            if sector_offset + sector_size <= len(ole_data):
                sector_data = ole_data[sector_offset:sector_offset + sector_size]
                stream_data += sector_data
        
        # Trim to actual stream size
        if len(stream_data) > stream_size:
            stream_data = stream_data[:stream_size]
        
        return stream_data

    def extract_caseware_document_stream_robust(self, ole_data):
        """Robust CasewareDocument stream extraction with multiple strategies"""
        
        # Strategy 1: Standard OLE parsing
        try:
            if len(ole_data) < 512 or ole_data[0:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                return None
            
            self.log("Valid OLE compound document detected")
            
            # Parse OLE header
            sector_shift = struct.unpack('<H', ole_data[30:32])[0]  
            sector_size = 1 << sector_shift
            self.log(f"Sector size: {sector_size} bytes")
            
            # Get FAT information
            fat_sectors_count = struct.unpack('<I', ole_data[44:48])[0]
            dir_first_sector = struct.unpack('<I', ole_data[48:52])[0]
            
            self.log(f"Directory first sector: {dir_first_sector}")
            self.log(f"FAT sectors count: {fat_sectors_count}")
            
            # Read FAT sector locations from header (first 109 entries)
            fat_sectors = []
            for i in range(109):
                fat_sector = struct.unpack('<I', ole_data[76 + i*4:80 + i*4])[0]
                if fat_sector != 0xFFFFFFFE:  # Not FREESECT
                    fat_sectors.append(fat_sector)
            
            # Search for CasewareDocument in directory
            self.log("Searching for CasewareDocument stream...")
            
            dir_offset = 512 + (dir_first_sector * sector_size)
            entries_per_sector = sector_size // 128
            sectors_to_check = min(10, (len(ole_data) - dir_offset) // sector_size)
            
            for sector in range(sectors_to_check):
                current_dir_offset = dir_offset + (sector * sector_size)
                
                for entry_idx in range(entries_per_sector):
                    entry_offset = current_dir_offset + (entry_idx * 128)
                    
                    if entry_offset + 128 > len(ole_data):
                        continue
                    
                    entry_data = ole_data[entry_offset:entry_offset + 128]
                    entry = self.parse_ole_directory_entry(entry_data)
                    
                    if entry and entry['name'] and len(entry['name'].strip()) >= 2:
                        self.log(f"Found entry: '{entry['name']}' (type: {entry['type']}, size: {entry['stream_size']})")
                        
                        if entry['name'].lower() == 'casewaredocument' and entry['type'] == 2:
                            self.log("⭐ Found CasewareDocument stream!", "SUCCESS")
                            
                            # Extract the stream
                            stream_data = self.extract_stream_data(
                                ole_data, 
                                entry['start_sector'], 
                                entry['stream_size'], 
                                sector_size, 
                                fat_sectors
                            )
                            
                            if stream_data:
                                self.log(f"Successfully extracted {len(stream_data):,} bytes", "SUCCESS")
                                return stream_data
            
            self.log("CasewareDocument stream not found in directory", "WARNING")
            
        except Exception as e:
            self.log(f"Standard OLE parsing failed: {e}", "WARNING")
        
        # Strategy 2: Brute-force search for CasewareDocument string
        self.log("Attempting brute-force CasewareDocument search...")
        
        try:
            # Look for CasewareDocument string patterns
            search_patterns = [
                b"CasewareDocument",
                "CasewareDocument".encode('utf-16le'),
                "CaseWareDocument".encode('utf-8'),
                "CaseWareDocument".encode('utf-16le')
            ]
            
            for pattern in search_patterns:
                pos = ole_data.find(pattern)
                if pos != -1:
                    self.log(f"Found pattern at offset {pos}")
                    
                    # Search for ZIP signature in nearby areas
                    search_start = max(0, pos - 50000)
                    search_end = min(len(ole_data), pos + 50000)
                    
                    zip_pos = ole_data.find(b'PK\x03\x04', search_start)
                    if zip_pos != -1 and zip_pos < search_end:
                        # Extract from ZIP position to end or reasonable size
                        max_size = min(10 * 1024 * 1024, len(ole_data) - zip_pos)
                        stream_data = ole_data[zip_pos:zip_pos + max_size]
                        self.log(f"Extracted {len(stream_data):,} bytes via brute-force method", "SUCCESS")
                        return stream_data
        
        except Exception as e:
            self.log(f"Brute-force search failed: {e}", "WARNING")
        
        # Strategy 3: Look for the largest contiguous data block
        self.log("Attempting largest data block extraction...")
        
        try:
            # Find the largest ZIP signature and extract
            zip_positions = []
            offset = 0
            while True:
                pos = ole_data.find(b'PK\x03\x04', offset)
                if pos == -1:
                    break
                zip_positions.append(pos)
                offset = pos + 1
            
            if zip_positions:
                # Use the first significant ZIP position
                zip_pos = zip_positions[0]
                for pos in zip_positions:
                    if pos > 1000:  # Skip header area
                        zip_pos = pos
                        break
                
                # Extract reasonable amount of data
                max_size = min(20 * 1024 * 1024, len(ole_data) - zip_pos)
                stream_data = ole_data[zip_pos:zip_pos + max_size]
                self.log(f"Extracted {len(stream_data):,} bytes via largest block method", "SUCCESS")
                return stream_data
        
        except Exception as e:
            self.log(f"Largest block extraction failed: {e}", "WARNING")
        
        return None

    def analyze_stream_content(self, stream_data):
        """Analyze extracted stream content"""
        analysis = {
            'size': len(stream_data),
            'has_zip_signature': b'PK\x03\x04' in stream_data[:1000],
            'zip_offset': -1,
            'first_32_bytes': stream_data[:32].hex() if len(stream_data) >= 32 else stream_data.hex()
        }
        
        # Find ZIP signature position
        zip_pos = stream_data.find(b'PK\x03\x04')
        if zip_pos != -1:
            analysis['zip_offset'] = zip_pos
        
        return analysis

    def extract_stream_from_file(self, file_path):
        """Extract CasewareDocument stream from a single .ac_ file"""
        self.log(f"\n🎯 Processing: {file_path.name}", "PROGRESS")
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                ole_data = f.read()
            
            self.stats['files_processed'] += 1
            
            # Extract stream
            stream_data = self.extract_caseware_document_stream_robust(ole_data)
            
            if not stream_data:
                self.log(f"Failed to extract stream from {file_path.name}", "ERROR")
                self.stats['streams_failed'] += 1
                return False
            
            # Analyze stream
            analysis = self.analyze_stream_content(stream_data)
            
            # Generate output filename
            output_filename = f"CasewareDocument_{file_path.stem}.bin"
            output_path = self.output_dir / output_filename
            
            # Save stream
            with open(output_path, 'wb') as f:
                f.write(stream_data)
            
            self.log(f"💾 Saved stream to: {output_filename}", "SUCCESS")
            self.log(f"📊 Stream size: {analysis['size']:,} bytes")
            
            if analysis['has_zip_signature']:
                if analysis['zip_offset'] == 0:
                    self.log("✅ Stream starts with ZIP signature", "SUCCESS")
                else:
                    self.log(f"✅ ZIP signature found at offset {analysis['zip_offset']}", "SUCCESS")
            else:
                self.log("ℹ️ No ZIP signature found in first 1000 bytes", "INFO")
            
            self.log(f"🔍 First 32 bytes: {analysis['first_32_bytes']}")
            
            self.stats['streams_extracted'] += 1
            self.stats['total_stream_size'] += analysis['size']
            
            return True
            
        except Exception as e:
            self.log(f"Error processing {file_path.name}: {e}", "ERROR")
            self.stats['streams_failed'] += 1
            return False

    def run(self):
        """Main execution function"""
        self.log("🎯 CaseWare Document Stream Extractor", "PROGRESS")
        self.log("=" * 50)
        self.log("Extracts complete CasewareDocument streams as .bin files")
        self.log("")
        
        # Find .ac_ files
        ac_files = list(self.source_dir.glob("*.ac_"))
        
        if not ac_files:
            self.log(f"No .ac_ files found in {self.source_dir}", "ERROR")
            return
        
        self.log(f"📂 Found {len(ac_files)} .ac_ file(s):")
        for i, f in enumerate(ac_files, 1):
            self.log(f"   {i}. {f.name}")
        
        self.log("")
        
        # Process each file
        for ac_file in ac_files:
            self.extract_stream_from_file(ac_file)
        
        # Print final statistics
        self.log("\n🎉 PROCESSING COMPLETED!", "SUCCESS")
        self.log("=" * 50)
        self.log(f"Files processed: {self.stats['files_processed']}")
        self.log(f"Streams extracted: {self.stats['streams_extracted']}")
        self.log(f"Streams failed: {self.stats['streams_failed']}")
        
        if self.stats['files_processed'] > 0:
            success_rate = (self.stats['streams_extracted'] / self.stats['files_processed']) * 100
            self.log(f"Success rate: {success_rate:.1f}%")
        
        if self.stats['total_stream_size'] > 0:
            self.log(f"Total stream data: {self.stats['total_stream_size']:,} bytes")
        
        if self.stats['streams_extracted'] > 0:
            self.log(f"\n💡 Next steps:")
            self.log(f"   • Process .bin files with CaseWare decompression tools")
            self.log(f"   • Use compound document analyzers to examine structure")
            self.log(f"   • Import into hex editors for detailed analysis")
            
        self.log(f"\n📁 Results saved to: {self.output_dir}", "SUCCESS")

def main():
    extractor = CaseWareStreamExtractor()
    extractor.run()

if __name__ == "__main__":
    main()
