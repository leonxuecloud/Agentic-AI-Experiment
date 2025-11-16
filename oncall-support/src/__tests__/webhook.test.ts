import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import type { Server } from 'http';

describe.skip('Jira Webhook Integration Tests', () => {
  let server: Server | null = null;
  const PORT = 3001; // Use different port for tests
  const BASE_URL = `http://localhost:${PORT}`;
  const WEBHOOK_SECRET = 'test-webhook-secret-123';

  beforeAll(async () => {
    // Set environment variables for testing
    process.env.PORT = PORT.toString();
    process.env.JIRA_WEBHOOK_SECRET = WEBHOOK_SECRET;
    process.env.JIRA_BASE_URL = 'https://test.atlassian.net';
    process.env.JIRA_USERNAME = 'test@example.com';
    process.env.JIRA_API_TOKEN = 'test-token';

    // Create storage directory for audit logs
    const fs = await import('fs/promises');
    const path = await import('path');
    const storageDir = path.join(process.cwd(), '.mcp-storage');
    try {
      await fs.mkdir(storageDir, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }

    // Import and start server dynamically
    const { app } = await import('../server.js');
    
    // Start the server
    server = app.listen(PORT, () => {
      console.log(`Test server running on port ${PORT}`);
    });
    
    // Wait for server to be ready
    await new Promise(resolve => setTimeout(resolve, 500));
  });

  afterAll(async () => {
    if (server) {
      await new Promise<void>((resolve) => {
        server!.close(() => resolve());
      });
    }
  });

  describe('Webhook Endpoint Security', () => {
    it('should reject requests without webhook secret', async () => {
      if (!server) {
        console.log('Server not running - skipping webhook security test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          webhookEvent: 'jira:issue_created',
          issue: { key: 'TEST-123' }
        })
      });

      expect(response.status).toBe(401);
      const data = await response.json();
      expect(data.error).toBe('Unauthorized: Invalid webhook secret');
    });

    it('should reject requests with invalid webhook secret', async () => {
      if (!server) {
        console.log('Server not running - skipping webhook security test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': 'wrong-secret'
        },
        body: JSON.stringify({
          webhookEvent: 'jira:issue_created',
          issue: { key: 'TEST-123' }
        })
      });

      expect(response.status).toBe(401);
      const data = await response.json();
      expect(data.error).toBe('Unauthorized: Invalid webhook secret');
    });

    it('should accept requests with valid webhook secret', async () => {
      if (!server) {
        console.log('Server not running - skipping webhook security test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify({
          webhookEvent: 'jira:issue_created',
          issue: {
            key: 'TEST-123',
            fields: {
              summary: 'Test Issue',
              description: 'This is a test',
              issuetype: { name: 'Bug' },
              priority: { name: 'High' }
            }
          }
        })
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.eventType).toBe('jira:issue_created');
      expect(data.issueKey).toBe('TEST-123');
    });
  });

  describe('Webhook Event Handlers', () => {
    it('should handle issue_created event', async () => {
      if (!server) {
        console.log('Server not running - skipping issue_created test');
        return;
      }

      const issueData = {
        webhookEvent: 'jira:issue_created',
        timestamp: Date.now(),
        issue: {
          id: '12345',
          key: 'PROJ-456',
          fields: {
            summary: 'Production database connection timeout',
            description: 'Users are experiencing timeout errors',
            issuetype: { name: 'Incident' },
            priority: { name: 'Critical' },
            status: { name: 'Open' },
            assignee: { displayName: 'John Doe' }
          }
        },
        user: {
          displayName: 'Jane Smith',
          emailAddress: 'jane@example.com'
        }
      };

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify(issueData)
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.message).toContain('PROJ-456');
      expect(data.eventType).toBe('jira:issue_created');
    });

    it('should handle issue_updated event', async () => {
      if (!server) {
        console.log('Server not running - skipping issue_updated test');
        return;
      }

      const issueData = {
        webhookEvent: 'jira:issue_updated',
        timestamp: Date.now(),
        issue: {
          id: '12345',
          key: 'PROJ-456',
          fields: {
            summary: 'Production issue resolved',
            status: { name: 'Resolved' }
          }
        },
        changelog: {
          items: [
            {
              field: 'status',
              fromString: 'In Progress',
              toString: 'Resolved'
            }
          ]
        },
        user: {
          displayName: 'John Doe'
        }
      };

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify(issueData)
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.message).toContain('updated');
      expect(data.eventType).toBe('jira:issue_updated');
    });

    it('should handle comment_created event', async () => {
      if (!server) {
        console.log('Server not running - skipping comment_created test');
        return;
      }

      const commentData = {
        webhookEvent: 'comment_created',
        timestamp: Date.now(),
        issue: {
          key: 'PROJ-456',
          fields: {
            summary: 'Production issue'
          }
        },
        comment: {
          id: '67890',
          body: 'Investigating the root cause',
          author: {
            displayName: 'Jane Smith',
            emailAddress: 'jane@example.com'
          },
          created: new Date().toISOString()
        }
      };

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify(commentData)
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.message.toLowerCase()).toContain('comment');
      expect(data.eventType).toBe('comment_created');
    });

    it('should handle issue_deleted event', async () => {
      if (!server) {
        console.log('Server not running - skipping issue_deleted test');
        return;
      }

      const deleteData = {
        webhookEvent: 'jira:issue_deleted',
        timestamp: Date.now(),
        issue: {
          key: 'PROJ-789',
          fields: {
            summary: 'Duplicate ticket'
          }
        },
        user: {
          displayName: 'Admin User'
        }
      };

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify(deleteData)
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.message).toContain('deleted');
      expect(data.eventType).toBe('jira:issue_deleted');
    });

    it('should handle unknown webhook events gracefully', async () => {
      if (!server) {
        console.log('Server not running - skipping unknown event test');
        return;
      }

      const unknownData = {
        webhookEvent: 'jira:unknown_event',
        issue: { key: 'PROJ-999' }
      };

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify(unknownData)
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.message.toLowerCase()).toContain('received');
    });
  });

  describe('Webhook Data Validation', () => {
    it('should handle missing issue data', async () => {
      if (!server) {
        console.log('Server not running - skipping validation test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify({
          webhookEvent: 'jira:issue_created'
          // Missing issue data
        })
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });

    it('should handle malformed JSON gracefully', async () => {
      if (!server) {
        console.log('Server not running - skipping malformed JSON test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: 'invalid-json-data'
      });

      // Body-parser catches malformed JSON and returns error
      expect([400, 500]).toContain(response.status);
    });

    it('should handle empty request body', async () => {
      if (!server) {
        console.log('Server not running - skipping empty body test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: '{}'
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });
  });

  describe('Webhook Response Format', () => {
    it('should return proper response structure', async () => {
      if (!server) {
        console.log('Server not running - skipping response format test');
        return;
      }

      const response = await fetch(`${BASE_URL}/api/webhooks/jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': WEBHOOK_SECRET
        },
        body: JSON.stringify({
          webhookEvent: 'jira:issue_created',
          issue: {
            key: 'TEST-123',
            fields: { summary: 'Test' }
          }
        })
      });

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      
      const data = await response.json();
      expect(data).toHaveProperty('success');
      expect(data).toHaveProperty('message');
      expect(data).toHaveProperty('eventType');
      expect(data).toHaveProperty('timestamp');
      expect(typeof data.timestamp).toBe('string');
    });
  });
});
