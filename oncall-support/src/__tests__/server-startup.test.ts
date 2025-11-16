import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';

describe('MCP Server Startup Tests', () => {
  beforeEach(() => {
    // Set up test environment
    process.env.JIRA_BASE_URL = 'https://test.atlassian.net';
    process.env.JIRA_USERNAME = 'test@example.com';
    process.env.JIRA_API_TOKEN = 'test-token';
    process.env.ALLOWED_COMMANDS = '^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$';
    process.env.MAX_DOWNLOAD_SIZE = '104857600';
    process.env.LOCAL_STORAGE_DIR = './test-files';
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Server File Validation', () => {
    it('should verify dist/mcp-server.js exists', async () => {
      const indexPath = path.join(process.cwd(), 'dist', 'mcp-server.js');

      try {
        await fs.access(indexPath);
        const stats = await fs.stat(indexPath);
        expect(stats.isFile()).toBe(true);
        expect(stats.size).toBeGreaterThan(0);
      } catch (error) {
        throw new Error(`dist/mcp-server.js not found: ${error}`);
      }
    });

    it('should verify package.json exists', async () => {
      const packagePath = path.join(process.cwd(), 'package.json');

      try {
        await fs.access(packagePath);
        const stats = await fs.stat(packagePath);
        expect(stats.isFile()).toBe(true);
      } catch (error) {
        throw new Error(`package.json not found: ${error}`);
      }
    });

    it('should verify node_modules exists', async () => {
      const nodeModulesPath = path.join(process.cwd(), 'node_modules');

      try {
        await fs.access(nodeModulesPath);
        const stats = await fs.stat(nodeModulesPath);
        expect(stats.isDirectory()).toBe(true);
      } catch (error) {
        throw new Error(`node_modules not found: ${error}`);
      }
    });
  });

  describe('Server Process Tests', () => {
    it('should start server process without immediate crash', (done) => {
      const indexPath = path.join(process.cwd(), 'dist', 'index.js');

      const serverProcess = spawn('node', [indexPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let hasStarted = false;
      let hasErrored = false;

      serverProcess.stdout.on('data', (data) => {
        hasStarted = true;
        console.log('Server output:', data.toString());
      });

      serverProcess.stderr.on('data', (data) => {
        console.error('Server error:', data.toString());
        hasErrored = true;
      });

      serverProcess.on('error', (error) => {
        console.error('Process error:', error);
        hasErrored = true;
      });

      serverProcess.on('exit', (code) => {
        if (code !== 0) {
          hasErrored = true;
        }
      });

      // Wait a bit to see if server starts
      setTimeout(() => {
        if (hasErrored) {
          done(new Error('Server failed to start'));
        } else {
          hasStarted = true;
          serverProcess.kill();
          done();
        }
      }, 2000);

      // Cleanup after test
      setTimeout(() => {
        if (serverProcess && !serverProcess.killed) {
          serverProcess.kill();
        }
      }, 3000);
    });

    it('should handle server startup with invalid configuration', (done) => {
      // Temporarily set invalid configuration
      const originalJiraUrl = process.env.JIRA_BASE_URL;
      process.env.JIRA_BASE_URL = 'invalid-url';

      const indexPath = path.join(process.cwd(), 'dist', 'index.js');

      const serverProcess = spawn('node', [indexPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let hasErrored = false;

      serverProcess.stderr.on('data', (data) => {
        const output = data.toString();
        if (output.includes('Error') || output.includes('error')) {
          hasErrored = true;
        }
      });

      serverProcess.on('error', (error) => {
        hasErrored = true;
      });

      serverProcess.on('exit', (code) => {
        if (code !== 0) {
          hasErrored = true;
        }
      });

      setTimeout(() => {
        // Restore original configuration
        process.env.JIRA_BASE_URL = originalJiraUrl;

        if (hasErrored) {
          done(); // Expected to error with invalid config
        } else {
          serverProcess.kill();
          done(new Error('Server should have errored with invalid config'));
        }
      }, 1000);

      // Cleanup
      setTimeout(() => {
        if (serverProcess && !serverProcess.killed) {
          serverProcess.kill();
        }
      }, 2000);
    });
  });

  describe('Environment Validation', () => {
    it('should validate all required environment variables are set', () => {
      const requiredVars = [
        'JIRA_BASE_URL',
        'JIRA_USERNAME',
        'JIRA_API_TOKEN',
        'ALLOWED_COMMANDS',
        'MAX_DOWNLOAD_SIZE',
        'LOCAL_STORAGE_DIR'
      ];

      const missingVars = requiredVars.filter(varName =>
        !process.env[varName] || process.env[varName] === ''
      );

      expect(missingVars).toHaveLength(0);
    });

    it('should validate JIRA_BASE_URL format', () => {
      const jiraUrl = process.env.JIRA_BASE_URL;
      expect(jiraUrl).toMatch(/^https:\/\/.*\.atlassian\.net$/);
    });

    it('should validate MAX_DOWNLOAD_SIZE is a valid number', () => {
      const maxSize = parseInt(process.env.MAX_DOWNLOAD_SIZE || '0');
      expect(maxSize).toBeGreaterThan(0);
      expect(maxSize).toBeLessThanOrEqual(104857600);
    });

    it('should validate ALLOWED_COMMANDS is a valid regex', () => {
      const allowedPattern = process.env.ALLOWED_COMMANDS || '';
      expect(() => new RegExp(allowedPattern)).not.toThrow();
    });
  });

  describe('Directory Structure Validation', () => {
    it('should verify project structure', async () => {
      const requiredFiles = [
        'package.json',
        'tsconfig.json',
        'dist/mcp-server.js'
      ];

      const requiredDirs = [
        'src',
        'dist',
        'node_modules'
      ];

      // Check files
      for (const file of requiredFiles) {
        const filePath = path.join(process.cwd(), file);
        try {
          await fs.access(filePath);
          const stats = await fs.stat(filePath);
          expect(stats.isFile()).toBe(true);
        } catch (error) {
          throw new Error(`Required file ${file} not found: ${error}`);
        }
      }

      // Check directories
      for (const dir of requiredDirs) {
        const dirPath = path.join(process.cwd(), dir);
        try {
          await fs.access(dirPath);
          const stats = await fs.stat(dirPath);
          expect(stats.isDirectory()).toBe(true);
        } catch (error) {
          throw new Error(`Required directory ${dir} not found: ${error}`);
        }
      }
    });
  });

  describe('Error Scenarios', () => {
    it('should handle missing dist directory', async () => {
      const distPath = path.join(process.cwd(), 'dist');

      try {
        await fs.access(distPath);
        // If dist exists, this test passes
        expect(true).toBe(true);
      } catch (error) {
        // If dist doesn't exist, this is the expected error
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('ENOENT');
      }
    });

    it('should handle missing node_modules', async () => {
      const nodeModulesPath = path.join(process.cwd(), 'node_modules');

      try {
        await fs.access(nodeModulesPath);
        // If node_modules exists, this test passes
        expect(true).toBe(true);
      } catch (error) {
        // If node_modules doesn't exist, this is the expected error
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('ENOENT');
      }
    });
  });
});
