// Simple test to check MCP remote connection
import { connectToRemoteMcpServer, getConnectionStatus } from '../dist/tools/mcp/mcp-client-connector.js';
import * as dotenv from 'dotenv';

dotenv.config();

console.log('Testing MCP remote connection...');
console.log(`ENABLE_MCP_SERVER: ${process.env.ENABLE_MCP_SERVER}`);

await connectToRemoteMcpServer();

const status = getConnectionStatus();
console.log('\nConnection Status:');
console.log(`  Connected: ${status.connected}`);
console.log(`  Tools: ${status.toolCount}`);
console.log(`  Prompts: ${status.promptCount}`);
if (status.error) {
  console.log(`  Error: ${status.error}`);
}
