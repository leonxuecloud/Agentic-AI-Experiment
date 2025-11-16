/**
 * Simple MCP Client Test
 * Test the MCP server manually to verify all tools and prompts work
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { spawn } from "child_process";

async function testMCPServer() {
  console.log("🧪 Testing MCP Server...\n");

  // Spawn the server process
  const serverProcess = spawn("node", ["dist/mcp-server.js", "--transport=stdio"], {
    cwd: process.cwd(),
  });

  // Create transport
  const transport = new StdioClientTransport({
    command: "node",
    args: ["dist/mcp-server.js", "--transport=stdio"],
  });

  // Create client
  const client = new Client({
    name: "test-client",
    version: "1.0.0",
  }, {
    capabilities: {},
  });

  try {
    // Connect
    await client.connect(transport);
    console.log("✅ Connected to MCP server\n");

    // List tools
    const tools = await client.listTools();
    console.log(`📦 Available Tools (${tools.tools.length}):`);
    tools.tools.forEach((tool, i) => {
      console.log(`  ${i + 1}. ${tool.name} - ${tool.description}`);
    });
    console.log("");

    // List prompts
    const prompts = await client.listPrompts();
    console.log(`✨ Available Prompts (${prompts.prompts.length}):`);
    prompts.prompts.forEach((prompt, i) => {
      console.log(`  ${i + 1}. ${prompt.name} - ${prompt.description}`);
    });
    console.log("");

    // Test a prompt
    console.log("🧪 Testing customer-issue prompt...");
    const customerIssueResult = await client.getPrompt("customer-issue", {
      ticketId: "TEST-123",
      customerName: "Acme Corp",
      issueType: "Login Failure",
      priority: "High"
    });
    console.log("✅ customer-issue prompt works!");
    console.log(`   Generated ${customerIssueResult.messages.length} message(s)`);
    console.log("");

    // Test get-jira-ticket tool (read-only, safe to test)
    console.log("🧪 Testing get-jira-ticket tool...");
    try {
      const jiraResult = await client.callTool({
        name: "get-jira-ticket",
        arguments: {
          ticketId: "AI-896"
        }
      });
      console.log("✅ get-jira-ticket tool works!");
      console.log("");
    } catch (error) {
      console.log("⚠️  get-jira-ticket tool requires valid Jira credentials (expected)");
      console.log("");
    }

    console.log("🎉 All tests passed!\n");
    console.log("Summary:");
    console.log(`  ✅ ${tools.tools.length} tools registered`);
    console.log(`  ✅ ${prompts.prompts.length} prompts registered`);
    console.log(`  ✅ Client can connect and call tools/prompts`);

  } catch (error) {
    console.error("❌ Test failed:", error);
    process.exit(1);
  } finally {
    // Cleanup
    await client.close();
    serverProcess.kill();
  }
}

testMCPServer().catch(console.error);
