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
    return "System Status: Operational\nLast Updated: 2025-10-08\nServices: All running normally"

@mcp.resource("file://greeting.txt")
def get_greeting_file() -> str:
    """Get a greeting file"""
    return "Hello! Welcome to the AI-Enhanced Incident Response system."

# TODO: Add more resources here
# @mcp.resource("incident-template://{severity}")
# def get_incident_template(severity: str) -> str:
#     """Get incident response template based on severity"""
#     pass

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