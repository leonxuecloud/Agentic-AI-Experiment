import * as fs from 'fs';
import * as path from 'path';

const MCP_CONFIG_FILENAME = 'mcp.json';

function getConfigPaths(): string[] {
    const workspaceDir = process.cwd();
    const homeDir = process.env.HOME || process.env.USERPROFILE || '';
    return [
        path.join(workspaceDir, MCP_CONFIG_FILENAME),
        homeDir ? path.join(homeDir, MCP_CONFIG_FILENAME) : ''
    ].filter(Boolean);
}

export function readMcpConfig(): any | null {
    for (const configPath of getConfigPaths()) {
        if (fs.existsSync(configPath)) {
            try {
                const raw = fs.readFileSync(configPath, 'utf-8');
                return JSON.parse(raw);
            } catch (err) {
                console.error('Failed to read MCP config:', err);
                return null;
            }
        }
    }
    return null;
}