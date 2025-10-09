#!/usr/bin/env python3
"""
WPLog Analyzer - Main Application
==================================

Command-line interface for analyzing CaseWare Working Papers log files.
Provides comprehensive analysis including bottleneck identification, error analysis,
and HTML report generation.

Usage:
    python main.py <log_file> [options]
    python main.py wplog.txt --html-report --json-export
"""

import argparse
import sys
from pathlib import Path
import json

from wplog_analyzer import WPLogAnalyzer
from html_report import HTMLReportGenerator
from markdown_report import MarkdownReportGenerator


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze CaseWare Working Papers log files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py wplog.txt                    # Basic analysis  
  python main.py wplog.txt --markdown-report # Generate Markdown report (recommended)
  python main.py wplog.txt --html-report     # Generate HTML report
  python main.py wplog.txt --json-export     # Export to JSON
  python main.py wplog.txt --all-outputs     # Generate all outputs
  python main.py wplog.txt --verified-bottlenecks --markdown-report  # Verified analysis
  python main.py wplog.txt --min-gap 30      # Show gaps >= 30 seconds
  python main.py wplog.txt --error-types winhttp http  # Filter error types
        """
    )
    
    # Required arguments
    parser.add_argument(
        'log_file',
        help='Path to the wplog.txt file to analyze'
    )
    
    # Output options
    parser.add_argument(
        '--html-report',
        action='store_true',
        help='Generate HTML report (saved as log_analysis.html)'
    )
    
    parser.add_argument(
        '--markdown-report',
        action='store_true',
        help='Generate Markdown report (saved as log_analysis.md)'
    )
    
    parser.add_argument(
        '--json-export',
        action='store_true',
        help='Export analysis data to JSON (saved as log_analysis.json)'
    )
    
    parser.add_argument(
        '--all-outputs',
        action='store_true',
        help='Generate all output formats (HTML + Markdown + JSON + console)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory to save output files (default: same directory as log file)'
    )
    
    # Analysis options
    parser.add_argument(
        '--min-gap',
        type=float,
        default=5.0,
        help='Minimum time gap in seconds to report (default: 5.0)'
    )
    
    parser.add_argument(
        '--max-gaps',
        type=int,
        default=10,
        help='Maximum number of gaps to show in console output (default: 10)'
    )
    
    parser.add_argument(
        '--error-types',
        nargs='*',
        help='Filter errors by type (winhttp, http, ssl, timeout, general)'
    )
    
    parser.add_argument(
        '--verified-bottlenecks',
        action='store_true',
        help='For userlog files: analyze verified bottlenecks (same user/process pairs only)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show verbose output during analysis'
    )
    
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    log_file = Path(args.log_file)
    if not log_file.exists():
        print(f"❌ Error: Log file '{log_file}' not found")
        sys.exit(1)
    
    if not log_file.is_file():
        print(f"❌ Error: '{log_file}' is not a file")
        sys.exit(1)
    
    # Set output directory to log file's directory if not specified
    if args.output_dir == '.':  # Default value
        output_dir = log_file.parent
    else:
        output_dir = Path(args.output_dir)
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize analyzer
        if not args.quiet:
            print(f"🔍 Analyzing log file: {log_file}")
            print("📊 Starting analysis...")
        
        analyzer = WPLogAnalyzer(verbose=args.verbose)
        
        # Load and analyze the log file
        analyzer.load_log_file(str(log_file))
        
        if not args.quiet:
            print(f"✅ Loaded {len(analyzer.log_entries):,} log entries")
        
        # Analyze time gaps
        analyzer.analyze_time_gaps(min_gap_seconds=args.min_gap)
        
        if not args.quiet:
            print(f"⏰ Found {len(analyzer.time_gaps)} time gaps")
        
        # Analyze errors
        analyzer.analyze_errors()
        
        if not args.quiet:
            print(f"🚨 Found {len(analyzer.errors)} errors")
        
        # Analyze verified bottlenecks for userlog files
        verified_bottlenecks = []
        if args.verified_bottlenecks:
            verified_bottlenecks = analyzer.analyze_verified_bottlenecks()
            if not args.quiet:
                print(f"🔍 Found {len(verified_bottlenecks)} verified bottlenecks (same user/process)")
        
        # Filter errors if requested
        if args.error_types:
            analyzer.errors = [
                error for error in analyzer.errors
                if any(error_type in error.error_type for error_type in args.error_types)
            ]
            if not args.quiet:
                print(f"🔍 Filtered to {len(analyzer.errors)} errors of types: {', '.join(args.error_types)}")
        
        # Extract log filename for reports
        log_filename = Path(args.log_file).name
        log_basename = Path(args.log_file).stem  # filename without extension
        
        # Generate outputs based on arguments
        if args.all_outputs:
            args.html_report = True
            args.markdown_report = True
            args.json_export = True
        
        # Console output (default unless quiet)
        if not args.quiet:
            _print_console_report(analyzer, args.max_gaps, verified_bottlenecks)
        
        # HTML report
        if args.html_report:
            html_file = output_dir / f"{log_basename}_analysis.html"
            html_generator = HTMLReportGenerator(analyzer, verified_bottlenecks, log_filename)
            html_generator.generate_html_report(str(html_file))
        
        # Markdown report (consistent with previous implementation)
        if args.markdown_report:
            md_file = output_dir / f"{log_basename}_analysis.md"
            md_generator = MarkdownReportGenerator(analyzer, verified_bottlenecks, log_filename)
            md_generator.generate_markdown_report(str(md_file))
        
        # JSON export
        if args.json_export:
            json_file = output_dir / f"{log_basename}_analysis.json"
            analyzer.export_to_json(str(json_file), verified_bottlenecks)
        
        # Final summary
        if not args.quiet:
            print("\n" + "="*60)
            print("✅ Analysis completed successfully!")
            if args.html_report:
                print(f"🌐 HTML report: {output_dir / 'log_analysis.html'}")
            if args.markdown_report:
                print(f"📄 Markdown report: {output_dir / 'log_analysis.md'}")
            if args.json_export:
                print(f"� JSON export: {output_dir / 'log_analysis.json'}")
            print("="*60)
    
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _print_console_report(analyzer: WPLogAnalyzer, max_gaps: int, verified_bottlenecks: list = None) -> None:
    """Print a comprehensive console report."""
    print("\n" + "="*60)
    print("📊 WPLOG ANALYSIS REPORT")
    print("="*60)
    
    # Verified bottlenecks section (if available)
    if verified_bottlenecks:
        print("\n🔍 VERIFIED BOTTLENECKS (Same User/Process)")
        print("-" * 50)
        for i, bottleneck in enumerate(verified_bottlenecks[:5], 1):  # Show top 5
            print(f"\n#{i}. {bottleneck['type']} - {bottleneck['duration_minutes']:.2f} minutes")
            print(f"    👤 User: {bottleneck['user']}")
            print(f"    ⚙️  Process: {bottleneck['process']}")
            print(f"    ⏰ Time: {bottleneck['start_time'].strftime('%H:%M:%S')} → {bottleneck['end_time'].strftime('%H:%M:%S')}")
            print(f"    📝 Start: {bottleneck['start_message'][:80]}...")
            print(f"    📝 End:   {bottleneck['end_message'][:80]}...")
    
    # Summary statistics
    total_entries = len(analyzer.log_entries)
    total_errors = len(analyzer.errors)
    total_gaps = len(analyzer.time_gaps)
    duration = analyzer._get_total_duration()
    
    print("\n📈 SUMMARY STATISTICS")
    print(f"Total Log Entries: {total_entries:,}")
    print(f"Total Errors: {total_errors:,}")
    print(f"Time Gaps Found: {total_gaps}")
    print(f"Session Duration: {duration}")
    
    # Detailed timestamp analysis
    print("\n📅 DETAILED TIMESTAMP ANALYSIS")
    print("="*60)
    timestamp_analysis = analyzer.generate_timestamp_analysis()
    print(timestamp_analysis)
    
    # Primary bottleneck
    if analyzer.time_gaps:
        primary_gap = analyzer.time_gaps[0]
        total_seconds = analyzer._get_total_seconds()
        impact_percentage = (primary_gap.duration_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        print("\n🎯 PRIMARY BOTTLENECK IDENTIFIED")
        print(f"Duration: {primary_gap.duration_seconds/60:.2f} minutes ({primary_gap.duration_seconds:.0f} seconds)")
        print(f"Lines: {primary_gap.start_line} → {primary_gap.end_line}")
        print(f"Time: {primary_gap.start_time.strftime('%H:%M:%S')} → {primary_gap.end_time.strftime('%H:%M:%S')}")
        print(f"Impact: {impact_percentage:.1f}% of total session time")
        print(f"Start: {primary_gap.start_message[:100]}...")
        print(f"End: {primary_gap.end_message[:100]}...")
        
        # Show additional gaps
        if len(analyzer.time_gaps) > 1:
            print(f"\n⏰ TOP TIME GAPS (showing up to {max_gaps})")
            for i, gap in enumerate(analyzer.time_gaps[:max_gaps], 1):
                print(f"\n{i:2}. Gap #{i}: {gap.duration_seconds/60:.2f} minutes")
                print(f"    Lines: {gap.start_line} → {gap.end_line}")
                print(f"    Time: {gap.start_time.strftime('%H:%M:%S')} → {gap.end_time.strftime('%H:%M:%S')}")
                print(f"    Start: {gap.start_message[:80]}...")
    else:
        print(f"\n⏰ No significant time gaps found (minimum threshold: {analyzer._min_gap_seconds}s)")
    
    # Error analysis
    if analyzer.errors:
        print("\n🚨 ERROR ANALYSIS")
        
        # Count errors by type
        error_counts = {}
        for error in analyzer.errors:
            error_type = analyzer._get_error_name(error.error_type)
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        print("Error Distribution:")
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(analyzer.errors)) * 100
            print(f"  {error_type}: {count:,} ({percentage:.1f}%)")
    else:
        print("\n🚨 No errors found in log file")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    if analyzer.time_gaps:
        primary_gap = analyzer.time_gaps[0]
        if "AutoClose" in primary_gap.start_message and "Deleting AutoCloseDesc" in primary_gap.start_message:
            print("• PRIMARY ISSUE: AutoClose descriptor deletion hang detected")
            print("• Focus troubleshooting on AutoClose subsystem and descriptor file locks")
            print("• Check filesystem permissions on AutoClose metadata files")
            print("• Consider upgrading CaseWare Working Papers to latest version")
            print("• Monitor disk I/O performance during AutoClose operations")
        else:
            print(f"• Investigate the operation: {primary_gap.start_message}")
        
        if analyzer.errors:
            error_counts = {}
            for error in analyzer.errors:
                error_counts[error.error_type] = error_counts.get(error.error_type, 0) + 1
            
            most_common = max(error_counts.items(), key=lambda x: x[1])
            if most_common[0] == 'winhttp_header':
                print("• High number of WinHTTP header errors indicate server communication issues")
                print("• These are likely symptoms of the primary bottleneck, not root causes")
                print("• Focus on resolving the primary bottleneck first")
    else:
        print("• No specific performance issues detected in this log file")
        print("• Log appears to show normal operation")


if __name__ == "__main__":
    main()