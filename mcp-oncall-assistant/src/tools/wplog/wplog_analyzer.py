#!/usr/bin/env python3
"""
WPLog Analyzer - Improved Version
==================================

Comprehensive analyzer for CaseWare Working Papers log files.
Handles multiple log formats and provides detailed analysis.
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import sys


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    line_number: int
    thread_id: str
    component: str
    message: str
    raw_line: str
    log_type: str = "wplog"  # wplog, userlog, storelog
    user: str = ""  # For userlog format
    process: str = ""  # For userlog format (just the process name, e.g., 'cwin64')
    pid: str = ""  # For userlog format (just the PID, e.g., '18232')
    server: str = ""  # For userlog format


@dataclass
class TimeGap:
    """Represents a time gap between log entries."""
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    start_line: int
    end_line: int
    start_message: str
    end_message: str


@dataclass
class ErrorEntry:
    """Represents an error found in the log."""
    timestamp: datetime
    line_number: int
    error_type: str
    message: str
    thread_id: str
    component: str


class WPLogAnalyzer:
    """Enhanced analyzer for multiple CaseWare log formats."""
    
    def __init__(self, verbose: bool = False):
        self.log_entries: List[LogEntry] = []
        self.time_gaps: List[TimeGap] = []
        self.errors: List[ErrorEntry] = []
        self.verbose = verbose
        self._min_gap_seconds = 5.0
        
        # Enhanced regex patterns for different log formats
        self.log_patterns = {
            # wplog.txt format: (Wed Sep 10 17:30:15 2025) MNP01TS23:admin.ed.turnbull cwin64:18232 [Component]: Message
            # Generic process pattern handles: cwin64, EXCEL, WORD, TWAINProxy32, cvwin64, etc.
            # Also handles optional line numbers at the beginning: 5039712   (Thu Sep 11 17:37:24 2025) MNP01TS23:Ed.Turnbull cwin64:7344 [firmstore   ]: Message
            'wplog': re.compile(r'^(?:\d+\s+)?\(([^)]+)\)\s+([^:]+):([^\s]+)\s+([A-Za-z][A-Za-z0-9]*):(\d+)\s+\[([^\]]+)\]:\s*(.*)$'),
            
            # userlog/storelog format: MNP01TS23 admin.ed.turnbu cwin64:17944 component 17:03:51 Message
            # Also generic process pattern for userlog format
            'other': re.compile(r'^([^\s]+)\s+([^\s]+)\s+([A-Za-z][A-Za-z0-9]*):(\d+)\s+([^\s]+)\s+(\d{2}:\d{2}:\d{2})\s+(.*)$')
        }
        
        # Error detection patterns based on our analysis
        self.error_patterns = {
            'winhttp_header': re.compile(r'(WinHttp Error|error query1)\s*:?\s*(\d+)', re.IGNORECASE),
            'http_error': re.compile(r'HTTP.*(?:Error|status)\s*:?\s*(\d+)', re.IGNORECASE),
            'ssl_error': re.compile(r'SSL.*(?:Certificate|Error)', re.IGNORECASE),
            'timeout': re.compile(r'(?:timeout|time.*out)', re.IGNORECASE),
            'autoclose': re.compile(r'AutoClose.*(?:error|failed|hang)', re.IGNORECASE),
            'database': re.compile(r'(?:database|DBF).*(?:error|failed)', re.IGNORECASE),
            'template_search': re.compile(r'Failed to find group for.*Templates', re.IGNORECASE),
            'connection_error': re.compile(r'connection.*(?:error|failed|lost)', re.IGNORECASE),
            'winhttp_error': re.compile(r'winhttp.*(?:error|failed)', re.IGNORECASE),
            'certificate_error': re.compile(r'certificate.*(?:error|failed|invalid)', re.IGNORECASE),
            'general_error': re.compile(r'(?:error|failed|exception)', re.IGNORECASE)
        }
    
    def load_log_file(self, log_file_path: str) -> None:
        """Load and parse a log file."""
        self.log_file_path = Path(log_file_path)
        
        if not self.log_file_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_file_path}")
        
        if self.verbose:
            print(f"📖 Loading log file: {self.log_file_path.name}")
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            raise RuntimeError(f"Error reading file: {e}")
        
        if self.verbose:
            print(f"📊 Processing {len(lines):,} lines...")
        
        # Clear previous data
        self.log_entries.clear()
        self.time_gaps.clear()
        self.errors.clear()
        
        # Parse each line
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            entry = self._parse_log_entry(line, line_num)
            if entry:
                self.log_entries.append(entry)
                
        if self.verbose:
            print(f"✅ Parsed {len(self.log_entries):,} valid log entries")
    
    def _parse_log_entry(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log entry with multiple format support."""
        
        # Clean up malformed lines that start with quoted words like "desc", "end", "entity" 
        # Example: "desc" :(...)(Thu Sep 11 17:37:32 2025) MNP01TS23:admin.ed.turnbull cwin64:12608 [sync]: Message
        cleaned_line = line.strip()
        if cleaned_line.startswith('"') and '" ' in cleaned_line:
            # Remove the quoted prefix
            quote_end = cleaned_line.find('" ')
            if quote_end > 0:
                cleaned_line = cleaned_line[quote_end + 2:].strip()
                # Remove any remaining colon at the start
                if cleaned_line.startswith(':'):
                    cleaned_line = cleaned_line[1:].strip()
        
        # Try wplog format FIRST (more specific pattern with parentheses around timestamp)
        match = self.log_patterns['wplog'].match(cleaned_line)
        if match:
            timestamp_str, server, user, process_type, process_id, component, message = match.groups()
            thread_id = f"{process_type}:{process_id}"  # Combine process type and ID
            log_type = "wplog"
        else:
            # Try userlog format: MNP01TS23       admin.ed.turnbu cwin64:20052    cwuser          00:37:26   Logging initialized.
            userlog_pattern = r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d{2}:\d{2}:\d{2})\s+(.+)$'
            userlog_match = re.match(userlog_pattern, cleaned_line)
            if userlog_match:
                server, user, process_pid, component, time_str, message = userlog_match.groups()
                # Parse process and pid from "process:pid" format
                if ':' in process_pid:
                    process, pid = process_pid.split(':', 1)
                else:
                    process = process_pid
                    pid = ""
                
                # Use today's date for time-only format
                today = datetime.now().date()
                try:
                    time_part = datetime.strptime(time_str, '%H:%M:%S').time()
                    timestamp = datetime.combine(today, time_part)
                    
                    # Validate userlog process names too
                    valid_apps = {'cwin64', 'EXCEL', 'WORD', 'TWAINProxy32', 'cvwin64', 'OUTLOOK', 'WINWORD', 'POWERPNT'}
                    is_valid_app = (process in valid_apps or 
                                  (len(process) > 4 and (any(c.isdigit() for c in process) or process.isupper())))
                    
                    if not is_valid_app:
                        if self.verbose:
                            print(f"⚠️  Skipped userlog entry with invalid application name '{process}' at line {line_number}")
                        return None
                    
                    return LogEntry(
                        timestamp=timestamp,
                        line_number=line_number,
                        thread_id=process_pid,  # Keep full process:pid as thread_id
                        component=component.strip(),
                        message=message.strip(),
                        raw_line=line,
                        log_type="userlog",
                        user=user,
                        process=process,  # Just the process name
                        pid=pid,         # Just the PID
                        server=server
                    )
                except ValueError:
                    pass
            
            # Try other formats (storelog/userlog alternative patterns)
            match = self.log_patterns['other'].match(line)
            if match:
                server, user, process_type, process_id, component, time_str, message = match.groups()
                thread_id = f"{process_type}:{process_id}"  # Combine process type and ID
                # Construct full timestamp (assuming current date)
                current_date = datetime.now().strftime('%a %b %d')
                timestamp_str = f"{current_date} {time_str} 2025"
                log_type = "other"
            else:
                # If no pattern matches, skip this line
                if self.verbose and "error" in line.lower():
                    print(f"⚠️  Skipped unparseable line {line_number}: {line[:80]}...")
                return None
        
        # Parse timestamp for wplog/other formats
        try:
            # Handle different timestamp formats
            if "Wed Sep 10" in timestamp_str:
                timestamp = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
            else:
                # Try alternate formats
                for fmt in ['%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%a %b %d %H:%M:%S %Y']:
                    try:
                        if fmt == '%H:%M:%S':
                            # Use today's date for time-only format
                            today = datetime.now().date()
                            time_part = datetime.strptime(timestamp_str, fmt).time()
                            timestamp = datetime.combine(today, time_part)
                        else:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    if self.verbose:
                        print(f"⚠️  Invalid timestamp format at line {line_number}: {timestamp_str}")
                    return None
        except ValueError as e:
            if self.verbose:
                print(f"⚠️  Failed to parse timestamp at line {line_number}: {timestamp_str} - {e}")
            return None
        
        # Validate that we have reasonable process/application names for wplog entries
        if log_type == "wplog":
            # Valid applications: known CaseWare and Windows applications
            valid_apps = {'cwin64', 'EXCEL', 'WORD', 'TWAINProxy32', 'cvwin64', 'OUTLOOK', 'WINWORD', 'POWERPNT'}
            # Also allow applications that look like proper Windows executables (contain numbers or are all caps, length > 4)
            is_valid_app = (process_type in valid_apps or 
                          (len(process_type) > 4 and (any(c.isdigit() for c in process_type) or process_type.isupper())))
            
            if not is_valid_app:
                if self.verbose:
                    print(f"⚠️  Skipped entry with invalid application name '{process_type}' at line {line_number}")
                return None
        
        return LogEntry(
            timestamp=timestamp,
            line_number=line_number,
            thread_id=thread_id,
            component=component.strip(),
            message=message.strip(),
            raw_line=line,
            log_type=log_type,
            user=user,  # Just the username part: "Ed.Turnbull" or "admin.ed.turnbull"
            process=process_type if log_type in ["wplog", "other"] else "",  # Application name like "EXCEL", "cwin64"
            pid=process_id if log_type in ["wplog", "other"] else "",        # Process ID like "19220"
            server=server if log_type == "wplog" else ""
        )
    
    def analyze_time_gaps(self, min_gap_seconds: float = 5.0) -> None:
        """Analyze time gaps between log entries."""
        self._min_gap_seconds = min_gap_seconds
        self.time_gaps.clear()
        
        if len(self.log_entries) < 2:
            return
        
        if self.verbose:
            print(f"⏰ Analyzing time gaps (minimum: {min_gap_seconds}s)")
        
        for i in range(len(self.log_entries) - 1):
            current = self.log_entries[i]
            next_entry = self.log_entries[i + 1]
            
            time_diff = (next_entry.timestamp - current.timestamp).total_seconds()
            
            if time_diff >= min_gap_seconds:
                # Verify user/process consistency for wplog format entries
                skip_gap = False
                if current.log_type == "wplog" and next_entry.log_type == "wplog":
                    # Extract user and process info from both entries
                    current_user = self._extract_user_from_message(current)
                    next_user = self._extract_user_from_message(next_entry)
                    current_process = current.thread_id
                    next_process = next_entry.thread_id
                    
                    # Skip gaps between different users or processes
                    if (current_user and next_user and current_user != next_user) or current_process != next_process:
                        skip_gap = True
                        if self.verbose:
                            print(f"⚠️  Skipping gap between different users/processes: {current_user}:{current_process} → {next_user}:{next_process}")
                
                if not skip_gap:
                    gap = TimeGap(
                        start_time=current.timestamp,
                        end_time=next_entry.timestamp,
                        duration_seconds=time_diff,
                        start_line=current.line_number,
                        end_line=next_entry.line_number,
                        start_message=current.message,
                        end_message=next_entry.message
                    )
                    self.time_gaps.append(gap)
        
        # Sort by duration (largest first)
        self.time_gaps.sort(key=lambda x: x.duration_seconds, reverse=True)
        
        # Filter out maintenance windows (based on corrected analysis from .md files)
        self.time_gaps = self._filter_maintenance_windows(self.time_gaps)
        
        if self.verbose:
            print(f"✅ Found {len(self.time_gaps)} time gaps (after filtering maintenance windows)")
    
    def _extract_user_from_message(self, entry_or_message) -> Optional[str]:
        """Extract user information from wplog message format."""
        # If we get a LogEntry, use the raw_line; if we get a string, use it directly
        if hasattr(entry_or_message, 'raw_line'):
            search_text = entry_or_message.raw_line
        else:
            search_text = entry_or_message
            
        # wplog format: (Thu Sep 11 18:14:51 2025) MNP01TS23:admin.ed.turnbull cwin64:18772 [ConsolidatingOnServer]: ...
        # Extract the user part between "MNP01TS23:" and " cwin64:"
        import re
        match = re.search(r'MNP01TS23:([^\s]+)', search_text)
        if match:
            return match.group(1)
        return None
    
    def _filter_maintenance_windows(self, gaps: List[TimeGap]) -> List[TimeGap]:
        """Filter out maintenance windows from time gaps based on corrected analysis."""
        filtered_gaps = []
        
        for gap in gaps:
            # Check if this looks like a maintenance window based on .md file analysis:
            # 1. Duration ~60 minutes (3500-3700 seconds)
            # 2. Ending with different user context
            # 3. WinHTTP async operations at start (system cleanup)
            # 4. CWinHttpRequest operations (false positives from async processing)
            is_maintenance = False
            
            # Filter out CWinHttpRequest operations (bias correction from .md analysis)
            if "CWinHttpRequest" in gap.start_message or "CWinHttpRequest" in gap.end_message:
                is_maintenance = True
                if self.verbose:
                    print(f"🔧 Filtered out CWinHttpRequest gap: {gap.duration_seconds/60:.1f}min (async operation, not genuine bottleneck)")
            
            # Filter out WINHTTP_CALLBACK_STATUS operations (maintenance windows)
            elif "WINHTTP_CALLBACK_STATUS" in gap.start_message:
                is_maintenance = True
                if self.verbose:
                    print(f"🔧 Filtered out WINHTTP maintenance window: {gap.duration_seconds/60:.1f}min (system maintenance)")
            
            # Check duration (58-62 minute range indicates maintenance window)
            elif 3480 <= gap.duration_seconds <= 3720:  # 58-62 minutes
                # Check for maintenance window patterns
                maintenance_patterns = [
                    "WinHttpRequest::SendRequest",
                    "WinHttpRequest::AsyncCallback", 
                    "async",
                    "background",
                    "system",
                    "CCoreAuthenticationModule::"
                ]
                
                if any(pattern.lower() in gap.start_message.lower() for pattern in maintenance_patterns):
                    is_maintenance = True
                    if self.verbose:
                        print(f"🔧 Filtered out maintenance window: {gap.duration_seconds/60:.1f}min ({gap.start_time.strftime('%H:%M:%S')})")
            
            if not is_maintenance:
                filtered_gaps.append(gap)
        
        return filtered_gaps
    
    def analyze_verified_bottlenecks(self) -> list:
        """
        Analyze bottlenecks ensuring same user/process consistency.
        Only returns operations from identical user+process pairs.
        """
        bottlenecks = []
        
        # Check if we have userlog entries (entries with user/process fields)
        userlog_entries = [entry for entry in self.log_entries if entry.log_type == "userlog" and entry.user and entry.process]
        
        if not userlog_entries:
            if self.verbose:
                print("⚠️  No userlog entries found for verified bottleneck analysis")
            return []
        
        if self.verbose:
            print(f"🔍 Analyzing {len(userlog_entries)} userlog entries for verified bottlenecks")
        
        # Look for bottlenecks starting with "starting syncing"
        sync_starts = {}
        for entry in userlog_entries:
            key = f"{entry.user}|{entry.process}"
            
            # Look for any operation with "starting syncing" - this is the bottleneck start
            if "starting syncing" in entry.message:
                sync_starts[key] = entry
                if self.verbose:
                    print(f"🔍 Found sync start: {entry.user}:{entry.process} - {entry.message}")
            elif key in sync_starts:
                # Look for session-ending operations by the same user/process
                start_entry = sync_starts[key]
                
                # Check if this is a session-ending operation
                session_end_markers = [
                    "UserLogOff", "CWMemMapObject::UserLogOff", "UserUninitialize"
                ]
                
                is_session_end = any(marker in entry.message for marker in session_end_markers)
                
                if is_session_end:
                    duration = (entry.timestamp - start_entry.timestamp).total_seconds() / 60.0
                    
                    if duration > 1:  # Only consider delays > 1 minute as bottlenecks
                        # Determine the operation type from the start message
                        if "SyncSecurityInfo" in start_entry.message:
                            operation_type = "SyncSecurityInfo"
                        elif "CloseMemMapMatchingCode4Dbs" in start_entry.message:
                            operation_type = "CloseMemMapMatchingCode4Dbs"
                        else:
                            # Extract operation name from message
                            operation_type = start_entry.message.split()[0] if start_entry.message else "Unknown"
                        
                        bottlenecks.append({
                            'type': operation_type,
                            'user': entry.user,
                            'process': entry.process,
                            'duration_minutes': duration,
                            'start_time': start_entry.timestamp,
                            'end_time': entry.timestamp,
                            'start_message': start_entry.message,
                            'end_message': entry.message
                        })
                        
                        if self.verbose:
                            print(f"🚨 Bottleneck found: {operation_type} - {duration:.2f}min (from 'starting syncing' to session end)")
                        
                        del sync_starts[key]
        
        return sorted(bottlenecks, key=lambda x: x['duration_minutes'], reverse=True)

    def analyze_errors(self) -> None:
        """Analyze and categorize errors in the log."""
        self.errors.clear()
        
        if self.verbose:
            print("🚨 Analyzing errors...")
        
        for entry in self.log_entries:
            error = self._detect_error(entry)
            if error:
                self.errors.append(error)
        
        if self.verbose:
            print(f"✅ Found {len(self.errors)} errors")
    
    def _detect_error(self, entry: LogEntry) -> Optional[ErrorEntry]:
        """Detect if a log entry represents an error."""
        # Check each error pattern
        for error_type, pattern in self.error_patterns.items():
            match = pattern.search(entry.message)
            if match:
                # Filter out false positives
                
                # 1. Skip "error = 0" or "error 0" as these are success messages
                if re.search(r'\berror\s*[:=]?\s*0\b', entry.message, re.IGNORECASE):
                    continue
                
                # 2. Skip "success: TRUE" messages
                if 'success: TRUE' in entry.message:
                    continue
                
                # 3. Special handling for WinHTTP errors
                if error_type == 'winhttp_header':
                    # Check if this is a normal WinHTTP response code (not an error)
                    # 12150: ERROR_WINHTTP_HEADER_NOT_FOUND - Normal "no more content" response
                    # 00000: Success/OK response
                    normal_codes = ['12150', '00000']
                    if any(code in entry.message for code in normal_codes):
                        continue  # Skip this as it's not actually an error
                
                return ErrorEntry(
                    timestamp=entry.timestamp,
                    line_number=entry.line_number,
                    error_type=error_type,
                    message=entry.raw_line,  # Use raw_line to show original message
                    thread_id=entry.thread_id,
                    component=entry.component
                )
        
        return None
    
    def _get_error_name(self, error_type: str) -> str:
        """Get human-readable error name."""
        names = {
            'winhttp_header': 'WinHTTP Header Issues',
            'http_error': 'HTTP Status Errors',
            'ssl_error': 'SSL Certificate Errors',
            'timeout': 'Timeout/Connection Issues',
            'autoclose': 'AutoClose Issues',
            'database': 'Database Errors',
            'template_search': 'Template Search Failures',
            'connection_error': 'Connection Errors',
            'winhttp_error': 'WinHTTP Errors',
            'certificate_error': 'Certificate Validation Errors',
            'general_error': 'General Application Errors'
        }
        return names.get(error_type, error_type.replace('_', ' ').title())
    
    def _get_total_duration(self) -> str:
        """Get total session duration as formatted string."""
        if len(self.log_entries) < 2:
            return "N/A"
        
        duration = self.log_entries[-1].timestamp - self.log_entries[0].timestamp
        total_seconds = duration.total_seconds()
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _get_total_seconds(self) -> float:
        """Get total session duration in seconds."""
        if len(self.log_entries) < 2:
            return 0.0
        
        duration = self.log_entries[-1].timestamp - self.log_entries[0].timestamp
        return duration.total_seconds()
    
    def export_to_json(self, output_file: str, verified_bottlenecks: list = None) -> None:
        """Export analysis results to JSON."""
        # Get detailed summary statistics including applications
        summary_stats = self.generate_summary_stats()
        
        data = {
            "summary": {
                "log_file": str(self.log_file_path.name) if hasattr(self, 'log_file_path') else "Unknown",
                "total_entries": len(self.log_entries),
                "total_errors": len(self.errors),
                "total_time_gaps": len(self.time_gaps),
                "session_duration": self._get_total_duration(),
                "analysis_timestamp": datetime.now().isoformat(),
                "verified_bottlenecks_count": len(verified_bottlenecks) if verified_bottlenecks else 0
            },
            "detailed_statistics": summary_stats,
            "verified_bottlenecks": [
                {
                    "type": bottleneck['type'],
                    "user": bottleneck['user'],
                    "process": bottleneck['process'],
                    "duration_minutes": bottleneck['duration_minutes'],
                    "start_time": bottleneck['start_time'].isoformat(),
                    "end_time": bottleneck['end_time'].isoformat(),
                    "start_message": bottleneck['start_message'],
                    "end_message": bottleneck['end_message']
                }
                for bottleneck in (verified_bottlenecks or [])
            ],
            "time_gaps": [
                {
                    "start_time": gap.start_time.isoformat(),
                    "end_time": gap.end_time.isoformat(),
                    "duration_seconds": gap.duration_seconds,
                    "start_line": gap.start_line,
                    "end_line": gap.end_line,
                    "start_message": gap.start_message,
                    "end_message": gap.end_message
                }
                for gap in self.time_gaps
            ],
            "errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "line_number": error.line_number,
                    "error_type": error.error_type,
                    "error_name": self._get_error_name(error.error_type),
                    "message": error.message,
                    "thread_id": error.thread_id,
                    "component": error.component
                }
                for error in self.errors
            ],
            "error_summary": {
                error_type: len([e for e in self.errors if e.error_type == error_type])
                for error_type in {e.error_type for e in self.errors}
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"📄 JSON export saved: {output_file}")

    def generate_timestamp_analysis(self) -> str:
        """Generate comprehensive timestamp analysis similar to time_analysis.txt format."""
        if not self.log_entries:
            return "No log entries found for timestamp analysis."
        
        # Get time bounds
        start_time = min(entry.timestamp for entry in self.log_entries if entry.timestamp)
        end_time = max(entry.timestamp for entry in self.log_entries if entry.timestamp)
        total_duration = end_time - start_time
        total_seconds = total_duration.total_seconds()
        
        analysis_lines = []
        analysis_lines.append(f"TIMESTAMP ANALYSIS - {self.log_file_path.name}")
        analysis_lines.append("")
        analysis_lines.append("=== MAJOR TIME PERIODS ===")
        analysis_lines.append("")
        
        # Sort time gaps by chronological order for period analysis
        time_gaps_chronological = sorted(self.time_gaps, key=lambda x: x.start_time)
        
        period_num = 1
        current_time = start_time
        period_durations = []
        
        for gap in time_gaps_chronological:
            # Activity period before this gap
            if gap.start_time > current_time:
                period_duration = (gap.start_time - current_time).total_seconds()
                if period_duration > 30:  # Only show periods longer than 30 seconds
                    analysis_lines.append(f"{period_num}. ACTIVITY PHASE: {current_time.strftime('%H:%M:%S')} - {gap.start_time.strftime('%H:%M:%S')} ({int(period_duration)} seconds)")
                    
                    # Add context from log entries in this period
                    period_entries = [entry for entry in self.log_entries 
                                    if current_time <= entry.timestamp < gap.start_time]
                    if period_entries:
                        # Show first few and last few entries
                        analysis_lines.append(f"   - Start activities: {period_entries[0].message[:80]}...")
                        if len(period_entries) > 1:
                            analysis_lines.append(f"   - End activities: {period_entries[-1].message[:80]}...")
                    
                    period_durations.append(("activity", period_duration))
                    period_num += 1
            
            # The gap itself
            gap_duration = gap.duration_seconds
            is_major_gap = gap_duration >= 60  # 1+ minute gaps are "major"
            gap_marker = " ⭐ BOTTLENECK" if is_major_gap else ""
            
            analysis_lines.append(f"{period_num}. **MAJOR GAP**: {gap.start_time.strftime('%H:%M:%S')} - {gap.end_time.strftime('%H:%M:%S')} ({int(gap_duration//60)} minutes {int(gap_duration%60)} seconds){gap_marker}")
            analysis_lines.append(f"   - Last entry: {gap.start_message[:80]}...")
            analysis_lines.append(f"   - Next entry: {gap.end_message[:80]}...")
            
            if is_major_gap:
                analysis_lines.append("   - This indicates a HANG or BLOCKING operation")
            
            period_durations.append(("gap", gap_duration))
            current_time = gap.end_time
            period_num += 1
        
        # Final activity period if any
        if current_time < end_time:
            final_duration = (end_time - current_time).total_seconds()
            if final_duration > 30:
                analysis_lines.append(f"{period_num}. FINAL ACTIVITY: {current_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')} ({int(final_duration)} seconds)")
                period_durations.append(("activity", final_duration))
        
        # Time breakdown analysis
        analysis_lines.append("")
        analysis_lines.append("=== TIME BREAKDOWN ===")
        total_minutes = total_seconds / 60
        analysis_lines.append(f"Total Duration: {int(total_minutes)} minutes {int(total_seconds % 60)} seconds")
        analysis_lines.append("")
        
        breakdown_num = 1
        total_gap_time = 0
        total_activity_time = 0
        
        for period_type, duration in period_durations:
            percentage = (duration / total_seconds) * 100
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            
            if period_type == "gap":
                total_gap_time += duration
                if duration >= 60:  # Major gaps
                    analysis_lines.append(f"{breakdown_num}. **MAIN BOTTLENECK**: {minutes} minutes {seconds} seconds ({percentage:.1f}%) ⭐")
                else:
                    analysis_lines.append(f"{breakdown_num}. Minor gap: {minutes} minutes {seconds} seconds ({percentage:.1f}%)")
            else:
                total_activity_time += duration
                analysis_lines.append(f"{breakdown_num}. Activity period: {minutes} minutes {seconds} seconds ({percentage:.1f}%)")
            
            breakdown_num += 1
        
        # Root cause analysis
        if self.time_gaps:
            primary_gap = max(self.time_gaps, key=lambda x: x.duration_seconds)
            analysis_lines.append("")
            analysis_lines.append("=== ROOT CAUSE IDENTIFIED ===")
            gap_minutes = int(primary_gap.duration_seconds // 60)
            gap_seconds = int(primary_gap.duration_seconds % 60)
            analysis_lines.append(f"The primary bottleneck is the {gap_minutes}+ minute gap between {primary_gap.start_time.strftime('%H:%M:%S')} and {primary_gap.end_time.strftime('%H:%M:%S')}.")
            analysis_lines.append("")
            analysis_lines.append(f'Last operation before gap: "{primary_gap.start_message[:80]}..."')
            analysis_lines.append(f'First operation after gap: "{primary_gap.end_message[:80]}..."')
            analysis_lines.append("")
            
            # Analyze the gap context for root cause
            if "AutoClose" in primary_gap.start_message or "AutoClose" in primary_gap.end_message:
                analysis_lines.append("This suggests the application HUNG while performing AutoClose operations")
                analysis_lines.append("related to database cleanup or file management.")
            elif "database" in primary_gap.start_message.lower() or "DBF" in primary_gap.start_message:
                analysis_lines.append("This suggests the application HUNG while accessing database files")
                analysis_lines.append("related to user/group management operations.")
            elif "sync" in primary_gap.start_message.lower():
                analysis_lines.append("This suggests the application HUNG during synchronization operations")
                analysis_lines.append("related to network communication or file synchronization.")
            else:
                analysis_lines.append("This suggests the application encountered a blocking operation")
                analysis_lines.append("that prevented normal log file writing.")
            
            # Add performance summary
            activity_percentage = (total_activity_time / total_seconds) * 100
            gap_percentage = (total_gap_time / total_seconds) * 100
            
            analysis_lines.append("")
            remaining_time = total_seconds - primary_gap.duration_seconds
            if remaining_time > 0:
                remaining_percentage = (remaining_time / total_seconds) * 100
                analysis_lines.append(f"The remaining {remaining_percentage:.1f}% of time may include recovery operations or timeout retry loops.")
        
        return "\n".join(analysis_lines)

    def generate_summary_stats(self) -> Dict:
        """Generate comprehensive summary statistics for the log analysis."""
        from collections import Counter
        
        if not self.log_entries:
            return {}
        
        # Extract statistics
        processes = Counter()
        applications = Counter()
        categories = Counter()
        users = Counter()
        servers = Counter()
        hourly_activity = Counter()
        
        for entry in self.log_entries:
            # Process statistics
            if hasattr(entry, 'process') and hasattr(entry, 'pid') and entry.process:
                full_process = f"{entry.process}:{entry.pid}"
                processes[full_process] += 1
                
                # Application statistics - include all valid applications
                # Only filter out cvwin64 which is a redundant CaseWare process wrapper
                if entry.process not in {'cvwin64'}:
                    applications[entry.process] += 1
            
            # Category statistics
            if hasattr(entry, 'component') and entry.component:
                categories[entry.component.strip()] += 1
            
            # User statistics (handle different formats)
            if hasattr(entry, 'user') and entry.user:
                users[entry.user] += 1
            elif hasattr(entry, 'server') and entry.server:
                # Extract user from server field for wplog format
                if ':' in entry.server:
                    parts = entry.server.split(':')
                    if len(parts) >= 2:
                        users[parts[1]] += 1
            
            # Server statistics
            if hasattr(entry, 'server') and entry.server:
                if ':' in entry.server:
                    server_name = entry.server.split(':')[0]
                    servers[server_name] += 1
                else:
                    servers[entry.server] += 1
            
            # Hourly activity
            if entry.timestamp:
                hour = entry.timestamp.hour
                hourly_activity[f"{hour:02d}:00"] += 1
        
        # Error statistics by type
        error_stats = Counter()
        for error in self.errors:
            error_stats[self._get_error_name(error.error_type)] += 1
        
        # Time period analysis
        if self.log_entries:
            start_time = min(entry.timestamp for entry in self.log_entries if entry.timestamp)
            end_time = max(entry.timestamp for entry in self.log_entries if entry.timestamp)
            duration = end_time - start_time
        else:
            start_time = end_time = None
            duration = None
        
        return {
            'overview': {
                'total_entries': len(self.log_entries),
                'total_errors': len(self.errors),
                'total_time_gaps': len(self.time_gaps),
                'analysis_period': {
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else 'N/A',
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'N/A',
                    'duration_hours': round(duration.total_seconds() / 3600, 2) if duration else 0
                }
            },
            'processes': dict(processes.most_common(10)),
            'applications': dict(applications.most_common()),
            'categories': dict(categories.most_common(15)),
            'users': dict(users.most_common()),
            'servers': dict(servers.most_common()),
            'hourly_activity': dict(sorted(hourly_activity.items())),
            'error_summary': dict(error_stats.most_common()),
            'bottleneck_summary': {
                'primary_bottleneck_duration': round(max([gap.duration_seconds for gap in self.time_gaps], default=0) / 60, 2),
                'total_gap_time': round(sum(gap.duration_seconds for gap in self.time_gaps) / 60, 2),
                'average_gap_duration': round(sum(gap.duration_seconds for gap in self.time_gaps) / len(self.time_gaps) / 60, 2) if self.time_gaps else 0
            }
        }


def main():
    """Test the analyzer with a sample file."""
    if len(sys.argv) != 2:
        print("Usage: python wplog_analyzer.py <log_file>")
        sys.exit(1)
    
    analyzer = WPLogAnalyzer(verbose=True)
    
    try:
        analyzer.load_log_file(sys.argv[1])
        analyzer.analyze_time_gaps()
        analyzer.analyze_errors()
        
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        print(f"Total entries: {len(analyzer.log_entries):,}")
        print(f"Total errors: {len(analyzer.errors):,}")
        print(f"Time gaps: {len(analyzer.time_gaps)}")
        print(f"Duration: {analyzer._get_total_duration()}")
        
        if analyzer.time_gaps:
            primary_gap = analyzer.time_gaps[0]
            print(f"\nPrimary bottleneck: {primary_gap.duration_seconds/60:.2f} minutes")
            print(f"Lines: {primary_gap.start_line} → {primary_gap.end_line}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()