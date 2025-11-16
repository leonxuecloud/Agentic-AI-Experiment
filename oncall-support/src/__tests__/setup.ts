import { vi } from 'vitest';
import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

// Global test setup
beforeAll(() => {
  // Set up test environment variables
  process.env.NODE_ENV = 'test';
  process.env.JIRA_BASE_URL = 'https://test.atlassian.net';
  process.env.JIRA_USERNAME = 'test@example.com';
  process.env.JIRA_API_TOKEN = 'test-token';
  process.env.ALLOWED_COMMANDS = '^(npm|yarn|git|ls|cat|grep|find|mkdir|rmdir|cp|mv|chmod|chown).*$';
  process.env.MAX_DOWNLOAD_SIZE = '104857600';
  process.env.LOCAL_STORAGE_DIR = './test-files';
});

afterAll(() => {
  // Clean up test environment
  vi.clearAllMocks();
});

beforeEach(() => {
  // Reset mocks before each test
  vi.clearAllMocks();
});

afterEach(() => {
  // Clean up after each test
  vi.clearAllMocks();
});
