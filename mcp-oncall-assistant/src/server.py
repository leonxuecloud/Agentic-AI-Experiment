import sys
import os
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from jira import JIRA
from dotenv import load_dotenv
import json
from typing import Dict, Any

# Import custom toolkits
sys.path.append(str(Path(__file__).parent))
from tools.wpfile.caseware_universal_extractor import CaseWareExtractor
from tools.wplog.wplog_analyzer import WPLogAnalyzer

# Load environment variables
load_dotenv()

# Import environment variables
JIRA_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

# Server configuration
REQUIRE_APPROVAL = os.getenv("REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"
MAX_FILE_SIZE_GB = int(os.getenv("MAX_FILE_SIZE_GB", 20))
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".ac,.ac_,.log,.txt,.md").split(",")
TOOLS_DIR = Path(os.getenv("TOOLS_DIR", "./tools")).resolve()
CASEWARE_DIR = Path(os.getenv("CASEWARE_TOOLS_PATH", TOOLS_DIR / "caseware")).resolve()
WPLOG_DIR = Path(os.getenv("WPLOG_TOOLS_PATH", TOOLS_DIR / "wplog")).resolve()

# Configure logging to stderr (never stdout for MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("incident-response-mcp")

# Initialize FastMCP server
mcp = FastMCP(name="AI-Enhanced Incident Response MCP Server",
              instructions="""A comprehensive server for incident response with Jira integration and CaseWare analysis tools. Available tools:
              
              🔧 JIRA INTEGRATION:
              - jira_search_issues (jql: str) -> list[str]: Search for Jira issues using JQL
              - jira_create_issue (project_key: str, summary: str, description: str, issuetype: str) -> str: Create a new Jira issue
              - jira_get_issue (issue_key: str) -> dict: Get a Jira issue by its key
              - jira_update_issue (issue_key: str, fields: dict) -> str: Update a Jira issue
              - jira_delete_issue (issue_key: str) -> str: Delete a Jira issue
              
              📁 CASEWARE FILE ANALYSIS:
              - caseware_extract_file (file_path: str, output_path: str = None) -> dict: Extract files from CaseWare .ac_ archives
              - caseware_analyze_file (file_path: str) -> dict: Analyze CaseWare file structure and contents
              
              📊 WPLOG ANALYSIS:
              - wplog_analyze_file (log_file_path: str) -> dict: Analyze CaseWare Working Papers log files
              - wplog_find_bottlenecks (log_file_path: str, min_gap_seconds: float = 5.0) -> dict: Find performance bottlenecks in logs
              - wplog_analyze_errors (log_file_path: str) -> dict: Analyze errors in log files
              - wplog_export_analysis (log_file_path: str, output_file: str, analysis_type: str = "full") -> dict: Export log analysis to JSON
              """)

# =============================================================================
# JIRA INITIALIZATION
# =============================================================================

def initialize_jira():
    """Initialize JIRA client with environment credentials"""
    return JIRA(
        server=JIRA_URL,
        basic_auth=(JIRA_EMAIL, JIRA_TOKEN)
    )

# =============================================================================
# TOOLS - Functions that can be called by the MCP client
# =============================================================================

@mcp.tool()
def jira_search_issues(jql: str):
    """Search for Jira issues using JQL (Jira Query Language)
    
    Args:
        jql (str): The JQL query string to search with
        
    Returns:
        list[str]: List of Jira issue keys matching the query
    """
    jira = initialize_jira()
    issues = jira.search_issues(jql)
    return [issue.key for issue in issues]


@mcp.tool()
def jira_create_issue(project_key: str, summary: str, description: str, issuetype: str):
    """Create a new Jira issue
    
    Args:
        project_key (str): The project key where the issue should be created (e.g. 'PROJ')
        summary (str): The summary/title of the issue
        description (str): The detailed description of the issue
        issuetype (str): The type of issue to create (e.g. 'Bug', 'Task', 'Story')
        
    Returns:
        str: The key of the newly created issue
    """
    jira = initialize_jira()
    issue = jira.create_issue(project=project_key, summary=summary, description=description, issuetype=issuetype)
    return issue.key


@mcp.tool()
def jira_get_issue(issue_key: str):
    """Get a Jira issue by its key
    
    Args:
        issue_key (str): The key of the issue to get
        
    Returns:
        str: A JSON string representation of the Jira issue
    """
    jira = initialize_jira()
    issue = jira.issue(issue_key)
    return issue.raw


@mcp.tool()
def jira_update_issue(issue_key: str, fields: dict):
    """Update a Jira issue
    
    Args:
        issue_key (str): The key of the issue to update
        fields (dict): Dictionary of fields to update and their new values
        
    Returns:
        str: A JSON string representation of the updated Jira issue
    """
    jira = initialize_jira()
    issue = jira.issue(issue_key)
    issue.update(fields=fields)
    return issue.raw


@mcp.tool()
def jira_delete_issue(issue_key: str):
    """Delete a Jira issue
    
    Args:
        issue_key (str): The key of the issue to delete
        
    Returns:
        str: The key of the deleted issue
    """
    jira = initialize_jira()
    issue = jira.issue(issue_key)
    issue.delete()
    return f"Issue {issue_key} deleted"


# =============================================================================
# CASEWARE FILE TOOLS
# =============================================================================

@mcp.tool()
def caseware_extract_file(file_path: str, output_path: str = None):
    """Extract files from CaseWare .ac_ archives
    
    Args:
        file_path (str): Path to the CaseWare .ac_ file to extract
        output_path (str, optional): Output directory for extracted files
        
    Returns:
        dict: Extraction results including success status, files extracted, and statistics
    """
    try:
        import io
        import contextlib
        
        # Redirect stdout to capture logging and prevent encoding issues
        stdout_capture = io.StringIO()
        
        with contextlib.redirect_stdout(stdout_capture):
            extractor = CaseWareExtractor(input_path=file_path, output_path=output_path)
            
            # Capture the extraction process
            initial_stats = extractor.stats.copy()
            
            try:
                extractor.run()
            except UnicodeEncodeError:
                # If we get encoding errors, continue anyway
                pass
            
            final_stats = extractor.stats.copy()
        
        # Get the captured output (without emojis causing issues)
        log_output = stdout_capture.getvalue()
        
        return {
            "success": True,
            "input_file": str(file_path),
            "output_directory": str(extractor.output_dir),
            "statistics": final_stats,
            "files_processed": final_stats["files_processed"],
            "files_extracted": final_stats["files_extracted"],
            "files_failed": final_stats["files_failed"],
            "success_rate": (final_stats["files_extracted"] / final_stats["files_processed"] * 100) if final_stats["files_processed"] > 0 else 0,
            "log_summary": f"Processed {final_stats['files_processed']} files, extracted {final_stats['files_extracted']}, failed {final_stats['files_failed']}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "input_file": str(file_path)
        }


@mcp.tool()
def caseware_analyze_file(file_path: str):
    """Analyze CaseWare file structure and contents without extraction
    
    Args:
        file_path (str): Path to the CaseWare file to analyze
        
    Returns:
        dict: Analysis results including file type, structure info, and metadata
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Read file for analysis
        with open(file_path_obj, 'rb') as f:
            data = f.read()
        
        # Calculate file hash manually to avoid logging issues
        import hashlib
        file_hash = hashlib.md5(data).hexdigest()
        
        # Analyze file structure
        analysis_result = {
            "success": True,
            "file_path": str(file_path_obj),
            "file_size": len(data),
            "file_hash": file_hash,
            "file_type": "unknown"
        }
        
        # Check if it's an OLE compound document
        if data.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            analysis_result["file_type"] = "OLE Compound Document"
            
            # Perform basic OLE analysis without using extractor logging
            try:
                # Basic OLE header parsing
                if len(data) >= 512:
                    import struct
                    
                    # Read OLE header information
                    ole_header = data[:512]
                    sector_size_power = struct.unpack('<H', ole_header[30:32])[0]
                    sector_size = 2 ** sector_size_power if sector_size_power < 20 else 512
                    
                    mini_sector_size_power = struct.unpack('<H', ole_header[32:34])[0]
                    mini_sector_size = 2 ** mini_sector_size_power if mini_sector_size_power < 20 else 64
                    
                    num_dir_sectors = struct.unpack('<I', ole_header[44:48])[0]
                    num_fat_sectors = struct.unpack('<I', ole_header[48:52])[0]
                    
                    analysis_result["ole_structure"] = {
                        "valid_ole_header": True,
                        "sector_size": sector_size,
                        "mini_sector_size": mini_sector_size,
                        "directory_sectors": num_dir_sectors,
                        "fat_sectors": num_fat_sectors,
                        "estimated_streams": num_dir_sectors * (sector_size // 128) if sector_size > 0 else 0
                    }
                    
                    # Look for CaseWare-specific patterns in the data
                    caseware_indicators = []
                    if b'CaseWare' in data:
                        caseware_indicators.append("CaseWare string found")
                    if b'VALIDE' in data:
                        caseware_indicators.append("VALIDE stream found")
                    if b'DocumentSummaryInformation' in data:
                        caseware_indicators.append("Document summary found")
                    
                    analysis_result["caseware_indicators"] = caseware_indicators
                    analysis_result["has_caseware_content"] = len(caseware_indicators) > 0
                    
            except Exception as e:
                analysis_result["ole_analysis_error"] = f"Failed to parse OLE structure: {str(e)}"
        
        # Check for ZIP signatures
        elif data.startswith(b'PK'):
            analysis_result["file_type"] = "ZIP Archive"
            
            # Basic ZIP analysis
            try:
                import zipfile
                import io
                
                with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
                    file_list = zf.namelist()
                    analysis_result["zip_structure"] = {
                        "valid_zip": True,
                        "file_count": len(file_list),
                        "files": file_list[:10] if len(file_list) <= 10 else file_list[:10] + ["...and more"]
                    }
            except Exception as e:
                analysis_result["zip_analysis_error"] = f"Failed to parse ZIP structure: {str(e)}"
        
        # Check for compressed data patterns
        elif b'\x5d\x00\x00' in data[:100]:  # LZMA2 signature
            analysis_result["file_type"] = "LZMA2 Compressed"
            
            # Look for compression headers
            lzma_positions = []
            search_pos = 0
            while search_pos < min(len(data), 10000):  # Search first 10KB
                pos = data.find(b'\x5d\x00\x00', search_pos)
                if pos == -1:
                    break
                lzma_positions.append(pos)
                search_pos = pos + 1
            
            analysis_result["compression_info"] = {
                "lzma_signatures_found": len(lzma_positions),
                "signature_positions": lzma_positions[:5]  # First 5 positions
            }
        
        # Additional file format detection
        if data.startswith(b'\x1f\x8b'):
            analysis_result["file_type"] = "GZIP Compressed"
        elif data.startswith(b'BZh'):
            analysis_result["file_type"] = "BZIP2 Compressed"
        elif data.startswith(b'\x37\x7A\xBC\xAF\x27\x1C'):
            analysis_result["file_type"] = "7-Zip Archive"
        
        return analysis_result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": str(file_path)
        }


# =============================================================================
# WPLOG ANALYSIS TOOLS
# =============================================================================

@mcp.tool()
def wplog_analyze_file(log_file_path: str):
    """Analyze CaseWare Working Papers log files
    
    Args:
        log_file_path (str): Path to the log file to analyze
        
    Returns:
        dict: Analysis results including entry count, errors, time gaps, and summary statistics
    """
    try:
        analyzer = WPLogAnalyzer(verbose=False)
        analyzer.load_log_file(log_file_path)
        analyzer.analyze_time_gaps()
        analyzer.analyze_errors()
        
        # Generate summary statistics
        summary_stats = analyzer.generate_summary_stats()
        
        return {
            "success": True,
            "log_file": str(log_file_path),
            "total_entries": len(analyzer.log_entries),
            "total_errors": len(analyzer.errors),
            "time_gaps_found": len(analyzer.time_gaps),
            "duration": analyzer._get_total_duration(),
            "duration_seconds": analyzer._get_total_seconds(),
            "summary_statistics": summary_stats,
            "first_entry": analyzer.log_entries[0].timestamp.isoformat() if analyzer.log_entries else None,
            "last_entry": analyzer.log_entries[-1].timestamp.isoformat() if analyzer.log_entries else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log_file": str(log_file_path)
        }


@mcp.tool()
def wplog_find_bottlenecks(log_file_path: str, min_gap_seconds: float = 5.0):
    """Find performance bottlenecks in CaseWare Working Papers log files
    
    Args:
        log_file_path (str): Path to the log file to analyze
        min_gap_seconds (float): Minimum gap duration in seconds to consider as a bottleneck
        
    Returns:
        dict: Bottleneck analysis results including time gaps and verified bottlenecks
    """
    try:
        analyzer = WPLogAnalyzer(verbose=False)
        analyzer.load_log_file(log_file_path)
        analyzer.analyze_time_gaps(min_gap_seconds=min_gap_seconds)
        
        # Get verified bottlenecks
        verified_bottlenecks = analyzer.analyze_verified_bottlenecks()
        
        # Format time gaps for response
        time_gaps = []
        for gap in analyzer.time_gaps[:10]:  # Top 10 gaps
            time_gaps.append({
                "start_time": gap.start_time.isoformat(),
                "end_time": gap.end_time.isoformat(),
                "duration_seconds": gap.duration_seconds,
                "duration_minutes": gap.duration_seconds / 60,
                "start_line": gap.start_line,
                "end_line": gap.end_line,
                "start_message": gap.start_message[:100] + "..." if len(gap.start_message) > 100 else gap.start_message,
                "end_message": gap.end_message[:100] + "..." if len(gap.end_message) > 100 else gap.end_message
            })
        
        return {
            "success": True,
            "log_file": str(log_file_path),
            "min_gap_threshold": min_gap_seconds,
            "total_gaps_found": len(analyzer.time_gaps),
            "top_time_gaps": time_gaps,
            "verified_bottlenecks": verified_bottlenecks[:5] if verified_bottlenecks else [],  # Top 5 verified
            "primary_bottleneck": {
                "duration_minutes": analyzer.time_gaps[0].duration_seconds / 60,
                "lines": f"{analyzer.time_gaps[0].start_line} → {analyzer.time_gaps[0].end_line}"
            } if analyzer.time_gaps else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log_file": str(log_file_path)
        }


@mcp.tool()
def wplog_analyze_errors(log_file_path: str):
    """Analyze errors in CaseWare Working Papers log files
    
    Args:
        log_file_path (str): Path to the log file to analyze
        
    Returns:
        dict: Error analysis results including error types, frequencies, and details
    """
    try:
        analyzer = WPLogAnalyzer(verbose=False)
        analyzer.load_log_file(log_file_path)
        analyzer.analyze_errors()
        
        # Group errors by type
        error_summary = {}
        error_details = []
        
        for error in analyzer.errors:
            error_type = error.error_type
            if error_type not in error_summary:
                error_summary[error_type] = 0
            error_summary[error_type] += 1
            
            error_details.append({
                "timestamp": error.timestamp.isoformat(),
                "line_number": error.line_number,
                "error_type": error_type,
                "error_name": analyzer._get_error_name(error_type),
                "message": error.message[:200] + "..." if len(error.message) > 200 else error.message
            })
        
        return {
            "success": True,
            "log_file": str(log_file_path),
            "total_errors": len(analyzer.errors),
            "error_summary": error_summary,
            "error_details": error_details[:20],  # Top 20 errors
            "most_common_error": max(error_summary.items(), key=lambda x: x[1]) if error_summary else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log_file": str(log_file_path)
        }


@mcp.tool()
def wplog_export_analysis(log_file_path: str, output_file: str, analysis_type: str = "full"):
    """Export log analysis to JSON file
    
    Args:
        log_file_path (str): Path to the log file to analyze
        output_file (str): Path for the output JSON file
        analysis_type (str): Type of analysis to export ("full", "errors", "bottlenecks", "summary")
        
    Returns:
        dict: Export results including file path and summary
    """
    try:
        analyzer = WPLogAnalyzer(verbose=False)
        analyzer.load_log_file(log_file_path)
        analyzer.analyze_time_gaps()
        analyzer.analyze_errors()
        
        verified_bottlenecks = analyzer.analyze_verified_bottlenecks() if analysis_type in ["full", "bottlenecks"] else None
        
        # Export to JSON
        analyzer.export_to_json(output_file, verified_bottlenecks)
        
        # Verify output file was created
        output_path = Path(output_file)
        if output_path.exists():
            file_size = output_path.stat().st_size
            return {
                "success": True,
                "log_file": str(log_file_path),
                "output_file": str(output_file),
                "analysis_type": analysis_type,
                "output_file_size": file_size,
                "total_entries_analyzed": len(analyzer.log_entries),
                "total_errors_found": len(analyzer.errors),
                "total_gaps_found": len(analyzer.time_gaps)
            }
        else:
            return {
                "success": False,
                "error": "Output file was not created",
                "log_file": str(log_file_path),
                "output_file": str(output_file)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log_file": str(log_file_path),
            "output_file": str(output_file)
        }

# =============================================================================
# RESOURCES - Data that can be accessed by the MCP client
# =============================================================================

@mcp.resource("file://status.txt")
def get_status_file() -> str:
    """Get the system status file content"""
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"System Status: Operational\nLast Updated: {current_date}\nServices: All running normally"


@mcp.resource("file://greeting.txt")
def get_greeting_file() -> str:
    """Get a greeting file"""
    return "Hello! Welcome to the AI-Enhanced Incident Response system."


# -----------------------------------------------------------------------------
# Example Resource: Incident Template (returns a template based on severity)
# -----------------------------------------------------------------------------
@mcp.resource("incident-template://{severity}")
def get_incident_template(severity: str) -> str:
    """
    Get an incident response template based on severity.
    Args:
        severity (str): Severity level (low, medium, high, critical)
    Returns:
        str: Incident response template text
    """
    templates = {
        "critical": "CRITICAL INCIDENT TEMPLATE: Immediate executive notification required.",
        "high": "HIGH INCIDENT TEMPLATE: Urgent response within 1 hour.",
        "medium": "MEDIUM INCIDENT TEMPLATE: Response within 4 hours.",
        "low": "LOW INCIDENT TEMPLATE: Response within 24 hours."
    }
    return templates.get(severity.lower(), templates["medium"])

# -----------------------------------------------------------------------------
# Example Prompt Template: Outage Notification
# -----------------------------------------------------------------------------
@mcp.prompt()
def outage_notification(service: str, duration_minutes: int) -> str:
    """
    Generate an outage notification template for a given service and duration.
    Args:
        service (str): Name of the affected service
        duration_minutes (int): Estimated outage duration in minutes
    Returns:
        str: Notification message
    """
    return (
        f"Attention: The {service} service is currently experiencing an outage. "
        f"Estimated resolution time is {duration_minutes} minutes. "
        "Our team is actively working to restore service. We apologize for the inconvenience."
    )

# -----------------------------------------------------------------------------
# Example Usage: Sampling the resource and template
# -----------------------------------------------------------------------------
# Sample usage (for documentation/testing):
#
# incident_template = get_incident_template("high")
# print("Sample Incident Template:", incident_template)
#
# notification = outage_notification("JIRA", 45)
# print("Sample Outage Notification:", notification)

# =============================================================================
# PROMPTS - Prompt templates that can be used by the MCP client  
# =============================================================================

@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }
    
    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


@mcp.prompt()
def analyze_ticket_with_similar_solutions(ticket_number: str, search_limit: int = 10) -> str:
    """
    Generate a prompt to analyze a Jira ticket and suggest solutions based on similar resolved tickets.
    
    Args:
        ticket_number: The Jira ticket ID to analyze (e.g., 'CS-3143')
        search_limit: Maximum number of similar tickets to analyze (default: 10)
    
    Returns:
        A detailed prompt for the AI to analyze the ticket and suggest solutions
    """
    return f"""Analyze Jira ticket {ticket_number} and suggest possible solutions based on similar resolved tickets.

**Step 1: Get Current Ticket Details**
Use the `jira_get_issue` tool to retrieve full details of ticket {ticket_number}, including:
- Issue type
- Component(s)
- Description
- Status
- Priority
- Labels
- Custom fields

**Step 2: Search for Similar Resolved Tickets**
Use the `jira_search_issues` tool to find similar tickets. Construct a JQL query based on:
- Same issue type
- Similar components
- Similar labels
- Status = "Resolved" or "Closed"
- Resolution is not empty

Example JQL: `project = {ticket_number.split('-')[0]} AND status IN (Resolved, Closed) AND resolution IS NOT EMPTY AND component IN ({{components_from_ticket}}) ORDER BY updated DESC`

Limit results to {search_limit} most recent matches.

**Step 3: Analyze Each Similar Ticket**
For each relevant match found, extract and present:
1. **Ticket ID and Link**: `{JIRA_URL}/browse/[TICKET-ID]`
2. **Summary**: Brief title/summary of the issue
3. **Description**: Key details about what the problem was
4. **Resolution Applied**: How the issue was resolved
5. **Resolution Date**: When it was resolved
6. **Linked Documentation**: Any referenced documentation, wiki pages, or confluence links
7. **Comments**: Key insights from the resolution comments
8. **Time to Resolve**: How long it took to resolve

**Step 4: Pattern Analysis**
Identify common patterns across the similar tickets:
- Most common root causes
- Most effective resolution strategies
- Frequently referenced documentation
- Average time to resolution
- Components most affected

**Step 5: Solution Recommendations**
Based on the analysis of similar tickets, provide:

**Primary Solution Recommendation:**
- Detailed step-by-step approach based on most successful resolutions
- Estimated time to implement
- Risk assessment (low/medium/high)
- Required resources or expertise

**Alternative Solutions (if applicable):**
- Secondary approaches that worked for similar issues
- When to use each alternative
- Pros and cons of each approach

**Preventive Measures:**
- How to prevent this issue in the future
- Monitoring or alerting recommendations
- Documentation updates needed

**Related Resources:**
- Links to relevant documentation
- Similar tickets for reference
- Knowledge base articles
- Team members who have resolved similar issues

**Next Steps:**
1. Immediate actions to take
2. Investigation areas if solution doesn't work
3. Escalation path if needed

Please present the findings in a clear, structured format with actionable recommendations."""


@mcp.prompt()
def incident_response_analysis(
    ticket_number: str,
    severity: str = "medium",
    include_caseware_logs: bool = False
) -> str:
    """
    Generate a comprehensive incident response analysis prompt.
    
    Args:
        ticket_number: The Jira ticket ID for the incident
        severity: Incident severity (low/medium/high/critical)
        include_caseware_logs: Whether to include CaseWare log analysis
    
    Returns:
        A detailed incident response analysis prompt
    """
    severity_context = {
        "critical": "This is a CRITICAL incident requiring immediate attention and executive notification.",
        "high": "This is a HIGH severity incident requiring urgent response within 1 hour.",
        "medium": "This is a MEDIUM severity incident requiring response within 4 hours.",
        "low": "This is a LOW severity incident requiring response within 24 hours."
    }
    
    log_analysis_section = ""
    if include_caseware_logs:
        log_analysis_section = """
**Step 4: CaseWare Log Analysis (if applicable)**
If this incident involves CaseWare Working Papers:
1. Use `wplog_analyze_file` to analyze relevant log files
2. Use `wplog_find_bottlenecks` to identify performance issues
3. Use `wplog_analyze_errors` to find error patterns
4. Use `caseware_analyze_file` to analyze any related CaseWare files

Present findings:
- Performance bottlenecks found
- Error patterns and frequencies
- Time gaps and their correlation to the incident
- File structure issues (if any)
"""
    
    return f"""**INCIDENT RESPONSE ANALYSIS FOR {ticket_number}**

{severity_context.get(severity.lower(), severity_context['medium'])}

**Step 1: Retrieve Incident Details**
Use `jira_get_issue` to get complete details of {ticket_number}:
- Issue type and category
- Description and impact
- Affected systems/components
- Reporter and assignee
- Priority and severity
- Time reported and SLA deadline

**Step 2: Check for Related Incidents**
Search for related or duplicate incidents using `jira_search_issues`:
- Same component failures in last 30 days
- Similar error messages or symptoms
- Incidents affecting the same customer/environment
- Ongoing incidents that might be related

JQL Example: `project = {ticket_number.split('-')[0]} AND status IN (Open, "In Progress") AND component IN ({{affected_components}}) AND created >= -30d`

**Step 3: Historical Pattern Analysis**
Find similar resolved incidents:
- Same root cause category
- Same affected systems
- Similar resolution time
- Effective mitigation strategies used

{log_analysis_section}

**Step 5: Root Cause Hypothesis**
Based on similar incidents and current data:
1. **Primary Hypothesis**: Most likely root cause
2. **Alternative Hypotheses**: Other possible causes
3. **Evidence Required**: What data/logs would confirm each hypothesis

**Step 6: Impact Assessment**
- **User Impact**: Number of users affected, business functions impacted
- **System Impact**: Services down/degraded, data integrity risks
- **Financial Impact**: Estimated cost of downtime
- **Reputational Impact**: Customer/stakeholder communication needs

**Step 7: Recommended Actions**
Provide prioritized action plan:

**IMMEDIATE (Within 15 minutes):**
1. [Action items for immediate stabilization]
2. [Communication to stakeholders]
3. [Monitoring to set up]

**SHORT-TERM (Within 1-4 hours):**
1. [Investigation steps]
2. [Temporary workarounds]
3. [Data collection needed]

**LONG-TERM (Within 24 hours):**
1. [Permanent fix implementation]
2. [Verification and testing]
3. [Documentation and post-mortem]

**Step 8: Communication Plan**
- **Internal**: Teams to notify and update frequency
- **External**: Customer communication templates if needed
- **Escalation**: When and to whom to escalate

**Step 9: Prevention Recommendations**
- Monitoring improvements
- Process changes
- Code/configuration updates
- Documentation needs

Present findings in a clear, action-oriented format suitable for incident response."""


@mcp.prompt()
def ticket_triage_assistant(
    ticket_number: str,
    auto_categorize: bool = True
) -> str:
    """
    Generate a prompt for intelligent ticket triage and routing.
    
    Args:
        ticket_number: The Jira ticket ID to triage
        auto_categorize: Whether to suggest automatic categorization
    
    Returns:
        A prompt for triaging and routing the ticket
    """
    return f"""**INTELLIGENT TICKET TRIAGE: {ticket_number}**

**Step 1: Analyze Ticket Content**
Use `jira_get_issue` to retrieve {ticket_number} and analyze:
- Description keywords and technical terms
- Component and labels
- Reporter's history (if accessible)
- Attachments and their types
- Priority and current assignment

**Step 2: Search Historical Patterns**
Use `jira_search_issues` to find similar tickets:
```
project = {ticket_number.split('-')[0]} AND status IN (Resolved, Closed) AND resolution IS NOT EMPTY ORDER BY resolved DESC
```

Analyze the top 20 matches for:
- Common component assignments
- Typical assignee/team
- Average resolution time
- Escalation patterns

**Step 3: Categorization Analysis**
{"Automatically categorize this ticket based on:" if auto_categorize else "Provide categorization recommendations:"}
- **Type**: Bug / Enhancement / Task / Story / Incident
- **Priority**: Critical / High / Medium / Low
- **Category**: (e.g., Performance, Security, UI/UX, Integration, Data)
- **Complexity**: Simple / Medium / Complex
- **Estimated Effort**: (based on similar tickets)

**Step 4: Team/Assignee Recommendation**
Suggest the best team and assignee based on:
- Component expertise (from historical assignments)
- Current workload (from active tickets)
- Past success rate with similar issues
- Availability (from recent activity)

Format:
- **Recommended Team**: [Team Name]
- **Recommended Assignee**: [Name] (resolved X similar tickets)
- **Alternative Assignees**: [Names] (if primary is unavailable)

**Step 5: SLA and Priority Assessment**
- **Suggested Priority**: [with justification]
- **SLA Target**: [based on priority and type]
- **Risk Factors**: [any factors that might impact resolution]

**Step 6: Immediate Actions**
List any immediate actions needed:
1. Request additional information (if description is incomplete)
2. Attach relevant logs or files
3. Link to related tickets
4. Add missing labels or components
5. Set up monitoring or alerts

**Step 7: Triage Summary**
Provide a one-paragraph summary suitable for team standup:
"Ticket {ticket_number} is a [category] [type] reported by [reporter]. Similar to [X] previous tickets. Recommend assigning to [team/person] with [priority] priority. Estimated resolution: [timeframe]. Key actions: [list]."

Present recommendations in a clear, actionable format."""

# TODO: Add more prompts here
# @mcp.prompt()
# def incident_response_prompt(severity: str = "medium") -> str:
#     """Generate an incident response prompt"""
#     pass

# =============================================================================
# MAIN FUNCTION
# =============================================================================


def main():
    """
    Initialize and run the AI-Enhanced Incident Response MCP server.
    
    This follows the official MCP specification for Python servers using FastMCP.
    """
    try:
        logger.info("Starting AI-Enhanced Incident Response MCP Server")
        logger.info(f"Tools directory: {TOOLS_DIR}")
        logger.info(f"Human approval required: {REQUIRE_APPROVAL}")
        
        # Verify tool directories exist
        if not CASEWARE_DIR.exists():
            logger.warning(f"CaseWare tools directory not found: {CASEWARE_DIR}")
        if not WPLOG_DIR.exists():
            logger.warning(f"WPLog tools directory not found: {WPLOG_DIR}")
        
        # Log registered components for debugging
        logger.info("MCP Server Registration Summary:")
        logger.info(f"Tools registered: {len(mcp._tools) if hasattr(mcp, '_tools') else 'Unknown'}")
        logger.info(f"Resources registered: {len(mcp._resources) if hasattr(mcp, '_resources') else 'Unknown'}")
        logger.info(f"Prompts registered: {len(mcp._prompts) if hasattr(mcp, '_prompts') else 'Unknown'}")
        
        # Run the FastMCP server with STDIO transport
        # This is the standard MCP server pattern for Claude Desktop integration
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()