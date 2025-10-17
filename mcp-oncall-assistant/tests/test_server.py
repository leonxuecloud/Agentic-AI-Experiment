#!/usr/bin/env python3
"""
Test script for the enhanced MCP server with toolkit integration
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from server import mcp

async def test_server_tools():
    """Test that all tools are properly registered"""
    print("🧪 Testing MCP Server Tool Registration")
    print("=" * 50)
    
    try:
        # Get registered tools
        tools_result = await mcp.list_tools()
        tools = [tool.name for tool in tools_result]
        
        print(f"✅ Total tools registered: {len(tools)}")
        print("\n📋 Registered Tools:")
        
        # Group tools by category
        jira_tools = [t for t in tools if t.startswith('jira_')]
        caseware_tools = [t for t in tools if t.startswith('caseware_')]
        wplog_tools = [t for t in tools if t.startswith('wplog_')]
        
        print(f"\n🔧 JIRA Tools ({len(jira_tools)}):")
        for tool in jira_tools:
            print(f"  - {tool}")
        
        print(f"\n📁 CaseWare Tools ({len(caseware_tools)}):")
        for tool in caseware_tools:
            print(f"  - {tool}")
        
        print(f"\n📊 WPLog Tools ({len(wplog_tools)}):")
        for tool in wplog_tools:
            print(f"  - {tool}")
        
        print(f"\n✨ Server is ready with {len(tools)} tools!")
        return True, tools_result
    except Exception as e:
        print(f"❌ Error listing tools: {e}")
        return False, []

async def test_tool_help(tools_result):
    """Test getting help information for tools"""
    print("\n🔍 Testing Tool Documentation")
    print("=" * 50)
    
    # Test a few key tools
    test_tools = ['caseware_extract_file', 'wplog_analyze_file', 'jira_create_issue']
    
    for tool_info in tools_result:
        if tool_info.name in test_tools:
            print(f"\n📖 {tool_info.name}:")
            print(f"  Description: {getattr(tool_info, 'description', 'No description')[:100]}...")

async def main():
    try:
        success, tools_result = await test_server_tools()
        if success:
            await test_tool_help(tools_result)
            print("\n🎉 All tests passed! Your MCP server is ready to use.")
        else:
            print("\n❌ Server setup incomplete.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error testing server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())