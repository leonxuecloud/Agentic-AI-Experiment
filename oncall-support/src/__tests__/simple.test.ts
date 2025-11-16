import { describe, it, expect } from 'vitest';

describe('Oncall Support MCP Server - Simple Tests', () => {
  it('should have proper environment configuration', () => {
    expect(process.env.JIRA_BASE_URL).toBeDefined();
    expect(process.env.JIRA_USERNAME).toBeDefined();
    expect(process.env.JIRA_API_TOKEN).toBeDefined();
    expect(process.env.ALLOWED_COMMANDS).toBeDefined();
    expect(process.env.MAX_DOWNLOAD_SIZE).toBeDefined();
    expect(process.env.LOCAL_STORAGE_DIR).toBeDefined();
  });

  it('should validate environment variables', () => {
    const requiredVars = [
      'JIRA_BASE_URL',
      'JIRA_USERNAME',
      'JIRA_API_TOKEN',
      'ALLOWED_COMMANDS',
      'MAX_DOWNLOAD_SIZE',
      'LOCAL_STORAGE_DIR'
    ];

    requiredVars.forEach(varName => {
      expect(process.env[varName]).toBeDefined();
      expect(process.env[varName]).not.toBe('');
    });
  });

  it('should have valid configuration values', () => {
    // Test JIRA_BASE_URL format
    expect(process.env.JIRA_BASE_URL).toMatch(/^https:\/\/.*\.atlassian\.net$/);

    // Test MAX_DOWNLOAD_SIZE is a number
    const maxSize = parseInt(process.env.MAX_DOWNLOAD_SIZE || '0');
    expect(maxSize).toBeGreaterThan(0);
    expect(maxSize).toBeLessThanOrEqual(104857600); // 100MB max

    // Test ALLOWED_COMMANDS is a valid regex
    const allowedPattern = process.env.ALLOWED_COMMANDS || '';
    expect(() => new RegExp(allowedPattern)).not.toThrow();
  });

  it('should have proper security settings', () => {
    const allowedCommands = process.env.ALLOWED_COMMANDS || '';
    const regex = new RegExp(allowedCommands);

    // Test that dangerous commands are blocked
    expect(regex.test('rm -rf /')).toBe(false);
    expect(regex.test('curl http://malicious-site.com')).toBe(false);
    expect(regex.test('wget http://malicious-site.com')).toBe(false);

    // Test that safe commands are allowed
    expect(regex.test('npm --version')).toBe(true);
    expect(regex.test('ls -la')).toBe(true);
    expect(regex.test('cat file.txt')).toBe(true);
  });
});
